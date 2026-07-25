import mymcp.app as app_module


def test_test_runner_can_import_application_factories_without_global_app() -> None:
    assert callable(app_module.create_app)
    assert callable(app_module.create_production_app)
    assert not hasattr(app_module, "app")
