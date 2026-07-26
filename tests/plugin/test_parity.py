import ast
from dataclasses import replace
from importlib.resources import files
from itertools import product
from pathlib import Path

import pytest

from mymcp.plugins.mnemosyne.plugin import (
    build_mnemosyne_contribution,
    mnemosyne_plugin_definition,
)
from mymcp.plugin.composition import ActivatedTool, PluginContribution
from mymcp.plugin.contracts import (
    CapabilityKind,
    CapabilityLocalId,
    ConsentRequirement,
    PluginId,
    PluginVersion,
    QualifiedCapabilityId,
    ToolEffects,
)
from mymcp.plugin.definition import (
    AuthorityDeclaration,
    CapabilityContractVersion,
    CapabilityDeclaration,
    ConfigurationDeclaration,
    ConfigurationSchema,
    ConfigurationSchemaVersion,
    ConfigurationType,
    FilesystemAuthority,
    HostApiRange,
    HostApiVersion,
    ManifestVersion,
    PluginDataSchemaVersion,
    PluginDefinition,
    PluginDescription,
    PluginTitle,
    SecretReferenceSlot,
)
from mymcp.plugin.manifest import (
    PluginContractError,
    PluginContractErrorCode,
    parse_manifest_bytes,
    validate_plugin_contract,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_MODULE = PROJECT_ROOT / "mymcp" / "plugin" / "manifest.py"
ALL_MNEMOSYNE_CAPABILITIES = (
    "memory_recall",
    "memory_list",
    "memory_inspect",
    "memory_archive",
    "memory_restore",
    "memory_remember",
    "memory_revise",
    "memory_forget",
)


def _definition(
    *,
    plugin_id: str = "example",
    version: str = "1.0.0",
    minimum_host_api: int = 1,
    maximum_host_api: int = 1,
    capabilities: tuple[CapabilityDeclaration, ...] | None = None,
) -> PluginDefinition:
    return PluginDefinition(
        manifest_version=ManifestVersion(1),
        plugin_id=PluginId(plugin_id),
        title=PluginTitle("Example"),
        description=PluginDescription("Example plugin."),
        version=PluginVersion(version),
        requires=HostApiRange(
            HostApiVersion(minimum_host_api),
            HostApiVersion(maximum_host_api),
        ),
        capabilities=capabilities
        or (
            CapabilityDeclaration(
                kind=CapabilityKind.TOOL,
                local_id=CapabilityLocalId("read_status"),
                version=CapabilityContractVersion("1.0.0"),
                effects=ToolEffects(True, False, True, False),
                consent=ConsentRequirement.NONE,
            ),
            CapabilityDeclaration(
                kind=CapabilityKind.TOOL,
                local_id=CapabilityLocalId("write_status"),
                version=CapabilityContractVersion("1.0.0"),
                effects=ToolEffects(False, False, True, False),
                consent=ConsentRequirement.PER_CALL,
            ),
        ),
        configuration=ConfigurationDeclaration(
            schema_version=ConfigurationSchemaVersion(1),
            schema=ConfigurationSchema(
                type=ConfigurationType.OBJECT,
                properties=(),
                required=(),
                additional_properties=False,
            ),
        ),
        secret_references=(),
        data_schema_version=PluginDataSchemaVersion(1),
        authority=AuthorityDeclaration(
            filesystem=(FilesystemAuthority.DATA_READ,),
            network=False,
        ),
    )


def _activated_tool(
    definition: PluginDefinition,
    index: int,
    *,
    plugin_id: PluginId | None = None,
    effects: ToolEffects | None = None,
    consent: ConsentRequirement | None = None,
) -> ActivatedTool:
    declaration = definition.capabilities[index]
    return ActivatedTool(
        capability=QualifiedCapabilityId(
            plugin_id=plugin_id or definition.plugin_id,
            kind=declaration.kind,
            local_id=declaration.local_id,
        ),
        tool={
            "name": declaration.local_id.value,
            "description": "Test Tool.",
            "inputSchema": {"type": "object"},
        },
        handler=lambda arguments: arguments,
        effects=effects or declaration.effects,
        consent=consent or declaration.consent,
    )


def _contribution(
    definition: PluginDefinition,
    *indexes: int,
    plugin_id: PluginId | None = None,
    version: PluginVersion | None = None,
    tools: tuple[ActivatedTool, ...] | None = None,
) -> PluginContribution:
    return PluginContribution(
        plugin_id=plugin_id or definition.plugin_id,
        version=version or definition.version,
        tools=tools
        if tools is not None
        else tuple(_activated_tool(definition, index) for index in indexes),
    )


def _assert_error(
    code: PluginContractErrorCode,
    operation,
) -> None:
    with pytest.raises(PluginContractError) as captured:
        operation()

    assert captured.value.code is code
    assert len(str(captured.value)) <= 128
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None


def test_exact_manifest_definition_and_contribution_parity_passes() -> None:
    definition = _definition()

    result = validate_plugin_contract(
        manifest_definition=definition,
        adapter_definition=definition,
        contribution=_contribution(definition, 0, 1),
        supported_host_api=HostApiVersion(1),
    )

    assert result is None


@pytest.mark.parametrize(
    ("minimum", "maximum", "supported", "passes"),
    [
        (1, 1, 1, True),
        (1, 2, 1, True),
        (1, 2, 2, True),
        (2, 2, 1, False),
        (1, 1, 2, False),
    ],
)
def test_host_api_compatibility_is_explicit(
    minimum: int,
    maximum: int,
    supported: int,
    passes: bool,
) -> None:
    definition = _definition(
        minimum_host_api=minimum,
        maximum_host_api=maximum,
    )

    operation = lambda: validate_plugin_contract(
        manifest_definition=definition,
        adapter_definition=definition,
        contribution=_contribution(definition, 0),
        supported_host_api=HostApiVersion(supported),
    )
    if passes:
        assert operation() is None
    else:
        _assert_error(PluginContractErrorCode.HOST_API_INCOMPATIBLE, operation)


@pytest.mark.parametrize(
    "replacement",
    [
        {"manifest_version": ManifestVersion(1), "title": PluginTitle("Other")},
        {"description": PluginDescription("Different description.")},
        {"version": PluginVersion("1.0.1")},
        {"requires": HostApiRange(HostApiVersion(1), HostApiVersion(2))},
        {
            "capabilities": (
                CapabilityDeclaration(
                    kind=CapabilityKind.TOOL,
                    local_id=CapabilityLocalId("read_status"),
                    version=CapabilityContractVersion("2.0.0"),
                    effects=ToolEffects(True, False, True, False),
                    consent=ConsentRequirement.NONE,
                ),
                _definition().capabilities[1],
            )
        },
        {
            "configuration": ConfigurationDeclaration(
                schema_version=ConfigurationSchemaVersion(1),
                schema=ConfigurationSchema(
                    type=ConfigurationType.OBJECT,
                    properties=(("enabled", ConfigurationSchema(type=ConfigurationType.BOOLEAN)),),
                    required=(),
                    additional_properties=False,
                ),
            )
        },
        {"secret_references": (SecretReferenceSlot("token"),)},
        {"data_schema_version": PluginDataSchemaVersion(2)},
        {
            "authority": AuthorityDeclaration(
                filesystem=(FilesystemAuthority.DATA_READ,),
                network=True,
            )
        },
    ],
)
def test_every_definition_difference_fails_exact_manifest_parity(
    replacement: dict[str, object],
) -> None:
    manifest_definition = _definition()
    adapter_definition = replace(manifest_definition, **replacement)

    _assert_error(
        PluginContractErrorCode.DEFINITION_MISMATCH,
        lambda: validate_plugin_contract(
            manifest_definition=manifest_definition,
            adapter_definition=adapter_definition,
            contribution=_contribution(adapter_definition, 0),
            supported_host_api=HostApiVersion(1),
        ),
    )


def test_contribution_plugin_identity_must_match_definition() -> None:
    definition = _definition()

    _assert_error(
        PluginContractErrorCode.CONTRIBUTION_PLUGIN_MISMATCH,
        lambda: validate_plugin_contract(
            manifest_definition=definition,
            adapter_definition=definition,
            contribution=_contribution(
                definition,
                0,
                plugin_id=PluginId("other"),
            ),
            supported_host_api=HostApiVersion(1),
        ),
    )


def test_contribution_version_must_match_definition() -> None:
    definition = _definition()

    _assert_error(
        PluginContractErrorCode.CONTRIBUTION_VERSION_MISMATCH,
        lambda: validate_plugin_contract(
            manifest_definition=definition,
            adapter_definition=definition,
            contribution=_contribution(
                definition,
                0,
                version=PluginVersion("1.0.1"),
            ),
            supported_host_api=HostApiVersion(1),
        ),
    )


def test_selected_capability_must_be_declared() -> None:
    definition = _definition()
    undeclared = ActivatedTool(
        capability=QualifiedCapabilityId(
            definition.plugin_id,
            CapabilityKind.TOOL,
            CapabilityLocalId("undeclared"),
        ),
        tool={"name": "undeclared", "inputSchema": {"type": "object"}},
        handler=lambda arguments: arguments,
        effects=ToolEffects(True, False, True, False),
        consent=ConsentRequirement.NONE,
    )

    _assert_error(
        PluginContractErrorCode.UNDECLARED_CAPABILITY,
        lambda: validate_plugin_contract(
            manifest_definition=definition,
            adapter_definition=definition,
            contribution=_contribution(definition, tools=(undeclared,)),
            supported_host_api=HostApiVersion(1),
        ),
    )


def test_selected_capabilities_must_not_repeat() -> None:
    definition = _definition()
    selected = _activated_tool(definition, 0)

    _assert_error(
        PluginContractErrorCode.DUPLICATE_SELECTED_CAPABILITY,
        lambda: validate_plugin_contract(
            manifest_definition=definition,
            adapter_definition=definition,
            contribution=_contribution(definition, tools=(selected, selected)),
            supported_host_api=HostApiVersion(1),
        ),
    )


def test_selected_capabilities_must_preserve_declaration_order() -> None:
    definition = _definition()

    _assert_error(
        PluginContractErrorCode.CAPABILITY_ORDER_MISMATCH,
        lambda: validate_plugin_contract(
            manifest_definition=definition,
            adapter_definition=definition,
            contribution=_contribution(definition, 1, 0),
            supported_host_api=HostApiVersion(1),
        ),
    )


@pytest.mark.parametrize(
    "tool",
    [
        lambda definition: _activated_tool(
            definition,
            0,
            effects=ToolEffects(False, True, False, True),
        ),
        lambda definition: _activated_tool(
            definition,
            0,
            consent=ConsentRequirement.PER_CALL,
        ),
    ],
)
def test_selected_capability_metadata_must_match_declaration(tool) -> None:
    definition = _definition()

    _assert_error(
        PluginContractErrorCode.CAPABILITY_METADATA_MISMATCH,
        lambda: validate_plugin_contract(
            manifest_definition=definition,
            adapter_definition=definition,
            contribution=_contribution(definition, tools=(tool(definition),)),
            supported_host_api=HostApiVersion(1),
        ),
    )


@pytest.mark.parametrize(
    ("remember", "archive_restore", "revise", "forget"),
    list(product((False, True), repeat=4)),
)
def test_every_mnemosyne_gate_subset_passes_complete_declaration_parity(
    remember: bool,
    archive_restore: bool,
    revise: bool,
    forget: bool,
) -> None:
    manifest_definition = parse_manifest_bytes(
        files("mymcp.plugins.mnemosyne").joinpath("manifest.json").read_bytes()
    )
    adapter_definition = mnemosyne_plugin_definition()
    contribution = build_mnemosyne_contribution(
        remember,
        memory_archive_restore_enabled=archive_restore,
        memory_revise_enabled=revise,
        memory_forget_enabled=forget,
    )

    assert validate_plugin_contract(
        manifest_definition=manifest_definition,
        adapter_definition=adapter_definition,
        contribution=contribution,
        supported_host_api=HostApiVersion(1),
    ) is None
    assert tuple(
        capability.local_id.value for capability in adapter_definition.capabilities
    ) == ALL_MNEMOSYNE_CAPABILITIES


def test_generic_parity_validation_imports_no_concrete_plugin_or_runtime() -> None:
    tree = ast.parse(MANIFEST_MODULE.read_text(encoding="utf-8"))
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
                "mymcp.host",
                "mymcp.mcp.integrations",
                "mymcp.mcp.tools",
                "mymcp.plugins.mnemosyne.memory",
                "mymcp.mnemosyne",
                "mymcp.routes",
                "fastapi",
            )
        )
        for imported in imports
    )
