import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_opencode_allows_listing_and_requires_memory_mutation_approval() -> None:
    config = json.loads(
        (PROJECT_ROOT / "opencode.json").read_text(encoding="utf-8")
    )
    expected_policy = [
        ("mymcp_*", "deny"),
        ("mymcp_list_tools", "allow"),
        ("mymcp_memory_recall", "allow"),
        ("mymcp_memory_inspect", "allow"),
        ("mymcp_memory_list", "allow"),
        ("mymcp_memory_remember", "ask"),
        ("mymcp_memory_revise", "ask"),
        ("mymcp_memory_archive", "ask"),
        ("mymcp_memory_restore", "ask"),
        ("mymcp_memory_forget", "ask"),
    ]

    assert list(config["permission"].items()) == expected_policy
    assert list(config["agent"]["mymcp"]["permission"].items()) == expected_policy
    assert list(config["mcp"]) == ["mymcp"]
    assert config["mcp"]["mymcp"] == {
        "type": "remote",
        "url": "http://127.0.0.1:8000/mcp",
        "enabled": True,
    }
    assert "mnemosyne" not in config["mcp"]
    assert "mnemosyne" not in config["agent"]
    assert "mnemosyne_" not in json.dumps(config)
