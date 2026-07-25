from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from mymcp.plugin.contracts import (
    CapabilityKind,
    CapabilityLocalId,
    ConsentRequirement,
    PluginId,
    PluginVersion,
    ToolEffects,
    _is_strict_semver,
)


_MAX_HOST_API_VERSION = 255
_MAX_PLUGIN_DATA_SCHEMA_VERSION = 255
_MAX_TITLE_LENGTH = 128
_MAX_DESCRIPTION_LENGTH = 4096
_MAX_CAPABILITIES = 64
_MAX_SECRET_REFERENCES = 32
_MAX_CONFIGURATION_PROPERTIES = 32
_MAX_CONFIGURATION_DEPTH = 4


def _is_control_free_text(value: object, *, maximum: int) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= maximum
        and all(ord(character) >= 32 and ord(character) != 127 for character in value)
    )


@dataclass(frozen=True, slots=True)
class ManifestVersion:
    value: int

    def __post_init__(self) -> None:
        if type(self.value) is not int or self.value != 1:
            raise ValueError("invalid manifest version")


@dataclass(frozen=True, slots=True)
class PluginTitle:
    value: str

    def __post_init__(self) -> None:
        if not _is_control_free_text(self.value, maximum=_MAX_TITLE_LENGTH):
            raise ValueError("invalid plugin title")


@dataclass(frozen=True, slots=True)
class PluginDescription:
    value: str

    def __post_init__(self) -> None:
        if not _is_control_free_text(self.value, maximum=_MAX_DESCRIPTION_LENGTH):
            raise ValueError("invalid plugin description")


@dataclass(frozen=True, slots=True)
class HostApiVersion:
    value: int

    def __post_init__(self) -> None:
        if (
            type(self.value) is not int
            or not 1 <= self.value <= _MAX_HOST_API_VERSION
        ):
            raise ValueError("invalid host api version")


@dataclass(frozen=True, slots=True)
class HostApiRange:
    minimum: HostApiVersion
    maximum: HostApiVersion

    def __post_init__(self) -> None:
        if (
            not isinstance(self.minimum, HostApiVersion)
            or not isinstance(self.maximum, HostApiVersion)
            or self.minimum.value > self.maximum.value
        ):
            raise ValueError("invalid host api range")


@dataclass(frozen=True, slots=True)
class CapabilityContractVersion:
    value: str

    def __post_init__(self) -> None:
        if not _is_strict_semver(self.value):
            raise ValueError("invalid capability contract version")


@dataclass(frozen=True, slots=True)
class CapabilityDeclaration:
    kind: CapabilityKind
    local_id: CapabilityLocalId
    version: CapabilityContractVersion
    effects: ToolEffects
    consent: ConsentRequirement

    def __post_init__(self) -> None:
        if (
            not isinstance(self.kind, CapabilityKind)
            or not isinstance(self.local_id, CapabilityLocalId)
            or not isinstance(self.version, CapabilityContractVersion)
            or not isinstance(self.effects, ToolEffects)
            or not isinstance(self.consent, ConsentRequirement)
        ):
            raise ValueError("invalid capability declaration")


class ConfigurationType(StrEnum):
    OBJECT = "object"
    ARRAY = "array"
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    NULL = "null"


@dataclass(frozen=True, init=False)
class ConfigurationSchema:
    type: ConfigurationType
    properties: tuple[tuple[str, "ConfigurationSchema"], ...]
    required: tuple[str, ...]
    additional_properties: bool | None
    items: "ConfigurationSchema | None"
    _depth: int

    def __init__(
        self,
        type: ConfigurationType,
        *,
        properties: Iterable[tuple[str, "ConfigurationSchema"]] = (),
        required: Iterable[str] = (),
        additional_properties: bool | None = None,
        items: "ConfigurationSchema | None" = None,
    ) -> None:
        selected_properties = tuple(properties)
        selected_required = tuple(required)
        valid_properties = (
            len(selected_properties) <= _MAX_CONFIGURATION_PROPERTIES
            and all(
                isinstance(name, str)
                and bool(name)
                and isinstance(schema, ConfigurationSchema)
                for name, schema in selected_properties
            )
            and len({name for name, _ in selected_properties})
            == len(selected_properties)
        )
        property_names = {name for name, _ in selected_properties}
        valid_required = (
            all(isinstance(name, str) for name in selected_required)
            and len(set(selected_required)) == len(selected_required)
            and set(selected_required) <= property_names
        )
        object_shape = (
            type is ConfigurationType.OBJECT
            and additional_properties is False
            and items is None
        )
        array_shape = (
            type is ConfigurationType.ARRAY
            and not selected_properties
            and not selected_required
            and additional_properties is None
            and isinstance(items, ConfigurationSchema)
        )
        scalar_shape = (
            isinstance(type, ConfigurationType)
            and type not in (ConfigurationType.OBJECT, ConfigurationType.ARRAY)
            and not selected_properties
            and not selected_required
            and additional_properties is None
            and items is None
        )
        child_depths = [schema._depth for _, schema in selected_properties]
        if isinstance(items, ConfigurationSchema):
            child_depths.append(items._depth)
        depth = 1 + max(child_depths, default=0)
        if (
            not isinstance(type, ConfigurationType)
            or not valid_properties
            or not valid_required
            or not (object_shape or array_shape or scalar_shape)
            or depth > _MAX_CONFIGURATION_DEPTH
        ):
            raise ValueError("invalid configuration schema")

        object.__setattr__(self, "type", type)
        object.__setattr__(self, "properties", selected_properties)
        object.__setattr__(self, "required", selected_required)
        object.__setattr__(self, "additional_properties", additional_properties)
        object.__setattr__(self, "items", items)
        object.__setattr__(self, "_depth", depth)


