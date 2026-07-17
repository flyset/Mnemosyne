from typing import Any

from mnemosyne.mcp.tools import list_tools

TOOLS = [list_tools.TOOL]

TOOL_HANDLERS = {
    list_tools.TOOL["name"]: lambda arguments: list_tools.handle(arguments, TOOLS),
}


def call_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any] | None:
    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return None

    return handler(arguments)
