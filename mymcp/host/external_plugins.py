import errno
import importlib
import os
import stat
from pathlib import Path

from mymcp.host.configuration import HostConfiguration
from mymcp.plugin.adapter import PluginAdapter
from mymcp.plugin.definition import HostApiVersion, PluginDefinition
from mymcp.plugin.manifest import PluginContractError, parse_manifest_bytes


EXTERNAL_PLUGIN_ERROR_MESSAGES = {
    "external_plugin_limit_exceeded": "MyMCP external plugin limit is exceeded",
    "external_manifest_unsafe_path": "MyMCP external manifest path is unsafe",
    "external_manifest_not_regular": "MyMCP external manifest source is not a regular file",
    "external_manifest_unsafe_permissions": (
        "MyMCP external manifest source permissions are unsafe"
    ),
    "external_manifest_unreadable": "MyMCP external manifest source could not be read",
    "external_manifest_too_large": "MyMCP external manifest exceeds 65536 bytes",
    "external_manifest_source_changed": "MyMCP external manifest changed while being read",
    "external_manifest_invalid": "MyMCP external manifest is invalid",
    "external_manifest_identity_mismatch": "MyMCP external manifest identity does not match configuration",
    "external_manifest_host_api_incompatible": (
        "MyMCP external manifest does not support the host API"
    ),
    "external_plugin_import_failed": "MyMCP external plugin import failed",
    "external_plugin_entrypoint_invalid": "MyMCP external plugin entrypoint is invalid",
    "external_plugin_contract_invalid": "MyMCP external plugin contract is invalid",
    "external_plugin_composition_invalid": "MyMCP external plugin composition is invalid",
}

_MAX_ENABLED_PLUGINS = 32
_MAX_EXTERNAL_CAPABILITIES = 256
_MAX_MANIFEST_BYTES = 64 * 1024
_OPEN_SUPPORTS_DIR_FD = os.open in os.supports_dir_fd


class ExternalPluginLoadError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(EXTERNAL_PLUGIN_ERROR_MESSAGES[code])


def _is_reparse_point(metadata: os.stat_result) -> bool:
    file_attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(file_attributes & reparse_attribute)


def _has_unsafe_posix_permissions(metadata: os.stat_result) -> bool:
    return os.name == "posix" and bool(stat.S_IMODE(metadata.st_mode) & 0o022)


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
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    if directory:
        flags |= getattr(os, "O_DIRECTORY", 0)
    return flags


def _close_descriptor(descriptor: int | None) -> None:
    if descriptor is not None:
        try:
            os.close(descriptor)
        except OSError:
            pass


def _source_error(error: OSError) -> ExternalPluginLoadError:
    if error.errno in {errno.ELOOP, errno.ENOTDIR}:
        return ExternalPluginLoadError("external_manifest_unsafe_path")
    if error.errno == errno.EISDIR:
        return ExternalPluginLoadError("external_manifest_not_regular")
    return ExternalPluginLoadError("external_manifest_unreadable")


