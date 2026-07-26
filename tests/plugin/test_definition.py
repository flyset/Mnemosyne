import ast
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

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


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFINITION_MODULE = PROJECT_ROOT / "mymcp" / "plugin" / "definition.py"


def _capability(name: str = "memory_recall") -> CapabilityDeclaration:
    return CapabilityDeclaration(
        kind=CapabilityKind.TOOL,
        local_id=CapabilityLocalId(name),
        version=CapabilityContractVersion("1.0.0"),
        effects=ToolEffects(True, False, True, False),
        consent=ConsentRequirement.NONE,
    )


def _empty_configuration() -> ConfigurationDeclaration:
    return ConfigurationDeclaration(
        schema_version=ConfigurationSchemaVersion(1),
        schema=ConfigurationSchema(
            type=ConfigurationType.OBJECT,
            properties=(),
            required=(),
            additional_properties=False,
        ),
    )


def _definition(**replacements: object) -> PluginDefinition:
    values: dict[str, object] = {
        "manifest_version": ManifestVersion(1),
        "plugin_id": PluginId("mnemosyne"),
        "title": PluginTitle("Mnemosyne"),
        "description": PluginDescription("User-governed local memory."),
        "version": PluginVersion("0.1.0"),
        "requires": HostApiRange(HostApiVersion(1), HostApiVersion(1)),
        "capabilities": (_capability(),),
        "configuration": _empty_configuration(),
        "secret_references": (),
        "data_schema_version": PluginDataSchemaVersion(1),
        "authority": AuthorityDeclaration(
            filesystem=(
                FilesystemAuthority.DATA_READ,
                FilesystemAuthority.DATA_WRITE,
            ),
            network=False,
        ),
    }
    values.update(replacements)
    return PluginDefinition(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("factory", "valid"),
    [
        (ManifestVersion, 1),
        (ConfigurationSchemaVersion, 1),
        (HostApiVersion, 1),
        (HostApiVersion, 255),
        (PluginDataSchemaVersion, 1),
        (PluginDataSchemaVersion, 255),
    ],
)
def test_integer_contract_values_accept_only_their_bounded_range(
    factory: type,
    valid: int,
) -> None:
    assert factory(valid).value == valid


@pytest.mark.parametrize(
    ("factory", "invalid"),
    [
        (ManifestVersion, 0),
        (ManifestVersion, 2),
        (ManifestVersion, True),
        (ConfigurationSchemaVersion, 0),
        (ConfigurationSchemaVersion, 2),
        (HostApiVersion, 0),
        (HostApiVersion, 256),
        (HostApiVersion, True),
        (PluginDataSchemaVersion, 0),
        (PluginDataSchemaVersion, 256),
        (PluginDataSchemaVersion, True),
    ],
)
def test_integer_contract_values_reject_invalid_values(
    factory: type,
    invalid: object,
) -> None:
    with pytest.raises(ValueError):
        factory(invalid)


def test_host_api_range_is_frozen_and_ordered() -> None:
    supported = HostApiRange(HostApiVersion(1), HostApiVersion(2))

    assert supported.minimum == HostApiVersion(1)
    assert supported.maximum == HostApiVersion(2)
    with pytest.raises(FrozenInstanceError):
        supported.minimum = HostApiVersion(2)  # type: ignore[misc]
    with pytest.raises(ValueError, match="^invalid host api range$"):
        HostApiRange(HostApiVersion(2), HostApiVersion(1))


@pytest.mark.parametrize(
    ("factory", "valid", "maximum"),
    [
        (PluginTitle, "M", 128),
        (PluginTitle, "M" * 128, 128),
        (PluginDescription, "Local memory.", 4096),
        (PluginDescription, "M" * 4096, 4096),
    ],
)
def test_bounded_text_contracts_accept_nonempty_control_free_unicode(
    factory: type,
    valid: str,
    maximum: int,
) -> None:
    value = factory(valid)

    assert value.value == valid
    assert len(value.value) <= maximum


@pytest.mark.parametrize(
    ("factory", "invalid"),
    [
        (PluginTitle, ""),
        (PluginTitle, "M" * 129),
        (PluginTitle, "bad\nname"),
        (PluginDescription, ""),
        (PluginDescription, "M" * 4097),
        (PluginDescription, "bad\x00description"),
    ],
)
def test_bounded_text_contracts_reject_empty_long_or_control_text(
    factory: type,
    invalid: str,
) -> None:
    with pytest.raises(ValueError):
        factory(invalid)


@pytest.mark.parametrize(
    "value",
    ["0.1.0", "1.0.0", "1.2.3-alpha.1", "1.0.0+schema.2"],
)
def test_capability_contract_version_uses_strict_semver(value: str) -> None:
    assert CapabilityContractVersion(value).value == value


