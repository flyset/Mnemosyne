import errno
import os
import stat
import tomllib
from dataclasses import dataclass
from pathlib import Path


SERVER_NAME = "mnemosyne"
SERVER_VERSION = "0.1.1"
PROTOCOL_VERSION = "2024-11-05"
APP_TITLE = "Mnemosyne MCP Server"

MEMORY_ROOT_ENV = "MNEMOSYNE_MEMORY_ROOT"
MEMORY_REMEMBER_ENABLED_ENV = "MNEMOSYNE_MEMORY_REMEMBER_ENABLED"
MEMORY_ARCHIVE_RESTORE_ENABLED_ENV = (
    "MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED"
)
MEMORY_FORGET_ENABLED_ENV = "MNEMOSYNE_MEMORY_FORGET_ENABLED"
MEMORY_REVISE_ENABLED_ENV = "MNEMOSYNE_MEMORY_REVISE_ENABLED"
SETTINGS_DIRECTORY_NAME = ".mnemosyne"
SETTINGS_FILE_NAME = "config.toml"
SETTINGS_MAX_BYTES = 16 * 1024

_SETTINGS_ERROR_MESSAGES = {
    "invalid_toml": "Mnemosyne settings file is not valid TOML",
    "invalid_schema": "Mnemosyne settings file has an invalid schema",
    "unreadable": "Mnemosyne settings file could not be read",
    "not_regular": "Mnemosyne settings source is not a regular file",
    "unsafe_path": "Mnemosyne settings file path is unsafe",
    "too_large": "Mnemosyne settings file exceeds 16384 bytes",
    "unsafe_permissions": "Mnemosyne settings source permissions are unsafe",
}


class SettingsError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(_SETTINGS_ERROR_MESSAGES[code])


@dataclass(frozen=True)
class MemoryToolSettings:
    remember_enabled: bool = False
    archive_restore_enabled: bool = False
    forget_enabled: bool = False
    revise_enabled: bool = False


def get_memory_root() -> Path:
    configured_root = os.getenv(MEMORY_ROOT_ENV)
    if configured_root:
        return Path(configured_root).expanduser()
    return Path.home() / SETTINGS_DIRECTORY_NAME / "memory"


def _has_unsafe_posix_permissions(metadata: os.stat_result) -> bool:
    return os.name == "posix" and bool(stat.S_IMODE(metadata.st_mode) & 0o022)


def _raise_bounded_source_error(error: OSError) -> None:
    if error.errno in {errno.ELOOP, errno.ENOTDIR}:
        raise SettingsError("unsafe_path") from None
    if error.errno == errno.EISDIR:
        raise SettingsError("not_regular") from None
    raise SettingsError("unreadable") from None


def _close_descriptor(descriptor: int | None) -> None:
    if descriptor is None:
        return
    try:
        os.close(descriptor)
    except OSError:
        pass


