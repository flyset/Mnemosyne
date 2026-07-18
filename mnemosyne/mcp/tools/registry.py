from typing import Any

from mnemosyne.mcp.tools import list_tools, memory_recall

TOOLS = [list_tools.TOOL, memory_recall.TOOL]

TOOL_HANDLERS = {
    list_tools.TOOL["name"]: lambda arguments: list_tools.handle(arguments, TOOLS),
    memory_recall.TOOL["name"]: memory_recall.handle,
}


def call_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any] | None:
    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return None

    return handler(arguments)
