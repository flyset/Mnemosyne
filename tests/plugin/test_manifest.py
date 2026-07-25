import ast
from copy import deepcopy
import json
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
from mymcp.plugin.manifest import (
    PluginContractError,
    PluginContractErrorCode,
    parse_manifest_bytes,
    parse_manifest_mapping,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_MODULE = PROJECT_ROOT / "mymcp" / "plugin" / "manifest.py"


def _manifest() -> dict[str, object]:
    return {
        "$schema": "https://mymcp.local/schemas/plugin-manifest-v1.json",
        "manifest_version": 1,
        "id": "example",
        "title": "Example",
        "description": "Example MyMCP plugin.",
        "version": "1.0.0",
        "requires": {"host_api": {"min": 1, "max": 1}},
        "capabilities": [
            {
                "kind": "tool",
                "id": "read_status",
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
                "properties": {
                    "enabled": {"type": "boolean"},
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["enabled"],
                "additionalProperties": False,
            },
        },
        "secret_references": ["api_token"],
        "data_schema_version": 1,
        "authority": {
            "filesystem": ["data_read", "data_write"],
            "network": False,
        },
    }


def test_parse_manifest_mapping_builds_complete_immutable_definition() -> None:
    definition = parse_manifest_mapping(_manifest())

    assert definition == PluginDefinition(
        manifest_version=ManifestVersion(1),
        plugin_id=PluginId("example"),
        title=PluginTitle("Example"),
        description=PluginDescription("Example MyMCP plugin."),
        version=PluginVersion("1.0.0"),
        requires=HostApiRange(HostApiVersion(1), HostApiVersion(1)),
        capabilities=(
            CapabilityDeclaration(
                kind=CapabilityKind.TOOL,
                local_id=CapabilityLocalId("read_status"),
                version=CapabilityContractVersion("1.0.0"),
                effects=ToolEffects(True, False, True, False),
                consent=ConsentRequirement.NONE,
            ),
        ),
        configuration=ConfigurationDeclaration(
            schema_version=ConfigurationSchemaVersion(1),
            schema=ConfigurationSchema(
                type=ConfigurationType.OBJECT,
                properties=(
                    (
                        "enabled",
                        ConfigurationSchema(type=ConfigurationType.BOOLEAN),
                    ),
                    (
                        "labels",
                        ConfigurationSchema(
                            type=ConfigurationType.ARRAY,
                            items=ConfigurationSchema(type=ConfigurationType.STRING),
                        ),
                    ),
                ),
                required=("enabled",),
                additional_properties=False,
            ),
        ),
        secret_references=(SecretReferenceSlot("api_token"),),
        data_schema_version=PluginDataSchemaVersion(1),
        authority=AuthorityDeclaration(
            filesystem=(
                FilesystemAuthority.DATA_READ,
                FilesystemAuthority.DATA_WRITE,
            ),
            network=False,
        ),
    )


def test_parse_manifest_bytes_accepts_strict_utf8_json_object() -> None:
    source = json.dumps(_manifest(), ensure_ascii=False).encode("utf-8")

    assert parse_manifest_bytes(source) == parse_manifest_mapping(_manifest())


def test_parse_manifest_bytes_accepts_exact_resource_limit() -> None:
    source = json.dumps(_manifest(), separators=(",", ":")).encode("utf-8")
    source += b" " * (64 * 1024 - len(source))

    assert len(source) == 64 * 1024
    assert parse_manifest_bytes(source) == parse_manifest_mapping(_manifest())


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ("not bytes", PluginContractErrorCode.INVALID_RESOURCE),
        (b"\xff", PluginContractErrorCode.INVALID_UTF8),
        (b"{", PluginContractErrorCode.INVALID_JSON),
        (b"[]", PluginContractErrorCode.INVALID_ROOT),
        (
            b'{"manifest_version":1,"manifest_version":1}',
            PluginContractErrorCode.DUPLICATE_KEY,
        ),
        (b" " * (64 * 1024 + 1), PluginContractErrorCode.RESOURCE_TOO_LARGE),
    ],
)
def test_parse_manifest_bytes_rejects_invalid_resources(
    source: object,
    code: PluginContractErrorCode,
) -> None:
    with pytest.raises(PluginContractError) as captured:
        parse_manifest_bytes(source)  # type: ignore[arg-type]

    assert captured.value.code is code