@dataclass(frozen=True, slots=True)
class ConfigurationSchemaVersion:
    value: int

    def __post_init__(self) -> None:
        if type(self.value) is not int or self.value != 1:
            raise ValueError("invalid configuration schema version")


@dataclass(frozen=True, slots=True)
class ConfigurationDeclaration:
    schema_version: ConfigurationSchemaVersion
    schema: ConfigurationSchema

    def __post_init__(self) -> None:
        if (
            not isinstance(self.schema_version, ConfigurationSchemaVersion)
            or not isinstance(self.schema, ConfigurationSchema)
            or self.schema.type is not ConfigurationType.OBJECT
        ):
            raise ValueError("invalid configuration declaration")


@dataclass(frozen=True, slots=True, init=False)
class SecretReferenceSlot:
    slot_id: CapabilityLocalId

    def __init__(self, slot_id: str | CapabilityLocalId) -> None:
        try:
            identity = (
                slot_id
                if isinstance(slot_id, CapabilityLocalId)
                else CapabilityLocalId(slot_id)
            )
        except (TypeError, ValueError) as error:
            raise ValueError("invalid secret reference slot") from error
        object.__setattr__(self, "slot_id", identity)


@dataclass(frozen=True, slots=True)
class PluginDataSchemaVersion:
    value: int

    def __post_init__(self) -> None:
        if (
            type(self.value) is not int
            or not 1 <= self.value <= _MAX_PLUGIN_DATA_SCHEMA_VERSION
        ):
            raise ValueError("invalid plugin data schema version")


class FilesystemAuthority(StrEnum):
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    STATE_READ = "state_read"
    STATE_WRITE = "state_write"
    CACHE_READ = "cache_read"
    CACHE_WRITE = "cache_write"


@dataclass(frozen=True, init=False)
class AuthorityDeclaration:
    filesystem: tuple[FilesystemAuthority, ...]
    network: bool

    def __init__(
        self,
        filesystem: Iterable[FilesystemAuthority],
        network: bool,
    ) -> None:
        selected_filesystem = tuple(filesystem)
        if (
            any(
                not isinstance(authority, FilesystemAuthority)
                for authority in selected_filesystem
            )
            or len(set(selected_filesystem)) != len(selected_filesystem)
            or type(network) is not bool
        ):
            raise ValueError("invalid authority declaration")
        object.__setattr__(self, "filesystem", selected_filesystem)
        object.__setattr__(self, "network", network)


@dataclass(frozen=True, init=False)
class PluginDefinition:
    manifest_version: ManifestVersion
    plugin_id: PluginId
    title: PluginTitle
    description: PluginDescription
    version: PluginVersion
    requires: HostApiRange
    capabilities: tuple[CapabilityDeclaration, ...]
    configuration: ConfigurationDeclaration
    secret_references: tuple[SecretReferenceSlot, ...]
    data_schema_version: PluginDataSchemaVersion
    authority: AuthorityDeclaration

    def __init__(
        self,
        manifest_version: ManifestVersion,
        plugin_id: PluginId,
        title: PluginTitle,
        description: PluginDescription,
        version: PluginVersion,
        requires: HostApiRange,
        capabilities: Iterable[CapabilityDeclaration],
        configuration: ConfigurationDeclaration,
        secret_references: Iterable[SecretReferenceSlot],
        data_schema_version: PluginDataSchemaVersion,
        authority: AuthorityDeclaration,
    ) -> None:
        selected_capabilities = tuple(capabilities)
        selected_secret_references = tuple(secret_references)
        capability_identities = tuple(
            (capability.kind, capability.local_id)
            for capability in selected_capabilities
            if isinstance(capability, CapabilityDeclaration)
        )
        secret_ids = tuple(
            slot.slot_id
            for slot in selected_secret_references
            if isinstance(slot, SecretReferenceSlot)
        )
        if (
            not isinstance(manifest_version, ManifestVersion)
            or not isinstance(plugin_id, PluginId)
            or not isinstance(title, PluginTitle)
            or not isinstance(description, PluginDescription)
            or not isinstance(version, PluginVersion)
            or not isinstance(requires, HostApiRange)
            or not selected_capabilities
            or len(selected_capabilities) > _MAX_CAPABILITIES
            or len(capability_identities) != len(selected_capabilities)
            or len(set(capability_identities)) != len(capability_identities)
            or not isinstance(configuration, ConfigurationDeclaration)
            or len(selected_secret_references) > _MAX_SECRET_REFERENCES
            or len(secret_ids) != len(selected_secret_references)
            or len(set(secret_ids)) != len(secret_ids)
            or not isinstance(data_schema_version, PluginDataSchemaVersion)
            or not isinstance(authority, AuthorityDeclaration)
        ):
            raise ValueError("invalid plugin definition")

        object.__setattr__(self, "manifest_version", manifest_version)
        object.__setattr__(self, "plugin_id", plugin_id)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "requires", requires)
        object.__setattr__(self, "capabilities", selected_capabilities)
        object.__setattr__(self, "configuration", configuration)
        object.__setattr__(self, "secret_references", selected_secret_references)
        object.__setattr__(self, "data_schema_version", data_schema_version)
        object.__setattr__(self, "authority", authority)
