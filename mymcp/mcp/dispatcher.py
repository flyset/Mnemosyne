from dataclasses import dataclass
from typing import Any, Protocol

from mymcp.mcp.messages import parse_message
from mymcp.mcp.protocol import mcp_error, mcp_result
from mymcp.mcp.tool_registry import ToolRegistry
from mymcp.settings import PROTOCOL_VERSION, SERVER_NAME, SERVER_VERSION


class RuntimeLike(Protocol):
    @property
    def registry(self) -> ToolRegistry: ...


@dataclass(frozen=True, init=False)
class MCPDispatcher:
    _registry: ToolRegistry

    def __init__(self, runtime: RuntimeLike) -> None:
        registry = runtime.registry
        if not isinstance(registry, ToolRegistry):
            raise ValueError("invalid MCP runtime")
        object.__setattr__(self, "_registry", registry)

    def dispatch(self, message: Any) -> dict[str, Any] | None:
        if not isinstance(message, dict):
            return mcp_error(None, -32600, "Invalid Request")

        parsed_message = parse_message(message)
        if parsed_message.is_notification:
            return None
        if not parsed_message.params_valid:
            return mcp_error(parsed_message.request_id, -32602, "Invalid params")

        if parsed_message.method == "initialize":
            return mcp_result(
                parsed_message.request_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION,
                    },
                },
            )
        if parsed_message.method in {"notifications/initialized", "ping"}:
            return mcp_result(parsed_message.request_id, {})
        if parsed_message.method == "tools/list":
            return mcp_result(
                parsed_message.request_id,
                {"tools": list(self._registry.tools)},
            )
        if parsed_message.method == "tools/call":
            tool_name = parsed_message.params.get("name")
            arguments = parsed_message.params.get("arguments", {})
            if not isinstance(arguments, dict):
                return mcp_error(
                    parsed_message.request_id,
                    -32602,
                    "Invalid params",
                )
            tool_result = self._registry.call_tool(tool_name, arguments)
            if tool_result is not None:
                return mcp_result(parsed_message.request_id, tool_result)
            return mcp_error(
                parsed_message.request_id,
                -32602,
                f"Unknown tool: {tool_name}",
            )
        return mcp_error(
            parsed_message.request_id,
            -32601,
            f"Unknown method: {parsed_message.method}",
        )
