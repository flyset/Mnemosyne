from __future__ import annotations

import errno
import ipaddress
import keyword
import logging
import os
import re
import stat
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from mymcp.authentication.contracts import AdapterId, EvidenceRoute
from mymcp.authentication.oauth import (
    OAUTH_JWT_PROFILE,
    validate_oauth_issuer,
)
from mymcp.plugin.contracts import PluginId


HOST_CONFIGURATION_SCHEMA_VERSION = 1
SUPPORTED_HOST_CONFIGURATION_SCHEMA_VERSIONS = frozenset({1, 2, 3, 4, 5})
DEFAULT_SERVER_ADDRESS = "127.0.0.1"
DEFAULT_SERVER_PORT = 8000
XDG_CONFIG_HOME_ENV = "XDG_CONFIG_HOME"
APPLICATION_DIRECTORY_NAME = "mymcp"
CONFIGURATION_FILE_NAME = "config.toml"
CONFIGURATION_MAX_BYTES = 64 * 1024
MAX_AUTHENTICATION_ADAPTERS = 32
OPERATOR_BEARER_ADAPTER_TYPE = "operator-bearer-v1"
OAUTH_JWT_ADAPTER_TYPE = OAUTH_JWT_PROFILE

_OPEN_SUPPORTS_DIR_FD = os.open in os.supports_dir_fd
_LOGGER = logging.getLogger("mymcp.host.configuration")
_AUTHENTICATION_TYPE_PATTERN = re.compile(
    r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z"
)

_ERROR_MESSAGES = {
    "invalid_location": "MyMCP configuration location is unavailable",
    "unsafe_path": "MyMCP configuration path is unsafe",
    "not_regular": "MyMCP configuration source is not a regular file",
    "unsafe_permissions": (
        "MyMCP configuration source permissions are unsafe"
    ),
    "unreadable": "MyMCP configuration source could not be read",
    "too_large": "MyMCP configuration exceeds 65536 bytes",
    "source_changed": "MyMCP configuration changed while being read",
    "invalid_utf8": "MyMCP configuration is not valid UTF-8",
    "invalid_toml": "MyMCP configuration is not valid TOML",
    "unsupported_schema_version": (
        "MyMCP configuration schema version is unsupported"
    ),
    "invalid_schema": "MyMCP configuration has an invalid schema",
    "duplicate_plugin": (
        "MyMCP configuration contains a duplicate plugin declaration"
    ),
    "duplicate_authentication_adapter_id": (
        "MyMCP configuration contains a duplicate authentication adapter identity"
    ),
    "duplicate_authentication_adapter_route": (
        "MyMCP configuration contains a duplicate authentication adapter route"
    ),
    "authentication_adapter_limit_exceeded": (
        "MyMCP authentication adapter limit is exceeded"
    ),
    "bundled_plugin_conflict": (
        "MyMCP configuration conflicts with a bundled plugin identity"
    ),
    "enabled_plugin_unsupported": (
        "MyMCP external plugin enablement is not supported by this build"
    ),
}


class HostConfigurationError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(_ERROR_MESSAGES[code])


def _is_reparse_point(metadata: os.stat_result) -> bool:
    file_attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(file_attributes & reparse_attribute)


def _has_unsafe_posix_permissions(metadata: os.stat_result) -> bool:
    return os.name == "posix" and bool(stat.S_IMODE(metadata.st_mode) & 0o022)


def _is_unrepresentable_location(value: str) -> bool:
    return "\x00" in value or any(0xD800 <= ord(character) <= 0xDFFF for character in value)


def resolve_host_configuration_path() -> Path:
    try:
        configured_home = os.getenv(XDG_CONFIG_HOME_ENV)
    except (OSError, RuntimeError, UnicodeError, ValueError):
        raise HostConfigurationError("invalid_location") from None

    if configured_home and _is_unrepresentable_location(configured_home):
        raise HostConfigurationError("invalid_location")

    try:
        if configured_home and Path(configured_home).is_absolute():
            base = Path(configured_home)
        else:
            base = Path.home() / ".config"
        if (
            not base.is_absolute()
            or _is_unrepresentable_location(os.fspath(base))
        ):
            raise ValueError("configuration base is not absolute")
        return base / APPLICATION_DIRECTORY_NAME / CONFIGURATION_FILE_NAME
    except (OSError, RuntimeError, UnicodeError, ValueError):
        raise HostConfigurationError("invalid_location") from None


