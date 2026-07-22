from collections.abc import Callable
import logging
from typing import Any

from mymcp.memory.records import MemoryReference
from mymcp.memory.service import MemoryResult, MemoryService
from mymcp.memory.store import FilesystemMemoryStore
from mymcp.mcp.tools._memory_lifecycle import execute_lifecycle
from mymcp.settings import get_memory_root


logger = logging.getLogger("mcp.memory_restore")
RestoreOperation = Callable[[MemoryReference, int], MemoryResult]


def _restore(reference: MemoryReference, revision: int) -> MemoryResult:
    return MemoryService(
        FilesystemMemoryStore(get_memory_root()),
        mutations_enabled=True,
    ).restore(reference, expected_revision=revision)


def handle(
    arguments: dict[str, Any],
    *,
    mutations_enabled: bool = False,
    restore_operation: RestoreOperation | None = None,
) -> dict[str, Any]:
    return execute_lifecycle(
        arguments,
        operation="restore",
        mutations_enabled=mutations_enabled,
        lifecycle_operation=restore_operation or _restore,
        logger=logger,
    )
