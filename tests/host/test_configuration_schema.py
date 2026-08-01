from dataclasses import FrozenInstanceError

import pytest

from mymcp.host.configuration import (
    HostConfiguration,
    HostConfigurationError,
    HostConfigurationSchemaVersion,
    HostServerConfiguration,
    parse_host_configuration_toml,
)
from mymcp.plugin.contracts import PluginId


def test_absent_document_defaults_are_explicit_and_immutable() -> None:
    configuration = HostConfiguration.default()

    assert configuration.schema_version == HostConfigurationSchemaVersion(1)
    assert configuration.server == HostServerConfiguration(
        address="127.0.0.1",
        port=8000,
    )
    assert configuration.plugins == ()

    with pytest.raises(FrozenInstanceError):
        configuration.server.port = 9000  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        configuration.schema_version.value = 2  # type: ignore[misc]


def test_plugin_declarations_and_nested_identity_are_immutable() -> None:
    configuration = parse_host_configuration_toml(
        'schema_version = 1\n[[plugins]]\nid = "alpha"\nenabled = false\n'
    )
    declaration = configuration.plugins[0]

    with pytest.raises(FrozenInstanceError):
        configuration.plugins += ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        declaration.enabled = True  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        declaration.plugin_id.value = "beta"  # type: ignore[misc]


@pytest.mark.parametrize("address", ["127.0.0.1", "127.0.0.2", "::1"])
def test_server_accepts_only_literal_loopback_addresses(address: str) -> None:
    configuration = parse_host_configuration_toml(
        f'schema_version = 1\n[server]\naddress = "{address}"\n'
    )

    assert configuration.server.address == address
    assert configuration.server.port == 8000


def test_server_settings_are_independently_optional() -> None:
    assert parse_host_configuration_toml(
        "schema_version = 1\n[server]\nport = 65535\n"
    ).server == HostServerConfiguration(address="127.0.0.1", port=65535)


@pytest.mark.parametrize(
    "server_source",
    [
        'address = "localhost"',
        'address = "0.0.0.0"',
        'address = "192.168.1.1"',
        'address = "8.8.8.8"',
        'address = "::"',
        "address = 127",
        'port = "8000"',
        "port = true",
        "port = 0",
        "port = -1",
        "port = 65536",
        "unknown = true",
    ],
)
def test_invalid_server_schema_is_bounded(server_source: str) -> None:
    with pytest.raises(HostConfigurationError) as captured:
        parse_host_configuration_toml(
            f"schema_version = 1\n[server]\n{server_source}\n"
        )

    assert captured.value.code == "invalid_schema"
    assert str(captured.value) == "MyMCP configuration has an invalid schema"


def test_plugin_declarations_preserve_order_and_explicit_enablement() -> None:
    configuration = parse_host_configuration_toml(
        """
schema_version = 1

[[plugins]]
id = "alpha-plugin"
enabled = false

[[plugins]]
id = "beta"
enabled = true
"""
    )

    assert tuple(
        (declaration.plugin_id, declaration.enabled)
        for declaration in configuration.plugins
    ) == (
        (PluginId("alpha-plugin"), False),
        (PluginId("beta"), True),
    )


@pytest.mark.parametrize(
    "plugin_source",
    [
        'id = "alpha"',
        "enabled = false",
        'id = ""\nenabled = false',
        'id = "Alpha"\nenabled = false',
        'id = " alpha"\nenabled = false',
        'id = "1alpha"\nenabled = false',
        'id = "alpha_plugin"\nenabled = false',
        'id = "alpha--plugin"\nenabled = false',
        'id = "alpha-"\nenabled = false',
        f'id = "{"a" * 65}"\nenabled = false',
        'id = "alpha"\nenabled = "false"',
        'id = "alpha"\nenabled = false\nunknown = 1',
    ],
)
def test_invalid_plugin_schema_is_bounded(plugin_source: str) -> None:
    with pytest.raises(HostConfigurationError) as captured:
        parse_host_configuration_toml(
            f"schema_version = 1\n[[plugins]]\n{plugin_source}\n"
        )

    assert captured.value.code == "invalid_schema"


def test_duplicate_plugin_declarations_have_a_distinct_bounded_error() -> None:
    with pytest.raises(HostConfigurationError) as captured:
        parse_host_configuration_toml(
            """
schema_version = 1
[[plugins]]
id = "duplicate"
enabled = false
[[plugins]]
id = "duplicate"
enabled = true
"""
        )

    assert captured.value.code == "duplicate_plugin"
    assert str(captured.value) == (
        "MyMCP configuration contains a duplicate plugin declaration"
    )


def test_plugin_id_accepts_the_contract_maximum_length() -> None:
    plugin_id = "a" * 64

    configuration = parse_host_configuration_toml(
        f'schema_version = 1\n[[plugins]]\nid = "{plugin_id}"\nenabled = false\n'
    )

    assert configuration.plugins[0].plugin_id == PluginId(plugin_id)


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ("", "invalid_schema"),
        ("schema_version = true", "invalid_schema"),
        ('schema_version = "1"', "invalid_schema"),
        ("schema_version = 0", "unsupported_schema_version"),
        ("schema_version = 2", "unsupported_schema_version"),
        ("schema_version = 1\nunknown = true", "invalid_schema"),
        ("schema_version = 1\nserver = []", "invalid_schema"),
        ("schema_version = 1\nplugins = {}", "invalid_schema"),
    ],
)
def test_document_schema_is_strict_and_versioned(source: str, code: str) -> None:
    with pytest.raises(HostConfigurationError) as captured:
        parse_host_configuration_toml(source)

    assert captured.value.code == code


def test_unsupported_schema_version_has_a_fixed_bounded_message() -> None:
    with pytest.raises(HostConfigurationError) as captured:
        parse_host_configuration_toml("schema_version = 2\n")

    assert captured.value.code == "unsupported_schema_version"
    assert str(captured.value) == (
        "MyMCP configuration schema version is unsupported"
    )


def test_malformed_or_duplicate_key_toml_has_a_bounded_error() -> None:
    with pytest.raises(HostConfigurationError) as captured:
        parse_host_configuration_toml(
            "schema_version = 1\nschema_version = 1\n"
        )

    assert captured.value.code == "invalid_toml"
    assert str(captured.value) == "MyMCP configuration is not valid TOML"
