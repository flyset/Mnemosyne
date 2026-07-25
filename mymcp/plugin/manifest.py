from collections.abc import Mapping
from enum import StrEnum
import json
from typing import NoReturn

from mymcp.plugin.composition import PluginContribution
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


_MAX_MANIFEST_BYTES = 64 * 1024
_MAX_SCHEMA_URI_LENGTH = 2048


class PluginContractErrorCode(StrEnum):
    INVALID_RESOURCE = "manifest_resource_invalid"
    RESOURCE_TOO_LARGE = "manifest_resource_too_large"
    INVALID_UTF8 = "manifest_resource_invalid_utf8"
    INVALID_JSON = "manifest_resource_invalid_json"
    DUPLICATE_KEY = "manifest_resource_duplicate_key"
    INVALID_ROOT = "manifest_root_invalid"
    UNKNOWN_FIELD = "manifest_unknown_field"
    MISSING_FIELD = "manifest_missing_field"
    INVALID_FIELD = "manifest_invalid_field"
    UNSUPPORTED_MANIFEST_VERSION = "manifest_version_unsupported"
    UNSUPPORTED_CAPABILITY_KIND = "manifest_capability_kind_unsupported"
    DUPLICATE_CAPABILITY = "manifest_duplicate_capability"
    DUPLICATE_SECRET_REFERENCE = "manifest_duplicate_secret_reference"
    INVALID_CONFIGURATION_SCHEMA = "manifest_configuration_schema_invalid"
    INVALID_AUTHORITY = "manifest_authority_invalid"
    HOST_API_INCOMPATIBLE = "host_api_incompatible"
    DEFINITION_MISMATCH = "definition_manifest_mismatch"
    CONTRIBUTION_PLUGIN_MISMATCH = "contribution_plugin_mismatch"
    CONTRIBUTION_VERSION_MISMATCH = "contribution_version_mismatch"
    UNDECLARED_CAPABILITY = "undeclared_capability"
    DUPLICATE_SELECTED_CAPABILITY = "duplicate_selected_capability"
    CAPABILITY_ORDER_MISMATCH = "capability_order_mismatch"
    CAPABILITY_METADATA_MISMATCH = "capability_metadata_mismatch"


class PluginContractError(ValueError):
    def __init__(self, code: PluginContractErrorCode, message: str) -> None:
        self.code = code
        super().__init__(message)


class _DuplicateJsonKeyError(ValueError):
    pass


def _fail(code: PluginContractErrorCode, message: str) -> NoReturn:
    raise PluginContractError(code, message)


