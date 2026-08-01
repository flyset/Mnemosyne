import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from mymcp import cli
from mymcp.host.configuration import (
    HostConfiguration,
    HostConfigurationError,
    HostConfigurationSchemaVersion,
    HostServerConfiguration,
    parse_host_configuration_toml,
)


def test_main_loads_once_and_starts_the_injected_production_application(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import mymcp.app as app_module
    import mymcp.host.configuration as configuration_module

    runner = Mock()
    application = object()
    snapshot = HostConfiguration(
        schema_version=HostConfigurationSchemaVersion(1),
        server=HostServerConfiguration(address="127.0.0.2", port=9000),
        plugins=(),
    )
    loader = Mock(return_value=snapshot)
    app_factory = Mock(return_value=application)
    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=runner))
    monkeypatch.setattr(configuration_module, "load_host_configuration", loader)
    monkeypatch.setattr(app_module, "create_production_app", app_factory)

    cli.main()

    loader.assert_called_once_with()
    app_factory.assert_called_once_with(snapshot)
    runner.assert_called_once_with(
        application,
        host="127.0.0.2",
        port=9000,
    )


def test_dev_supervisor_loads_validates_and_uses_configured_binding_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import mymcp.host.bootstrap as bootstrap_module
    import mymcp.host.configuration as configuration_module

    runner = Mock()
    snapshot = HostConfiguration(
        schema_version=HostConfigurationSchemaVersion(1),
        server=HostServerConfiguration(address="::1", port=9001),
        plugins=(),
    )
    loader = Mock(return_value=snapshot)
    validator = Mock(return_value=snapshot)
    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=runner))
    monkeypatch.setattr(configuration_module, "load_host_configuration", loader)
    monkeypatch.setattr(
        bootstrap_module,
        "validate_production_configuration",
        validator,
        raising=False,
    )

    cli.dev()

    loader.assert_called_once_with()
    validator.assert_called_once_with(snapshot)
    runner.assert_called_once_with(
        "mymcp.app:create_production_app",
        host="::1",
        port=9001,
        reload=True,
        factory=True,
    )


def test_dev_rejects_enabled_external_plugin_before_uvicorn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import mymcp.host.configuration as configuration_module

    runner = Mock()
    snapshot = parse_host_configuration_toml(
        'schema_version = 1\n[[plugins]]\nid = "external"\nenabled = true\n'
    )
    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=runner))
    monkeypatch.setattr(
        configuration_module,
        "load_host_configuration",
        Mock(return_value=snapshot),
    )

    with pytest.raises(HostConfigurationError) as captured:
        cli.dev()

    assert captured.value.code == "enabled_plugin_unsupported"
    runner.assert_not_called()


def test_test_runs_the_repository_suite(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(cli.subprocess, "run", runner)

    assert cli.test() == 0
    runner.assert_called_once_with(
        [sys.executable, "-m", "pytest", "tests"], check=False
    )
