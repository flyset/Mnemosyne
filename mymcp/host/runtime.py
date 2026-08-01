import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from uuid import uuid4

from mymcp.mcp.tool_registry import ToolRegistry
from mymcp.plugin.composition import (
    CapabilityOrigin,
    HostRegistrationFactory,
    PluginContribution,
    compose_tool_surface,
)
from mymcp.plugin.contracts import (
    ConsentRequirement,
    PluginId,
    PluginVersion,
    PublicToolBinding,
    QualifiedCapabilityId,
    ToolEffects,
)


_MAX_GENERATION_ID_LENGTH = 128
_GENERATION_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._~-]*\Z")


class HostRuntimeCompositionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RuntimeGenerationId:
    value: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.value, str)
            or len(self.value) > _MAX_GENERATION_ID_LENGTH
            or _GENERATION_ID_PATTERN.fullmatch(self.value) is None
        ):
            raise ValueError("invalid runtime generation id")


@dataclass(frozen=True, init=False)
class HostRuntime:
    registry: ToolRegistry
    plugin_inventory: tuple[tuple[PluginId, PluginVersion], ...]
    origins: Mapping[str, CapabilityOrigin]
    effects: Mapping[QualifiedCapabilityId, ToolEffects]
    consent: Mapping[QualifiedCapabilityId, ConsentRequirement]
    bindings: Mapping[QualifiedCapabilityId, str]
    generation: RuntimeGenerationId

    def __init__(
        self,
        *,
        registry: ToolRegistry,
        plugin_inventory: tuple[tuple[PluginId, PluginVersion], ...],
        origins: Mapping[str, CapabilityOrigin],
        effects: Mapping[QualifiedCapabilityId, ToolEffects],
        consent: Mapping[QualifiedCapabilityId, ConsentRequirement],
        bindings: Mapping[QualifiedCapabilityId, str],
        generation: RuntimeGenerationId,
    ) -> None:
        if not isinstance(registry, ToolRegistry) or not isinstance(
            generation, RuntimeGenerationId
        ):
            raise ValueError("invalid host runtime")
        object.__setattr__(self, "registry", registry)
        object.__setattr__(self, "plugin_inventory", tuple(plugin_inventory))
        object.__setattr__(self, "origins", MappingProxyType(dict(origins)))
        object.__setattr__(self, "effects", MappingProxyType(dict(effects)))
        object.__setattr__(self, "consent", MappingProxyType(dict(consent)))
        object.__setattr__(self, "bindings", MappingProxyType(dict(bindings)))
        object.__setattr__(self, "generation", generation)


GenerationFactory = Callable[[], str]


def _new_generation_id() -> str:
    return f"generation_{uuid4().hex}"


def build_host_runtime(
    contributions: Iterable[PluginContribution],
    bindings: Iterable[PublicToolBinding],
    host_registration_factory: HostRegistrationFactory,
    *,
    generation_factory: GenerationFactory = _new_generation_id,
) -> HostRuntime:
    try:
        surface = compose_tool_surface(
            contributions,
            bindings,
            host_registration_factory,
        )
    except ValueError as error:
        raise HostRuntimeCompositionError(str(error)) from None
    generation = RuntimeGenerationId(generation_factory())
    return HostRuntime(
        registry=surface.registry,
        plugin_inventory=surface.plugin_inventory,
        origins=surface.origins,
        effects=surface.effects,
        consent=surface.consent,
        bindings=surface.bindings,
        generation=generation,
    )