@pytest.mark.parametrize("value", ["", "1", "v1.0.0", "01.0.0", "1.0.0+"])
def test_capability_contract_version_rejects_invalid_semver(value: str) -> None:
    with pytest.raises(ValueError, match="^invalid capability contract version$"):
        CapabilityContractVersion(value)


def test_capability_declaration_is_frozen_and_typed() -> None:
    capability = _capability()

    assert capability.kind is CapabilityKind.TOOL
    assert capability.local_id == CapabilityLocalId("memory_recall")
    with pytest.raises(FrozenInstanceError):
        capability.consent = ConsentRequirement.PER_CALL  # type: ignore[misc]
    with pytest.raises(ValueError, match="^invalid capability declaration$"):
        CapabilityDeclaration(  # type: ignore[arg-type]
            kind="tool",
            local_id=capability.local_id,
            version=capability.version,
            effects=capability.effects,
            consent=capability.consent,
        )


@pytest.mark.parametrize(
    "configuration_type",
    list(ConfigurationType),
)
def test_configuration_schema_supports_only_closed_types(
    configuration_type: ConfigurationType,
) -> None:
    if configuration_type is ConfigurationType.OBJECT:
        schema = ConfigurationSchema(
            type=configuration_type,
            properties=(),
            required=(),
            additional_properties=False,
        )
    elif configuration_type is ConfigurationType.ARRAY:
        schema = ConfigurationSchema(
            type=configuration_type,
            items=ConfigurationSchema(type=ConfigurationType.STRING),
        )
    else:
        schema = ConfigurationSchema(type=configuration_type)

    assert schema.type is configuration_type


def test_configuration_schema_snapshots_nested_properties() -> None:
    properties = [
        ("enabled", ConfigurationSchema(type=ConfigurationType.BOOLEAN)),
    ]
    required = ["enabled"]
    schema = ConfigurationSchema(
        type=ConfigurationType.OBJECT,
        properties=properties,
        required=required,
        additional_properties=False,
    )
    properties.append(("other", ConfigurationSchema(type=ConfigurationType.STRING)))
    required.append("other")

    assert schema.properties == (
        ("enabled", ConfigurationSchema(type=ConfigurationType.BOOLEAN)),
    )
    assert schema.required == ("enabled",)
    with pytest.raises(FrozenInstanceError):
        schema.type = ConfigurationType.STRING  # type: ignore[misc]


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "type": ConfigurationType.OBJECT,
            "properties": (),
            "required": (),
            "additional_properties": True,
        },
        {
            "type": ConfigurationType.OBJECT,
            "properties": (
                ("name", ConfigurationSchema(type=ConfigurationType.STRING)),
                ("name", ConfigurationSchema(type=ConfigurationType.STRING)),
            ),
            "required": (),
            "additional_properties": False,
        },
        {
            "type": ConfigurationType.OBJECT,
            "properties": (),
            "required": ("missing",),
            "additional_properties": False,
        },
        {
            "type": ConfigurationType.OBJECT,
            "properties": tuple(
                (f"p{index}", ConfigurationSchema(type=ConfigurationType.STRING))
                for index in range(33)
            ),
            "required": (),
            "additional_properties": False,
        },
        {"type": ConfigurationType.ARRAY},
        {
            "type": ConfigurationType.STRING,
            "items": ConfigurationSchema(type=ConfigurationType.STRING),
        },
    ],
)
def test_configuration_schema_rejects_invalid_shape(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="^invalid configuration schema$"):
        ConfigurationSchema(**kwargs)  # type: ignore[arg-type]


def test_configuration_schema_rejects_depth_above_four() -> None:
    schema = ConfigurationSchema(type=ConfigurationType.STRING)
    for _ in range(2):
        schema = ConfigurationSchema(type=ConfigurationType.ARRAY, items=schema)

    schema = ConfigurationSchema(type=ConfigurationType.ARRAY, items=schema)
    assert schema._depth == 4
    with pytest.raises(ValueError, match="^invalid configuration schema$"):
        ConfigurationSchema(
            type=ConfigurationType.ARRAY,
            items=schema,
        )


def test_configuration_declaration_is_typed_and_frozen() -> None:
    configuration = _empty_configuration()

    assert configuration.schema_version == ConfigurationSchemaVersion(1)
    with pytest.raises(FrozenInstanceError):
        configuration.schema = ConfigurationSchema(  # type: ignore[misc]
            type=ConfigurationType.STRING
        )
    with pytest.raises(ValueError, match="^invalid configuration declaration$"):
        ConfigurationDeclaration(  # type: ignore[arg-type]
            schema_version=1,
            schema=configuration.schema,
        )


