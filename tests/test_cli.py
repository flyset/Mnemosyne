import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from mnemosyne import cli


def test_test_runs_the_repository_suite(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(cli.subprocess, "run", runner)

    assert cli.test() == 0
    runner.assert_called_once_with(
        [sys.executable, "-m", "pytest", "tests"], check=False
    )