@pytest.mark.parametrize(
    ("source", "code"),
    [
        (
            b'{"outer":{"key":1,"key":2}}',
            PluginContractErrorCode.DUPLICATE_KEY,
        ),
        (b'{"value":NaN}', PluginContractErrorCode.INVALID_JSON),
        (b'{"value":Infinity}', PluginContractErrorCode.INVALID_JSON),
        (b'{"value":-Infinity}', PluginContractErrorCode.INVALID_JSON),
    ],
)
def test_parse_manifest_bytes_rejects_nested_duplicates_and_json_constants(
    source: bytes,
    code: PluginContractErrorCode,
) -> None:
    with pytest.raises(PluginContractError) as captured:
        parse_manifest_bytes(source)

    assert captured.value.code is code


@pytest.mark.parametrize("value", [None, [], "manifest", 1, True])
def test_parse_manifest_mapping_requires_a_mapping(value: object) -> None:
    with pytest.raises(PluginContractError) as captured:
        parse_manifest_mapping(value)  # type: ignore[arg-type]

    assert captured.value.code is PluginContractErrorCode.INVALID_ROOT


@pytest.mark.parametrize(
    ("field", "code"),
    [
        ("manifest_version", PluginContractErrorCode.MISSING_FIELD),
        ("id", PluginContractErrorCode.MISSING_FIELD),
        ("title", PluginContractErrorCode.MISSING_FIELD),
        ("description", PluginContractErrorCode.MISSING_FIELD),
        ("version", PluginContractErrorCode.MISSING_FIELD),
        ("requires", PluginContractErrorCode.MISSING_FIELD),
        ("capabilities", PluginContractErrorCode.MISSING_FIELD),
        ("configuration", PluginContractErrorCode.MISSING_FIELD),
        ("secret_references", PluginContractErrorCode.MISSING_FIELD),
        ("data_schema_version", PluginContractErrorCode.MISSING_FIELD),
        ("authority", PluginContractErrorCode.MISSING_FIELD),
    ],
)
def test_manifest_rejects_each_missing_required_field(
    field: str,
    code: PluginContractErrorCode,
) -> None:
    manifest = _manifest()
    del manifest[field]

    with pytest.raises(PluginContractError) as captured:
        parse_manifest_mapping(manifest)

    assert captured.value.code is code


@pytest.mark.parametrize(
    "container_path",
    [
        (),
        ("requires",),
        ("requires", "host_api"),
        ("capabilities", 0),
        ("configuration",),
        ("configuration", "schema"),
        ("configuration", "schema", "properties", "enabled"),
        ("authority",),
    ],
)
def test_manifest_rejects_unknown_fields_at_every_level(
    container_path: tuple[object, ...],
) -> None:
    manifest = _manifest()
    container: object = manifest
    for part in container_path:
        container = container[part]  # type: ignore[index]
    assert isinstance(container, dict)
    container["unexpected"] = "must-not-appear"

    with pytest.raises(PluginContractError) as captured:
        parse_manifest_mapping(manifest)

    assert captured.value.code is PluginContractErrorCode.UNKNOWN_FIELD
    assert "must-not-appear" not in str(captured.value)


