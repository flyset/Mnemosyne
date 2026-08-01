import json
import os
import stat
from pathlib import Path

import pytest

from mymcp.host.configuration import parse_host_configuration_toml
from mymcp.host.external_plugins import (
    EXTERNAL_PLUGIN_ERROR_MESSAGES,
    ExternalPluginLoadError,
    preflight_external_manifests,
)


def _manifest(
    plugin_id: str = "external",
    *,
    minimum: int = 1,
    maximum: int = 1,
    capability_count: int = 1,
) -> bytes:
    return json.dumps(
        {
            "manifest_version": 1,
            "id": plugin_id,
            "title": "External",
            "description": "An explicit external plugin.",
            "version": "1.0.0",
            "requires": {"host_api": {"min": minimum, "max": maximum}},
            "capabilities": [
                {
                    "kind": "tool",
                    "id": f"external_tool_{index}",
                    "version": "1.0.0",
                    "read_only": True,
                    "destructive": False,
                    "idempotent": True,
                    "open_world": False,
                    "consent": "none",
                }
                for index in range(capability_count)
            ],
            "configuration": {
                "schema_version": 1,
                "schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False,
                },
            },
            "secret_references": [],
            "data_schema_version": 1,
            "authority": {"filesystem": [], "network": False},
        }
    ).encode()


def _configuration(*declarations: tuple[str, bool, Path, str]):
    source = ["schema_version = 2"]
    for plugin_id, enabled, manifest_path, module in declarations:
        source.extend(
            (
                "[[plugins]]",
                f'id = "{plugin_id}"',
                f"enabled = {str(enabled).lower()}",
                f'manifest_path = "{manifest_path}"',
                f'module = "{module}"',
            )
        )
    return parse_host_configuration_toml("\n".join(source))


def test_preflight_reads_enabled_manifests_once_in_declaration_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    disabled = tmp_path / "disabled.json"
    first.write_bytes(_manifest("first"))
    second.write_bytes(_manifest("second"))
    configuration = _configuration(
        ("first", True, first, "operator_plugins.first"),
        ("disabled", False, disabled, "operator_plugins.disabled"),
        ("second", True, second, "operator_plugins.second"),
    )
    import mymcp.host.external_plugins as external_plugins

    reads: list[Path] = []
    original = external_plugins._read_manifest_source

    def read_once(path: Path) -> bytes:
        reads.append(path)
        return original(path)

    monkeypatch.setattr(external_plugins, "_read_manifest_source", read_once)

    definitions = preflight_external_manifests(configuration)

    assert [definition.plugin_id.value for definition in definitions] == ["first", "second"]
    assert reads == [first, second]


def test_preflight_rejects_enabled_schema_v1_internal_input() -> None:
    configuration = parse_host_configuration_toml(
        'schema_version = 1\n[[plugins]]\nid = "external"\nenabled = true\n'
    )

    with pytest.raises(
        ValueError,
        match="^invalid external manifest preflight input$",
    ):
        preflight_external_manifests(configuration)


def test_preflight_rejects_limit_and_duplicate_modules_before_any_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import mymcp.host.external_plugins as external_plugins

    path = tmp_path / "manifest.json"
    declarations = tuple(
        (f"plugin-{index}", True, path, f"operator_plugins.plugin_{index}")
        for index in range(33)
    )
    configuration = _configuration(*declarations)
    monkeypatch.setattr(
        external_plugins,
        "_read_manifest_source",
        lambda _: pytest.fail("preflight read before enforcing its limit"),
    )

    with pytest.raises(ExternalPluginLoadError) as captured:
        preflight_external_manifests(configuration)

    assert captured.value.code == "external_plugin_limit_exceeded"

    configuration = _configuration(
        ("first", True, path, "operator_plugins.shared"),
        ("second", True, path, "operator_plugins.shared"),
    )
    with pytest.raises(ExternalPluginLoadError) as captured:
        preflight_external_manifests(configuration)

    assert captured.value.code == "external_plugin_composition_invalid"


