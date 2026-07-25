import ast
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

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


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_MODULE = PROJECT_ROOT / "mymcp" / "plugin" / "contracts.py"
PLUGIN_INIT_MODULE = PROJECT_ROOT / "mymcp" / "plugin" / "__init__.py"


@pytest.mark.parametrize("value", ["a", "mnemosyne", "my-plugin", "plugin-2"])
def test_plugin_id_accepts_bounded_lowercase_kebab_identity(value: str) -> None:
    assert PluginId(value).value == value


@pytest.mark.parametrize(
    "value",
    ["", "Mnemosyne", "my_plugin", "-plugin", "plugin-", "my--plugin", "a" * 65],
)
def test_plugin_id_rejects_invalid_identity(value: str) -> None:
    with pytest.raises(ValueError, match="^invalid plugin id$"):
        PluginId(value)


def test_plugin_id_is_frozen() -> None:
    plugin_id = PluginId("mnemosyne")

    with pytest.raises(FrozenInstanceError):
        plugin_id.value = "other"  # type: ignore[misc]


@pytest.mark.parametrize("value", ["a", "memory_recall", "tool2", "tool_2"])
def test_capability_local_id_accepts_bounded_lowercase_underscore_identity(
    value: str,
) -> None:
    assert CapabilityLocalId(value).value == value


@pytest.mark.parametrize(
    "value",
    ["", "MemoryRecall", "memory-recall", "_tool", "tool_", "my__tool", "a" * 65],
)
def test_capability_local_id_rejects_invalid_identity(value: str) -> None:
    with pytest.raises(ValueError, match="^invalid capability local id$"):
        CapabilityLocalId(value)


def test_capability_local_id_is_frozen() -> None:
    local_id = CapabilityLocalId("memory_recall")

    with pytest.raises(FrozenInstanceError):
        local_id.value = "memory_list"  # type: ignore[misc]


def test_host_api_v1_admits_only_tool_capabilities() -> None:
    assert CapabilityKind("tool") is CapabilityKind.TOOL
    with pytest.raises(ValueError):
        CapabilityKind("resource")


@pytest.mark.parametrize(
    "value",
    [
        "0.1.0",
        "1.0.0",
        "1.2.3-alpha.1",
        "1.2.3+build.5",
        "1.0.0-rc.1+x",
        "1.0.0+" + "a" * 58,
    ],
)
def test_plugin_version_accepts_strict_bounded_semver(value: str) -> None:
    assert PluginVersion(value).value == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "1",
        "1.0",
        "v1.0.0",
        "01.0.0",
        "1.01.0",
        "1.0.01",
        "1.0.0-01",
        "1.0.0-alpha..1",
        "1.0.0-alpha.",
        "1.0.0+",
        "1.0.0+" + "a" * 59,
    ],
)
def test_plugin_version_rejects_invalid_semver(value: str) -> None:
    with pytest.raises(ValueError, match="^invalid plugin version$"):
        PluginVersion(value)


def test_plugin_version_is_frozen() -> None:
    version = PluginVersion("1.0.0")

    with pytest.raises(FrozenInstanceError):
        version.value = "2.0.0"  # type: ignore[misc]


def test_qualified_capability_identity_is_frozen_and_typed() -> None:
    identity = QualifiedCapabilityId(
        plugin_id=PluginId("mnemosyne"),
        kind=CapabilityKind.TOOL,
        local_id=CapabilityLocalId("memory_recall"),
    )

    assert identity == QualifiedCapabilityId(
        PluginId("mnemosyne"), CapabilityKind.TOOL, CapabilityLocalId("memory_recall")
    )
    with pytest.raises(FrozenInstanceError):
        identity.local_id = CapabilityLocalId("memory_list")  # type: ignore[misc]
    with pytest.raises(ValueError, match="^invalid qualified capability id$"):
        QualifiedCapabilityId(  # type: ignore[arg-type]
            plugin_id="mnemosyne",
            kind=CapabilityKind.TOOL,
            local_id=CapabilityLocalId("memory_recall"),
        )


def test_tool_effects_are_frozen() -> None:
    effects = ToolEffects(
        read_only=True,
        destructive=False,
        idempotent=True,
        open_world=False,
    )

    assert effects.read_only is True
    with pytest.raises(FrozenInstanceError):
        effects.destructive = True  # type: ignore[misc]


@pytest.mark.parametrize(
    "field",
    ["read_only", "destructive", "idempotent", "open_world"],
)
def test_tool_effects_require_actual_booleans(field: str) -> None:
    values: dict[str, object] = {
        "read_only": True,
        "destructive": False,
        "idempotent": True,
        "open_world": False,
    }
    values[field] = 1

    with pytest.raises(ValueError, match="^invalid tool effects$"):
        ToolEffects(**values)  # type: ignore[arg-type]


def test_consent_requirement_is_closed_to_none_or_per_call() -> None:
    assert ConsentRequirement("none") is ConsentRequirement.NONE
    assert ConsentRequirement("per_call") is ConsentRequirement.PER_CALL
    with pytest.raises(ValueError):
        ConsentRequirement("session")


def test_public_tool_binding_retains_qualified_and_public_identity() -> None:
    identity = QualifiedCapabilityId(
        PluginId("mnemosyne"), CapabilityKind.TOOL, CapabilityLocalId("memory_recall")
    )
    binding = PublicToolBinding(capability=identity, public_name="memory_recall")
    broad_binding = PublicToolBinding(capability=identity, public_name="memory-recall")

    assert binding.capability is identity
    assert binding.public_name == "memory_recall"
    assert broad_binding.public_name == "memory-recall"
    with pytest.raises(FrozenInstanceError):
        binding.public_name = "other"  # type: ignore[misc]
    with pytest.raises(ValueError, match="^invalid public tool binding$"):
        PublicToolBinding(capability=identity, public_name="")
    with pytest.raises(ValueError, match="^invalid public tool binding$"):
        PublicToolBinding(capability="mnemosyne", public_name="memory_recall")  # type: ignore[arg-type]


@pytest.mark.parametrize("module", [CONTRACTS_MODULE, PLUGIN_INIT_MODULE])
def test_generic_contracts_import_no_concrete_plugin_or_domain(module: Path) -> None:
    tree = ast.parse(module.read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert all(
        not imported.startswith(
            (
                "mymcp.plugins",
                "mymcp.mnemosyne",
                "mymcp.memory",
                "mymcp.mcp.tools",
                "mymcp.mcp.integrations.mnemosyne",
            )
        )
        for imported in imports
    )
