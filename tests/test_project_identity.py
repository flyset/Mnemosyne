import tomllib
from pathlib import Path

from mymcp import cli
from mymcp.settings import APP_TITLE, PROTOCOL_VERSION, SERVER_NAME, SERVER_VERSION


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_public_host_and_package_identify_mymcp_0_5_0() -> None:
    project = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]

    assert SERVER_NAME == "mymcp"
    assert SERVER_VERSION == "0.5.0"
    assert APP_TITLE == "MyMCP"
    assert PROTOCOL_VERSION == "2024-11-05"
    assert project["name"] == "mymcp"
    assert project["version"] == SERVER_VERSION
    assert project["description"] == (
        "Local-first MCP host for narrowly scoped integrations, "
        "with bundled Mnemosyne memory."
    )
    assert project["urls"] == {
        "Homepage": "https://github.com/flyset/MyMCP",
        "Repository": "https://github.com/flyset/MyMCP",
        "Issues": "https://github.com/flyset/MyMCP/issues",
    }
    assert project["scripts"] == {
        "mymcp": "mymcp.cli:main",
        "mymcp-dev": "mymcp.cli:dev",
        "mymcp-test": "mymcp.cli:test",
    }
    assert cli.__name__ == "mymcp.cli"
