from collections.abc import Callable, Iterable
from copy import deepcopy

from mymcp.mcp.tool_registry import ToolRegistration, ToolRegistry
from mymcp.mcp.tools import list_tools


ToolIntegration = Callable[[], tuple[ToolRegistration, ...]]


def compose_tool_registry(
    integrations: Iterable[ToolIntegration],
) -> ToolRegistry:
    registrations = tuple(
        registration
        for integration in integrations
        for registration in integration()
    )
    selected_tools = [deepcopy(dict(list_tools.TOOL))]
    selected_tools.extend(
        deepcopy(dict(registration.tool)) for registration in registrations
    )
    list_tools_registration = ToolRegistration(
        tool=list_tools.TOOL,
        handler=lambda arguments: list_tools.handle(arguments, selected_tools),
    )
    return ToolRegistry((list_tools_registration, *registrations))
