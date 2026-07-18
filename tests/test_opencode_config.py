import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_opencode_requires_exact_memory_remember_approval() -> None:
    config = json.loads(
        (PROJECT_ROOT / "opencode.json").read_text(encoding="utf-8")
    )

    assert config["permission"]["mnemosyne_memory_remember"] == "ask"
    assert list(config["agent"]["mnemosyne"]["permission"].items()) == [
        ("mnemosyne_*", "deny"),
        ("mnemosyne_list_tools", "allow"),
        ("mnemosyne_memory_recall", "allow"),
        ("mnemosyne_memory_remember", "ask"),
    ]
    assert config["mcp"]["mnemosyne"] == {
        "type": "remote",
        "url": "http://127.0.0.1:8000/mcp",
        "enabled": True,
    }
