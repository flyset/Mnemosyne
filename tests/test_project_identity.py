import tomllib
from pathlib import Path

from mymcp import cli


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_project_uses_mymcp_host_identity() -> None:
    project = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]

    assert project["name"] == "mymcp"
    assert project["scripts"] == {
        "mymcp": "mymcp.cli:main",
        "mymcp-dev": "mymcp.cli:dev",
        "mymcp-test": "mymcp.cli:test",
    }
    assert cli.__name__ == "mymcp.cli"