@pytest.mark.parametrize(
    ("path", "value", "code"),
    [
        (("$schema",), "", PluginContractErrorCode.INVALID_FIELD),
        (("$schema",), 1, PluginContractErrorCode.INVALID_FIELD),
        (
            ("manifest_version",),
            2,
            PluginContractErrorCode.UNSUPPORTED_MANIFEST_VERSION,
        ),
        (
            ("manifest_version",),
            True,
            PluginContractErrorCode.UNSUPPORTED_MANIFEST_VERSION,
        ),
        (("id",), "Example", PluginContractErrorCode.INVALID_FIELD),
        (("title",), "bad\nname", PluginContractErrorCode.INVALID_FIELD),
        (("description",), "", PluginContractErrorCode.INVALID_FIELD),
        (("version",), "v1.0.0", PluginContractErrorCode.INVALID_FIELD),
        (("requires", "host_api", "min"), 0, PluginContractErrorCode.INVALID_FIELD),
        (("requires", "host_api", "max"), True, PluginContractErrorCode.INVALID_FIELD),
        (("capabilities",), {}, PluginContractErrorCode.INVALID_FIELD),
        (("secret_references",), {}, PluginContractErrorCode.INVALID_FIELD),
        (("data_schema_version",), 0, PluginContractErrorCode.INVALID_FIELD),
        (("authority", "network"), 0, PluginContractErrorCode.INVALID_AUTHORITY),
    ],
)
def test_manifest_rejects_invalid_scalar_and_collection_values(
    path: tuple[object, ...],
    value: object,
    code: PluginContractErrorCode,
) -> None:
    manifest = _manifest()
    container: object = manifest
    for part in path[:-1]:
        container = container[part]  # type: ignore[index]
    container[path[-1]] = value  # type: ignore[index]

    with pytest.raises(PluginContractError) as captured:
        parse_manifest_mapping(manifest)

    assert captured.value.code is code


@pytest.mark.parametrize(
    ("path", "code"),
    [
        (("capabilities",), PluginContractErrorCode.INVALID_FIELD),
        (("secret_references",), PluginContractErrorCode.INVALID_FIELD),
        (
            ("configuration", "schema", "required"),
            PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA,
        ),
        (("authority", "filesystem"), PluginContractErrorCode.INVALID_AUTHORITY),
    ],
)
def test_mapping_parser_rejects_non_json_tuple_arrays(
    path: tuple[object, ...],
    code: PluginContractErrorCode,
) -> None:
    manifest = _manifest()
    container: object = manifest
    for part in path[:-1]:
        container = container[part]  # type: ignore[index]
    original = container[path[-1]]  # type: ignore[index]
    container[path[-1]] = tuple(original)  # type: ignore[index]

    with pytest.raises(PluginContractError) as captured:
        parse_manifest_mapping(manifest)

    assert captured.value.code is code


def test_manifest_rejects_invalid_or_unsupported_host_api_range() -> None:
    manifest = _manifest()
    manifest["requires"] = {"host_api": {"min": 2, "max": 1}}

    with pytest.raises(PluginContractError) as captured:
        parse_manifest_mapping(manifest)

    assert captured.value.code is PluginContractErrorCode.INVALID_FIELD


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("kind", "resource", PluginContractErrorCode.UNSUPPORTED_CAPABILITY_KIND),
        ("id", "read-status", PluginContractErrorCode.INVALID_FIELD),
        ("version", "1", PluginContractErrorCode.INVALID_FIELD),
        ("read_only", 1, PluginContractErrorCode.INVALID_FIELD),
        ("destructive", 0, PluginContractErrorCode.INVALID_FIELD),
        ("idempotent", "yes", PluginContractErrorCode.INVALID_FIELD),
        ("open_world", None, PluginContractErrorCode.INVALID_FIELD),
        ("consent", "session", PluginContractErrorCode.INVALID_FIELD),
    ],
)
def test_manifest_rejects_invalid_capability_fields(
    field: str,
    value: object,
    code: PluginContractErrorCode,
) -> None:
    manifest = _manifest()
    capability = manifest["capabilities"][0]  # type: ignore[index]
    capability[field] = value

    with pytest.raises(PluginContractError) as captured:
        parse_manifest_mapping(manifest)

    assert captured.value.code is code


def test_manifest_rejects_duplicate_capability_identity() -> None:
    manifest = _manifest()
    manifest["capabilities"].append(  # type: ignore[union-attr]
        deepcopy(manifest["capabilities"][0])  # type: ignore[index]
    )

    with pytest.raises(PluginContractError) as captured:
        parse_manifest_mapping(manifest)

    assert captured.value.code is PluginContractErrorCode.DUPLICATE_CAPABILITY


