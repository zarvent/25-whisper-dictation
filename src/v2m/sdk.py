import asyncio
import json
import logging
from typing import Any, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from v2m.core.rpc import JsonRpcRequest, JsonRpcResponse, SOCKET_PATH

logger = logging.getLogger(__name__)

class V2MClient:
    """
    cliente para interactuar con el daemon de v2m mediante rpc

    encapsula la comunicación por unix socket y maneja la reconexión automática
    utiliza la librería `tenacity` para reintentar operaciones fallidas en caso de desconexión

    atributos
    - socket_path (str): ruta al archivo del socket unix del daemon
    - _request_id (int): contador para identificar las peticiones rpc
    """
    def __init__(self, socket_path: str = SOCKET_PATH):
        self.socket_path = socket_path
        self._request_id = 0

    @retry(
        stop=stop_after_attempt(10),
        wait=wait_fixed(0.5),
        retry=retry_if_exception_type((ConnectionRefusedError, FileNotFoundError, ConnectionError)),
        reraise=True
    )
    async def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        envía una petición rpc al daemon y espera la respuesta

        esta función es resiliente a fallos de conexión realizando reintentos automáticos
        serializa la petición a json y deserializa la respuesta

        args
        - method (str): nombre del método rpc a invocar
        - params (dict opcional): parámetros para el método

        returns
        - any: el resultado de la ejecución remota

        raises
        - ConnectionError: si no se puede conectar al daemon tras los reintentos
        - RuntimeError: si el daemon retorna un error rpc
        """
        self._request_id += 1
        request = JsonRpcRequest(method=method, params=params, id=self._request_id)

        try:
            reader, writer = await asyncio.open_unix_connection(self.socket_path)
        except (FileNotFoundError, ConnectionRefusedError) as e:
            logger.error(f"Could not connect to daemon at {self.socket_path}: {e}")
            raise ConnectionError(f"Could not connect to daemon: {e}")

        try:
            message = request.model_dump_json()
            writer.write(message.encode())
            await writer.drain()

            data = await reader.read(4096) # Adjust buffer size if needed
            response_text = data.decode()

            if not response_text:
                raise ConnectionError("Empty response from daemon")

            try:
                response_dict = json.loads(response_text)
                response = JsonRpcResponse(**response_dict)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON response: {response_text}")
            except Exception as e:
                raise ValueError(f"Invalid RPC response structure: {e}")

            if response.error:
                raise RuntimeError(f"RPC Error {response.error.code}: {response.error.message} - {response.error.data}")

            return response.result

        finally:
            writer.close()
            await writer.wait_closed()

    async def connect(self) -> bool:
        """verifica la conectividad con el daemon enviando un ping"""
        try:
            pong = await self._send_request("ping")
            return pong == "pong"
        except Exception:
            return False

    async def start_capture(self):
        """solicita al daemon iniciar la captura de audio"""
        return await self._send_request("start_capture")

    async def stop_capture(self):
        """solicita al daemon detener la captura y retornar la transcripción"""
        return await self._send_request("stop_capture")

    async def get_status(self):
        """consulta el estado actual del daemon"""
        return await self._send_request("get_status")

    async def transcribe(self, use_llm: bool = True):
        """
        solicita al daemon realizar una transcripción
        puede desencadenar una grabación inteligente si no hay una activa
        """
        # This might be a command to trigger transcription of buffered audio or similar
        # Depending on how the daemon works. For now, following the plan.
        return await self._send_request("transcribe", {"use_llm": use_llm})
