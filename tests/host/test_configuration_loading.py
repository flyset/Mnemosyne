import logging
import os
from types import SimpleNamespace
from pathlib import Path

import pytest

import mymcp.host.configuration as configuration_module
from mymcp.host.configuration import (
    CONFIGURATION_MAX_BYTES,
    HostConfiguration,
    HostConfigurationError,
    load_host_configuration,
    resolve_host_configuration_path,
)


VALID_SOURCE = b"schema_version = 1\n"
CONFIGURATION_LOGGER = "mymcp.host.configuration"


def _write_configuration(base: Path, source: bytes = VALID_SOURCE) -> Path:
    application_directory = base / "mymcp"
    application_directory.mkdir(mode=0o700, parents=True)
    application_directory.chmod(0o700)
    configuration_path = application_directory / "config.toml"
    configuration_path.write_bytes(source)
    configuration_path.chmod(0o600)
    return configuration_path


def test_present_source_emits_one_bounded_loaded_event(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    selected = tmp_path / "selected"
    _write_configuration(
        selected,
        b"""
schema_version = 1
[server]
address = "::1"
port = 9000
[[plugins]]
id = "alpha"
enabled = false
[[plugins]]
id = "beta"
enabled = true
""",
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))

    with caplog.at_level(logging.INFO, logger=CONFIGURATION_LOGGER):
        snapshot = load_host_configuration()

    assert snapshot.server.address == "::1"
    assert caplog.messages == [
        "host_configuration outcome=loaded schema_version=1 address=::1 "
        "port=9000 declarations=2 enabled=1"
    ]


def test_schema_v2_present_source_emits_one_bounded_loaded_event(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    selected = tmp_path / "selected"
    _write_configuration(
        selected,
        b"""
schema_version = 2
[[plugins]]
id = "alpha"
enabled = true
manifest_path = "/opt/alpha/manifest.json"
module = "operator_plugins.alpha"
""",
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))

    with caplog.at_level(logging.INFO, logger=CONFIGURATION_LOGGER):
        snapshot = load_host_configuration()

    assert snapshot.schema_version.value == 2
    assert caplog.messages == [
        "host_configuration outcome=loaded schema_version=2 "
        "address=127.0.0.1 port=8000 declarations=1 enabled=1"
    ]


def test_absent_source_emits_one_bounded_defaults_event_without_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    selected = tmp_path / "selected"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))

    with caplog.at_level(logging.INFO, logger=CONFIGURATION_LOGGER):
        snapshot = load_host_configuration()

    assert snapshot == HostConfiguration.default()
    assert caplog.messages == [
        "host_configuration outcome=absent_defaults schema_version=1 "
        "address=127.0.0.1 port=8000 declarations=0 enabled=0"
    ]
    assert not selected.exists()


@pytest.mark.parametrize("value", [None, "", "relative/path"])
def test_invalid_or_absent_xdg_home_uses_the_fixed_home_fallback(
    value: str | None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)
    if value is None:
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    else:
        monkeypatch.setenv("XDG_CONFIG_HOME", value)

    assert resolve_host_configuration_path() == (
        home / ".config" / "mymcp" / "config.toml"
    )
    assert not home.exists()


def test_absolute_xdg_home_is_used_verbatim_without_home_or_expansion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "$UNEXPANDED" / "~"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))
    monkeypatch.setattr(
        Path,
        "home",
        lambda: pytest.fail("absolute XDG selection must not inspect home"),
    )

    assert resolve_host_configuration_path() == selected / "mymcp" / "config.toml"


@pytest.mark.skipif(os.name != "nt", reason="native Windows path semantics")
@pytest.mark.parametrize("selected", [r"C:\settings", r"\\server\share\settings"])
def test_windows_accepts_absolute_drive_and_unc_xdg_locations(
    selected: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", selected)
    monkeypatch.setattr(
        Path,
        "home",
        lambda: pytest.fail("absolute Windows XDG selection must not inspect home"),
    )

    assert resolve_host_configuration_path() == (
        Path(selected) / "mymcp" / "config.toml"
    )


@pytest.mark.skipif(os.name != "nt", reason="native Windows path semantics")
def test_windows_drive_relative_xdg_location_uses_xdg_home_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("XDG_CONFIG_HOME", r"C:settings")
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "localappdata"))
    monkeypatch.setattr(Path, "home", lambda: home)

    assert resolve_host_configuration_path() == (
        home / ".config" / "mymcp" / "config.toml"
    )


