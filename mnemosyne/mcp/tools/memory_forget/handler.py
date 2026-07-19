from collections.abc import Callable
import logging
from typing import Any

from mnemosyne.memory.records import MemoryReference
from mnemosyne.memory.service import ForgetResult, MemoryService
from mnemosyne.memory.store import FilesystemMemoryStore
from mnemosyne.mcp.tools._memory_forget import execute_forget
from mnemosyne.settings import get_memory_root


logger = logging.getLogger("mcp.memory_forget")
ForgetOperation = Callable[[MemoryReference, int], ForgetResult]


def _forget(reference: MemoryReference, revision: int) -> ForgetResult:
    return MemoryService(
        FilesystemMemoryStore(get_memory_root()),
        mutations_enabled=True,
    ).forget(reference, expected_revision=revision)


def handle(
    arguments: dict[str, Any],
    *,
    mutations_enabled: bool = False,
    forget_operation: ForgetOperation | None = None,
) -> dict[str, Any]:
    return execute_forget(
        arguments,
        mutations_enabled=mutations_enabled,
        forget_operation=forget_operation or _forget,
        logger=logger,
    )
