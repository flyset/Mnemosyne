"""Generic MyMCP plugin contracts."""

from mymcp.plugin.composition import (
    ActivatedTool,
    ComposedToolSurface,
    HostToolOrigin,
    PluginContribution,
    compose_tool_surface,
)
from mymcp.plugin.contracts import (
    CapabilityKind,
    CapabilityLocalId,
    ConsentRequirement,
    PluginId,
    PluginVersion,
    PublicToolBinding,
    QualifiedCapabilityId,
    ToolEffects,
)

__all__ = [
    "ActivatedTool",
    "CapabilityKind",
    "CapabilityLocalId",
    "ComposedToolSurface",
    "ConsentRequirement",
    "HostToolOrigin",
    "PluginId",
    "PluginContribution",
    "PluginVersion",
    "PublicToolBinding",
    "QualifiedCapabilityId",
    "ToolEffects",
    "compose_tool_surface",
]
