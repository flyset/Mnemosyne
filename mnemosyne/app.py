import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

app = FastAPI(title="Mnemosyne MCP Server")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp")


TOOLS = [
    {
        "name": "hello",
        "description": "Returns a greeting for the given name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name to greet.",
                }
            },
            "required": ["name"],
        },
    },
    {
        "name": "list_tools",
        "description": "Returns the list of tools exposed by this MCP server.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    }
]


@app.get("/mcp")
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


@app.post("/mcp")
async def mcp_endpoint(request: Request) -> JSONResponse:
    message = await request.json()
    logger.info("REQUEST %s", json.dumps(message, indent=2))

    method = message.get("method")
    request_id = message.get("id")
    params: dict[str, Any] = message.get("params", {})

    if method == "initialize":
        return mcp_result(
            request_id,
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "mnemosyne",
                    "version": "0.1.0",
                },
            },
        )

    if method == "notifications/initialized":
        return mcp_result(request_id, {})

    if method == "ping":
        return mcp_result(request_id, {})

    if method == "tools/list":
        return mcp_result(request_id, {"tools": TOOLS})

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "hello":
            name = arguments.get("name", "world")
            return mcp_result(
                request_id,
                {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Hello, {name}!",
                        }
                    ]
                },
            )

        if tool_name == "list_tools":
            tool_names = [tool["name"] for tool in TOOLS]
            return mcp_result(
                request_id,
                {
                    "content": [
                        {
                            "type": "text",
                            "text": "Available tools: " + ", ".join(tool_names),
                        }
                    ]
                },
            )

        return mcp_error(request_id, -32602, f"Unknown tool: {tool_name}")

    return mcp_error(request_id, -32601, f"Unknown method: {method}")


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
