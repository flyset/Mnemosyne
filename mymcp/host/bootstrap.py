from copy import deepcopy
from typing import Any

from mymcp.host.runtime import GenerationFactory, HostRuntime, build_host_runtime
from mymcp.mcp.integrations.mnemosyne import mnemosyne_contribution
from mymcp.mcp.tool_registry import ToolRegistration
from mymcp.mcp.tools import list_tools
from mymcp.plugin.composition import PluginContribution
from mymcp.plugin.contracts import (
    CapabilityKind,
    CapabilityLocalId,
    PluginId,
    PublicToolBinding,
    QualifiedCapabilityId,
)


_MNEMOSYNE_PLUGIN_ID = PluginId("mnemosyne")


def _mnemosyne_identity(local_id: str) -> QualifiedCapabilityId:
    return QualifiedCapabilityId(
        plugin_id=_MNEMOSYNE_PLUGIN_ID,
        kind=CapabilityKind.TOOL,
        local_id=CapabilityLocalId(local_id),
    )


_PINNED_BINDINGS = tuple(
    PublicToolBinding(_mnemosyne_identity(name), name)
    for name in (
        "memory_recall",
        "memory_list",
        "memory_inspect",
        "memory_archive",
        "memory_restore",
        "memory_remember",
        "memory_revise",
        "memory_forget",
    )
)


def _selected_bindings(
    contribution: PluginContribution,
) -> tuple[PublicToolBinding, ...]:
    selected = {tool.capability for tool in contribution.tools}
    return tuple(binding for binding in _PINNED_BINDINGS if binding.capability in selected)


def _host_list_tools_registration(
    plugin_tools: tuple[dict[str, Any], ...],
) -> ToolRegistration:
    complete_tools = [deepcopy(dict(list_tools.TOOL)), *deepcopy(plugin_tools)]
    return ToolRegistration(
        tool=list_tools.TOOL,
        handler=lambda arguments: list_tools.handle(arguments, complete_tools),
    )


def build_production_runtime(
    *,
    generation_factory: GenerationFactory | None = None,
) -> HostRuntime:
    contribution = mnemosyne_contribution()
    bindings = _selected_bindings(contribution)
    if generation_factory is None:
        return build_host_runtime(
            (contribution,),
            bindings,
            _host_list_tools_registration,
        )
    return build_host_runtime(
        (contribution,),
        bindings,
        _host_list_tools_registration,
        generation_factory=generation_factory,
    )
