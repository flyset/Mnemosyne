import asyncio
import json
import logging
from time import perf_counter
from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from mnemosyne.mcp.methods import handle_message

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp")


@router.get("/mcp")
async def mcp_stream() -> StreamingResponse:
    async def event_stream() -> AsyncIterator[str]:
        while True:
            yield ": keep-alive\n\n"
            await asyncio.sleep(15)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/mcp")
async def mcp_endpoint(request: Request) -> JSONResponse:
    message = await request.json()
    request_id = message.get("id") if isinstance(message, dict) else None
    method = message.get("method") if isinstance(message, dict) else None
    is_notification = isinstance(message, dict) and "id" not in message
    if not is_notification:
        logger.info("request id=%s method=%s", request_id, method)

    started_at = perf_counter()
    response = handle_message(message)
    duration_ms = round((perf_counter() - started_at) * 1000)
    if response is None:
        logger.debug("notification method=%s duration_ms=%s", method, duration_ms)
        return Response(status_code=202)

    response_body = json.loads(response.body)

    if "error" in response_body:
        logger.warning(
            "response id=%s method=%s outcome=error code=%s duration_ms=%s",
            request_id,
            method,
            response_body["error"]["code"],
            duration_ms,
        )
    else:
        logger.info(
            "response id=%s method=%s outcome=ok duration_ms=%s",
            request_id,
            method,
            duration_ms,
        )

    return response
