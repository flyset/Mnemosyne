from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from mymcp.mcp.tool_registry import ToolHandler, ToolRegistration, ToolRegistry
from mymcp.plugin.contracts import (
    ConsentRequirement,
    PluginId,
    PluginVersion,
    PublicToolBinding,
    QualifiedCapabilityId,
    ToolEffects,
)


class HostToolOrigin(StrEnum):
    HOST = "host"


@dataclass(frozen=True, init=False)
class ActivatedTool:
    capability: QualifiedCapabilityId
    _tool: dict[str, Any]
    handler: ToolHandler
    effects: ToolEffects
    consent: ConsentRequirement

    def __init__(
        self,
        capability: QualifiedCapabilityId,
        tool: Mapping[str, Any],
        handler: ToolHandler,
        effects: ToolEffects,
        consent: ConsentRequirement,
    ) -> None:
        if (
            not isinstance(capability, QualifiedCapabilityId)
            or not isinstance(tool, Mapping)
            or not callable(handler)
            or not isinstance(effects, ToolEffects)
            or not isinstance(consent, ConsentRequirement)
        ):
            raise ValueError("invalid activated tool")
        object.__setattr__(self, "capability", capability)
        object.__setattr__(self, "_tool", deepcopy(dict(tool)))
        object.__setattr__(self, "handler", handler)
        object.__setattr__(self, "effects", effects)
        object.__setattr__(self, "consent", consent)

    @property
    def tool(self) -> dict[str, Any]:
        return deepcopy(self._tool)


@dataclass(frozen=True, init=False)
class PluginContribution:
    plugin_id: PluginId
    version: PluginVersion
    tools: tuple[ActivatedTool, ...]

    def __init__(
        self,
        plugin_id: PluginId,
        version: PluginVersion,
        tools: Iterable[ActivatedTool],
    ) -> None:
        selected_tools = tuple(tools)
        if (
            not isinstance(plugin_id, PluginId)
            or not isinstance(version, PluginVersion)
            or any(not isinstance(tool, ActivatedTool) for tool in selected_tools)
        ):
            raise ValueError("invalid plugin contribution")
        object.__setattr__(self, "plugin_id", plugin_id)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "tools", selected_tools)


CapabilityOrigin = HostToolOrigin | QualifiedCapabilityId
HostRegistrationFactory = Callable[
    [tuple[dict[str, Any], ...]],
    ToolRegistration,
]


@dataclass(frozen=True, init=False)
class ComposedToolSurface:
    registry: ToolRegistry
    plugin_inventory: tuple[tuple[PluginId, PluginVersion], ...]
    origins: Mapping[str, CapabilityOrigin]
    effects: Mapping[QualifiedCapabilityId, ToolEffects]
    consent: Mapping[QualifiedCapabilityId, ConsentRequirement]
    bindings: Mapping[QualifiedCapabilityId, str]

    def __init__(
        self,
        registry: ToolRegistry,
        plugin_inventory: tuple[tuple[PluginId, PluginVersion], ...],
        origins: Mapping[str, CapabilityOrigin],
        effects: Mapping[QualifiedCapabilityId, ToolEffects],
        consent: Mapping[QualifiedCapabilityId, ConsentRequirement],
        bindings: Mapping[QualifiedCapabilityId, str],
    ) -> None:
        object.__setattr__(self, "registry", registry)
        object.__setattr__(self, "plugin_inventory", plugin_inventory)
        object.__setattr__(self, "origins", MappingProxyType(dict(origins)))
        object.__setattr__(self, "effects", MappingProxyType(dict(effects)))
        object.__setattr__(self, "consent", MappingProxyType(dict(consent)))
        object.__setattr__(self, "bindings", MappingProxyType(dict(bindings)))


def compose_tool_surface(
    contributions: Iterable[PluginContribution],
    bindings: Iterable[PublicToolBinding],
    host_registration_factory: HostRegistrationFactory,
) -> ComposedToolSurface:
    selected_contributions = tuple(contributions)
    selected_bindings = tuple(bindings)
    if any(
        not isinstance(contribution, PluginContribution)
        for contribution in selected_contributions
    ):
        raise ValueError("invalid plugin contribution")
    if any(not isinstance(binding, PublicToolBinding) for binding in selected_bindings):
        raise ValueError("invalid public tool binding")

    plugin_ids: set[PluginId] = set()
    selected_tools: list[ActivatedTool] = []
    selected_capabilities: set[QualifiedCapabilityId] = set()
    for contribution in selected_contributions:
        if contribution.plugin_id in plugin_ids:
            raise ValueError("duplicate plugin id")
        plugin_ids.add(contribution.plugin_id)
        for activated_tool in contribution.tools:
            if activated_tool.capability.plugin_id != contribution.plugin_id:
                raise ValueError("capability plugin mismatch")
            if activated_tool.capability in selected_capabilities:
                raise ValueError("duplicate qualified capability")
            selected_capabilities.add(activated_tool.capability)
            selected_tools.append(activated_tool)

    binding_by_capability: dict[QualifiedCapabilityId, str] = {}
    public_names: set[str] = set()
    for binding in selected_bindings:
        if binding.capability in binding_by_capability:
            raise ValueError("duplicate capability binding")
        if binding.capability not in selected_capabilities:
            raise ValueError("unknown capability binding")
        if binding.public_name == "list_tools" or binding.public_name.startswith(
            "mymcp_"
        ):
            raise ValueError("reserved public tool name")
        if binding.public_name in public_names:
            raise ValueError("duplicate public tool name")
        binding_by_capability[binding.capability] = binding.public_name
        public_names.add(binding.public_name)

    if binding_by_capability.keys() != selected_capabilities:
        raise ValueError("missing capability binding")

    registrations: list[ToolRegistration] = []
    projected_tools: list[dict[str, Any]] = []
    origins: dict[str, CapabilityOrigin] = {"list_tools": HostToolOrigin.HOST}
    effects: dict[QualifiedCapabilityId, ToolEffects] = {}
    consent: dict[QualifiedCapabilityId, ConsentRequirement] = {}
    for activated_tool in selected_tools:
        public_name = binding_by_capability[activated_tool.capability]
        projected_tool = activated_tool.tool
        projected_tool["name"] = public_name
        registrations.append(
            ToolRegistration(tool=projected_tool, handler=activated_tool.handler)
        )
        projected_tools.append(projected_tool)
        origins[public_name] = activated_tool.capability
        effects[activated_tool.capability] = activated_tool.effects
        consent[activated_tool.capability] = activated_tool.consent

    host_registration = host_registration_factory(tuple(deepcopy(projected_tools)))
    if (
        not isinstance(host_registration, ToolRegistration)
        or dict(host_registration.tool).get("name") != "list_tools"
    ):
        raise ValueError("invalid host tool registration")
    registry = ToolRegistry((host_registration, *registrations))

    return ComposedToolSurface(
        registry=registry,
        plugin_inventory=tuple(
            (contribution.plugin_id, contribution.version)
            for contribution in selected_contributions
        ),
        origins=origins,
        effects=effects,
        consent=consent,
        bindings=binding_by_capability,
    )