def test_xdg_home_is_read_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    selected = str(tmp_path / "xdg")
    calls = 0

    def getenv(name: str) -> str | None:
        nonlocal calls
        assert name == "XDG_CONFIG_HOME"
        calls += 1
        return selected

    monkeypatch.setattr(configuration_module.os, "getenv", getenv)

    assert resolve_host_configuration_path() == Path(selected) / "mymcp" / "config.toml"
    assert calls == 1


def test_unrepresentable_xdg_home_has_a_bounded_location_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(configuration_module.os, "getenv", lambda _name: "/tmp/\udcff")

    with pytest.raises(HostConfigurationError) as captured:
        resolve_host_configuration_path()

    assert captured.value.code == "invalid_location"
    assert str(captured.value) == "MyMCP configuration location is unavailable"
    assert captured.value.__cause__ is None


def test_unavailable_home_has_a_bounded_location_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: (_ for _ in ()).throw(RuntimeError("secret")))

    with pytest.raises(HostConfigurationError) as captured:
        resolve_host_configuration_path()

    assert captured.value.code == "invalid_location"
    assert "secret" not in str(captured.value)
    assert captured.value.__cause__ is None


def test_unrepresentable_home_has_a_bounded_location_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: Path("/tmp/\udcff"))

    with pytest.raises(HostConfigurationError) as captured:
        resolve_host_configuration_path()

    assert captured.value.code == "invalid_location"


def test_missing_configuration_returns_defaults_without_creating_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "xdg"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))

    assert load_host_configuration() == HostConfiguration.default()
    assert not selected.exists()


def test_present_configuration_loads_once_from_the_selected_xdg_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected"
    _write_configuration(
        selected,
        b"schema_version = 1\n[server]\nport = 9000\n",
    )
    fallback = tmp_path / "home" / ".config"
    _write_configuration(fallback, b"schema_version = 1\n[server]\nport = 7000\n")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    original = configuration_module._read_configuration_source
    calls = 0

    def counted_read(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(configuration_module, "_read_configuration_source", counted_read)

    assert load_host_configuration().server.port == 9000
    assert calls == 1


def test_invalid_selected_source_never_falls_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected"
    selected.mkdir()
    (selected / "mymcp").write_text("not a directory", encoding="utf-8")
    fallback_home = tmp_path / "home"
    _write_configuration(
        fallback_home / ".config",
        b"schema_version = 1\n[server]\nport = 7000\n",
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))
    monkeypatch.setattr(Path, "home", lambda: fallback_home)

    with pytest.raises(HostConfigurationError) as captured:
        load_host_configuration()

    assert captured.value.code == "unsafe_path"


def test_symlinked_xdg_ancestor_is_allowed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "target"
    _write_configuration(target)
    selected = tmp_path / "selected"
    try:
        selected.symlink_to(target, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlink unavailable: {error}")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))

    assert load_host_configuration() == HostConfiguration.default()


@pytest.mark.parametrize("symlink_part", ["application", "file"])
def test_selected_application_and_file_symlinks_are_rejected(
    symlink_part: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected"
    selected.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    if symlink_part == "application":
        _write_configuration(target)
        link = selected / "mymcp"
        destination = target / "mymcp"
        directory = True
    else:
        application_directory = selected / "mymcp"
        application_directory.mkdir(mode=0o700)
        application_directory.chmod(0o700)
        destination = target / "config.toml"
        destination.write_bytes(VALID_SOURCE)
        link = application_directory / "config.toml"
        directory = False
    try:
        link.symlink_to(destination, target_is_directory=directory)
    except OSError as error:
        pytest.skip(f"symlink unavailable: {error}")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))

    with pytest.raises(HostConfigurationError) as captured:
        load_host_configuration()

    assert captured.value.code == "unsafe_path"


@pytest.mark.parametrize("invalid_part", ["application", "file"])
def test_non_directory_application_and_non_regular_file_are_rejected(
    invalid_part: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected"
    selected.mkdir()
    application = selected / "mymcp"
    if invalid_part == "application":
        application.write_bytes(b"not a directory")
        expected = "unsafe_path"
    else:
        application.mkdir(mode=0o700)
        application.chmod(0o700)
        (application / "config.toml").mkdir()
        expected = "not_regular"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))

    with pytest.raises(HostConfigurationError) as captured:
        load_host_configuration()

    assert captured.value.code == expected


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission policy")
@pytest.mark.parametrize("unsafe_part", ["application", "file"])
def test_group_or_world_writable_sources_are_rejected(
    unsafe_part: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected"
    path = _write_configuration(selected)
    if unsafe_part == "application":
        path.parent.chmod(0o722)
    else:
        path.chmod(0o622)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))

    with pytest.raises(HostConfigurationError) as captured:
        load_host_configuration()

    assert captured.value.code == "unsafe_permissions"


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission policy")
def test_non_writable_shared_read_modes_are_accepted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected"
    path = _write_configuration(selected)
    path.parent.chmod(0o755)
    path.chmod(0o644)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))

    assert load_host_configuration() == HostConfiguration.default()


