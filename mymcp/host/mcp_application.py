from dataclasses import dataclass
from typing import Any

from mymcp.authentication.contracts import Principal
from mymcp.mcp.dispatcher import MCPDispatcher


@dataclass(frozen=True, slots=True)
class PrincipalAwareMCPApplication:
    dispatcher: MCPDispatcher

    def __post_init__(self) -> None:
        if not isinstance(self.dispatcher, MCPDispatcher):
            raise ValueError("invalid principal-aware MCP application")

    def dispatch(
        self,
        principal: Principal,
        message: Any,
    ) -> dict[str, Any] | None:
        if not isinstance(principal, Principal):
            raise ValueError("invalid authenticated principal")
        return self.dispatcher.dispatch(message)
