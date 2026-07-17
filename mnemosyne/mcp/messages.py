from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MCPMessage:
    request_id: Any
    method: str | None
    params: dict[str, Any]


def parse_message(message: dict[str, Any]) -> MCPMessage:
    params = message.get("params", {})
    if not isinstance(params, dict):
        params = {}

    return MCPMessage(
        request_id=message.get("id"),
        method=message.get("method"),
        params=params,
    )
