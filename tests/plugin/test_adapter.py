import dataclasses

import pytest

from mymcp.plugin.adapter import PluginAdapter
from mymcp.plugin.composition import PluginContribution
from mymcp.plugin.manifest import parse_manifest_mapping


def _definition():
    return parse_manifest_mapping(
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


def test_plugin_adapter_is_immutable_and_contains_generic_contracts() -> None:
    definition = _definition()
    contribution = PluginContribution(definition.plugin_id, definition.version, ())
    adapter = PluginAdapter(definition, contribution)

    assert adapter.definition is definition
    assert adapter.contribution is contribution
    with pytest.raises(dataclasses.FrozenInstanceError):
        adapter.definition = definition  # type: ignore[misc]


@pytest.mark.parametrize("definition, contribution", [(object(), object()), (None, None)])
def test_plugin_adapter_rejects_invalid_direct_construction(
    definition: object, contribution: object
) -> None:
    with pytest.raises(ValueError, match="^invalid plugin adapter$"):
        PluginAdapter(definition, contribution)  # type: ignore[arg-type]
