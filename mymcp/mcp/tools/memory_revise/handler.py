import logging
from typing import Any

from mymcp.mcp.tools._memory_revise import ReviseOperation, execute_revise


logger = logging.getLogger("mcp.memory_revise")

def handle(
    arguments: dict[str, Any],
    *,
    revise_operation: ReviseOperation,
    mutations_enabled: bool = False,
) -> dict[str, Any]:
    return execute_revise(
        arguments,
        mutations_enabled=mutations_enabled,
        revise_operation=revise_operation,
        logger=logger,
    )
