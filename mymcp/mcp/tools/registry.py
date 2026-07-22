from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from mymcp.mcp.tool_arguments import normalize_tool_arguments
from mymcp.mcp.tools import (
    list_tools,
    memory_archive,
    memory_forget,
    memory_inspect,
    memory_list,
    memory_recall,
    memory_remember,
    memory_revise,
    memory_restore,
)
from mymcp.settings import get_memory_tool_settings

ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class ToolRegistry:
    tools: tuple[dict[str, Any], ...]
    handlers: Mapping[str, ToolHandler]
    input_schemas: Mapping[str, dict[str, Any]]

    def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any] | None:
        handler = self.handlers.get(tool_name)
        if handler is None:
            return None
        input_schema = self.input_schemas[tool_name]
        return handler(normalize_tool_arguments(arguments, input_schema))


def build_tool_registry(
    memory_remember_enabled: bool,
    *,
    memory_archive_restore_enabled: bool = False,
    memory_forget_enabled: bool = False,
    memory_revise_enabled: bool = False,
    memory_list_tool: dict[str, Any] | None = None,
    memory_list_handler: ToolHandler | None = None,
    memory_inspect_tool: dict[str, Any] | None = None,
    memory_inspect_handler: ToolHandler | None = None,
    memory_archive_tool: dict[str, Any] | None = None,
    memory_archive_handler: ToolHandler | None = None,
    memory_restore_tool: dict[str, Any] | None = None,
    memory_restore_handler: ToolHandler | None = None,
    memory_remember_tool: dict[str, Any] | None = None,
    memory_remember_handler: ToolHandler | None = None,
    memory_revise_tool: dict[str, Any] | None = None,
    memory_revise_handler: ToolHandler | None = None,
    memory_forget_tool: dict[str, Any] | None = None,
    memory_forget_handler: ToolHandler | None = None,
) -> ToolRegistry:
    tools = [list_tools.TOOL, memory_recall.TOOL]
    handlers: dict[str, ToolHandler] = {
        memory_recall.TOOL["name"]: memory_recall.handle,
    }

    if (memory_list_tool is None) != (memory_list_handler is None):
        raise ValueError("memory list registration is unavailable")
    if memory_list_tool is not None and memory_list_handler is not None:
        tools.append(memory_list_tool)
        handlers[memory_list_tool["name"]] = memory_list_handler

    if (memory_inspect_tool is None) != (memory_inspect_handler is None):
        raise ValueError("memory inspect registration is unavailable")
    if memory_inspect_tool is not None and memory_inspect_handler is not None:
        tools.append(memory_inspect_tool)
        handlers[memory_inspect_tool["name"]] = memory_inspect_handler

    if memory_archive_restore_enabled:
        lifecycle_registration = (
            memory_archive_tool,
            memory_archive_handler,
            memory_restore_tool,
            memory_restore_handler,
        )
        if any(item is None for item in lifecycle_registration):
            raise ValueError("memory archive/restore registration is unavailable")
        assert memory_archive_tool is not None
        assert memory_archive_handler is not None
        assert memory_restore_tool is not None
        assert memory_restore_handler is not None
        tools.extend((memory_archive_tool, memory_restore_tool))
        handlers[memory_archive_tool["name"]] = memory_archive_handler
        handlers[memory_restore_tool["name"]] = memory_restore_handler

    if memory_remember_enabled:
        if memory_remember_tool is None or memory_remember_handler is None:
            raise ValueError("memory remember registration is unavailable")
        tools.append(memory_remember_tool)
        handlers[memory_remember_tool["name"]] = memory_remember_handler

    if memory_revise_enabled:
        if memory_revise_tool is None or memory_revise_handler is None:
            raise ValueError("memory revise registration is unavailable")
        tools.append(memory_revise_tool)
        handlers[memory_revise_tool["name"]] = memory_revise_handler

    if memory_forget_enabled:
        if memory_forget_tool is None or memory_forget_handler is None:
            raise ValueError("memory forget registration is unavailable")
        tools.append(memory_forget_tool)
        handlers[memory_forget_tool["name"]] = memory_forget_handler

    selected_tools = tuple(tools)
    handlers[list_tools.TOOL["name"]] = lambda arguments: list_tools.handle(
        arguments,
        selected_tools,
    )
    return ToolRegistry(
        tools=selected_tools,
        handlers=MappingProxyType(handlers),
        input_schemas=MappingProxyType(
            {tool["name"]: tool["inputSchema"] for tool in selected_tools}
        ),
    )


def build_startup_tool_registry(
    memory_remember_enabled: bool,
    memory_archive_restore_enabled: bool = False,
    memory_forget_enabled: bool = False,
    *,
    memory_revise_enabled: bool = False,
) -> ToolRegistry:
    return build_tool_registry(
        memory_remember_enabled,
        memory_archive_restore_enabled=memory_archive_restore_enabled,
        memory_forget_enabled=memory_forget_enabled,
        memory_revise_enabled=memory_revise_enabled,
        memory_list_tool=memory_list.TOOL,
        memory_list_handler=memory_list.handle,
        memory_inspect_tool=memory_inspect.TOOL,
        memory_inspect_handler=memory_inspect.handle,
        memory_archive_tool=memory_archive.TOOL,
        memory_archive_handler=lambda arguments: memory_archive.handle(
            arguments,
            mutations_enabled=True,
        ),
        memory_restore_tool=memory_restore.TOOL,
        memory_restore_handler=lambda arguments: memory_restore.handle(
            arguments,
            mutations_enabled=True,
        ),
        memory_remember_tool=memory_remember.TOOL,
        memory_remember_handler=lambda arguments: memory_remember.handle(
            arguments,
            mutations_enabled=True,
        ),
        memory_revise_tool=memory_revise.TOOL,
        memory_revise_handler=lambda arguments: memory_revise.handle(
            arguments,
            mutations_enabled=True,
        ),
        memory_forget_tool=memory_forget.TOOL,
        memory_forget_handler=lambda arguments: memory_forget.handle(
            arguments,
            mutations_enabled=True,
        ),
    )


_MEMORY_TOOL_SETTINGS = get_memory_tool_settings()
REGISTRY = build_startup_tool_registry(
    memory_remember_enabled=_MEMORY_TOOL_SETTINGS.remember_enabled,
    memory_archive_restore_enabled=_MEMORY_TOOL_SETTINGS.archive_restore_enabled,
    memory_forget_enabled=_MEMORY_TOOL_SETTINGS.forget_enabled,
    memory_revise_enabled=_MEMORY_TOOL_SETTINGS.revise_enabled,
)
TOOLS = REGISTRY.tools
TOOL_HANDLERS = REGISTRY.handlers


def call_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any] | None:
    return REGISTRY.call_tool(tool_name, arguments)
