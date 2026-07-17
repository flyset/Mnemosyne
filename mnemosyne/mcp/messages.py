from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MCPMessage:
    request_id: Any
    method: str | None
    params: dict[str, Any]
    params_valid: bool


def parse_message(message: dict[str, Any]) -> MCPMessage:
    params = message.get("params", {})
    params_valid = isinstance(params, dict)

    return MCPMessage(
        request_id=message.get("id"),
        method=message.get("method"),
        params=params if params_valid else {},
        params_valid=params_valid,
    )
