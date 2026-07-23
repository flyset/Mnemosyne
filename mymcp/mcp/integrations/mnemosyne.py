from mymcp.mcp.tool_registry import ToolRegistration
from mymcp.mcp.tools import (
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
from mymcp.mnemosyne.configuration import (
    get_memory_root,
    get_memory_tool_settings,
)


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


def build_mnemosyne_registrations(
    memory_remember_enabled: bool,
    *,
    memory_archive_restore_enabled: bool = False,
    memory_forget_enabled: bool = False,
    memory_revise_enabled: bool = False,
) -> tuple[ToolRegistration, ...]:
    registrations = [
        ToolRegistration(
            tool=memory_recall.TOOL,
            handler=lambda arguments: memory_recall.handle(
                arguments,
                recall_operation=_recall,
            ),
        ),
        ToolRegistration(
            tool=memory_list.TOOL,
            handler=lambda arguments: memory_list.handle(
                arguments,
                list_operation=_list_memories,
            ),
        ),
        ToolRegistration(
            tool=memory_inspect.TOOL,
            handler=lambda arguments: memory_inspect.handle(
                arguments,
                inspect_operation=_inspect,
            ),
        ),
    ]

    if memory_archive_restore_enabled:
        registrations.extend(
            (
                ToolRegistration(
                    tool=memory_archive.TOOL,
                    handler=lambda arguments: memory_archive.handle(
                        arguments,
                        archive_operation=_archive,
                        mutations_enabled=True,
                    ),
                ),
                ToolRegistration(
                    tool=memory_restore.TOOL,
                    handler=lambda arguments: memory_restore.handle(
                        arguments,
                        restore_operation=_restore,
                        mutations_enabled=True,
                    ),
                ),
            )
        )

    if memory_remember_enabled:
        registrations.append(
            ToolRegistration(
                tool=memory_remember.TOOL,
                handler=lambda arguments: memory_remember.handle(
                    arguments,
                    remember_operation=_remember,
                    mutations_enabled=True,
                ),
            )
        )

    if memory_revise_enabled:
        registrations.append(
            ToolRegistration(
                tool=memory_revise.TOOL,
                handler=lambda arguments: memory_revise.handle(
                    arguments,
                    revise_operation=_revise,
                    mutations_enabled=True,
                ),
            )
        )

    if memory_forget_enabled:
        registrations.append(
            ToolRegistration(
                tool=memory_forget.TOOL,
                handler=lambda arguments: memory_forget.handle(
                    arguments,
                    forget_operation=_forget,
                    mutations_enabled=True,
                ),
            )
        )

    return tuple(registrations)


def mnemosyne_integration() -> tuple[ToolRegistration, ...]:
    settings = get_memory_tool_settings()
    return build_mnemosyne_registrations(
        memory_remember_enabled=settings.remember_enabled,
        memory_archive_restore_enabled=settings.archive_restore_enabled,
        memory_forget_enabled=settings.forget_enabled,
        memory_revise_enabled=settings.revise_enabled,
    )
