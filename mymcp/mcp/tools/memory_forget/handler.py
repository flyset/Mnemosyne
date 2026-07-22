from collections.abc import Callable
import logging
from typing import Any

from mymcp.memory.records import MemoryReference
from mymcp.memory.service import ForgetResult
from mymcp.mcp.tools._memory_forget import execute_forget


logger = logging.getLogger("mcp.memory_forget")
ForgetOperation = Callable[[MemoryReference, int], ForgetResult]


def handle(
    arguments: dict[str, Any],
    *,
    forget_operation: ForgetOperation,
    mutations_enabled: bool = False,
) -> dict[str, Any]:
    return execute_forget(
        arguments,
        mutations_enabled=mutations_enabled,
        forget_operation=forget_operation,
        logger=logger,
    )