def test_preflight_enforces_aggregate_capability_limit(tmp_path: Path) -> None:
    declarations: list[tuple[str, bool, Path, str]] = []
    for index in range(4):
        plugin_id = f"plugin-{index}"
        path = tmp_path / f"manifest-{index}.json"
        path.write_bytes(_manifest(plugin_id, capability_count=64))
        declarations.append(
            (plugin_id, True, path, f"operator_plugins.plugin_{index}")
        )

    assert len(preflight_external_manifests(_configuration(*declarations))) == 4

    overflow_path = tmp_path / "manifest-overflow.json"
    overflow_path.write_bytes(_manifest("overflow", capability_count=1))
    declarations.append(
        ("overflow", True, overflow_path, "operator_plugins.overflow")
    )
    with pytest.raises(ExternalPluginLoadError) as captured:
        preflight_external_manifests(_configuration(*declarations))

    assert captured.value.code == "external_plugin_limit_exceeded"


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (b"{", "external_manifest_invalid"),
        (_manifest("different"), "external_manifest_identity_mismatch"),
        (_manifest(minimum=2, maximum=2), "external_manifest_host_api_incompatible"),
    ],
)
def test_preflight_maps_manifest_validation_failures_to_bounded_errors(
    tmp_path: Path, source: bytes, expected: str
) -> None:
    path = tmp_path / "manifest.json"
    path.write_bytes(source)

    with pytest.raises(ExternalPluginLoadError) as captured:
        preflight_external_manifests(
            _configuration(("external", True, path, "operator_plugins.external"))
        )

    assert captured.value.code == expected
    assert captured.value.__cause__ is None
    assert str(captured.value) == EXTERNAL_PLUGIN_ERROR_MESSAGES[expected]


