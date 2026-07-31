import json
from typing import Any

import pytest

from mymcp.host.bootstrap import build_production_runtime


def _payload(result: dict[str, Any] | None) -> dict[str, Any]:
    assert result is not None
    assert len(result["content"]) == 1
    return json.loads(result["content"][0]["text"])


def test_agent_scope_uses_the_complete_existing_memory_lifecycle(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory_root = tmp_path / "memory"
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(memory_root))
    monkeypatch.setenv("MNEMOSYNE_MEMORY_REMEMBER_ENABLED", "true")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED", "true")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_REVISE_ENABLED", "true")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_FORGET_ENABLED", "true")
    registry = build_production_runtime(
        generation_factory=lambda: "agent-lifecycle-test"
    ).registry

    remembered = _payload(
        registry.call_tool(
            "memory_remember",
            {
                "scope": "agent",
                "namespace": {
                    "kind": "agent",
                    "id": "neuromancer",
                    "label": "Neuromancer",
                },
                "collection": {"id": "policies", "label": "Policies"},
                "kind": "policy",
                "language": "en",
                "title": "Confirm state-changing actions",
                "content": "Request explicit approval before changing repository state.",
                "tags": ["approval", "workflow"],
                "origin": "user_approved_proposal",
            },
        )
    )
    assert remembered["status"] == "remembered"
    assert remembered["lifecycle"] == {"state": "active", "revision": 1}
    reference = {"schema_version": 2, **remembered["reference"]}
    assert reference["scope"] == "agent"

    recalled = _payload(
        registry.call_tool(
            "memory_recall",
            {
                "scope": "agent",
                "namespace_id": "neuromancer",
                "query": "approval repository state",
            },
        )
    )
    assert recalled["status"] == "ok"
    assert recalled["memories"][0]["reference"] == reference

    listed = _payload(
        registry.call_tool(
            "memory_list",
            {
                "scope": "agent",
                "namespace_id": "neuromancer",
                "collection_id": "policies",
            },
        )
    )
    assert listed["status"] == "ok"
    assert listed["page"]["total_count"] == 1
    assert listed["memories"][0]["reference"] == reference

    inspected = _payload(
        registry.call_tool("memory_inspect", {"reference": reference})
    )
    assert inspected["status"] == "ok"
    assert inspected["memory"]["scope"] == "agent"
    assert inspected["memory"]["kind"] == "policy"

    revised = _payload(
        registry.call_tool(
            "memory_revise",
            {
                "reference": reference,
                "expected_revision": 1,
                "namespace_label": "Neuromancer",
                "collection_label": "Policies",
                "title": "Confirm repository mutations",
                "content": "Request exact approval before changing repository state.",
                "tags": ["approval", "repository-workflow"],
            },
        )
    )
    assert revised == {
        "status": "revised",
        "reference": reference,
        "lifecycle": {"state": "active", "revision": 2},
    }

    archived = _payload(
        registry.call_tool(
            "memory_archive",
            {"reference": reference, "expected_revision": 2},
        )
    )
    assert archived["lifecycle"] == {"state": "archived", "revision": 3}
    assert _payload(
        registry.call_tool(
            "memory_recall",
            {
                "scope": "agent",
                "namespace_id": "neuromancer",
                "query": "approval repository state",
            },
        )
    ) == {"status": "no_matches", "memories": []}
    assert _payload(
        registry.call_tool("memory_inspect", {"reference": reference})
    )["memory"]["lifecycle"] == {"state": "archived", "revision": 3}

    restored = _payload(
        registry.call_tool(
            "memory_restore",
            {"reference": reference, "expected_revision": 3},
        )
    )
    assert restored["lifecycle"] == {"state": "active", "revision": 4}
    assert _payload(
        registry.call_tool(
            "memory_recall",
            {
                "scope": "agent",
                "namespace_id": "neuromancer",
                "query": "exact approval repository state",
            },
        )
    )["status"] == "ok"

    rearchived = _payload(
        registry.call_tool(
            "memory_archive",
            {"reference": reference, "expected_revision": 4},
        )
    )
    assert rearchived["lifecycle"] == {"state": "archived", "revision": 5}
    assert _payload(
        registry.call_tool(
            "memory_forget",
            {"reference": reference, "expected_revision": 5},
        )
    ) == {"status": "forgotten", "reference": reference}
    assert _payload(
        registry.call_tool("memory_inspect", {"reference": reference})
    )["code"] == "not_found"
    assert not list(memory_root.rglob("*.json"))
