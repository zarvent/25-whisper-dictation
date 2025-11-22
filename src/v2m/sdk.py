import asyncio
import json
import logging
from typing import Any, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from v2m.core.rpc import JsonRpcRequest, JsonRpcResponse, SOCKET_PATH

logger = logging.getLogger(__name__)

class V2MClient:
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
        """Check connection to daemon."""
        try:
            pong = await self._send_request("ping")
            return pong == "pong"
        except Exception:
            return False

    async def start_capture(self):
        return await self._send_request("start_capture")

    async def stop_capture(self):
        return await self._send_request("stop_capture")

    async def get_status(self):
        return await self._send_request("get_status")

    async def transcribe(self, use_llm: bool = True):
        # This might be a command to trigger transcription of buffered audio or similar
        # Depending on how the daemon works. For now, following the plan.
        return await self._send_request("transcribe", {"use_llm": use_llm})