def test_exact_source_limit_is_accepted_and_one_extra_byte_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected"
    prefix = VALID_SOURCE
    exact_source = prefix + b"#" + b"x" * (CONFIGURATION_MAX_BYTES - len(prefix) - 2) + b"\n"
    path = _write_configuration(selected, exact_source)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))

    assert len(exact_source) == CONFIGURATION_MAX_BYTES
    assert load_host_configuration() == HostConfiguration.default()

    path.write_bytes(exact_source + b"\n")
    path.chmod(0o600)
    with pytest.raises(HostConfigurationError) as captured:
        load_host_configuration()
    assert captured.value.code == "too_large"


def test_invalid_utf8_is_distinct_from_invalid_toml(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected"
    _write_configuration(selected, b"\xff")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))

    with pytest.raises(HostConfigurationError) as captured:
        load_host_configuration()

    assert captured.value.code == "invalid_utf8"
    assert str(captured.value) == "MyMCP configuration is not valid UTF-8"


def test_malformed_toml_remains_bounded_through_source_loading(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected"
    _write_configuration(selected, b"schema_version = [\n")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))

    with pytest.raises(HostConfigurationError) as captured:
        load_host_configuration()

    assert captured.value.code == "invalid_toml"


def test_descriptor_replacement_before_open_is_a_source_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected"
    path = _write_configuration(selected)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))
    original_open = configuration_module.os.open
    replaced = False

    def replacing_open(target, flags, *args, **kwargs):
        nonlocal replaced
        if (target == "config.toml" or Path(target) == path) and not replaced:
            replaced = True
            path.unlink()
            path.write_bytes(VALID_SOURCE)
            path.chmod(0o600)
        return original_open(target, flags, *args, **kwargs)

    monkeypatch.setattr(configuration_module.os, "open", replacing_open)

    with pytest.raises(HostConfigurationError) as captured:
        load_host_configuration()

    assert captured.value.code == "source_changed"


def test_mutation_during_descriptor_read_is_a_source_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected"
    path = _write_configuration(selected)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))
    original_read = configuration_module.os.read
    mutated = False

    def mutating_read(descriptor: int, size: int) -> bytes:
        nonlocal mutated
        chunk = original_read(descriptor, size)
        if chunk and not mutated:
            mutated = True
            path.write_bytes(b"schema_version = 1\n# changed\n")
            path.chmod(0o600)
        return chunk

    monkeypatch.setattr(configuration_module.os, "read", mutating_read)

    with pytest.raises(HostConfigurationError) as captured:
        load_host_configuration()

    assert captured.value.code == "source_changed"


def test_path_replacement_while_descriptor_is_open_is_a_source_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected"
    path = _write_configuration(selected)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))
    original_read = configuration_module.os.read
    replaced = False

    def replacing_read(descriptor: int, size: int) -> bytes:
        nonlocal replaced
        chunk = original_read(descriptor, size)
        if chunk and not replaced:
            replaced = True
            replacement = path.with_suffix(".replacement")
            replacement.write_bytes(VALID_SOURCE)
            replacement.chmod(0o600)
            os.replace(replacement, path)
        return chunk

    monkeypatch.setattr(configuration_module.os, "read", replacing_read)

    with pytest.raises(HostConfigurationError) as captured:
        load_host_configuration()

    assert captured.value.code == "source_changed"


def test_unreadable_source_error_does_not_expose_underlying_detail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected"
    _write_configuration(selected)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))

    def denied_open(*_args, **_kwargs):
        raise PermissionError("private operating-system detail")

    monkeypatch.setattr(configuration_module.os, "open", denied_open)

    with pytest.raises(HostConfigurationError) as captured:
        load_host_configuration()

    assert captured.value.code == "unreadable"
    assert str(captured.value) == "MyMCP configuration source could not be read"
    assert "private" not in str(captured.value)
    assert captured.value.__cause__ is None


