import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_opencode_allows_listing_and_requires_memory_mutation_approval() -> None:
    config = json.loads(
        (PROJECT_ROOT / "opencode.json").read_text(encoding="utf-8")
    )

    assert list(config["permission"].items()) == [
        ("mnemosyne_memory_list", "allow"),
        ("mnemosyne_memory_remember", "ask"),
        ("mnemosyne_memory_revise", "ask"),
        ("mnemosyne_memory_archive", "ask"),
        ("mnemosyne_memory_restore", "ask"),
        ("mnemosyne_memory_forget", "ask"),
    ]
    assert list(config["agent"]["mnemosyne"]["permission"].items()) == [
        ("mnemosyne_*", "deny"),
        ("mnemosyne_list_tools", "allow"),
        ("mnemosyne_memory_recall", "allow"),
        ("mnemosyne_memory_inspect", "allow"),
        ("mnemosyne_memory_list", "allow"),
        ("mnemosyne_memory_remember", "ask"),
        ("mnemosyne_memory_revise", "ask"),
        ("mnemosyne_memory_archive", "ask"),
        ("mnemosyne_memory_restore", "ask"),
        ("mnemosyne_memory_forget", "ask"),
    ]
    assert config["mcp"]["mnemosyne"] == {
        "type": "remote",
        "url": "http://127.0.0.1:8000/mcp",
        "enabled": True,
    }


def test_opencode_agent_file_allows_listing_and_preserves_mutation_approval() -> None:
    source = (PROJECT_ROOT / ".opencode" / "agents" / "mnemosyne.md").read_text(
        encoding="utf-8"
    )
    permission_lines = [
        line.strip()
        for line in source.split("---", 2)[1].splitlines()
        if line.strip().startswith('"mnemosyne_')
    ]

    assert permission_lines == [
        '"mnemosyne_*": deny',
        '"mnemosyne_list_tools": allow',
        '"mnemosyne_memory_recall": allow',
        '"mnemosyne_memory_inspect": allow',
        '"mnemosyne_memory_list": allow',
        '"mnemosyne_memory_remember": ask',
        '"mnemosyne_memory_revise": ask',
        '"mnemosyne_memory_archive": ask',
        '"mnemosyne_memory_restore": ask',
        '"mnemosyne_memory_forget": ask',
    ]
