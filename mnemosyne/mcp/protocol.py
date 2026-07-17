from typing import Any

from fastapi.responses import JSONResponse


def mcp_result(request_id: Any, result: dict[str, Any]) -> JSONResponse:
    response = {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    }
    return JSONResponse(
        response
    )


def mcp_error(request_id: Any, code: int, message: str) -> JSONResponse:
    response = {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message,
        },
    }
    return JSONResponse(
        response
    )