def test_manifest_enforces_capability_count_boundaries() -> None:
    manifest = _manifest()
    base = manifest["capabilities"][0]  # type: ignore[index]
    manifest["capabilities"] = [
        deepcopy(base) | {"id": f"tool{index}"} for index in range(64)
    ]

    assert len(parse_manifest_mapping(manifest).capabilities) == 64
    manifest["capabilities"].append(deepcopy(base) | {"id": "tool64"})  # type: ignore[union-attr]
    with pytest.raises(PluginContractError) as captured:
        parse_manifest_mapping(manifest)

    assert captured.value.code is PluginContractErrorCode.INVALID_FIELD


def test_manifest_rejects_duplicate_secret_reference_slot() -> None:
    manifest = _manifest()
    manifest["secret_references"] = ["api_token", "api_token"]

    with pytest.raises(PluginContractError) as captured:
        parse_manifest_mapping(manifest)

    assert captured.value.code is PluginContractErrorCode.DUPLICATE_SECRET_REFERENCE


def test_manifest_enforces_secret_reference_count_boundaries() -> None:
    manifest = _manifest()
    manifest["secret_references"] = [f"slot{index}" for index in range(32)]

    assert len(parse_manifest_mapping(manifest).secret_references) == 32
    manifest["secret_references"].append("slot32")  # type: ignore[union-attr]
    with pytest.raises(PluginContractError) as captured:
        parse_manifest_mapping(manifest)

    assert captured.value.code is PluginContractErrorCode.INVALID_FIELD


@pytest.mark.parametrize(
    ("schema", "code"),
    [
        ({"type": "resource"}, PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA),
        (
            {
                "type": "object",
                "properties": {},
                "additionalProperties": True,
            },
            PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA,
        ),
        (
            {
                "type": "object",
                "properties": {},
                "required": ["missing"],
                "additionalProperties": False,
            },
            PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA,
        ),
        ({"type": "array"}, PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA),
        (
            {
                "type": "object",
                "properties": [[{"unhashable": "name"}]],
                "additionalProperties": False,
            },
            PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA,
        ),
        (
            {
                "type": "object",
                "properties": {},
                "required": "not-an-array",
                "additionalProperties": False,
            },
            PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA,
        ),
        (
            {"type": "string", "default": "value"},
            PluginContractErrorCode.UNKNOWN_FIELD,
        ),
        (
            {"type": "string", "$ref": "elsewhere"},
            PluginContractErrorCode.UNKNOWN_FIELD,
        ),
    ],
)
def test_manifest_rejects_invalid_configuration_schemas(
    schema: dict[str, object],
    code: PluginContractErrorCode,
) -> None:
    manifest = _manifest()
    manifest["configuration"] = {"schema_version": 1, "schema": schema}

    with pytest.raises(PluginContractError) as captured:
        parse_manifest_mapping(manifest)

    assert captured.value.code is code


def test_manifest_enforces_configuration_property_and_depth_boundaries() -> None:
    manifest = _manifest()
    properties = {f"p{index}": {"type": "string"} for index in range(32)}
    schema: dict[str, object] = {
        "type": "object",
        "properties": properties,
        "required": [],
        "additionalProperties": False,
    }
    manifest["configuration"] = {"schema_version": 1, "schema": schema}

    assert len(parse_manifest_mapping(manifest).configuration.schema.properties) == 32
    properties["p32"] = {"type": "string"}
    with pytest.raises(PluginContractError) as captured:
        parse_manifest_mapping(manifest)
    assert captured.value.code is PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA

    nested: dict[str, object] = {"type": "string"}
    for _ in range(2):
        nested = {"type": "array", "items": nested}
    manifest["configuration"] = {
        "schema_version": 1,
        "schema": {
            "type": "object",
            "properties": {"nested": nested},
            "required": [],
            "additionalProperties": False,
        },
    }
    assert parse_manifest_mapping(manifest).configuration.schema._depth == 4
    nested = {"type": "array", "items": nested}
    manifest["configuration"] = {
        "schema_version": 1,
        "schema": {
            "type": "object",
            "properties": {"nested": nested},
            "required": [],
            "additionalProperties": False,
        },
    }
    with pytest.raises(PluginContractError) as captured:
        parse_manifest_mapping(manifest)
    assert captured.value.code is PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA


