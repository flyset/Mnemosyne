import json

from fastapi.testclient import TestClient

from mymcp.app import create_production_app
from mymcp.mcp.tools import list_tools, memory_inspect, memory_list, memory_recall


def test_default_production_factory_preserves_public_read_only_surface(
    tmp_path,
    monkeypatch,
) -> None:
    memory_root = tmp_path / "memory"
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(memory_root))
    monkeypatch.setenv("MNEMOSYNE_MEMORY_REMEMBER_ENABLED", "false")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED", "false")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_REVISE_ENABLED", "false")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_FORGET_ENABLED", "false")
    client = TestClient(create_production_app())
    expected_tools = [
        list_tools.TOOL,
        memory_recall.TOOL,
        memory_list.TOOL,
        memory_inspect.TOOL,
    ]

    discovered = client.post("/mcp", json={"id": "tools", "method": "tools/list"})
    reported = client.post(
        "/mcp",
        json={
            "id": "reported",
            "method": "tools/call",
            "params": {"name": "list_tools", "arguments": {}},
        },
    )
    listed = client.post(
        "/mcp",
        json={
            "id": "list",
            "method": "tools/call",
            "params": {
                "name": "memory_list",
                "arguments": {"scope": "project"},
            },
        },
    )
    recalled = client.post(
        "/mcp",
        json={
            "id": "recall",
            "method": "tools/call",
            "params": {
                "name": "memory_recall",
                "arguments": {
                    "query": "compatibility-audit-7f2c9d1e-no-match",
                    "scope": "project",
                },
            },
        },
    )

    assert discovered.status_code == 200
    assert discovered.json()["result"]["tools"] == expected_tools
    assert reported.json()["result"] == {
        "content": [
            {
                "type": "text",
                "text": (
                    "Server: mnemosyne 0.1.4. Available tools: "
                    "list_tools, memory_recall, memory_list, memory_inspect"
                ),
            }
        ]
    }
    assert json.loads(listed.json()["result"]["content"][0]["text"]) == {
        "status": "ok",
        "memories": [],
        "page": {
            "number": 1,
            "count": 0,
            "total_count": 0,
            "total_pages": 0,
            "truncated": False,
            "next_cursor": None,
        },
    }
    assert json.loads(recalled.json()["result"]["content"][0]["text"]) == {
        "status": "no_matches",
        "memories": [],
    }
    assert not memory_root.exists()