def _raise_bounded_source_error(error: OSError) -> None:
    if error.errno in {errno.ELOOP, errno.ENOTDIR}:
        raise HostConfigurationError("unsafe_path") from None
    if error.errno == errno.EISDIR:
        raise HostConfigurationError("not_regular") from None
    raise HostConfigurationError("unreadable") from None


def _close_descriptor(descriptor: int | None) -> None:
    if descriptor is None:
        return
    try:
        os.close(descriptor)
    except OSError:
        pass


def _same_file(expected: os.stat_result, observed: os.stat_result) -> bool:
    return expected.st_dev == observed.st_dev and expected.st_ino == observed.st_ino


def _same_source_state(expected: os.stat_result, observed: os.stat_result) -> bool:
    return (
        _same_file(expected, observed)
        and expected.st_size == observed.st_size
        and expected.st_mtime_ns == observed.st_mtime_ns
        and expected.st_ctime_ns == observed.st_ctime_ns
    )


def _open_flags(*, directory: bool = False) -> int:
    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    if directory:
        flags |= getattr(os, "O_DIRECTORY", 0)
    return flags


def _validate_application_directory(path: Path) -> os.stat_result | None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return None
    except OSError as error:
        _raise_bounded_source_error(error)

    if (
        stat.S_ISLNK(metadata.st_mode)
        or _is_reparse_point(metadata)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        raise HostConfigurationError("unsafe_path")
    if _has_unsafe_posix_permissions(metadata):
        raise HostConfigurationError("unsafe_permissions")
    return metadata


def _validate_configuration_path(path: Path) -> os.stat_result | None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return None
    except OSError as error:
        _raise_bounded_source_error(error)

    if stat.S_ISLNK(metadata.st_mode) or _is_reparse_point(metadata):
        raise HostConfigurationError("unsafe_path")
    if not stat.S_ISREG(metadata.st_mode):
        raise HostConfigurationError("not_regular")
    if _has_unsafe_posix_permissions(metadata):
        raise HostConfigurationError("unsafe_permissions")
    if metadata.st_size > CONFIGURATION_MAX_BYTES:
        raise HostConfigurationError("too_large")
    return metadata


def _read_descriptor(descriptor: int, initial: os.stat_result) -> bytes:
    chunks: list[bytes] = []
    remaining = CONFIGURATION_MAX_BYTES + 1
    try:
        while remaining:
            chunk = os.read(descriptor, min(8192, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        final = os.fstat(descriptor)
    except OSError as error:
        _raise_bounded_source_error(error)

    source = b"".join(chunks)
    if len(source) > CONFIGURATION_MAX_BYTES:
        raise HostConfigurationError("too_large")
    if not _same_source_state(initial, final) or len(source) != final.st_size:
        raise HostConfigurationError("source_changed")
    if _has_unsafe_posix_permissions(final):
        raise HostConfigurationError("unsafe_permissions")
    return source


def _read_configuration_source(
    application_directory: Path,
    configuration_path: Path,
    application_metadata: os.stat_result,
    configuration_metadata: os.stat_result,
) -> bytes:
    directory_descriptor: int | None = None
    configuration_descriptor: int | None = None
    try:
        directory_descriptor = os.open(
            application_directory,
            _open_flags(directory=True),
        )
        opened_directory = os.fstat(directory_descriptor)
        if (
            not stat.S_ISDIR(opened_directory.st_mode)
            or _is_reparse_point(opened_directory)
        ):
            raise HostConfigurationError("unsafe_path")
        if not _same_file(application_metadata, opened_directory):
            raise HostConfigurationError("source_changed")
        if _has_unsafe_posix_permissions(opened_directory):
            raise HostConfigurationError("unsafe_permissions")

        if _OPEN_SUPPORTS_DIR_FD:
            configuration_descriptor = os.open(
                CONFIGURATION_FILE_NAME,
                _open_flags(),
                dir_fd=directory_descriptor,
            )
        else:
            configuration_descriptor = os.open(configuration_path, _open_flags())
        opened_configuration = os.fstat(configuration_descriptor)
        if (
            stat.S_ISLNK(opened_configuration.st_mode)
            or _is_reparse_point(opened_configuration)
        ):
            raise HostConfigurationError("unsafe_path")
        if not stat.S_ISREG(opened_configuration.st_mode):
            raise HostConfigurationError("not_regular")
        if not _same_file(configuration_metadata, opened_configuration):
            raise HostConfigurationError("source_changed")
        if _has_unsafe_posix_permissions(opened_configuration):
            raise HostConfigurationError("unsafe_permissions")
        if opened_configuration.st_size > CONFIGURATION_MAX_BYTES:
            raise HostConfigurationError("too_large")
        return _read_descriptor(configuration_descriptor, opened_configuration)
    except FileNotFoundError:
        raise HostConfigurationError("source_changed") from None
    except HostConfigurationError:
        raise
    except OSError as error:
        _raise_bounded_source_error(error)
    finally:
        _close_descriptor(configuration_descriptor)
        _close_descriptor(directory_descriptor)


def _log_configuration_loaded(
    outcome: str,
    configuration: HostConfiguration,
) -> None:
    _LOGGER.info(
        "host_configuration outcome=%s schema_version=%s address=%s port=%s "
        "declarations=%s enabled=%s",
        outcome,
        configuration.schema_version.value,
        configuration.server.address,
        configuration.server.port,
        len(configuration.plugins),
        sum(declaration.enabled for declaration in configuration.plugins),
    )


def _load_host_configuration() -> HostConfiguration:
    configuration_path = resolve_host_configuration_path()
    application_directory = configuration_path.parent
    application_metadata = _validate_application_directory(application_directory)
    if application_metadata is None:
        configuration = HostConfiguration.default()
        _log_configuration_loaded("absent_defaults", configuration)
        return configuration

    configuration_metadata = _validate_configuration_path(configuration_path)
    if configuration_metadata is None:
        configuration = HostConfiguration.default()
        _log_configuration_loaded("absent_defaults", configuration)
        return configuration

    source = _read_configuration_source(
        application_directory,
        configuration_path,
        application_metadata,
        configuration_metadata,
    )
    try:
        decoded = source.decode("utf-8")
    except UnicodeDecodeError:
        raise HostConfigurationError("invalid_utf8") from None
    configuration = parse_host_configuration_toml(decoded)
    _log_configuration_loaded("loaded", configuration)
    return configuration


def load_host_configuration() -> HostConfiguration:
    try:
        return _load_host_configuration()
    except HostConfigurationError as error:
        _LOGGER.error(
            "host_configuration outcome=error code=%s",
            error.code,
        )
        raise


@dataclass(frozen=True, slots=True)
class HostConfigurationSchemaVersion:
    value: int

    def __post_init__(self) -> None:
        if (
            type(self.value) is not int
            or self.value not in SUPPORTED_HOST_CONFIGURATION_SCHEMA_VERSIONS
        ):
            raise ValueError("invalid host configuration schema version")


@dataclass(frozen=True, slots=True)
class HostServerConfiguration:
    address: str = DEFAULT_SERVER_ADDRESS
    port: int = DEFAULT_SERVER_PORT

    def __post_init__(self) -> None:
        try:
            parsed_address = ipaddress.ip_address(self.address)
        except (TypeError, ValueError):
            raise ValueError("invalid host server configuration") from None
        if (
            not isinstance(self.address, str)
            or "%" in self.address
            or not parsed_address.is_loopback
            or type(self.port) is not int
            or not 1 <= self.port <= 65535
        ):
            raise ValueError("invalid host server configuration")


@dataclass(frozen=True, slots=True)
class ExternalPluginDeclaration:
    plugin_id: PluginId
    enabled: bool
    manifest_path: str | None = None
    module: str | None = None

    def __post_init__(self) -> None:
        locators = (self.manifest_path, self.module)
        if (
            not isinstance(self.plugin_id, PluginId)
            or type(self.enabled) is not bool
            or not (
                locators == (None, None)
                or (
                    _valid_manifest_path(self.manifest_path)
                    and _valid_module(self.module)
                )
            )
        ):
            raise ValueError("invalid external plugin declaration")


@dataclass(frozen=True, slots=True)
class AuthenticationAdapterDeclaration:
    adapter_id: AdapterId
    adapter_type: str
    enabled: bool
    route: EvidenceRoute

    def __post_init__(self) -> None:
        if (
            not isinstance(self.adapter_id, AdapterId)
            or not _valid_authentication_type(self.adapter_type)
            or type(self.enabled) is not bool
            or not isinstance(self.route, EvidenceRoute)
        ):
            raise ValueError("invalid authentication adapter declaration")


@dataclass(frozen=True, slots=True)
class HostOperatorBearerConfiguration:
    verifier_path: str

    def __post_init__(self) -> None:
        if not _valid_operator_bearer_verifier_path(self.verifier_path):
            raise ValueError("invalid host operator bearer configuration")


@dataclass(frozen=True, slots=True)
class HostOAuthJwtConfiguration:
    issuer: str

    def __post_init__(self) -> None:
        try:
            validate_oauth_issuer(self.issuer)
        except ValueError:
            raise ValueError("invalid host operator oauth configuration") from None


@dataclass(frozen=True, slots=True)
class HostAuthenticationConfiguration:
    anonymous_enabled: bool
    adapters: tuple[AuthenticationAdapterDeclaration, ...]
    operator_bearer: HostOperatorBearerConfiguration | None = None
    oauth_jwt: HostOAuthJwtConfiguration | None = None

    def __post_init__(self) -> None:
        if (
            type(self.anonymous_enabled) is not bool
            or type(self.adapters) is not tuple
            or any(
                not isinstance(adapter, AuthenticationAdapterDeclaration)
                for adapter in self.adapters
            )
            or (
                self.operator_bearer is not None
                and not isinstance(
                    self.operator_bearer, HostOperatorBearerConfiguration
                )
            )
            or (
                self.oauth_jwt is not None
                and not isinstance(self.oauth_jwt, HostOAuthJwtConfiguration)
            )
            or len({adapter.adapter_id for adapter in self.adapters})
            != len(self.adapters)
            or len({adapter.route for adapter in self.adapters}) != len(self.adapters)
        ):
            raise ValueError("invalid host authentication configuration")


@dataclass(frozen=True, slots=True)
class HostConfiguration:
    schema_version: HostConfigurationSchemaVersion
    server: HostServerConfiguration
    plugins: tuple[ExternalPluginDeclaration, ...]
    authentication: HostAuthenticationConfiguration = HostAuthenticationConfiguration(
        True, ()
    )

    def __post_init__(self) -> None:
        if (
            not isinstance(self.schema_version, HostConfigurationSchemaVersion)
            or not isinstance(self.server, HostServerConfiguration)
            or not isinstance(self.authentication, HostAuthenticationConfiguration)
            or type(self.plugins) is not tuple
            or any(
                not isinstance(plugin, ExternalPluginDeclaration)
                for plugin in self.plugins
            )
            or len({plugin.plugin_id for plugin in self.plugins}) != len(self.plugins)
            or any(
                (plugin.manifest_path is not None)
                != (self.schema_version.value in {2, 3, 4, 5})
                for plugin in self.plugins
            )
            or (
                self.schema_version.value in {1, 2}
                and self.authentication != HostAuthenticationConfiguration(True, ())
            )
            or (
                self.schema_version.value == 3
                and (
                    self.authentication.operator_bearer is not None
                    or self.authentication.oauth_jwt is not None
                )
            )
            or (
                self.schema_version.value == 4
                and (
                    (self.authentication.operator_bearer is not None)
                    != _has_operator_bearer_declaration(
                        self.authentication.adapters
                    )
                    or self.authentication.oauth_jwt is not None
                )
            )
            or (
                self.schema_version.value == 5
                and (
                    (self.authentication.operator_bearer is not None)
                    != _has_operator_bearer_declaration(
                        self.authentication.adapters
                    )
                    or (self.authentication.oauth_jwt is not None)
                    != _has_oauth_jwt_declaration(self.authentication.adapters)
                    or (
                        self.authentication.operator_bearer is not None
                        and self.authentication.oauth_jwt is not None
                    )
                    or (
                        _has_operator_bearer_declaration(
                            self.authentication.adapters
                        )
                        and _has_oauth_jwt_declaration(
                            self.authentication.adapters
                        )
                    )
                )
            )
        ):
            raise ValueError("invalid host configuration")

    @classmethod
    def default(cls) -> "HostConfiguration":
        return cls(
            schema_version=HostConfigurationSchemaVersion(
                HOST_CONFIGURATION_SCHEMA_VERSION
            ),
            server=HostServerConfiguration(),
            plugins=(),
            authentication=HostAuthenticationConfiguration(True, ()),
        )


def _parse_server(value: object) -> HostServerConfiguration:
    if not isinstance(value, dict) or not set(value) <= {"address", "port"}:
        raise HostConfigurationError("invalid_schema")
    try:
        return HostServerConfiguration(
            address=value.get("address", DEFAULT_SERVER_ADDRESS),
            port=value.get("port", DEFAULT_SERVER_PORT),
        )
    except ValueError:
        raise HostConfigurationError("invalid_schema") from None


def _valid_manifest_path(value: object) -> bool:
    if type(value) is not str or not Path(value).is_absolute():
        return False
    if (
        not value
        or "\x00" in value
        or "~" in value
        or "$" in value
        or "%" in value
    ):
        return False
    return not any(part in {".", ".."} for part in re.split(r"[/\\]", value))


def _valid_module(value: object) -> bool:
    if type(value) is not str:
        return False
    parts = value.split(".")
    return (
        1 <= len(value) <= 255
        and value.isascii()
        and all(
            part.isidentifier() and not keyword.iskeyword(part)
            for part in parts
        )
    )


def _valid_authentication_type(value: object) -> bool:
    return (
        type(value) is str
        and 1 <= len(value) <= 64
        and _AUTHENTICATION_TYPE_PATTERN.fullmatch(value) is not None
    )


def _valid_operator_bearer_verifier_path(value: object) -> bool:
    if type(value) is not str or not value or not Path(value).is_absolute():
        return False
    if "\x00" in value or "~" in value or "$" in value or "%" in value:
        return False
    return not any(part in {".", ".."} for part in re.split(r"[/\\]", value))


def _has_operator_bearer_declaration(
    adapters: Iterable[AuthenticationAdapterDeclaration],
) -> bool:
    return any(
        adapter.adapter_type == OPERATOR_BEARER_ADAPTER_TYPE
        for adapter in adapters
    )


def _has_oauth_jwt_declaration(
    adapters: Iterable[AuthenticationAdapterDeclaration],
) -> bool:
    return any(
        adapter.adapter_type == OAUTH_JWT_ADAPTER_TYPE
        for adapter in adapters
    )


def _parse_plugins_v1(value: object) -> tuple[ExternalPluginDeclaration, ...]:
    if not isinstance(value, list):
        raise HostConfigurationError("invalid_schema")

    declarations: list[ExternalPluginDeclaration] = []
    identities: set[PluginId] = set()
    for item in value:
        if not isinstance(item, dict) or set(item) != {"id", "enabled"}:
            raise HostConfigurationError("invalid_schema")
        try:
            declaration = ExternalPluginDeclaration(
                plugin_id=PluginId(item["id"]),
                enabled=item["enabled"],
            )
        except (TypeError, ValueError):
            raise HostConfigurationError("invalid_schema") from None
        if declaration.plugin_id in identities:
            raise HostConfigurationError("duplicate_plugin")
        identities.add(declaration.plugin_id)
        declarations.append(declaration)
    return tuple(declarations)


def _parse_plugins_v2(value: object) -> tuple[ExternalPluginDeclaration, ...]:
    if not isinstance(value, list):
        raise HostConfigurationError("invalid_schema")

    declarations: list[ExternalPluginDeclaration] = []
    identities: set[PluginId] = set()
    for item in value:
        if not isinstance(item, dict) or set(item) != {
            "id",
            "enabled",
            "manifest_path",
            "module",
        }:
            raise HostConfigurationError("invalid_schema")
        if not _valid_manifest_path(item["manifest_path"]) or not _valid_module(
            item["module"]
        ):
            raise HostConfigurationError("invalid_schema")
        try:
            declaration = ExternalPluginDeclaration(
                plugin_id=PluginId(item["id"]),
                enabled=item["enabled"],
                manifest_path=item["manifest_path"],
                module=item["module"],
            )
        except (TypeError, ValueError):
            raise HostConfigurationError("invalid_schema") from None
        if declaration.plugin_id in identities:
            raise HostConfigurationError("duplicate_plugin")
        identities.add(declaration.plugin_id)
        declarations.append(declaration)
    return tuple(declarations)


def _parse_authentication_adapter(
    value: object,
) -> AuthenticationAdapterDeclaration:
    if not isinstance(value, dict) or set(value) != {
        "id",
        "type",
        "enabled",
        "route",
    }:
        raise HostConfigurationError("invalid_schema")
    route = value["route"]
    if (
        not isinstance(route, dict)
        or not {"source", "scheme"} <= set(route)
        or not set(route) <= {"source", "scheme", "profile"}
    ):
        raise HostConfigurationError("invalid_schema")
    try:
        return AuthenticationAdapterDeclaration(
            adapter_id=AdapterId(value["id"]),
            adapter_type=value["type"],
            enabled=value["enabled"],
            route=EvidenceRoute(
                source=route["source"],
                scheme=route["scheme"],
                profile=route.get("profile"),
            ),
        )
    except (TypeError, ValueError):
        raise HostConfigurationError("invalid_schema") from None


def _parse_operator_bearer(value: object) -> HostOperatorBearerConfiguration:
    if not isinstance(value, dict) or set(value) != {"verifier_path"}:
        raise HostConfigurationError("invalid_schema")
    try:
        return HostOperatorBearerConfiguration(verifier_path=value["verifier_path"])
    except ValueError:
        raise HostConfigurationError("invalid_schema") from None


def _parse_oauth_jwt(value: object) -> HostOAuthJwtConfiguration:
    if not isinstance(value, dict) or set(value) != {"issuer"}:
        raise HostConfigurationError("invalid_schema")
    try:
        return HostOAuthJwtConfiguration(issuer=value["issuer"])
    except (TypeError, ValueError):
        raise HostConfigurationError("invalid_schema") from None


def _parse_authentication(
    value: object,
    schema_version: int,
) -> HostAuthenticationConfiguration:
    allowed_keys = (
        {"anonymous_enabled", "adapters", "operator_bearer", "oauth_jwt"}
        if schema_version == 5
        else {"anonymous_enabled", "adapters", "operator_bearer"}
        if schema_version == 4
        else {"anonymous_enabled", "adapters"}
    )
    if (
        not isinstance(value, dict)
        or not set(value) <= allowed_keys
        or "anonymous_enabled" not in value
    ):
        raise HostConfigurationError("invalid_schema")
    raw_adapters = value.get("adapters", [])
    if not isinstance(raw_adapters, list):
        raise HostConfigurationError("invalid_schema")
    if len(raw_adapters) > MAX_AUTHENTICATION_ADAPTERS:
        raise HostConfigurationError("authentication_adapter_limit_exceeded")

    adapters = tuple(_parse_authentication_adapter(item) for item in raw_adapters)
    if (
        schema_version == 5
        and _has_operator_bearer_declaration(adapters)
        and _has_oauth_jwt_declaration(adapters)
    ):
        raise HostConfigurationError("invalid_schema")
    identities: set[AdapterId] = set()
    routes: set[EvidenceRoute] = set()
    for adapter in adapters:
        if adapter.adapter_id in identities:
            raise HostConfigurationError("duplicate_authentication_adapter_id")
        if adapter.route in routes:
            raise HostConfigurationError("duplicate_authentication_adapter_route")
        identities.add(adapter.adapter_id)
        routes.add(adapter.route)

    operator_bearer: HostOperatorBearerConfiguration | None = None
    if schema_version in {4, 5} and value.get("operator_bearer") is not None:
        operator_bearer = _parse_operator_bearer(value["operator_bearer"])
    if (
        schema_version in {4, 5}
        and _has_operator_bearer_declaration(adapters)
        != (operator_bearer is not None)
    ):
        raise HostConfigurationError("invalid_schema")

    oauth_jwt: HostOAuthJwtConfiguration | None = None
    if schema_version == 5 and value.get("oauth_jwt") is not None:
        oauth_jwt = _parse_oauth_jwt(value["oauth_jwt"])
    if (
        schema_version == 5
        and _has_oauth_jwt_declaration(adapters) != (oauth_jwt is not None)
    ):
        raise HostConfigurationError("invalid_schema")
    if (
        schema_version == 5
        and (
            (operator_bearer is not None and oauth_jwt is not None)
            or (
                _has_operator_bearer_declaration(adapters)
                and _has_oauth_jwt_declaration(adapters)
            )
        )
    ):
        raise HostConfigurationError("invalid_schema")
    try:
        return HostAuthenticationConfiguration(
            anonymous_enabled=value["anonymous_enabled"],
            adapters=adapters,
            operator_bearer=operator_bearer,
            oauth_jwt=oauth_jwt,
        )
    except ValueError:
        raise HostConfigurationError("invalid_schema") from None


def parse_host_configuration_toml(source: str) -> HostConfiguration:
    try:
        document = tomllib.loads(source)
    except (TypeError, tomllib.TOMLDecodeError):
        raise HostConfigurationError("invalid_toml") from None

    if not set(document) <= {
        "schema_version",
        "server",
        "plugins",
        "authentication",
    }:
        raise HostConfigurationError("invalid_schema")
    if "schema_version" not in document:
        raise HostConfigurationError("invalid_schema")

    schema_version = document["schema_version"]
    if type(schema_version) is not int:
        raise HostConfigurationError("invalid_schema")
    if schema_version not in SUPPORTED_HOST_CONFIGURATION_SCHEMA_VERSIONS:
        raise HostConfigurationError("unsupported_schema_version")

    server = _parse_server(document.get("server", {}))
    if schema_version in {1, 2} and "authentication" in document:
        raise HostConfigurationError("invalid_schema")
    if schema_version in {3, 4, 5} and "authentication" not in document:
        raise HostConfigurationError("invalid_schema")

    if schema_version == 1:
        plugins = _parse_plugins_v1(document.get("plugins", []))
    else:
        plugins = _parse_plugins_v2(document.get("plugins", []))
    authentication = (
        _parse_authentication(document["authentication"], schema_version)
        if schema_version in {3, 4, 5}
        else HostAuthenticationConfiguration(True, ())
    )
    return HostConfiguration(
        schema_version=HostConfigurationSchemaVersion(schema_version),
        server=server,
        plugins=plugins,
        authentication=authentication,
    )


def validate_host_configuration_semantics(
    configuration: HostConfiguration,
    *,
    bundled_plugin_ids: Iterable[PluginId],
) -> HostConfiguration:
    bundled_identities = tuple(bundled_plugin_ids)
    if (
        not isinstance(configuration, HostConfiguration)
        or any(
            not isinstance(plugin_id, PluginId)
            for plugin_id in bundled_identities
        )
    ):
        raise ValueError("invalid host configuration semantic input")

    configured_identities = {
        declaration.plugin_id for declaration in configuration.plugins
    }
    if configured_identities.intersection(bundled_identities):
        raise HostConfigurationError("bundled_plugin_conflict")
    if (
        configuration.schema_version.value == 1
        and any(declaration.enabled for declaration in configuration.plugins)
    ):
        raise HostConfigurationError("enabled_plugin_unsupported")
    return configuration
