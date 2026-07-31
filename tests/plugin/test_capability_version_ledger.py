import copy
import hashlib
import json
import re
from pathlib import Path

import pytest

from mymcp.plugins.mnemosyne import plugin as mnemosyne
from mymcp.plugins.mnemosyne.mcp.tools import (
    memory_archive,
    memory_forget,
    memory_inspect,
    memory_list,
    memory_recall,
    memory_remember,
    memory_restore,
    memory_revise,
)
from mymcp.plugin.definition import CapabilityContractVersion


LEDGER_PATH = Path(__file__).with_name("capability_contract_ledger.json")
TOOLS = {
    tool["name"]: tool
    for tool in (
        memory_recall.TOOL,
        memory_list.TOOL,
        memory_inspect.TOOL,
        memory_archive.TOOL,
        memory_restore.TOOL,
        memory_remember.TOOL,
        memory_revise.TOOL,
        memory_forget.TOOL,
    )
}


def _validate_ledger(
    ledger: dict[str, dict[str, dict[str, object]]],
) -> None:
    assert set(ledger) <= set(TOOLS)
    for name, versions in ledger.items():
        assert versions
        for version, entry in versions.items():
            CapabilityContractVersion(version)
            assert set(entry) == {"digest", "properties", "required"}
            assert isinstance(entry["digest"], str)
            assert re.fullmatch(r"[0-9a-f]{64}", entry["digest"]) is not None
            properties = entry["properties"]
            required = entry["required"]
            assert isinstance(properties, list)
            assert isinstance(required, list)
            assert all(isinstance(value, str) for value in properties)
            assert all(isinstance(value, str) for value in required)
            assert len(properties) == len(set(properties))
            assert len(required) == len(set(required))
            assert set(required) <= set(properties)


def _load_ledger() -> dict[str, dict[str, dict[str, object]]]:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    assert isinstance(ledger, dict)
    _validate_ledger(ledger)
    return ledger


def _fingerprint(tool: dict[str, object]) -> dict[str, object]:
    canonical = json.dumps(
        tool,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    input_schema = tool["inputSchema"]
    assert isinstance(input_schema, dict)
    properties = input_schema.get("properties", {})
    required = input_schema.get("required", [])
    assert isinstance(properties, dict)
    assert isinstance(required, list)
    return {
        "digest": hashlib.sha256(canonical).hexdigest(),
        "properties": list(properties),
        "required": required,
    }


def _declared_versions() -> dict[str, str]:
    return {
        capability.local_id.value: capability.version.value
        for capability in mnemosyne.mnemosyne_plugin_definition().capabilities
    }


def _assert_current_contracts(
    ledger: dict[str, dict[str, dict[str, object]]],
    *,
    tools: dict[str, dict[str, object]] = TOOLS,
    declared_versions: dict[str, str] | None = None,
) -> None:
    versions = declared_versions or _declared_versions()
    assert set(tools) == set(versions) == set(ledger)
    for name, version in versions.items():
        assert tools[name]["name"] == name
        assert version in ledger[name], f"missing {name}@{version} ledger entry"
        assert ledger[name][version] == _fingerprint(tools[name])


def _current_ledger() -> dict[str, dict[str, dict[str, object]]]:
    return {
        name: {version: _fingerprint(TOOLS[name])}
        for name, version in _declared_versions().items()
    }


def test_current_tool_definitions_match_their_declared_contract_versions() -> None:
    _assert_current_contracts(_load_ledger())


def test_memory_recall_ledger_preserves_the_pre_namespace_contract() -> None:
    historical = _load_ledger()["memory_recall"]["1.0.0"]

    assert historical == {
        "digest": "4534ad171c0c6f2f8c58df5208cb9b0f3912e32ab2c74a0e7c81299e0e598280",
        "properties": ["query", "scope", "tags"],
        "required": ["query", "scope"],
    }


def test_ledger_preserves_every_pre_agent_scope_contract() -> None:
    ledger = _load_ledger()

    assert {"1.0.0", "1.1.0"} <= set(ledger["memory_recall"])
    for name in set(TOOLS) - {"memory_recall"}:
        assert "1.0.0" in ledger[name]


def test_digest_is_independent_of_tool_mapping_key_order() -> None:
    reordered = dict(reversed(list(memory_recall.TOOL.items())))

    assert _fingerprint(reordered)["digest"] == _fingerprint(
        memory_recall.TOOL
    )["digest"]


@pytest.mark.parametrize(
    "ledger",
    [
        {"unknown": {"1.0.0": {}}},
        {"memory_recall": {"invalid": {}}},
        {
            "memory_recall": {
                "1.1.0": {
                    "digest": "not-a-digest",
                    "properties": [],
                    "required": [],
                }
            }
        },
    ],
)
def test_ledger_rejects_malformed_historical_entries(
    ledger: dict[str, dict[str, dict[str, object]]],
) -> None:
    with pytest.raises((AssertionError, ValueError)):
        _validate_ledger(ledger)


def test_guard_rejects_definition_drift_under_the_declared_version() -> None:
    tools = copy.deepcopy(TOOLS)
    properties = tools["memory_recall"]["inputSchema"]["properties"]
    assert isinstance(properties, dict)
    properties["unversioned"] = {"type": "string"}

    with pytest.raises(AssertionError):
        _assert_current_contracts(_current_ledger(), tools=tools)


def test_guard_rejects_a_declared_version_without_a_ledger_entry() -> None:
    versions = _declared_versions()
    versions["memory_recall"] = "1.3.0"

    with pytest.raises(
        AssertionError,
        match="missing memory_recall@1.3.0 ledger entry",
    ):
        _assert_current_contracts(
            _current_ledger(),
            declared_versions=versions,
        )
