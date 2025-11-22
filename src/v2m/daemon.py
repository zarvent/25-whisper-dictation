import asyncio
import json
import signal
import sys
from pathlib import Path
from typing import Callable, Dict, Any, Optional

from v2m.core.logging import logger
from v2m.core.rpc import SOCKET_PATH, JsonRpcRequest, JsonRpcResponse, parse_request, create_response, create_error_response
from v2m.core.di.container import container
from v2m.application.commands import StartRecordingCommand, StopRecordingCommand, ProcessTextCommand, SmartCaptureCommand

class Daemon:
    """
    daemon principal del sistema v2m gestiona las conexiones rpc y orquesta los comandos

    responsabilidades
    - iniciar y detener el servidor rpc sobre unix socket
    - recibir mensajes json-rpc parsearlos y despacharlos
    - mantener el ciclo de vida de la aplicación

    atributos
    - running (bool): estado de ejecución del daemon
    - socket_path (path): ruta al archivo del socket unix
    - command_bus: bus de comandos para enviar acciones a la capa de aplicación
    - methods (dict): mapa de nombres de métodos rpc a funciones del daemon
    """
    def __init__(self):
        self.running = False
        self.socket_path = Path(SOCKET_PATH)
        self.command_bus = container.get_command_bus()
        self.methods: Dict[str, Callable] = {
            "ping": self.ping,
            "start_capture": self.start_capture,
            "stop_capture": self.stop_capture,
            "transcribe": self.transcribe,
            "get_status": self.get_status,
            "shutdown": self.shutdown_rpc
        }

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        maneja una conexión entrante de un cliente rpc

        lee los datos del socket los decodifica y procesa la petición rpc
        finalmente envía la respuesta de vuelta y cierra la conexión
        """
        try:
            data = await reader.read(4096)
            if not data:
                return

            message = data.decode().strip()
            logger.debug(f"Received RPC message: {message}")

            request = parse_request(message)

            if isinstance(request, JsonRpcResponse): # It's an error response from parser
                response = request
            else:
                response = await self.dispatch(request)

            response_str = response.model_dump_json()
            writer.write(response_str.encode())
            await writer.drain()

        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            writer.close()
            # await writer.wait_closed() # Sometimes causes issues if already closed

    async def dispatch(self, request: JsonRpcRequest) -> JsonRpcResponse:
        """
        enruta la petición rpc al método correspondiente

        verifica si el método existe en `self.methods` y lo ejecuta con los parámetros provistos
        retorna una respuesta rpc exitosa o de error
        """
        if request.method not in self.methods:
            return create_error_response(request.id, -32601, "Method not found")

        try:
            method = self.methods[request.method]
            # Handle params if needed, for now assuming simple methods or dict params
            params = request.params or {}

            if isinstance(params, list):
                result = await method(*params)
            elif isinstance(params, dict):
                result = await method(**params)
            else:
                result = await method()

            return create_response(request.id, result)
        except Exception as e:
            logger.error(f"Error executing method {request.method}: {e}")
            return create_error_response(request.id, -32000, str(e))

    # --- RPC Methods ---

    async def ping(self):
        """responde con 'pong' para verificar conectividad"""
        return "pong"

    async def start_capture(self):
        """inicia el proceso de grabación de audio enviando un comando al bus"""
        await self.command_bus.dispatch(StartRecordingCommand())
        return "started"

    async def stop_capture(self):
        """
        detiene la grabación y retorna el texto transcrito
        el comando stoprecordingcommand ahora retorna el resultado de la transcripción
        """
        # StopRecordingCommand now returns the transcription text
        text = await self.command_bus.dispatch(StopRecordingCommand())
        return {"text": text}

    async def transcribe(self, use_llm: bool = True):
        """
        orquesta el flujo completo de transcripción
        1 intenta detener una grabación en curso
        2 si no hay grabación inicia una captura inteligente (smart batching)
        3 opcionalmente procesa el texto con un LLM
        """
        # Check if recording is active by trying to stop it
        try:
            text = await self.command_bus.dispatch(StopRecordingCommand())
        except Exception:
            # If error (e.g. not recording), assume we want to start a smart capture
            text = ""

        if not text:
            # Start smart batching (VAD loop)
            text = await self.command_bus.dispatch(SmartCaptureCommand())

        if use_llm and text:
            # Process with LLM
            refined_text = await self.command_bus.dispatch(ProcessTextCommand(text))
            return {"text": refined_text, "original": text}

        return {"text": text}

    async def get_status(self):
        """retorna el estado actual del daemon (mock)"""
        # TODO: Implement real status check
        return {"running": True, "recording": False} # Mock for now

    async def shutdown_rpc(self):
        """inicia el apagado controlado del daemon"""
        self.running = False
        asyncio.create_task(self.stop_later())
        return "shutting_down"

    async def stop_later(self):
        """helper para detener el daemon después de un breve delay permitiendo enviar la respuesta rpc"""
        await asyncio.sleep(0.1)
        self.stop()

    # --- Server Lifecycle ---

    async def start_server(self):
        """
        inicializa el servidor unix socket
        verifica si el socket ya existe (daemon corriendo) y maneja la limpieza si es un socket huérfano
        """
        if self.socket_path.exists():
            try:
                reader, writer = await asyncio.open_unix_connection(str(self.socket_path))
                writer.close()
                await writer.wait_closed()
                logger.error("Daemon is already running.")
                sys.exit(1)
            except (ConnectionRefusedError, FileNotFoundError):
                self.socket_path.unlink()

        server = await asyncio.start_unix_server(self.handle_client, str(self.socket_path))
        logger.info(f"Daemon listening on {self.socket_path}")

        self.running = True
        async with server:
            await server.serve_forever()

    def stop(self):
        """detiene el daemon y limpia el archivo del socket"""
        logger.info("Stopping daemon...")
        if self.socket_path.exists():
            self.socket_path.unlink()
        sys.exit(0)

    def run(self):
        """punto de entrada para ejecutar el daemon maneja el loop de eventos y señales"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        def signal_handler():
            logger.info("Signal received, shutting down...")
            # We can't await here, so we just exit or set a flag
            # But serve_forever blocks.
            # Best way is to raise KeyboardInterrupt or cancel tasks.
            # For simplicity in this script:
            sys.exit(0)

        # loop.add_signal_handler(signal.SIGINT, signal_handler)
        # loop.add_signal_handler(signal.SIGTERM, signal_handler)

        try:
            loop.run_until_complete(self.start_server())
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

if __name__ == "__main__":
    daemon = Daemon()
    daemon.run()
