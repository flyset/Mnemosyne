from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from mymcp.mcp.tool_arguments import normalize_tool_arguments


ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class ToolRegistration:
    tool: Mapping[str, Any]
    handler: ToolHandler


@dataclass(frozen=True, init=False)
class ToolRegistry:
    _tools: tuple[dict[str, Any], ...]
    _handlers: Mapping[str, ToolHandler]
    _input_schemas: Mapping[str, dict[str, Any]]

    def __init__(self, registrations: Iterable[ToolRegistration]) -> None:
        tools: list[dict[str, Any]] = []
        handlers: dict[str, ToolHandler] = {}
        input_schemas: dict[str, dict[str, Any]] = {}

        for registration in registrations:
            if not isinstance(registration, ToolRegistration) or not callable(
                registration.handler
            ):
                raise ValueError("invalid tool registration")

            tool = deepcopy(dict(registration.tool))
            name = tool.get("name")
            input_schema = tool.get("inputSchema")
            if not isinstance(name, str) or not name or not isinstance(
                input_schema, dict
            ):
                raise ValueError("invalid tool registration")
            if name in handlers:
                raise ValueError(f"duplicate tool registration: {name}")

            tools.append(tool)
            handlers[name] = registration.handler
            input_schemas[name] = input_schema

        object.__setattr__(self, "_tools", tuple(tools))
        object.__setattr__(self, "_handlers", MappingProxyType(handlers))
        object.__setattr__(self, "_input_schemas", MappingProxyType(input_schemas))

    @property
    def tools(self) -> tuple[dict[str, Any], ...]:
        return deepcopy(self._tools)

    @property
    def handlers(self) -> Mapping[str, ToolHandler]:
        return self._handlers

    @property
    def input_schemas(self) -> Mapping[str, dict[str, Any]]:
        return MappingProxyType(deepcopy(dict(self._input_schemas)))

    def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any] | None:
        handler = self._handlers.get(tool_name)
        if handler is None:
            return None
        input_schema = self._input_schemas[tool_name]
        return handler(normalize_tool_arguments(arguments, input_schema))
