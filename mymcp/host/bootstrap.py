from copy import deepcopy
from importlib.resources import files
from typing import Any

from mymcp.host.configuration import (
    HostConfiguration,
    validate_host_configuration_semantics,
)
from mymcp.host.runtime import GenerationFactory, HostRuntime, build_host_runtime
from mymcp.plugins.mnemosyne.plugin import (
    mnemosyne_contribution,
    mnemosyne_plugin_definition,
)
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
from mymcp.plugin.definition import HostApiVersion
from mymcp.plugin.manifest import parse_manifest_bytes, validate_plugin_contract


_MNEMOSYNE_PLUGIN_ID = PluginId("mnemosyne")
_BUNDLED_PLUGIN_IDS = (_MNEMOSYNE_PLUGIN_ID,)


def validate_production_configuration(
    configuration: HostConfiguration,
) -> HostConfiguration:
    return validate_host_configuration_semantics(
        configuration,
        bundled_plugin_ids=_BUNDLED_PLUGIN_IDS,
    )


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
    configuration: HostConfiguration,
    *,
    generation_factory: GenerationFactory | None = None,
) -> HostRuntime:
    validate_production_configuration(configuration)
    manifest_definition = parse_manifest_bytes(
        files("mymcp.plugins.mnemosyne").joinpath("manifest.json").read_bytes()
    )
    adapter_definition = mnemosyne_plugin_definition()
    contribution = mnemosyne_contribution()
    validate_plugin_contract(
        manifest_definition=manifest_definition,
        adapter_definition=adapter_definition,
        contribution=contribution,
        supported_host_api=HostApiVersion(1),
    )
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
