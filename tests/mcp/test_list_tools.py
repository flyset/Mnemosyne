import tomllib
from pathlib import Path

from mnemosyne.mcp.tools.list_tools import handle
from mnemosyne.settings import SERVER_NAME, SERVER_VERSION


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_list_tools_formats_the_supplied_tool_names() -> None:
    assert handle({}, [{"name": "one"}, {"name": "two"}]) == {
        "content": [
            {
                "type": "text",
                "text": (
                    f"Server: {SERVER_NAME} {SERVER_VERSION}. Available tools: one, two"
                ),
            }
        ]
    }


def test_server_and_package_versions_identify_the_compatibility_build() -> None:
    project = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]

    assert SERVER_VERSION == "0.1.2"
    assert project["version"] == SERVER_VERSION
