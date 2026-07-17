import asyncio
import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

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
    logger.info("REQUEST %s", json.dumps(message, indent=2))
    return handle_message(message)
