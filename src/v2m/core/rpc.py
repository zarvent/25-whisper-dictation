import json
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ValidationError

SOCKET_PATH = "/tmp/v2m.sock"

class JsonRpcRequest(BaseModel):
    jsonrpc: str = Field("2.0", pattern="^2.0$")
    method: str
    params: Optional[Union[Dict[str, Any], List[Any]]] = None
    id: Optional[Union[str, int]] = None

class JsonRpcError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None

class JsonRpcResponse(BaseModel):
    jsonrpc: str = Field("2.0", pattern="^2.0$")
    result: Optional[Any] = None
    error: Optional[JsonRpcError] = None
    id: Optional[Union[str, int]] = None

    def is_error(self) -> bool:
        return self.error is not None

def parse_request(data: str) -> Union[JsonRpcRequest, JsonRpcError]:
    try:
        parsed = json.loads(data)
        return JsonRpcRequest(**parsed)
    except json.JSONDecodeError:
        return JsonRpcError(code=-32700, message="Parse error")
    except ValidationError as e:
        return JsonRpcError(code=-32600, message="Invalid Request", data=str(e))

def create_response(req_id: Optional[Union[str, int]], result: Any = None, error: Optional[JsonRpcError] = None) -> JsonRpcResponse:
    return JsonRpcResponse(id=req_id, result=result, error=error)

def create_error_response(req_id: Optional[Union[str, int]], code: int, message: str, data: Optional[Any] = None) -> JsonRpcResponse:
    return JsonRpcResponse(id=req_id, error=JsonRpcError(code=code, message=message, data=data))