def _strict_object(
    value: object,
    *,
    required: frozenset[str],
    optional: frozenset[str] = frozenset(),
    invalid_code: PluginContractErrorCode = PluginContractErrorCode.INVALID_FIELD,
    missing_code: PluginContractErrorCode = PluginContractErrorCode.MISSING_FIELD,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(
        not isinstance(key, str) for key in value
    ):
        _fail(invalid_code, "plugin manifest contains an invalid object")
    keys = frozenset(value)
    if keys - required - optional:
        _fail(
            PluginContractErrorCode.UNKNOWN_FIELD,
            "plugin manifest contains an unknown field",
        )
    if required - keys:
        _fail(
            missing_code,
            "plugin manifest is missing a required field",
        )
    return value


def _strict_list(
    value: object,
    *,
    code: PluginContractErrorCode = PluginContractErrorCode.INVALID_FIELD,
) -> list[object]:
    if not isinstance(value, list):
        _fail(code, "plugin manifest contains an invalid array")
    return value


def _strict_bool(
    value: object,
    *,
    code: PluginContractErrorCode = PluginContractErrorCode.INVALID_FIELD,
) -> bool:
    if type(value) is not bool:
        _fail(code, "plugin manifest contains an invalid boolean")
    return value


def _parse_capability(value: object) -> CapabilityDeclaration:
    fields = _strict_object(
        value,
        required=frozenset(
            {
                "kind",
                "id",
                "version",
                "read_only",
                "destructive",
                "idempotent",
                "open_world",
                "consent",
            }
        ),
    )
    if fields["kind"] != CapabilityKind.TOOL.value:
        _fail(
            PluginContractErrorCode.UNSUPPORTED_CAPABILITY_KIND,
            "plugin manifest declares an unsupported capability kind",
        )
    try:
        capability = CapabilityDeclaration(
            kind=CapabilityKind.TOOL,
            local_id=CapabilityLocalId(fields["id"]),  # type: ignore[arg-type]
            version=CapabilityContractVersion(fields["version"]),  # type: ignore[arg-type]
            effects=ToolEffects(
                read_only=_strict_bool(fields["read_only"]),
                destructive=_strict_bool(fields["destructive"]),
                idempotent=_strict_bool(fields["idempotent"]),
                open_world=_strict_bool(fields["open_world"]),
            ),
            consent=ConsentRequirement(fields["consent"]),
        )
    except PluginContractError:
        raise
    except (TypeError, ValueError):
        capability = None
    if capability is None:
        _fail(
            PluginContractErrorCode.INVALID_FIELD,
            "plugin manifest contains an invalid capability field",
        )
    return capability


def _parse_configuration_schema(value: object) -> ConfigurationSchema:
    fields = _strict_object(
        value,
        required=frozenset({"type"}),
        optional=frozenset(
            {"properties", "required", "additionalProperties", "items"}
        ),
        invalid_code=PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA,
    )
    try:
        configuration_type = ConfigurationType(fields["type"])
    except (TypeError, ValueError):
        configuration_type = None
    if configuration_type is None:
        _fail(
            PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA,
            "plugin manifest contains an invalid configuration schema",
        )

    try:
        if configuration_type is ConfigurationType.OBJECT:
            object_fields = _strict_object(
                fields,
                required=frozenset({"type", "properties", "additionalProperties"}),
                optional=frozenset({"required"}),
                invalid_code=PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA,
                missing_code=PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA,
            )
            properties = object_fields["properties"]
            if not isinstance(properties, Mapping) or any(
                not isinstance(name, str) for name in properties
            ):
                _fail(
                    PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA,
                    "plugin manifest contains an invalid configuration schema",
                )
            required = _strict_list(
                object_fields.get("required", []),
                code=PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA,
            )
            return ConfigurationSchema(
                type=configuration_type,
                properties=tuple(
                    (name, _parse_configuration_schema(schema))
                    for name, schema in properties.items()
                ),
                required=tuple(required),  # type: ignore[arg-type]
                additional_properties=_strict_bool(
                    object_fields["additionalProperties"],
                    code=PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA,
                ),
            )
        if configuration_type is ConfigurationType.ARRAY:
            array_fields = _strict_object(
                fields,
                required=frozenset({"type", "items"}),
                invalid_code=PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA,
                missing_code=PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA,
            )
            return ConfigurationSchema(
                type=configuration_type,
                items=_parse_configuration_schema(array_fields["items"]),
            )
        _strict_object(
            fields,
            required=frozenset({"type"}),
            invalid_code=PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA,
        )
        return ConfigurationSchema(type=configuration_type)
    except PluginContractError:
        raise
    except (TypeError, ValueError):
        pass
    _fail(
        PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA,
        "plugin manifest contains an invalid configuration schema",
    )


def _parse_configuration(value: object) -> ConfigurationDeclaration:
    fields = _strict_object(
        value,
        required=frozenset({"schema_version", "schema"}),
    )
    try:
        configuration = ConfigurationDeclaration(
            schema_version=ConfigurationSchemaVersion(fields["schema_version"]),  # type: ignore[arg-type]
            schema=_parse_configuration_schema(fields["schema"]),
        )
    except PluginContractError:
        raise
    except (TypeError, ValueError):
        configuration = None
    if configuration is None:
        _fail(
            PluginContractErrorCode.INVALID_CONFIGURATION_SCHEMA,
            "plugin manifest contains an invalid configuration schema",
        )
    return configuration


def _parse_authority(value: object) -> AuthorityDeclaration:
    fields = _strict_object(
        value,
        required=frozenset({"filesystem", "network"}),
        invalid_code=PluginContractErrorCode.INVALID_AUTHORITY,
    )
    try:
        filesystem = _strict_list(
            fields["filesystem"],
            code=PluginContractErrorCode.INVALID_AUTHORITY,
        )
        authority = AuthorityDeclaration(
            filesystem=tuple(FilesystemAuthority(item) for item in filesystem),
            network=_strict_bool(
                fields["network"],
                code=PluginContractErrorCode.INVALID_AUTHORITY,
            ),
        )
    except PluginContractError:
        raise
    except (TypeError, ValueError):
        authority = None
    if authority is None:
        _fail(
            PluginContractErrorCode.INVALID_AUTHORITY,
            "plugin manifest contains an invalid authority declaration",
        )
    return authority


def parse_manifest_mapping(source: Mapping[str, object]) -> PluginDefinition:
    fields = _strict_object(
        source,
        required=frozenset(
            {
                "manifest_version",
                "id",
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
        ),
        optional=frozenset({"$schema"}),
        invalid_code=PluginContractErrorCode.INVALID_ROOT,
    )
    schema_uri = fields.get("$schema")
    if schema_uri is not None and (
        not isinstance(schema_uri, str)
        or not 0 < len(schema_uri) <= _MAX_SCHEMA_URI_LENGTH
        or any(ord(character) < 32 or ord(character) == 127 for character in schema_uri)
    ):
        _fail(
            PluginContractErrorCode.INVALID_FIELD,
            "plugin manifest contains an invalid schema identifier",
        )
    if type(fields["manifest_version"]) is not int or fields["manifest_version"] != 1:
        _fail(
            PluginContractErrorCode.UNSUPPORTED_MANIFEST_VERSION,
            "plugin manifest version is unsupported",
        )

    requires = _strict_object(
        fields["requires"],
        required=frozenset({"host_api"}),
    )
    host_api = _strict_object(
        requires["host_api"],
        required=frozenset({"min", "max"}),
    )
    capability_values = _strict_list(fields["capabilities"])
    capabilities = tuple(_parse_capability(value) for value in capability_values)
    capability_identities = tuple(
        (capability.kind, capability.local_id) for capability in capabilities
    )
    if len(set(capability_identities)) != len(capability_identities):
        _fail(
            PluginContractErrorCode.DUPLICATE_CAPABILITY,
            "plugin manifest contains a duplicate capability",
        )

    secret_values = _strict_list(fields["secret_references"])
    try:
        secret_references = tuple(SecretReferenceSlot(value) for value in secret_values)
    except (TypeError, ValueError):
        secret_references = None
    if secret_references is None:
        _fail(
            PluginContractErrorCode.INVALID_FIELD,
            "plugin manifest contains an invalid secret reference",
        )
    secret_ids = tuple(slot.slot_id for slot in secret_references)
    if len(set(secret_ids)) != len(secret_ids):
        _fail(
            PluginContractErrorCode.DUPLICATE_SECRET_REFERENCE,
            "plugin manifest contains a duplicate secret reference",
        )

    try:
        definition = PluginDefinition(
            manifest_version=ManifestVersion(fields["manifest_version"]),
            plugin_id=PluginId(fields["id"]),  # type: ignore[arg-type]
            title=PluginTitle(fields["title"]),  # type: ignore[arg-type]
            description=PluginDescription(fields["description"]),  # type: ignore[arg-type]
            version=PluginVersion(fields["version"]),  # type: ignore[arg-type]
            requires=HostApiRange(
                minimum=HostApiVersion(host_api["min"]),  # type: ignore[arg-type]
                maximum=HostApiVersion(host_api["max"]),  # type: ignore[arg-type]
            ),
            capabilities=capabilities,
            configuration=_parse_configuration(fields["configuration"]),
            secret_references=secret_references,
            data_schema_version=PluginDataSchemaVersion(
                fields["data_schema_version"]  # type: ignore[arg-type]
            ),
            authority=_parse_authority(fields["authority"]),
        )
    except PluginContractError:
        raise
    except (TypeError, ValueError):
        definition = None
    if definition is None:
        _fail(
            PluginContractErrorCode.INVALID_FIELD,
            "plugin manifest contains an invalid field",
        )
    return definition


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKeyError
        result[key] = value
    return result


def _reject_json_constant(_: str) -> NoReturn:
    raise ValueError


def parse_manifest_bytes(source: bytes) -> PluginDefinition:
    if not isinstance(source, bytes):
        _fail(
            PluginContractErrorCode.INVALID_RESOURCE,
            "plugin manifest resource must be bytes",
        )
    if len(source) > _MAX_MANIFEST_BYTES:
        _fail(
            PluginContractErrorCode.RESOURCE_TOO_LARGE,
            "plugin manifest resource is too large",
        )
    try:
        text = source.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        text = None
    if text is None:
        _fail(
            PluginContractErrorCode.INVALID_UTF8,
            "plugin manifest resource is not valid UTF-8",
        )
    json_error: PluginContractErrorCode | None = None
    try:
        decoded = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except _DuplicateJsonKeyError:
        decoded = None
        json_error = PluginContractErrorCode.DUPLICATE_KEY
    except (ValueError, json.JSONDecodeError):
        decoded = None
        json_error = PluginContractErrorCode.INVALID_JSON
    if json_error is PluginContractErrorCode.DUPLICATE_KEY:
        _fail(
            PluginContractErrorCode.DUPLICATE_KEY,
            "plugin manifest resource contains a duplicate key",
        )
    if json_error is PluginContractErrorCode.INVALID_JSON:
        _fail(
            PluginContractErrorCode.INVALID_JSON,
            "plugin manifest resource is not valid JSON",
        )
    if not isinstance(decoded, Mapping):
        _fail(
            PluginContractErrorCode.INVALID_ROOT,
            "plugin manifest root must be an object",
        )
    return parse_manifest_mapping(decoded)


def validate_plugin_contract(
    *,
    manifest_definition: PluginDefinition,
    adapter_definition: PluginDefinition,
    contribution: PluginContribution,
    supported_host_api: HostApiVersion,
) -> None:
    if (
        not isinstance(manifest_definition, PluginDefinition)
        or not isinstance(adapter_definition, PluginDefinition)
        or manifest_definition != adapter_definition
    ):
        _fail(
            PluginContractErrorCode.DEFINITION_MISMATCH,
            "plugin definition does not match manifest",
        )
    if (
        not isinstance(supported_host_api, HostApiVersion)
        or not manifest_definition.requires.minimum.value
        <= supported_host_api.value
        <= manifest_definition.requires.maximum.value
    ):
        _fail(
            PluginContractErrorCode.HOST_API_INCOMPATIBLE,
            "plugin does not support the host API",
        )
    if (
        not isinstance(contribution, PluginContribution)
        or contribution.plugin_id != manifest_definition.plugin_id
    ):
        _fail(
            PluginContractErrorCode.CONTRIBUTION_PLUGIN_MISMATCH,
            "plugin contribution identity does not match definition",
        )
    if contribution.version != manifest_definition.version:
        _fail(
            PluginContractErrorCode.CONTRIBUTION_VERSION_MISMATCH,
            "plugin contribution version does not match definition",
        )

    declarations = {
        (declaration.kind, declaration.local_id): (index, declaration)
        for index, declaration in enumerate(manifest_definition.capabilities)
    }
    selected_capabilities = tuple(
        activated_tool.capability for activated_tool in contribution.tools
    )
    if len(set(selected_capabilities)) != len(selected_capabilities):
        _fail(
            PluginContractErrorCode.DUPLICATE_SELECTED_CAPABILITY,
            "plugin contribution selects a capability more than once",
        )

    selected_indexes: list[int] = []
    for activated_tool in contribution.tools:
        capability = activated_tool.capability
        declared = declarations.get((capability.kind, capability.local_id))
        if capability.plugin_id != manifest_definition.plugin_id or declared is None:
            _fail(
                PluginContractErrorCode.UNDECLARED_CAPABILITY,
                "plugin contribution selects an undeclared capability",
            )
        index, declaration = declared
        selected_indexes.append(index)
        if (
            activated_tool.effects != declaration.effects
            or activated_tool.consent is not declaration.consent
        ):
            _fail(
                PluginContractErrorCode.CAPABILITY_METADATA_MISMATCH,
                "selected capability metadata does not match definition",
            )
    if selected_indexes != sorted(selected_indexes):
        _fail(
            PluginContractErrorCode.CAPABILITY_ORDER_MISMATCH,
            "selected capability order does not match definition",
        )
