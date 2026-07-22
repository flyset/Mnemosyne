from collections.abc import Callable
import logging
from typing import Any

from mymcp.memory.records import MemoryReference
from mymcp.memory.service import MemoryResult
from mymcp.mcp.tools._memory_lifecycle import execute_lifecycle


logger = logging.getLogger("mcp.memory_archive")
ArchiveOperation = Callable[[MemoryReference, int], MemoryResult]


def handle(
    arguments: dict[str, Any],
    *,
    archive_operation: ArchiveOperation,
    mutations_enabled: bool = False,
) -> dict[str, Any]:
    return execute_lifecycle(
        arguments,
        operation="archive",
        mutations_enabled=mutations_enabled,
        lifecycle_operation=archive_operation,
        logger=logger,
    )
