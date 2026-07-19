import os
from pathlib import Path

import pytest

import mnemosyne.settings as settings
from mnemosyne.settings import (
    SETTINGS_MAX_BYTES,
    SettingsError,
    get_memory_archive_restore_enabled,
    get_memory_forget_enabled,
    get_memory_remember_enabled,
    get_memory_revise_enabled,
    get_memory_tool_settings,
)


def _isolate_home(
    home: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.delenv("MNEMOSYNE_MEMORY_REMEMBER_ENABLED", raising=False)
    monkeypatch.delenv(
        "MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED",
        raising=False,
    )
    monkeypatch.delenv("MNEMOSYNE_MEMORY_FORGET_ENABLED", raising=False)
    monkeypatch.delenv("MNEMOSYNE_MEMORY_REVISE_ENABLED", raising=False)


def _write_settings(home: Path, source: bytes) -> Path:
    application_directory = home / ".mnemosyne"
    application_directory.mkdir(mode=0o700)
    application_directory.chmod(0o700)
    settings_path = application_directory / "config.toml"
    settings_path.write_bytes(source)
    settings_path.chmod(0o600)
    return settings_path


@pytest.mark.parametrize(
    ("configured_value", "expected"),
    [
        (None, False),
        ("false", False),
        ("true", True),
    ],
)
def test_memory_remember_enablement_uses_strict_boolean_values(
    configured_value: str | None,
    expected: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    if configured_value is None:
        monkeypatch.delenv("MNEMOSYNE_MEMORY_REMEMBER_ENABLED", raising=False)
    else:
        monkeypatch.setenv(
            "MNEMOSYNE_MEMORY_REMEMBER_ENABLED",
            configured_value,
        )

    assert get_memory_remember_enabled() is expected


@pytest.mark.parametrize(
    ("configured_value", "expected"),
    [(None, False), ("false", False), ("true", True)],
)
def test_memory_archive_restore_enablement_uses_strict_boolean_values(
    configured_value: str | None,
    expected: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("MNEMOSYNE_MEMORY_REMEMBER_ENABLED", "false")
    if configured_value is None:
        monkeypatch.delenv(
            "MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED",
            raising=False,
        )
    else:
        monkeypatch.setenv(
            "MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED",
            configured_value,
        )

    assert get_memory_archive_restore_enabled() is expected


@pytest.mark.parametrize(
    ("configured_value", "expected"),
    [(None, False), ("false", False), ("true", True)],
)
def test_memory_forget_enablement_uses_strict_boolean_values(
    configured_value: str | None,
    expected: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("MNEMOSYNE_MEMORY_REMEMBER_ENABLED", "false")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED", "false")
    if configured_value is None:
        monkeypatch.delenv("MNEMOSYNE_MEMORY_FORGET_ENABLED", raising=False)
    else:
        monkeypatch.setenv("MNEMOSYNE_MEMORY_FORGET_ENABLED", configured_value)

    assert get_memory_forget_enabled() is expected


@pytest.mark.parametrize(
    ("configured_value", "expected"),
    [(None, False), ("false", False), ("true", True)],
)
def test_memory_revise_enablement_uses_strict_boolean_values(
    configured_value: str | None,
    expected: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("MNEMOSYNE_MEMORY_REMEMBER_ENABLED", "false")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED", "false")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_FORGET_ENABLED", "false")
    if configured_value is None:
        monkeypatch.delenv("MNEMOSYNE_MEMORY_REVISE_ENABLED", raising=False)
    else:
        monkeypatch.setenv("MNEMOSYNE_MEMORY_REVISE_ENABLED", configured_value)

    assert get_memory_revise_enabled() is expected


@pytest.mark.parametrize(
    "configured_value",
    ["", " true", "true ", "TRUE", "False", "1", "0", "yes"],
)
def test_memory_remember_enablement_fails_closed_without_echoing_invalid_value(
    configured_value: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        Path,
        "home",
        lambda: pytest.fail("an environment value must prevent file access"),
    )
    monkeypatch.setenv(
        "MNEMOSYNE_MEMORY_REMEMBER_ENABLED",
        configured_value,
    )

    with pytest.raises(ValueError) as error:
        get_memory_remember_enabled()

    assert str(error.value) == (
        "MNEMOSYNE_MEMORY_REMEMBER_ENABLED must be 'true' or 'false'"
    )


@pytest.mark.parametrize(
    "configured_value",
    ["", " true", "true ", "TRUE", "False", "1", "0", "yes"],
)
def test_archive_restore_enablement_fails_closed_without_file_access(
    configured_value: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        Path,
        "home",
        lambda: pytest.fail("invalid environment must fail before file access"),
    )
    monkeypatch.delenv("MNEMOSYNE_MEMORY_REMEMBER_ENABLED", raising=False)
    monkeypatch.setenv(
        "MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED",
        configured_value,
    )

    with pytest.raises(ValueError) as error:
        get_memory_tool_settings()

    assert str(error.value) == (
        "MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED must be 'true' or 'false'"
    )


@pytest.mark.parametrize(
    "configured_value",
    ["", " true", "true ", "TRUE", "False", "1", "0", "yes"],
)
def test_forget_enablement_fails_closed_without_file_access(
    configured_value: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        Path,
        "home",
        lambda: pytest.fail("invalid environment must fail before file access"),
    )
    monkeypatch.delenv("MNEMOSYNE_MEMORY_REMEMBER_ENABLED", raising=False)
    monkeypatch.delenv(
        "MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED",
        raising=False,
    )
    monkeypatch.setenv("MNEMOSYNE_MEMORY_FORGET_ENABLED", configured_value)

    with pytest.raises(ValueError) as error:
        get_memory_tool_settings()

    assert str(error.value) == (
        "MNEMOSYNE_MEMORY_FORGET_ENABLED must be 'true' or 'false'"
    )


@pytest.mark.parametrize(
    "configured_value",
    ["", " true", "true ", "TRUE", "False", "1", "0", "yes"],
)
def test_revise_enablement_fails_closed_without_file_access(
    configured_value: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        Path,
        "home",
        lambda: pytest.fail("invalid environment must fail before file access"),
    )
    monkeypatch.setenv("MNEMOSYNE_MEMORY_REVISE_ENABLED", configured_value)

    with pytest.raises(ValueError) as error:
        get_memory_tool_settings()

    assert str(error.value) == (
        "MNEMOSYNE_MEMORY_REVISE_ENABLED must be 'true' or 'false'"
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (b"", False),
        (b"[memory]\n", False),
        (b"[memory]\nremember_enabled = false\n", False),
        (b"[memory]\nremember_enabled = true\n", True),
    ],
)
def test_memory_remember_enablement_uses_strict_local_toml(
    source: bytes,
    expected: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_home(tmp_path, monkeypatch)
    settings_path = _write_settings(tmp_path, source)
    original_mode = settings_path.stat().st_mode & 0o777

    assert get_memory_remember_enabled() is expected
    assert settings_path.read_bytes() == source
    assert settings_path.stat().st_mode & 0o777 == original_mode


@pytest.mark.parametrize(
    (
        "source",
        "remember_enabled",
        "archive_restore_enabled",
        "forget_enabled",
        "revise_enabled",
    ),
    [
        (b"", False, False, False, False),
        (
            b"[memory]\nremember_enabled = true\narchive_restore_enabled = false\n",
            True,
            False,
            False,
            False,
        ),
        (
            b"[memory]\nremember_enabled = false\narchive_restore_enabled = true\n",
            False,
            True,
            False,
            False,
        ),
        (b"[memory]\narchive_restore_enabled = true\n", False, True, False, False),
        (b"[memory]\nforget_enabled = true\n", False, False, True, False),
        (b"[memory]\nrevise_enabled = true\n", False, False, False, True),
    ],
)
def test_memory_tool_settings_use_one_strict_local_document(
    source: bytes,
    remember_enabled: bool,
    archive_restore_enabled: bool,
    forget_enabled: bool,
    revise_enabled: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_home(tmp_path, monkeypatch)
    _write_settings(tmp_path, source)

    resolved = get_memory_tool_settings()

    assert resolved.remember_enabled is remember_enabled
    assert resolved.archive_restore_enabled is archive_restore_enabled
    assert resolved.forget_enabled is forget_enabled
    assert resolved.revise_enabled is revise_enabled


def test_memory_tool_settings_read_the_file_at_most_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_home(tmp_path, monkeypatch)
    _write_settings(
        tmp_path,
        b"[memory]\nremember_enabled = true\narchive_restore_enabled = true\nforget_enabled = true\nrevise_enabled = true\n",
    )
    original = settings._read_settings_source
    calls = 0

    def counted_read(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(settings, "_read_settings_source", counted_read)

    assert get_memory_tool_settings() == settings.MemoryToolSettings(True, True, True, True)
    assert calls == 1


@pytest.mark.parametrize(
    ("environment_name", "expected"),
    [
        (
            "MNEMOSYNE_MEMORY_REMEMBER_ENABLED",
            settings.MemoryToolSettings(False, True, True, True),
        ),
        (
            "MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED",
            settings.MemoryToolSettings(True, False, True, True),
        ),
        (
            "MNEMOSYNE_MEMORY_FORGET_ENABLED",
            settings.MemoryToolSettings(True, True, False, True),
        ),
        (
            "MNEMOSYNE_MEMORY_REVISE_ENABLED",
            settings.MemoryToolSettings(True, True, True, False),
        ),
    ],
)
def test_each_environment_override_preserves_the_other_file_setting(
    environment_name: str,
    expected: settings.MemoryToolSettings,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_home(tmp_path, monkeypatch)
    _write_settings(
        tmp_path,
        b"[memory]\nremember_enabled = true\narchive_restore_enabled = true\nforget_enabled = true\nrevise_enabled = true\n",
    )
    monkeypatch.setenv(environment_name, "false")

    resolved = get_memory_tool_settings()

    assert resolved == expected


def test_missing_settings_default_off_without_creating_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_home(tmp_path, monkeypatch)

    assert get_memory_remember_enabled() is False
    assert not (tmp_path / ".mnemosyne").exists()


@pytest.mark.parametrize("configured_value", ["true", "false"])
def test_complete_valid_environment_overrides_prevent_any_file_access(
    configured_value: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        Path,
        "home",
        lambda: pytest.fail("an environment override must prevent file access"),
    )
    monkeypatch.setenv(
        "MNEMOSYNE_MEMORY_REMEMBER_ENABLED",
        configured_value,
    )
    monkeypatch.setenv(
        "MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED",
        "false",
    )
    monkeypatch.setenv("MNEMOSYNE_MEMORY_FORGET_ENABLED", "false")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_REVISE_ENABLED", "false")

    assert get_memory_remember_enabled() is (configured_value == "true")


@pytest.mark.parametrize(
    "source",
    [
        b"remember_enabled = true\n",
        b"memory = true\n",
        b"[other]\nvalue = true\n",
        b"[memory]\nunknown = true\n",
        b"[memory]\nremember_enabled = 1\n",
        b'[memory]\nremember_enabled = "true"\n',
        b"[memory]\narchive_restore_enabled = 1\n",
        b'[memory]\narchive_restore_enabled = "true"\n',
        b"[memory]\nforget_enabled = 1\n",
        b'[memory]\nforget_enabled = "true"\n',
        b"[memory]\nrevise_enabled = 1\n",
        b'[memory]\nrevise_enabled = "true"\n',
        b"[memory.remember_enabled]\nvalue = true\n",
    ],
)
def test_settings_reject_unknown_structure_and_non_boolean_values(
    source: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_home(tmp_path, monkeypatch)
    _write_settings(tmp_path, source)

    with pytest.raises(SettingsError) as error:
        get_memory_remember_enabled()

    assert error.value.code == "invalid_schema"
    assert str(error.value) == "Mnemosyne settings file has an invalid schema"
    assert source.decode() not in str(error.value)


@pytest.mark.parametrize("source", [b"[memory\n", b"\xff"])
def test_settings_reject_invalid_toml_without_parser_details(
    source: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_home(tmp_path, monkeypatch)
    _write_settings(tmp_path, source)

    with pytest.raises(SettingsError) as error:
        get_memory_remember_enabled()

    assert error.value.code == "invalid_toml"
    assert str(error.value) == "Mnemosyne settings file is not valid TOML"


def test_settings_accept_exact_size_limit_and_reject_larger_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_home(tmp_path, monkeypatch)
    prefix = b"[memory]\nremember_enabled = true\n"
    exact_source = prefix + b"#" + b"x" * (
        SETTINGS_MAX_BYTES - len(prefix) - 2
    ) + b"\n"
    settings_path = _write_settings(tmp_path, exact_source)

    assert len(exact_source) == SETTINGS_MAX_BYTES
    assert get_memory_remember_enabled() is True

    settings_path.write_bytes(exact_source + b"\n")
    with pytest.raises(SettingsError) as error:
        get_memory_remember_enabled()

    assert error.value.code == "too_large"
    assert str(error.value) == "Mnemosyne settings file exceeds 16384 bytes"


def test_settings_reject_symlinked_application_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_home(tmp_path, monkeypatch)
    target = tmp_path / "redirected"
    target.mkdir()
    (tmp_path / ".mnemosyne").symlink_to(target, target_is_directory=True)

    with pytest.raises(SettingsError) as error:
        get_memory_remember_enabled()

    assert error.value.code == "unsafe_path"
    assert str(error.value) == "Mnemosyne settings file path is unsafe"


def test_settings_reject_symlinked_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_home(tmp_path, monkeypatch)
    target = tmp_path / "redirected.toml"
    target.write_text("[memory]\nremember_enabled = true\n")
    application_directory = tmp_path / ".mnemosyne"
    application_directory.mkdir(mode=0o700)
    (application_directory / "config.toml").symlink_to(target)

    with pytest.raises(SettingsError) as error:
        get_memory_remember_enabled()

    assert error.value.code == "unsafe_path"
    assert str(error.value) == "Mnemosyne settings file path is unsafe"


def test_settings_reject_non_directory_application_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_home(tmp_path, monkeypatch)
    (tmp_path / ".mnemosyne").write_text("not a directory")

    with pytest.raises(SettingsError) as error:
        get_memory_remember_enabled()

    assert error.value.code == "unsafe_path"
    assert str(error.value) == "Mnemosyne settings file path is unsafe"


def test_settings_reject_non_regular_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_home(tmp_path, monkeypatch)
    application_directory = tmp_path / ".mnemosyne"
    application_directory.mkdir(mode=0o700)
    (application_directory / "config.toml").mkdir()

    with pytest.raises(SettingsError) as error:
        get_memory_remember_enabled()

    assert error.value.code == "not_regular"
    assert str(error.value) == (
        "Mnemosyne settings source is not a regular file"
    )


@pytest.mark.skipif(os.name != "posix", reason="POSIX mode policy")
@pytest.mark.parametrize("unsafe_source", ["directory", "file"])
def test_settings_reject_group_or_world_writable_sources(
    unsafe_source: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_home(tmp_path, monkeypatch)
    settings_path = _write_settings(
        tmp_path,
        b"[memory]\nremember_enabled = true\n",
    )
    unsafe_path = (
        settings_path.parent if unsafe_source == "directory" else settings_path
    )
    unsafe_path.chmod(0o722 if unsafe_source == "directory" else 0o622)

    with pytest.raises(SettingsError) as error:
        get_memory_remember_enabled()

    assert error.value.code == "unsafe_permissions"
    assert str(error.value) == (
        "Mnemosyne settings source permissions are unsafe"
    )


@pytest.mark.skipif(os.name != "posix", reason="POSIX mode policy")
def test_settings_accept_non_writable_non_private_modes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_home(tmp_path, monkeypatch)
    settings_path = _write_settings(
        tmp_path,
        b"[memory]\nremember_enabled = true\n",
    )
    settings_path.parent.chmod(0o755)
    settings_path.chmod(0o644)

    assert get_memory_remember_enabled() is True


def test_settings_bounds_unreadable_source_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_home(tmp_path, monkeypatch)
    _write_settings(tmp_path, b"[memory]\nremember_enabled = true\n")

    def deny_open(*args: object, **kwargs: object) -> int:
        raise PermissionError("synthetic private operating-system detail")

    monkeypatch.setattr(settings.os, "open", deny_open)

    with pytest.raises(SettingsError) as error:
        get_memory_remember_enabled()

    assert error.value.code == "unreadable"
    assert str(error.value) == "Mnemosyne settings file could not be read"
    assert "synthetic" not in str(error.value)
