from typing import Any

from mymcp.mcp.tool_registry import ToolHandler, ToolRegistration, ToolRegistry
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
from mymcp.memory.listing import MemoryListResult, MemoryListSelector
from mymcp.memory.records import (
    LegacyMemoryRecordV1,
    LegacyMemoryReference,
    MemoryDraft,
    MemoryRecordV2,
    MemoryReference,
    MemoryRevision,
)
from mymcp.memory.retrieval import MemoryMatch
from mymcp.memory.scopes import MemoryScope
from mymcp.memory.service import ForgetResult, MemoryResult, MemoryService
from mymcp.memory.store import FilesystemMemoryStore
from mymcp.settings import MemoryToolSettings, get_memory_root


def _memory_service(*, mutations_enabled: bool) -> MemoryService:
    return MemoryService(
        FilesystemMemoryStore(get_memory_root()),
        mutations_enabled=mutations_enabled,
    )


def _recall(
    scope: MemoryScope,
    query: str,
    tags: list[str],
) -> list[MemoryMatch]:
    return _memory_service(mutations_enabled=False).recall(scope, query, tags)


def _list_memories(
    selector: MemoryListSelector,
    page_size: int | None,
    cursor: str | None,
) -> MemoryListResult:
    return _memory_service(mutations_enabled=False).list_memories(
        selector,
        page_size=page_size,
        cursor=cursor,
    )


def _inspect(
    reference: MemoryReference | LegacyMemoryReference,
) -> MemoryRecordV2 | LegacyMemoryRecordV1:
    return _memory_service(mutations_enabled=False).inspect(reference)


def _remember(draft: MemoryDraft) -> MemoryResult:
    return _memory_service(mutations_enabled=True).remember(draft)


def _archive(reference: MemoryReference, revision: int) -> MemoryResult:
    return _memory_service(mutations_enabled=True).archive(
        reference,
        expected_revision=revision,
    )


def _restore(reference: MemoryReference, revision: int) -> MemoryResult:
    return _memory_service(mutations_enabled=True).restore(
        reference,
        expected_revision=revision,
    )


def _revise(
    reference: MemoryReference,
    revision: MemoryRevision,
) -> MemoryResult:
    return _memory_service(mutations_enabled=True).revise(reference, revision)


def _forget(reference: MemoryReference, revision: int) -> ForgetResult:
    return _memory_service(mutations_enabled=True).forget(
        reference,
        expected_revision=revision,
    )


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
        memory_recall.TOOL["name"]: lambda arguments: memory_recall.handle(
            arguments,
            recall_operation=_recall,
        ),
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
        ToolRegistration(tool=tool, handler=handlers[tool["name"]])
        for tool in selected_tools
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
        memory_list_handler=lambda arguments: memory_list.handle(
            arguments,
            list_operation=_list_memories,
        ),
        memory_inspect_tool=memory_inspect.TOOL,
        memory_inspect_handler=lambda arguments: memory_inspect.handle(
            arguments,
            inspect_operation=_inspect,
        ),
        memory_archive_tool=memory_archive.TOOL,
        memory_archive_handler=lambda arguments: memory_archive.handle(
            arguments,
            archive_operation=_archive,
            mutations_enabled=True,
        ),
        memory_restore_tool=memory_restore.TOOL,
        memory_restore_handler=lambda arguments: memory_restore.handle(
            arguments,
            restore_operation=_restore,
            mutations_enabled=True,
        ),
        memory_remember_tool=memory_remember.TOOL,
        memory_remember_handler=lambda arguments: memory_remember.handle(
            arguments,
            remember_operation=_remember,
            mutations_enabled=True,
        ),
        memory_revise_tool=memory_revise.TOOL,
        memory_revise_handler=lambda arguments: memory_revise.handle(
            arguments,
            revise_operation=_revise,
            mutations_enabled=True,
        ),
        memory_forget_tool=memory_forget.TOOL,
        memory_forget_handler=lambda arguments: memory_forget.handle(
            arguments,
            forget_operation=_forget,
            mutations_enabled=True,
        ),
    )


def compose_mnemosyne_registry(settings: MemoryToolSettings) -> ToolRegistry:
    return build_startup_tool_registry(
        memory_remember_enabled=settings.remember_enabled,
        memory_archive_restore_enabled=settings.archive_restore_enabled,
        memory_forget_enabled=settings.forget_enabled,
        memory_revise_enabled=settings.revise_enabled,
    )
