from importlib.resources import files
import json
from pathlib import Path

import pytest

from mymcp.plugins.mnemosyne import plugin as mnemosyne
from mymcp.plugin.contracts import (
    CapabilityKind,
    CapabilityLocalId,
    ConsentRequirement,
    PluginId,
    PluginVersion,
    ToolEffects,
)
from mymcp.plugin.definition import (
    AuthorityDeclaration,
    CapabilityContractVersion,
    ConfigurationSchemaVersion,
    ConfigurationType,
    FilesystemAuthority,
    ManifestVersion,
    PluginDataSchemaVersion,
)
from mymcp.plugin.manifest import parse_manifest_bytes


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MNEMOSYNE_PACKAGE = PROJECT_ROOT / "mymcp" / "plugins" / "mnemosyne"
REQUIRED_CANONICAL_SOURCE_FILES = {
    "__init__.py",
    "manifest.json",
    "plugin.py",
    "configuration.py",
    "memory/__init__.py",
    "memory/errors.py",
    "memory/listing.py",
    "memory/normalization.py",
    "memory/paths.py",
    "memory/policy.py",
    "memory/records.py",
    "memory/retrieval.py",
    "memory/scopes.py",
    "memory/service.py",
    "memory/store.py",
    "mcp/__init__.py",
    "mcp/tools/__init__.py",
    "mcp/tools/_memory_content_refusal.py",
    "mcp/tools/_memory_forget.py",
    "mcp/tools/_memory_lifecycle.py",
    "mcp/tools/_memory_revise.py",
}
EXPECTED_CAPABILITIES = (
    "memory_recall",
    "memory_list",
    "memory_inspect",
    "memory_archive",
    "memory_restore",
    "memory_remember",
    "memory_revise",
    "memory_forget",
)
REQUIRED_CANONICAL_SOURCE_FILES.update(
    f"mcp/tools/{name}/{part}.py"
    for name in EXPECTED_CAPABILITIES
    for part in ("__init__", "definition", "handler")
)
READ_ONLY_CAPABILITIES = {
    "memory_recall",
    "memory_list",
    "memory_inspect",
}
NON_DESTRUCTIVE_MUTATIONS = {
    "memory_archive",
    "memory_restore",
    "memory_remember",
}
DESTRUCTIVE_MUTATIONS = {"memory_revise", "memory_forget"}


def _manifest_bytes() -> bytes:
    return files("mymcp.plugins.mnemosyne").joinpath("manifest.json").read_bytes()


def test_mnemosyne_manifest_is_one_fixed_parseable_package_resource() -> None:
    resource = files("mymcp.plugins.mnemosyne").joinpath("manifest.json")

    assert resource.is_file()
    assert parse_manifest_bytes(resource.read_bytes())
    source_files = {
        path.relative_to(MNEMOSYNE_PACKAGE).as_posix()
        for path in MNEMOSYNE_PACKAGE.rglob("*")
        if path.is_file() and (path.suffix == ".py" or path.name == "manifest.json")
    }
    assert REQUIRED_CANONICAL_SOURCE_FILES <= source_files
    assert sum(path.name == "manifest.json" for path in MNEMOSYNE_PACKAGE.rglob("*")) == 1


def test_mnemosyne_manifest_matches_the_trusted_adapter_definition() -> None:
    manifest_definition = parse_manifest_bytes(_manifest_bytes())
    adapter_definition = mnemosyne.mnemosyne_plugin_definition()

    assert manifest_definition == adapter_definition
    assert manifest_definition.manifest_version == ManifestVersion(1)
    assert manifest_definition.plugin_id == PluginId("mnemosyne")
    assert manifest_definition.title.value == "Mnemosyne"
    assert manifest_definition.version == PluginVersion("0.1.0")
    assert manifest_definition.requires.minimum.value == 1
    assert manifest_definition.requires.maximum.value == 1


def test_mnemosyne_manifest_declares_all_capabilities_in_canonical_order() -> None:
    definition = parse_manifest_bytes(_manifest_bytes())

    assert tuple(
        capability.local_id.value for capability in definition.capabilities
    ) == EXPECTED_CAPABILITIES
    assert all(
        capability.kind is CapabilityKind.TOOL
        and capability.version == CapabilityContractVersion("1.0.0")
        for capability in definition.capabilities
    )
    assert len(
        {
            (capability.kind, capability.local_id)
            for capability in definition.capabilities
        }
    ) == len(EXPECTED_CAPABILITIES)


