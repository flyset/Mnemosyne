from copy import deepcopy
from importlib.resources import files
import logging
from typing import Any

from mymcp.host.configuration import (
    HostConfiguration,
    validate_host_configuration_semantics,
)
from mymcp.host.external_plugins import (
    ExternalPluginLoadError,
    load_external_plugins,
    preflight_external_manifests,
)
from mymcp.host.runtime import (
    GenerationFactory,
    HostRuntime,
    HostRuntimeCompositionError,
    build_host_runtime,
)
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
from mymcp.plugin.manifest import (
    PluginContractError,
    parse_manifest_bytes,
    validate_plugin_contract,
)


_MNEMOSYNE_PLUGIN_ID = PluginId("mnemosyne")
_BUNDLED_PLUGIN_IDS = (_MNEMOSYNE_PLUGIN_ID,)
_LOGGER = logging.getLogger("mymcp.host.bootstrap")


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


def _external_bindings(
    contributions: tuple[PluginContribution, ...],
) -> tuple[PublicToolBinding, ...]:
    return tuple(
        PublicToolBinding(
            tool.capability,
            f"{contribution.plugin_id.value}__{tool.capability.local_id.value}",
        )
        for contribution in contributions
        for tool in contribution.tools
    )


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
    try:
        runtime = _build_production_runtime(
            configuration,
            generation_factory=generation_factory,
        )
    except ExternalPluginLoadError as error:
        _LOGGER.error("runtime_composition outcome=error code=%s", error.code)
        raise

    _LOGGER.info(
        "runtime_composition outcome=loaded bundled=%s external=%s capabilities=%s",
        len(_BUNDLED_PLUGIN_IDS),
        len(runtime.plugin_inventory) - len(_BUNDLED_PLUGIN_IDS),
        len(runtime.bindings),
    )
    return runtime


def _build_production_runtime(
    configuration: HostConfiguration,
    *,
    generation_factory: GenerationFactory | None = None,
) -> HostRuntime:
    validate_production_configuration(configuration)
    external_definitions = preflight_external_manifests(configuration)
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
    adapters = load_external_plugins(configuration, external_definitions)
    try:
        for external_definition, adapter in zip(
            external_definitions, adapters, strict=True
        ):
            validate_plugin_contract(
                manifest_definition=external_definition,
                adapter_definition=adapter.definition,
                contribution=adapter.contribution,
                supported_host_api=HostApiVersion(1),
            )
    except PluginContractError:
        raise ExternalPluginLoadError("external_plugin_composition_invalid") from None

    external_contributions = tuple(adapter.contribution for adapter in adapters)
    contributions = (contribution, *external_contributions)
    bindings = (
        *_selected_bindings(contribution),
        *_external_bindings(external_contributions),
    )
    try:
        if generation_factory is None:
            return build_host_runtime(
                contributions,
                bindings,
                _host_list_tools_registration,
            )
        return build_host_runtime(
            contributions,
            bindings,
            _host_list_tools_registration,
            generation_factory=generation_factory,
        )
    except HostRuntimeCompositionError:
        if adapters:
            raise ExternalPluginLoadError("external_plugin_composition_invalid") from None
        raise
