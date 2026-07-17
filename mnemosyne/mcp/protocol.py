import json
import logging
from typing import Any

from fastapi.responses import JSONResponse

logger = logging.getLogger("mcp")


def mcp_result(request_id: Any, result: dict[str, Any]) -> JSONResponse:
    response = {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    }
    logger.info("RESPONSE %s", json.dumps(response, indent=2))
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
    logger.info("ERROR %s", json.dumps(response, indent=2))
    return JSONResponse(
        response
    )
