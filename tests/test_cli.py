import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from mnemosyne import cli


def test_main_starts_the_shared_application_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = Mock()
    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=runner))

    cli.main()

    runner.assert_called_once_with(
        "mnemosyne.app:app",
        host="127.0.0.1",
        port=8000,
    )


def test_dev_starts_the_shared_application_import_with_reload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = Mock()
    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=runner))

    cli.dev()

    runner.assert_called_once_with(
        "mnemosyne.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


def test_test_runs_the_repository_suite(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(cli.subprocess, "run", runner)

    assert cli.test() == 0
    runner.assert_called_once_with(
        [sys.executable, "-m", "pytest", "tests"], check=False
    )
