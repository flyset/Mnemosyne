from mymcp.plugin.adapter import PluginAdapter
from mymcp.plugin.composition import ActivatedTool, PluginContribution
from mymcp.plugin.contracts import (
    CapabilityKind,
    CapabilityLocalId,
    ConsentRequirement,
    QualifiedCapabilityId,
    ToolEffects,
)
from mymcp.plugin.manifest import parse_manifest_mapping


def mymcp_plugin_v1() -> PluginAdapter:
    definition = parse_manifest_mapping(
        {
            "manifest_version": 1,
            "id": "external",
            "title": "External",
            "description": "An external plugin.",
            "version": "1.0.0",
            "requires": {"host_api": {"min": 1, "max": 1}},
            "capabilities": [
                {
                    "kind": "tool",
                    "id": "external_tool",
                    "version": "1.0.0",
                    "read_only": True,
                    "destructive": False,
                    "idempotent": True,
                    "open_world": False,
                    "consent": "none",
                }
            ],
            "configuration": {
                "schema_version": 1,
                "schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False,
                },
            },
            "secret_references": [],
            "data_schema_version": 1,
            "authority": {"filesystem": [], "network": False},
        }
    )
    tool = ActivatedTool(
        capability=QualifiedCapabilityId(
            definition.plugin_id,
            CapabilityKind.TOOL,
            CapabilityLocalId("external_tool"),
        ),
        tool={
            "name": "external_tool",
            "description": "A deterministic external fixture Tool.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        handler=lambda arguments: {"content": [], "arguments": arguments},
        effects=ToolEffects(True, False, True, False),
        consent=ConsentRequirement.NONE,
    )
    return PluginAdapter(
        definition,
        PluginContribution(definition.plugin_id, definition.version, (tool,)),
    )