def test_preflight_maps_manifest_source_failures_without_details(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import mymcp.host.external_plugins as external_plugins

    path = tmp_path / "manifest.json"
    path.write_bytes(_manifest())
    configuration = _configuration(("external", True, path, "operator_plugins.external"))
    monkeypatch.setattr(external_plugins, "_same_source_state", lambda *_: False)

    with pytest.raises(ExternalPluginLoadError) as captured:
        preflight_external_manifests(configuration)

    assert captured.value.code == "external_manifest_source_changed"
    assert captured.value.__cause__ is None
    assert str(path) not in str(captured.value)


def test_preflight_maps_unreadable_source_without_details(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import mymcp.host.external_plugins as external_plugins

    path = tmp_path / "manifest.json"
    path.write_bytes(_manifest())
    configuration = _configuration(("external", True, path, "operator_plugins.external"))
    monkeypatch.setattr(
        external_plugins.os,
        "open",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(PermissionError("hidden")),
    )

    with pytest.raises(ExternalPluginLoadError) as captured:
        preflight_external_manifests(configuration)

    assert captured.value.code == "external_manifest_unreadable"
    assert captured.value.__cause__ is None


def test_preflight_accepts_exact_manifest_source_limit(tmp_path: Path) -> None:
    source = _manifest()
    source += b" " * (64 * 1024 - len(source))
    path = tmp_path / "manifest.json"
    path.write_bytes(source)

    definitions = preflight_external_manifests(
        _configuration(("external", True, path, "operator_plugins.external"))
    )

    assert len(definitions) == 1


@pytest.mark.skipif(os.name == "nt", reason="POSIX source permission contract")
def test_preflight_rejects_unsafe_permissions_and_oversized_source(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_bytes(_manifest())
    path.chmod(stat.S_IMODE(path.stat().st_mode) | 0o022)

    with pytest.raises(ExternalPluginLoadError) as captured:
        preflight_external_manifests(
            _configuration(("external", True, path, "operator_plugins.external"))
        )

    assert captured.value.code == "external_manifest_unsafe_permissions"
    path.chmod(0o600)
    path.write_bytes(b"x" * (64 * 1024 + 1))

    with pytest.raises(ExternalPluginLoadError) as captured:
        preflight_external_manifests(
            _configuration(("external", True, path, "operator_plugins.external"))
        )

    assert captured.value.code == "external_manifest_too_large"


@pytest.mark.skipif(os.name == "nt", reason="POSIX parent permission contract")
def test_preflight_rejects_unsafe_immediate_parent_permissions(tmp_path: Path) -> None:
    parent = tmp_path / "external"
    parent.mkdir(mode=0o700)
    path = parent / "manifest.json"
    path.write_bytes(_manifest())
    parent.chmod(0o722)

    try:
        with pytest.raises(ExternalPluginLoadError) as captured:
            preflight_external_manifests(
                _configuration(
                    ("external", True, path, "operator_plugins.external")
                )
            )
    finally:
        parent.chmod(0o700)

    assert captured.value.code == "external_manifest_unsafe_permissions"


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink source contract")
def test_preflight_rejects_symlink_parent_final_and_non_regular_source(tmp_path: Path) -> None:
    source_directory = tmp_path / "source"
    source_directory.mkdir()
    (source_directory / "manifest.json").write_bytes(_manifest())
    linked_parent = tmp_path / "linked"
    linked_parent.symlink_to(source_directory, target_is_directory=True)

    with pytest.raises(ExternalPluginLoadError) as captured:
        preflight_external_manifests(
            _configuration(
                ("external", True, linked_parent / "manifest.json", "operator_plugins.external")
            )
        )

    assert captured.value.code == "external_manifest_unsafe_path"
    linked_source = tmp_path / "linked-manifest.json"
    linked_source.symlink_to(source_directory / "manifest.json")
    with pytest.raises(ExternalPluginLoadError) as captured:
        preflight_external_manifests(
            _configuration(("external", True, linked_source, "operator_plugins.external"))
        )

    assert captured.value.code == "external_manifest_unsafe_path"
    directory = tmp_path / "directory"
    directory.mkdir()
    with pytest.raises(ExternalPluginLoadError) as captured:
        preflight_external_manifests(
            _configuration(("external", True, directory, "operator_plugins.external"))
        )

    assert captured.value.code == "external_manifest_not_regular"


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink anchor contract")
def test_preflight_accepts_symlink_ancestor_above_immediate_parent(
    tmp_path: Path,
) -> None:
    anchor = tmp_path / "anchor"
    parent = anchor / "external"
    parent.mkdir(parents=True)
    (parent / "manifest.json").write_bytes(_manifest())
    selected = tmp_path / "selected"
    selected.symlink_to(anchor, target_is_directory=True)

    definitions = preflight_external_manifests(
        _configuration(
            (
                "external",
                True,
                selected / "external" / "manifest.json",
                "operator_plugins.external",
            )
        )
    )

    assert len(definitions) == 1


def test_external_plugin_error_vocabulary_is_fixed_and_non_identifying() -> None:
    assert set(EXTERNAL_PLUGIN_ERROR_MESSAGES) == {
        "external_plugin_limit_exceeded",
        "external_manifest_unsafe_path",
        "external_manifest_not_regular",
        "external_manifest_unsafe_permissions",
        "external_manifest_unreadable",
        "external_manifest_too_large",
        "external_manifest_source_changed",
        "external_manifest_invalid",
        "external_manifest_identity_mismatch",
        "external_manifest_host_api_incompatible",
        "external_plugin_import_failed",
        "external_plugin_entrypoint_invalid",
        "external_plugin_contract_invalid",
        "external_plugin_composition_invalid",
    }
    for code, message in EXTERNAL_PLUGIN_ERROR_MESSAGES.items():
        error = ExternalPluginLoadError(code)
        assert error.code == code
        assert str(error) == message
        assert error.__cause__ is None
