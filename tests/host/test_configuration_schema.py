from dataclasses import FrozenInstanceError

import pytest

from mymcp.host.configuration import (
    ExternalPluginDeclaration,
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


def test_schema_v2_declarations_preserve_explicit_immutable_locators() -> None:
    configuration = parse_host_configuration_toml(
        """
schema_version = 2

[[plugins]]
id = "alpha-plugin"
enabled = false
manifest_path = "/opt/mymcp/alpha/manifest.json"
module = "operator_plugins.alpha"

[[plugins]]
id = "beta"
enabled = true
manifest_path = "/opt/mymcp/beta/manifest.json"
module = "operator_plugins.beta"
"""
    )

    assert configuration.schema_version == HostConfigurationSchemaVersion(2)
    assert tuple(
        (
            declaration.plugin_id,
            declaration.enabled,
            declaration.manifest_path,
            declaration.module,
        )
        for declaration in configuration.plugins
    ) == (
        (
            PluginId("alpha-plugin"),
            False,
            "/opt/mymcp/alpha/manifest.json",
            "operator_plugins.alpha",
        ),
        (
            PluginId("beta"),
            True,
            "/opt/mymcp/beta/manifest.json",
            "operator_plugins.beta",
        ),
    )
    with pytest.raises(FrozenInstanceError):
        configuration.plugins[0].module = "replacement"  # type: ignore[misc]


@pytest.mark.parametrize(
    "plugin_source",
    [
        'id = "alpha"\nenabled = false\nmanifest_path = "/opt/a/manifest.json"',
        'id = "alpha"\nenabled = false\nmodule = "plugins.alpha"',
        (
            'id = "alpha"\nenabled = false\n'
            'manifest_path = "/opt/a/manifest.json"\n'
            'module = "plugins.alpha"\nunknown = true'
        ),
    ],
)
def test_schema_v2_plugin_tables_require_exact_fields(plugin_source: str) -> None:
    with pytest.raises(HostConfigurationError) as captured:
        parse_host_configuration_toml(
            f"schema_version = 2\n[[plugins]]\n{plugin_source}\n"
        )

    assert captured.value.code == "invalid_schema"


@pytest.mark.parametrize(
    "manifest_path",
    [
        "relative/manifest.json",
        "~/plugins/manifest.json",
        "/opt/$PLUGIN/manifest.json",
        "/opt/%PLUGIN%/manifest.json",
        "/opt/plugins/./manifest.json",
        "/opt/plugins/../manifest.json",
        "/opt/plugins/manifest.json\x00ignored",
    ],
)
def test_schema_v2_rejects_invalid_manifest_locators(manifest_path: str) -> None:
    source = (
        "schema_version = 2\n[[plugins]]\n"
        'id = "alpha"\nenabled = false\n'
        f'manifest_path = "{manifest_path.replace(chr(0), "\\u0000")}"\n'
        'module = "plugins.alpha"\n'
    )

    with pytest.raises(HostConfigurationError) as captured:
        parse_host_configuration_toml(source)

    assert captured.value.code == "invalid_schema"


@pytest.mark.parametrize(
    "module",
    [
        "",
        ".plugins.alpha",
        "plugins.alpha.",
        "plugins..alpha",
        "plugins-alpha",
        "plugins.α",
        f"plugins.{'a' * 248}",
    ],
)
def test_schema_v2_rejects_invalid_module_locators(module: str) -> None:
    with pytest.raises(HostConfigurationError) as captured:
        parse_host_configuration_toml(
            "schema_version = 2\n[[plugins]]\n"
            'id = "alpha"\nenabled = false\n'
            'manifest_path = "/opt/plugins/manifest.json"\n'
            f'module = "{module}"\n'
        )

    assert captured.value.code == "invalid_schema"


def test_schema_v1_rejects_schema_v2_locator_fields() -> None:
    with pytest.raises(HostConfigurationError) as captured:
        parse_host_configuration_toml(
            "schema_version = 1\n[[plugins]]\n"
            'id = "alpha"\nenabled = false\n'
            'manifest_path = "/opt/plugins/manifest.json"\n'
            'module = "plugins.alpha"\n'
        )

    assert captured.value.code == "invalid_schema"


def test_snapshot_schema_and_declaration_shape_cannot_disagree() -> None:
    v1_declaration = ExternalPluginDeclaration(PluginId("alpha"), False)
    v2_declaration = ExternalPluginDeclaration(
        PluginId("alpha"),
        False,
        "/opt/plugins/manifest.json",
        "plugins.alpha",
    )

    with pytest.raises(ValueError, match="^invalid host configuration$"):
        HostConfiguration(
            HostConfigurationSchemaVersion(1),
            HostServerConfiguration(),
            (v2_declaration,),
        )
    with pytest.raises(ValueError, match="^invalid host configuration$"):
        HostConfiguration(
            HostConfigurationSchemaVersion(2),
            HostServerConfiguration(),
            (v1_declaration,),
        )


@pytest.mark.parametrize("module", ["plugins.class", "plugins.import"])
def test_schema_v2_rejects_keyword_module_components(module: str) -> None:
    with pytest.raises(HostConfigurationError) as captured:
        parse_host_configuration_toml(
            "schema_version = 2\n[[plugins]]\n"
            'id = "alpha"\nenabled = false\n'
            'manifest_path = "/opt/plugins/manifest.json"\n'
            f'module = "{module}"\n'
        )

    assert captured.value.code == "invalid_schema"


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
        ("schema_version = 3", "unsupported_schema_version"),
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
        parse_host_configuration_toml("schema_version = 3\n")

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