@pytest.mark.parametrize("name", sorted(READ_ONLY_CAPABILITIES))
def test_mnemosyne_manifest_declares_read_only_policy(name: str) -> None:
    definition = parse_manifest_bytes(_manifest_bytes())
    by_name = {
        capability.local_id.value: capability
        for capability in definition.capabilities
    }

    assert by_name[name].effects == ToolEffects(True, False, True, False)
    assert by_name[name].consent is ConsentRequirement.NONE


@pytest.mark.parametrize("name", sorted(NON_DESTRUCTIVE_MUTATIONS))
def test_mnemosyne_manifest_declares_non_destructive_mutation_policy(
    name: str,
) -> None:
    definition = parse_manifest_bytes(_manifest_bytes())
    by_name = {
        capability.local_id.value: capability
        for capability in definition.capabilities
    }

    assert by_name[name].effects == ToolEffects(False, False, True, False)
    assert by_name[name].consent is ConsentRequirement.PER_CALL


@pytest.mark.parametrize("name", sorted(DESTRUCTIVE_MUTATIONS))
def test_mnemosyne_manifest_declares_destructive_mutation_policy(name: str) -> None:
    definition = parse_manifest_bytes(_manifest_bytes())
    by_name = {
        capability.local_id.value: capability
        for capability in definition.capabilities
    }

    assert by_name[name].effects == ToolEffects(False, True, True, False)
    assert by_name[name].consent is ConsentRequirement.PER_CALL


def test_mnemosyne_manifest_declares_inert_configuration_data_and_authority() -> None:
    definition = parse_manifest_bytes(_manifest_bytes())

    assert definition.configuration.schema_version == ConfigurationSchemaVersion(1)
    assert definition.configuration.schema.type is ConfigurationType.OBJECT
    assert definition.configuration.schema.properties == ()
    assert definition.configuration.schema.required == ()
    assert definition.configuration.schema.additional_properties is False
    assert definition.secret_references == ()
    assert definition.data_schema_version == PluginDataSchemaVersion(1)
    assert definition.authority == AuthorityDeclaration(
        filesystem=(
            FilesystemAuthority.DATA_READ,
            FilesystemAuthority.DATA_WRITE,
        ),
        network=False,
    )


def test_mnemosyne_manifest_is_inert_and_contains_no_tool_schema_or_values() -> None:
    manifest = json.loads(_manifest_bytes())
    serialized = json.dumps(manifest, sort_keys=True)
    forbidden_fields = {
        "module",
        "class",
        "command",
        "arguments",
        "handler",
        "inputSchema",
        "outputSchema",
        "public_name",
        "path",
        "environment",
        "configuration_values",
        "secret_values",
        "enabled",
        "approved",
        "lifecycle",
    }

    def keys(value: object) -> set[str]:
        if isinstance(value, dict):
            return set(value) | {
                nested_key
                for nested_value in value.values()
                for nested_key in keys(nested_value)
            }
        if isinstance(value, list):
            return {
                nested_key
                for nested_value in value
                for nested_key in keys(nested_value)
            }
        return set()

    assert keys(manifest).isdisjoint(forbidden_fields)
    assert "MNEMOSYNE_" not in serialized
    assert "~/.mnemosyne" not in serialized
    assert "memory_root" not in serialized


def test_adapter_definition_is_complete_even_when_mutations_are_disabled() -> None:
    definition = mnemosyne.mnemosyne_plugin_definition()
    contribution = mnemosyne.build_mnemosyne_contribution(False)

    assert tuple(
        capability.local_id for capability in definition.capabilities
    ) == tuple(CapabilityLocalId(name) for name in EXPECTED_CAPABILITIES)
    assert tuple(
        tool.capability.local_id.value for tool in contribution.tools
    ) == EXPECTED_CAPABILITIES[:3]


def test_contribution_policy_is_derived_from_the_canonical_definition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    definition = mnemosyne.mnemosyne_plugin_definition()
    capability = definition.capabilities[0]
    changed = tuple(
        type(item)(
            kind=item.kind,
            local_id=item.local_id,
            version=item.version,
            effects=(
                ToolEffects(False, True, False, True)
                if item is capability
                else item.effects
            ),
            consent=(
                ConsentRequirement.PER_CALL
                if item is capability
                else item.consent
            ),
        )
        for item in definition.capabilities
    )
    monkeypatch.setattr(mnemosyne, "_CAPABILITY_DECLARATIONS", changed)

    contribution = mnemosyne.build_mnemosyne_contribution(False)

    assert contribution.tools[0].effects == ToolEffects(False, True, False, True)
    assert contribution.tools[0].consent is ConsentRequirement.PER_CALL