def test_manifest_rejects_duplicate_required_configuration_names() -> None:
    manifest = _manifest()
    schema = manifest["configuration"]["schema"]  # type: ignore[index]
    schema["required"] = ["enabled", "enabled"]

    with pytest.raises(PluginContractError) as captured:
        parse_manifest_mapping(manifest)

    assert captured.value.code is PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA


@pytest.mark.parametrize(
    "filesystem",
    [
        ["host_root_read"],
        ["data_read", "data_read"],
        "data_read",
        [1],
    ],
)
def test_manifest_rejects_invalid_authority_filesystem_classes(
    filesystem: object,
) -> None:
    manifest = _manifest()
    manifest["authority"] = {"filesystem": filesystem, "network": False}

    with pytest.raises(PluginContractError) as captured:
        parse_manifest_mapping(manifest)

    assert captured.value.code is PluginContractErrorCode.INVALID_AUTHORITY


def test_manifest_accepts_every_closed_authority_class() -> None:
    manifest = _manifest()
    manifest["authority"] = {
        "filesystem": [authority.value for authority in FilesystemAuthority],
        "network": True,
    }

    parsed = parse_manifest_mapping(manifest)

    assert parsed.authority.filesystem == tuple(FilesystemAuthority)
    assert parsed.authority.network is True


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("module", "plugin.main"),
        ("class", "Plugin"),
        ("command", ["run"]),
        ("arguments", ["--unsafe"]),
        ("path", "/tmp/plugin"),
        ("public_name", "claimed_name"),
        ("enabled", True),
        ("approved", True),
        ("lifecycle", "active"),
        ("configuration_values", {"secret": "must-not-appear"}),
    ],
)
def test_manifest_rejects_forbidden_top_level_contract_fields(
    field: str,
    value: object,
) -> None:
    manifest = _manifest()
    manifest[field] = value

    with pytest.raises(PluginContractError) as captured:
        parse_manifest_mapping(manifest)

    assert captured.value.code is PluginContractErrorCode.UNKNOWN_FIELD
    assert "must-not-appear" not in str(captured.value)


def test_manifest_errors_are_bounded_and_do_not_expose_source_values() -> None:
    marker = "sensitive-value-that-must-not-appear"
    manifest = _manifest()
    manifest["unexpected"] = marker

    with pytest.raises(PluginContractError) as captured:
        parse_manifest_mapping(manifest)

    error = captured.value
    assert isinstance(error.code, PluginContractErrorCode)
    assert len(str(error)) <= 128
    assert marker not in str(error)
    assert "/" not in str(error)


@pytest.mark.parametrize(
    "operation",
    [
        lambda: parse_manifest_bytes(b"\xffsensitive-bytes"),
        lambda: parse_manifest_bytes(b'{"sensitive-json":'),
        lambda: parse_manifest_mapping(
            _manifest()
            | {
                "capabilities": [
                    _manifest()["capabilities"][0]  # type: ignore[index]
                    | {"consent": "sensitive-consent"}
                ]
            }
        ),
    ],
)
def test_manifest_errors_do_not_chain_source_bearing_exceptions(operation) -> None:
    with pytest.raises(PluginContractError) as captured:
        operation()

    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None


def test_manifest_module_performs_no_discovery_or_io() -> None:
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
                "importlib",
                "pathlib",
                "pkgutil",
                "socket",
                "urllib",
                "http.client",
                "mymcp.plugins",
                "mymcp.host",
                "mymcp.mnemosyne",
                "mymcp.memory",
                "mymcp.mcp",
                "mymcp.routes",
                "fastapi",
            )
        )
        for imported in imports
    )