def test_no_follow_descriptor_flags_are_used_when_available(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected"
    _write_configuration(selected)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))
    original_open = configuration_module.os.open
    observed: list[tuple[object, int, dict[str, object]]] = []

    def recording_open(target, flags, *args, **kwargs):
        observed.append((target, flags, kwargs))
        return original_open(target, flags, *args, **kwargs)

    monkeypatch.setattr(configuration_module.os, "open", recording_open)

    assert load_host_configuration() == HostConfiguration.default()
    assert observed
    if hasattr(os, "O_NOFOLLOW"):
        assert all(flags & os.O_NOFOLLOW for _, flags, _ in observed)
    if hasattr(os, "O_DIRECTORY"):
        assert observed[0][1] & os.O_DIRECTORY
    if configuration_module._OPEN_SUPPORTS_DIR_FD:
        assert observed[1][0] == "config.toml"
        assert "dir_fd" in observed[1][2]


def test_absolute_file_open_fallback_avoids_directory_fd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected"
    path = _write_configuration(selected)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))
    monkeypatch.setattr(configuration_module, "_OPEN_SUPPORTS_DIR_FD", False)
    original_open = configuration_module.os.open
    observed: list[tuple[object, dict[str, object]]] = []

    def recording_open(target, flags, *args, **kwargs):
        observed.append((target, kwargs))
        return original_open(target, flags, *args, **kwargs)

    monkeypatch.setattr(configuration_module.os, "open", recording_open)

    assert load_host_configuration() == HostConfiguration.default()
    assert observed[1] == (path, {})


def test_reparse_point_detection_uses_the_platform_file_attribute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = 0x400
    monkeypatch.setattr(
        configuration_module.stat,
        "FILE_ATTRIBUTE_REPARSE_POINT",
        marker,
        raising=False,
    )

    assert configuration_module._is_reparse_point(
        SimpleNamespace(st_file_attributes=marker)
    )


@pytest.mark.parametrize(
    ("code", "message"),
    [
        ("invalid_location", "MyMCP configuration location is unavailable"),
        ("unsafe_path", "MyMCP configuration path is unsafe"),
        ("not_regular", "MyMCP configuration source is not a regular file"),
        (
            "unsafe_permissions",
            "MyMCP configuration source permissions are unsafe",
        ),
        ("unreadable", "MyMCP configuration source could not be read"),
        ("too_large", "MyMCP configuration exceeds 65536 bytes"),
        ("source_changed", "MyMCP configuration changed while being read"),
        ("invalid_utf8", "MyMCP configuration is not valid UTF-8"),
    ],
)
def test_source_errors_have_fixed_bounded_messages(code: str, message: str) -> None:
    error = HostConfigurationError(code)

    assert error.code == code
    assert str(error) == message


@pytest.mark.parametrize(
    "code",
    [
        "invalid_location",
        "unsafe_path",
        "not_regular",
        "unsafe_permissions",
        "unreadable",
        "too_large",
        "source_changed",
        "invalid_utf8",
        "invalid_toml",
        "unsupported_schema_version",
        "invalid_schema",
        "duplicate_plugin",
    ],
)
def test_each_load_failure_emits_one_bounded_error_and_reraises_same_exception(
    code: str,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    expected = HostConfigurationError(code)

    def fail_resolution() -> Path:
        raise expected

    monkeypatch.setattr(
        configuration_module,
        "resolve_host_configuration_path",
        fail_resolution,
    )

    with caplog.at_level(logging.ERROR, logger=CONFIGURATION_LOGGER):
        with pytest.raises(HostConfigurationError) as captured:
            load_host_configuration()

    assert captured.value is expected
    assert caplog.messages == [f"host_configuration outcome=error code={code}"]


def test_failure_log_omits_path_environment_source_and_exception_details(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    selected = tmp_path / "private-location-marker"
    _write_configuration(
        selected,
        b'private_source_marker = "private_plugin_marker"\n',
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))

    with caplog.at_level(logging.ERROR, logger=CONFIGURATION_LOGGER):
        with pytest.raises(HostConfigurationError) as captured:
            load_host_configuration()

    assert captured.value.code == "invalid_schema"
    assert caplog.messages == [
        "host_configuration outcome=error code=invalid_schema"
    ]
    rendered = " ".join(caplog.messages)
    assert "private-location-marker" not in rendered
    assert "private_source_marker" not in rendered
    assert "private_plugin_marker" not in rendered
