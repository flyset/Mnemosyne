import importlib

import pytest

import mymcp.host.configuration as configuration_module
from mymcp.host.configuration import (
    HostConfigurationError,
    parse_host_configuration_toml,
    validate_host_configuration_semantics,
)
from mymcp.plugin.contracts import PluginId


BUNDLED_PLUGIN_IDS = (PluginId("mnemosyne"),)


def _configuration(*declarations: tuple[str, bool]):
    plugin_source = "".join(
        (
            "[[plugins]]\n"
            f'id = "{plugin_id}"\n'
            f"enabled = {str(enabled).lower()}\n"
        )
        for plugin_id, enabled in declarations
    )
    return parse_host_configuration_toml(
        f"schema_version = 1\n{plugin_source}"
    )


def _schema_v2_configuration(*declarations: tuple[str, bool]):
    plugin_source = "".join(
        (
            "[[plugins]]\n"
            f'id = "{plugin_id}"\n'
            f"enabled = {str(enabled).lower()}\n"
            f'manifest_path = "/opt/{plugin_id}/manifest.json"\n'
            f'module = "operator_plugins.{plugin_id.replace("-", "_")}"\n'
        )
        for plugin_id, enabled in declarations
    )
    return parse_host_configuration_toml(
        f"schema_version = 2\n{plugin_source}"
    )


def test_disabled_external_declarations_are_validated_without_reordering() -> None:
    snapshot = _configuration(("alpha", False), ("beta-plugin", False))

    validated = validate_host_configuration_semantics(
        snapshot,
        bundled_plugin_ids=BUNDLED_PLUGIN_IDS,
    )

    assert validated is snapshot
    assert tuple(plugin.plugin_id.value for plugin in validated.plugins) == (
        "alpha",
        "beta-plugin",
    )


@pytest.mark.parametrize(
    "declarations",
    [
        (("alpha", True),),
        (("alpha", False), ("beta", True)),
        (("alpha", True), ("beta", False)),
    ],
)
def test_any_enabled_external_plugin_fails_with_one_bounded_unsupported_error(
    declarations: tuple[tuple[str, bool], ...],
) -> None:
    with pytest.raises(HostConfigurationError) as captured:
        validate_host_configuration_semantics(
            _configuration(*declarations),
            bundled_plugin_ids=BUNDLED_PLUGIN_IDS,
        )

    assert captured.value.code == "enabled_plugin_unsupported"
    assert str(captured.value) == (
        "MyMCP external plugin enablement is not supported by this build"
    )
    assert all(
        plugin_id not in str(captured.value)
        for plugin_id, _enabled in declarations
    )


def test_schema_v2_enabled_declarations_pass_semantic_validation() -> None:
    snapshot = _schema_v2_configuration(("alpha", True), ("beta-plugin", False))

    assert validate_host_configuration_semantics(
        snapshot,
        bundled_plugin_ids=BUNDLED_PLUGIN_IDS,
    ) is snapshot


@pytest.mark.parametrize("enabled", [False, True])
def test_bundled_plugin_identity_conflicts_regardless_of_enablement(
    enabled: bool,
) -> None:
    with pytest.raises(HostConfigurationError) as captured:
        validate_host_configuration_semantics(
            _configuration(("mnemosyne", enabled)),
            bundled_plugin_ids=BUNDLED_PLUGIN_IDS,
        )

    assert captured.value.code == "bundled_plugin_conflict"
    assert str(captured.value) == (
        "MyMCP configuration conflicts with a bundled plugin identity"
    )
    assert "mnemosyne" not in str(captured.value)


def test_bundled_collision_precedes_unsupported_enabled_state() -> None:
    snapshot = _configuration(("external", True), ("mnemosyne", False))

    with pytest.raises(HostConfigurationError) as captured:
        validate_host_configuration_semantics(
            snapshot,
            bundled_plugin_ids=BUNDLED_PLUGIN_IDS,
        )

    assert captured.value.code == "bundled_plugin_conflict"


def test_semantic_validation_performs_no_loading_discovery_or_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = _configuration(("operator-installed", False))
    monkeypatch.setattr(
        configuration_module,
        "load_host_configuration",
        lambda: pytest.fail("semantic validation reread configuration"),
    )
    monkeypatch.setattr(
        configuration_module,
        "parse_host_configuration_toml",
        lambda _source: pytest.fail("semantic validation reparsed configuration"),
    )
    monkeypatch.setattr(
        importlib,
        "import_module",
        lambda _name: pytest.fail("semantic validation imported plugin code"),
    )

    assert validate_host_configuration_semantics(
        snapshot,
        bundled_plugin_ids=BUNDLED_PLUGIN_IDS,
    ) is snapshot


def test_semantic_validation_rejects_invalid_internal_inputs() -> None:
    snapshot = _configuration(("external", False))

    with pytest.raises(
        ValueError,
        match="^invalid host configuration semantic input$",
    ):
        validate_host_configuration_semantics(  # type: ignore[arg-type]
            None,
            bundled_plugin_ids=BUNDLED_PLUGIN_IDS,
        )
    with pytest.raises(
        ValueError,
        match="^invalid host configuration semantic input$",
    ):
        validate_host_configuration_semantics(
            snapshot,
            bundled_plugin_ids=("mnemosyne",),  # type: ignore[arg-type]
        )
