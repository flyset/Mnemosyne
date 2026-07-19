import logging
from typing import Any

from mnemosyne.mcp.tools._memory_revise import ReviseOperation, execute_revise
from mnemosyne.memory.records import MemoryReference, MemoryRevision
from mnemosyne.memory.service import MemoryResult, MemoryService
from mnemosyne.memory.store import FilesystemMemoryStore
from mnemosyne.settings import get_memory_root


logger = logging.getLogger("mcp.memory_revise")


def _revise(
    reference: MemoryReference,
    revision: MemoryRevision,
) -> MemoryResult:
    return MemoryService(
        FilesystemMemoryStore(get_memory_root()),
        mutations_enabled=True,
    ).revise(reference, revision)


def handle(
    arguments: dict[str, Any],
    *,
    mutations_enabled: bool = False,
    revise_operation: ReviseOperation = _revise,
) -> dict[str, Any]:
    return execute_revise(
        arguments,
        mutations_enabled=mutations_enabled,
        revise_operation=revise_operation,
        logger=logger,
    )