def _read_descriptor(descriptor: int) -> bytes:
    chunks: list[bytes] = []
    remaining = SETTINGS_MAX_BYTES + 1
    try:
        while remaining:
            chunk = os.read(descriptor, min(8192, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
    except OSError as error:
        _raise_bounded_source_error(error)

    source = b"".join(chunks)
    if len(source) > SETTINGS_MAX_BYTES:
        raise SettingsError("too_large")
    return source


def _validate_application_directory(
    application_directory: Path,
) -> os.stat_result | None:
    try:
        metadata = application_directory.lstat()
    except FileNotFoundError:
        return None
    except OSError as error:
        _raise_bounded_source_error(error)

    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise SettingsError("unsafe_path")
    if _has_unsafe_posix_permissions(metadata):
        raise SettingsError("unsafe_permissions")
    return metadata


def _validate_settings_path(settings_path: Path) -> os.stat_result | None:
    try:
        metadata = settings_path.lstat()
    except FileNotFoundError:
        return None
    except OSError as error:
        _raise_bounded_source_error(error)

    if stat.S_ISLNK(metadata.st_mode):
        raise SettingsError("unsafe_path")
    if not stat.S_ISREG(metadata.st_mode):
        raise SettingsError("not_regular")
    if _has_unsafe_posix_permissions(metadata):
        raise SettingsError("unsafe_permissions")
    if metadata.st_size > SETTINGS_MAX_BYTES:
        raise SettingsError("too_large")
    return metadata


def _same_file(
    expected: os.stat_result,
    observed: os.stat_result,
) -> bool:
    return (
        expected.st_dev == observed.st_dev
        and expected.st_ino == observed.st_ino
    )


def _open_flags(*, directory: bool = False) -> int:
    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    if directory:
        flags |= getattr(os, "O_DIRECTORY", 0)
    return flags


def _read_settings_source(
    application_directory: Path,
    settings_path: Path,
    application_metadata: os.stat_result,
    settings_metadata: os.stat_result,
) -> bytes | None:
    directory_descriptor: int | None = None
    settings_descriptor: int | None = None
    try:
        directory_descriptor = os.open(
            application_directory,
            _open_flags(directory=True),
        )
        opened_directory_metadata = os.fstat(directory_descriptor)
        if not stat.S_ISDIR(opened_directory_metadata.st_mode) or not _same_file(
            application_metadata,
            opened_directory_metadata,
        ):
            raise SettingsError("unsafe_path")
        if _has_unsafe_posix_permissions(opened_directory_metadata):
            raise SettingsError("unsafe_permissions")

        if os.open in os.supports_dir_fd:
            settings_descriptor = os.open(
                SETTINGS_FILE_NAME,
                _open_flags(),
                dir_fd=directory_descriptor,
            )
        else:
            settings_descriptor = os.open(settings_path, _open_flags())
        opened_settings_metadata = os.fstat(settings_descriptor)
        if not stat.S_ISREG(opened_settings_metadata.st_mode):
            raise SettingsError("not_regular")
        if not _same_file(settings_metadata, opened_settings_metadata):
            raise SettingsError("unsafe_path")
        if _has_unsafe_posix_permissions(opened_settings_metadata):
            raise SettingsError("unsafe_permissions")
        if opened_settings_metadata.st_size > SETTINGS_MAX_BYTES:
            raise SettingsError("too_large")
        return _read_descriptor(settings_descriptor)
    except FileNotFoundError:
        return None
    except SettingsError:
        raise
    except OSError as error:
        _raise_bounded_source_error(error)
    finally:
        _close_descriptor(settings_descriptor)
        _close_descriptor(directory_descriptor)


def _get_file_memory_tool_settings() -> MemoryToolSettings:
    application_directory = Path.home() / SETTINGS_DIRECTORY_NAME
    application_metadata = _validate_application_directory(application_directory)
    if application_metadata is None:
        return MemoryToolSettings()

    settings_path = application_directory / SETTINGS_FILE_NAME
    settings_metadata = _validate_settings_path(settings_path)
    if settings_metadata is None:
        return MemoryToolSettings()

    source = _read_settings_source(
        application_directory,
        settings_path,
        application_metadata,
        settings_metadata,
    )
    if source is None:
        return MemoryToolSettings()

    try:
        document = tomllib.loads(source.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        raise SettingsError("invalid_toml") from None

    if set(document) - {"memory"}:
        raise SettingsError("invalid_schema")
    memory_settings = document.get("memory")
    if memory_settings is None:
        return MemoryToolSettings()
    if not isinstance(memory_settings, dict):
        raise SettingsError("invalid_schema")
    if set(memory_settings) - {
        "remember_enabled",
        "archive_restore_enabled",
        "forget_enabled",
        "revise_enabled",
    }:
        raise SettingsError("invalid_schema")
    values = {
        "remember_enabled": memory_settings.get("remember_enabled", False),
        "archive_restore_enabled": memory_settings.get(
            "archive_restore_enabled",
            False,
        ),
        "forget_enabled": memory_settings.get("forget_enabled", False),
        "revise_enabled": memory_settings.get("revise_enabled", False),
    }
    if any(not isinstance(value, bool) for value in values.values()):
        raise SettingsError("invalid_schema")
    return MemoryToolSettings(**values)


def _environment_boolean(name: str) -> bool | None:
    value = os.getenv(name)
    if value == "false":
        return False
    if value == "true":
        return True
    if value is None:
        return None
    raise ValueError(f"{name} must be 'true' or 'false'")


def get_memory_tool_settings() -> MemoryToolSettings:
    remember_override = _environment_boolean(MEMORY_REMEMBER_ENABLED_ENV)
    archive_restore_override = _environment_boolean(
        MEMORY_ARCHIVE_RESTORE_ENABLED_ENV
    )
    forget_override = _environment_boolean(MEMORY_FORGET_ENABLED_ENV)
    revise_override = _environment_boolean(MEMORY_REVISE_ENABLED_ENV)
    if (
        remember_override is not None
        and archive_restore_override is not None
        and forget_override is not None
        and revise_override is not None
    ):
        return MemoryToolSettings(
            remember_enabled=remember_override,
            archive_restore_enabled=archive_restore_override,
            forget_enabled=forget_override,
            revise_enabled=revise_override,
        )

    file_settings = _get_file_memory_tool_settings()
    return MemoryToolSettings(
        remember_enabled=(
            file_settings.remember_enabled
            if remember_override is None
            else remember_override
        ),
        archive_restore_enabled=(
            file_settings.archive_restore_enabled
            if archive_restore_override is None
            else archive_restore_override
        ),
        forget_enabled=(
            file_settings.forget_enabled
            if forget_override is None
            else forget_override
        ),
        revise_enabled=(
            file_settings.revise_enabled
            if revise_override is None
            else revise_override
        ),
    )


def get_memory_remember_enabled() -> bool:
    return get_memory_tool_settings().remember_enabled


def get_memory_archive_restore_enabled() -> bool:
    return get_memory_tool_settings().archive_restore_enabled


def get_memory_forget_enabled() -> bool:
    return get_memory_tool_settings().forget_enabled


def get_memory_revise_enabled() -> bool:
    return get_memory_tool_settings().revise_enabled
