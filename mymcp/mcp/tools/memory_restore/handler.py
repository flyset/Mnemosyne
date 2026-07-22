from collections.abc import Callable
import logging
from typing import Any

from mymcp.memory.records import MemoryReference
from mymcp.memory.service import MemoryResult
from mymcp.mcp.tools._memory_lifecycle import execute_lifecycle


logger = logging.getLogger("mcp.memory_restore")
RestoreOperation = Callable[[MemoryReference, int], MemoryResult]


def handle(
    arguments: dict[str, Any],
    *,
    restore_operation: RestoreOperation,
    mutations_enabled: bool = False,
) -> dict[str, Any]:
    return execute_lifecycle(
        arguments,
        operation="restore",
        mutations_enabled=mutations_enabled,
        lifecycle_operation=restore_operation,
        logger=logger,
    )
