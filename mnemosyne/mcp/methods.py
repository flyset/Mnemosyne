from typing import Any

from fastapi.responses import JSONResponse

from mnemosyne.mcp.messages import MCPMessage, parse_message
from mnemosyne.mcp.protocol import mcp_error, mcp_result
from mnemosyne.mcp.tools import TOOLS, call_tool
from mnemosyne.settings import PROTOCOL_VERSION, SERVER_NAME, SERVER_VERSION


def handle_message(message: Any) -> JSONResponse | None:
    if not isinstance(message, dict):
        return mcp_error(None, -32600, "Invalid Request")

    parsed_message = parse_message(message)
    if parsed_message.is_notification:
        return None

    if not parsed_message.params_valid:
        return mcp_error(parsed_message.request_id, -32602, "Invalid params")

    handler = METHOD_HANDLERS.get(parsed_message.method)

    if handler is None:
        return mcp_error(
            parsed_message.request_id,
            -32601,
            f"Unknown method: {parsed_message.method}",
        )

    return handler(parsed_message)


def handle_initialize(message: MCPMessage) -> JSONResponse:
    return mcp_result(
        message.request_id,
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


def handle_initialized(message: MCPMessage) -> JSONResponse:
    return mcp_result(message.request_id, {})


def handle_ping(message: MCPMessage) -> JSONResponse:
    return mcp_result(message.request_id, {})


def handle_tools_list(message: MCPMessage) -> JSONResponse:
    return mcp_result(message.request_id, {"tools": TOOLS})


def handle_tools_call(message: MCPMessage) -> JSONResponse:
    tool_name = message.params.get("name")
    arguments = message.params.get("arguments", {})
    if not isinstance(arguments, dict):
        return mcp_error(message.request_id, -32602, "Invalid params")

    tool_result = call_tool(tool_name, arguments)
    if tool_result is not None:
        return mcp_result(message.request_id, tool_result)

    return mcp_error(message.request_id, -32602, f"Unknown tool: {tool_name}")


METHOD_HANDLERS = {
    "initialize": handle_initialize,
    "notifications/initialized": handle_initialized,
    "ping": handle_ping,
    "tools/list": handle_tools_list,
    "tools/call": handle_tools_call,
}
