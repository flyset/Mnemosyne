from typing import Any

from fastapi.responses import JSONResponse

from mnemosyne.mcp.protocol import mcp_error, mcp_result
from mnemosyne.mcp.tools import TOOLS, call_tool
from mnemosyne.settings import PROTOCOL_VERSION, SERVER_NAME, SERVER_VERSION


def handle_message(message: dict[str, Any]) -> JSONResponse:
    method = message.get("method")
    request_id = message.get("id")
    params: dict[str, Any] = message.get("params", {})

    if method == "initialize":
        return mcp_result(
            request_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": SERVER_NAME,
                    "version": SERVER_VERSION,
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

        tool_result = call_tool(tool_name, arguments)
        if tool_result is not None:
            return mcp_result(request_id, tool_result)

        return mcp_error(request_id, -32602, f"Unknown tool: {tool_name}")

    return mcp_error(request_id, -32601, f"Unknown method: {method}")