def _validate_parent(path: Path) -> os.stat_result:
    try:
        metadata = path.parent.lstat()
    except OSError as error:
        raise _source_error(error) from None
    if (
        stat.S_ISLNK(metadata.st_mode)
        or _is_reparse_point(metadata)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        raise ExternalPluginLoadError("external_manifest_unsafe_path")
    if _has_unsafe_posix_permissions(metadata):
        raise ExternalPluginLoadError("external_manifest_unsafe_permissions")
    return metadata


def _validate_source(path: Path) -> os.stat_result:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise _source_error(error) from None
    if stat.S_ISLNK(metadata.st_mode) or _is_reparse_point(metadata):
        raise ExternalPluginLoadError("external_manifest_unsafe_path")
    if not stat.S_ISREG(metadata.st_mode):
        raise ExternalPluginLoadError("external_manifest_not_regular")
    if _has_unsafe_posix_permissions(metadata):
        raise ExternalPluginLoadError("external_manifest_unsafe_permissions")
    if metadata.st_size > _MAX_MANIFEST_BYTES:
        raise ExternalPluginLoadError("external_manifest_too_large")
    return metadata


def _read_descriptor(descriptor: int, initial: os.stat_result) -> bytes:
    chunks: list[bytes] = []
    remaining = _MAX_MANIFEST_BYTES + 1
    try:
        while remaining:
            chunk = os.read(descriptor, min(8192, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        final = os.fstat(descriptor)
    except OSError as error:
        raise _source_error(error) from None

    source = b"".join(chunks)
    if len(source) > _MAX_MANIFEST_BYTES:
        raise ExternalPluginLoadError("external_manifest_too_large")
    if not _same_source_state(initial, final) or len(source) != final.st_size:
        raise ExternalPluginLoadError("external_manifest_source_changed")
    if _has_unsafe_posix_permissions(final):
        raise ExternalPluginLoadError("external_manifest_unsafe_permissions")
    return source


def _read_manifest_source(path: Path) -> bytes:
    parent_metadata = _validate_parent(path)
    source_metadata = _validate_source(path)
    parent_descriptor: int | None = None
    source_descriptor: int | None = None
    try:
        parent_descriptor = os.open(path.parent, _open_flags(directory=True))
        opened_parent = os.fstat(parent_descriptor)
        if (
            not stat.S_ISDIR(opened_parent.st_mode)
            or _is_reparse_point(opened_parent)
        ):
            raise ExternalPluginLoadError("external_manifest_unsafe_path")
        if not _same_file(parent_metadata, opened_parent):
            raise ExternalPluginLoadError("external_manifest_source_changed")
        if _has_unsafe_posix_permissions(opened_parent):
            raise ExternalPluginLoadError("external_manifest_unsafe_permissions")

        if _OPEN_SUPPORTS_DIR_FD:
            source_descriptor = os.open(
                path.name,
                _open_flags(),
                dir_fd=parent_descriptor,
            )
        else:
            source_descriptor = os.open(path, _open_flags())
        opened_source = os.fstat(source_descriptor)
        if _is_reparse_point(opened_source):
            raise ExternalPluginLoadError("external_manifest_unsafe_path")
        if not stat.S_ISREG(opened_source.st_mode):
            raise ExternalPluginLoadError("external_manifest_not_regular")
        if not _same_file(source_metadata, opened_source):
            raise ExternalPluginLoadError("external_manifest_source_changed")
        if _has_unsafe_posix_permissions(opened_source):
            raise ExternalPluginLoadError("external_manifest_unsafe_permissions")
        if opened_source.st_size > _MAX_MANIFEST_BYTES:
            raise ExternalPluginLoadError("external_manifest_too_large")
        source = _read_descriptor(source_descriptor, opened_source)

        # Detect a replacement at the configured path after the descriptor read.
        if not _same_source_state(parent_metadata, path.parent.lstat()):
            raise ExternalPluginLoadError("external_manifest_source_changed")
        if not _same_source_state(source_metadata, path.lstat()):
            raise ExternalPluginLoadError("external_manifest_source_changed")
        return source
    except ExternalPluginLoadError:
        raise
    except OSError as error:
        raise _source_error(error) from None
    finally:
        _close_descriptor(source_descriptor)
        _close_descriptor(parent_descriptor)


def preflight_external_manifests(
    configuration: HostConfiguration,
) -> tuple[PluginDefinition, ...]:
    if not isinstance(configuration, HostConfiguration):
        raise ValueError("invalid external manifest preflight input")
    enabled = tuple(declaration for declaration in configuration.plugins if declaration.enabled)
    if enabled and configuration.schema_version.value != 2:
        raise ValueError("invalid external manifest preflight input")
    if len(enabled) > _MAX_ENABLED_PLUGINS:
        raise ExternalPluginLoadError("external_plugin_limit_exceeded")
    modules = tuple(declaration.module for declaration in enabled)
    if len(set(modules)) != len(modules):
        raise ExternalPluginLoadError("external_plugin_composition_invalid")

    definitions: list[PluginDefinition] = []
    capability_count = 0
    for declaration in enabled:
        try:
            definition = parse_manifest_bytes(
                _read_manifest_source(Path(declaration.manifest_path))  # type: ignore[arg-type]
            )
        except ExternalPluginLoadError:
            raise
        except PluginContractError:
            raise ExternalPluginLoadError("external_manifest_invalid") from None
        if definition.plugin_id != declaration.plugin_id:
            raise ExternalPluginLoadError("external_manifest_identity_mismatch")
        if not (
            definition.requires.minimum.value
            <= HostApiVersion(1).value
            <= definition.requires.maximum.value
        ):
            raise ExternalPluginLoadError("external_manifest_host_api_incompatible")
        capability_count += len(definition.capabilities)
        if capability_count > _MAX_EXTERNAL_CAPABILITIES:
            raise ExternalPluginLoadError("external_plugin_limit_exceeded")
        definitions.append(definition)
    return tuple(definitions)


def load_external_plugins(
    configuration: HostConfiguration,
    definitions: tuple[PluginDefinition, ...],
) -> tuple[PluginAdapter, ...]:
    if not isinstance(configuration, HostConfiguration):
        raise ValueError("invalid external plugin loading input")
    enabled = tuple(
        declaration for declaration in configuration.plugins if declaration.enabled
    )
    if (
        type(definitions) is not tuple
        or len(enabled) != len(definitions)
        or any(
            not isinstance(definition, PluginDefinition)
            or definition.plugin_id != declaration.plugin_id
            for declaration, definition in zip(enabled, definitions, strict=True)
        )
    ):
        raise ValueError("invalid external plugin loading input")

    adapters: list[PluginAdapter] = []
    for declaration in enabled:
        try:
            module = importlib.import_module(declaration.module)  # type: ignore[arg-type]
        except Exception:
            raise ExternalPluginLoadError("external_plugin_import_failed") from None
        try:
            entrypoint = module.mymcp_plugin_v1
        except Exception:
            raise ExternalPluginLoadError("external_plugin_entrypoint_invalid") from None
        if not callable(entrypoint):
            raise ExternalPluginLoadError("external_plugin_entrypoint_invalid")
        try:
            adapter = entrypoint()
        except Exception:
            raise ExternalPluginLoadError("external_plugin_entrypoint_invalid") from None
        if not isinstance(adapter, PluginAdapter):
            raise ExternalPluginLoadError("external_plugin_contract_invalid")
        adapters.append(adapter)
    return tuple(adapters)