@pytest.mark.parametrize(
    "schema",
    [
        ConfigurationSchema(type=ConfigurationType.STRING),
        ConfigurationSchema(
            type=ConfigurationType.ARRAY,
            items=ConfigurationSchema(type=ConfigurationType.STRING),
        ),
    ],
)
def test_configuration_declaration_requires_an_object_root(
    schema: ConfigurationSchema,
) -> None:
    with pytest.raises(ValueError, match="^invalid configuration declaration$"):
        ConfigurationDeclaration(
            schema_version=ConfigurationSchemaVersion(1),
            schema=schema,
        )


@pytest.mark.parametrize(
    "value",
    ["api_token", "database_password", "slot2"],
)
def test_secret_reference_slots_use_bounded_local_identity(value: str) -> None:
    assert SecretReferenceSlot(value).slot_id == CapabilityLocalId(value)


@pytest.mark.parametrize("value", ["", "API_TOKEN", "api-token", "a" * 65])
def test_secret_reference_slots_reject_invalid_identity(value: str) -> None:
    with pytest.raises(ValueError, match="^invalid secret reference slot$"):
        SecretReferenceSlot(value)


def test_authority_declaration_is_closed_frozen_and_value_free() -> None:
    authorities = [FilesystemAuthority.DATA_READ, FilesystemAuthority.DATA_WRITE]
    authority = AuthorityDeclaration(filesystem=authorities, network=False)
    authorities.append(FilesystemAuthority.CACHE_READ)

    assert authority.filesystem == (
        FilesystemAuthority.DATA_READ,
        FilesystemAuthority.DATA_WRITE,
    )
    assert authority.network is False
    with pytest.raises(FrozenInstanceError):
        authority.network = True  # type: ignore[misc]
    with pytest.raises(ValueError, match="^invalid authority declaration$"):
        AuthorityDeclaration(
            filesystem=(FilesystemAuthority.DATA_READ,) * 2,
            network=False,
        )
    with pytest.raises(ValueError, match="^invalid authority declaration$"):
        AuthorityDeclaration(filesystem=(), network=0)  # type: ignore[arg-type]


def test_plugin_definition_is_complete_frozen_and_defensive() -> None:
    capabilities = [_capability()]
    secret_references = [SecretReferenceSlot("api_token")]
    definition = _definition(
        capabilities=capabilities,
        secret_references=secret_references,
    )
    capabilities.append(_capability("memory_list"))
    secret_references.append(SecretReferenceSlot("other"))

    assert definition.capabilities == (_capability(),)
    assert definition.secret_references == (SecretReferenceSlot("api_token"),)
    with pytest.raises(FrozenInstanceError):
        definition.plugin_id = PluginId("other")  # type: ignore[misc]
    assert {field.name for field in fields(PluginDefinition)} == {
        "manifest_version",
        "plugin_id",
        "title",
        "description",
        "version",
        "requires",
        "capabilities",
        "configuration",
        "secret_references",
        "data_schema_version",
        "authority",
    }


def test_plugin_definition_rejects_duplicate_or_excessive_declarations() -> None:
    with pytest.raises(ValueError, match="^invalid plugin definition$"):
        _definition(capabilities=(_capability(), _capability()))
    with pytest.raises(ValueError, match="^invalid plugin definition$"):
        _definition(capabilities=tuple(_capability(f"tool{index}") for index in range(65)))
    with pytest.raises(ValueError, match="^invalid plugin definition$"):
        _definition(
            secret_references=(SecretReferenceSlot("token"),) * 2,
        )
    with pytest.raises(ValueError, match="^invalid plugin definition$"):
        _definition(
            secret_references=tuple(
                SecretReferenceSlot(f"slot{index}") for index in range(33)
            ),
        )


def test_plugin_definition_rejects_untyped_fields() -> None:
    with pytest.raises(ValueError, match="^invalid plugin definition$"):
        _definition(plugin_id="mnemosyne")
    with pytest.raises(ValueError, match="^invalid plugin definition$"):
        _definition(capabilities=("memory_recall",))
    with pytest.raises(ValueError, match="^invalid plugin definition$"):
        _definition(secret_references=("token",))


def test_definition_module_imports_no_concrete_plugin_runtime_or_domain() -> None:
    tree = ast.parse(DEFINITION_MODULE.read_text(encoding="utf-8"))
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
                "mymcp.mnemosyne",
                "mymcp.plugins.mnemosyne.memory",
                "mymcp.mcp",
                "mymcp.routes",
                "fastapi",
            )
        )
        for imported in imports
    )
