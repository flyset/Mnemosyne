from mymcp.app import app


def test_test_runner_can_import_the_application() -> None:
    assert app is not None
