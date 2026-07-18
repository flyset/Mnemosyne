from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from mnemosyne.mcp.tools import (
    list_tools,
    memory_inspect,
    memory_recall,
    memory_remember,
)
from mnemosyne.settings import get_memory_remember_enabled

ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class ToolRegistry:
    tools: tuple[dict[str, Any], ...]
    handlers: Mapping[str, ToolHandler]

    def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any] | None:
        handler = self.handlers.get(tool_name)
        if handler is None:
            return None
        return handler(arguments)


def build_tool_registry(
    memory_remember_enabled: bool,
    *,
    memory_inspect_tool: dict[str, Any] | None = None,
    memory_inspect_handler: ToolHandler | None = None,
    memory_remember_tool: dict[str, Any] | None = None,
    memory_remember_handler: ToolHandler | None = None,
) -> ToolRegistry:
    tools = [list_tools.TOOL, memory_recall.TOOL]
    handlers: dict[str, ToolHandler] = {
        memory_recall.TOOL["name"]: memory_recall.handle,
    }

    if (memory_inspect_tool is None) != (memory_inspect_handler is None):
        raise ValueError("memory inspect registration is unavailable")
    if memory_inspect_tool is not None and memory_inspect_handler is not None:
        tools.append(memory_inspect_tool)
        handlers[memory_inspect_tool["name"]] = memory_inspect_handler

    if memory_remember_enabled:
        if memory_remember_tool is None or memory_remember_handler is None:
            raise ValueError("memory remember registration is unavailable")
        tools.append(memory_remember_tool)
        handlers[memory_remember_tool["name"]] = memory_remember_handler

    selected_tools = tuple(tools)
    handlers[list_tools.TOOL["name"]] = lambda arguments: list_tools.handle(
        arguments,
        selected_tools,
    )
    return ToolRegistry(
        tools=selected_tools,
        handlers=MappingProxyType(handlers),
    )


def build_startup_tool_registry(memory_remember_enabled: bool) -> ToolRegistry:
    return build_tool_registry(
        memory_remember_enabled,
        memory_inspect_tool=memory_inspect.TOOL,
        memory_inspect_handler=memory_inspect.handle,
        memory_remember_tool=memory_remember.TOOL,
        memory_remember_handler=lambda arguments: memory_remember.handle(
            arguments,
            mutations_enabled=True,
        ),
    )


REGISTRY = build_startup_tool_registry(get_memory_remember_enabled())
TOOLS = REGISTRY.tools
TOOL_HANDLERS = REGISTRY.handlers


def call_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any] | None:
    return REGISTRY.call_tool(tool_name, arguments)
