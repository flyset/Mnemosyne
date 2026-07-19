import json
import logging
from copy import deepcopy
from pathlib import Path

import pytest

from mnemosyne.mcp.tools.memory_remember import TOOL, handle
from mnemosyne.mcp.tools.memory_remember import handler as handler_module
from mnemosyne.mcp.tools.memory_remember.definition import TOOL as DEFINED_TOOL
from mnemosyne.memory.errors import (
    CandidateLimitExceeded,
    MemorySourceUnavailable,
    MutationDisabled,
    UnsafeMemoryPath,
    WriteConflict,
)
from mnemosyne.memory.records import ALLOWED_KINDS, MemoryReference
from mnemosyne.memory.scopes import SCOPE_DEFINITIONS
from mnemosyne.memory.service import MemoryService
from mnemosyne.memory.store import FilesystemMemoryStore


FIELDS = {
    "scope",
    "namespace",
    "collection",
    "kind",
    "language",
    "title",
    "content",
    "tags",
    "origin",
}


def _arguments() -> dict[str, object]:
    return {
        "scope": "project",
        "namespace": {
            "kind": "project",
            "id": "mnemosyne",
            "label": "Mnemosyne",
        },
        "collection": {
            "id": "decisions",
            "label": "Decisions",
        },
        "kind": "decision",
        "language": "en",
        "title": "Remember boundary",
        "content": "Memory creation requires exact per-call approval.",
        "tags": ["architecture", "consent"],
        "origin": "user_approved_proposal",
    }


def _payload(result: dict[str, object]) -> dict[str, object]:
    content = result["content"]
    assert isinstance(content, list)
    return json.loads(content[0]["text"])


def test_memory_remember_schema_derives_scope_dimensions_and_bounds() -> None:
    assert TOOL["name"] == "memory_remember"
    schema = TOOL["inputSchema"]
    assert set(schema) == {
        "type",
        "properties",
        "required",
        "additionalProperties",
        "oneOf",
    }
    assert schema["type"] == "object"
    assert set(schema["properties"]) == FIELDS
    assert set(schema["required"]) == FIELDS
    assert schema["additionalProperties"] is False
    assert schema["properties"]["scope"]["type"] == "string"
    assert schema["properties"]["scope"]["enum"] == [
        definition.scope.value for definition in SCOPE_DEFINITIONS
    ]
    assert schema["properties"]["origin"] == {
        "type": "string",
        "enum": [
            "explicit_user_statement",
            "user_approved_proposal",
        ],
        "description": (
            "Caller-supplied provenance context, not consent. Use "
            "explicit_user_statement for a direct user statement or "
            "user_approved_proposal for an approved proposed memory."
        ),
    }
    branches = schema["oneOf"]
    assert len(branches) == len(SCOPE_DEFINITIONS)

    branches_by_scope = {
        branch["properties"]["scope"]["const"]: branch for branch in branches
    }
    for definition in SCOPE_DEFINITIONS:
        branch = branches_by_scope[definition.scope.value]
        properties = branch["properties"]
        assert set(properties) == FIELDS
        assert set(branch["required"]) == FIELDS
        assert branch["additionalProperties"] is False
        assert properties["scope"] == {
            "const": definition.scope.value,
            "description": definition.description,
        }
        assert properties["namespace"]["properties"]["kind"]["enum"] == list(
            definition.namespace_kinds
        )
        assert properties["kind"]["enum"] == [
            kind.value for kind in ALLOWED_KINDS[definition.scope]
        ]
        assert properties["origin"]["enum"] == [
            "explicit_user_statement",
            "user_approved_proposal",
        ]

    project = branches_by_scope["project"]["properties"]
    assert project["namespace"] == {
        "type": "object",
        "properties": {
            "kind": {"type": "string", "enum": ["project"]},
            "id": {
                "type": "string",
                "minLength": 1,
                "maxLength": 64,
                "pattern": "^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$",
            },
            "label": {
                "anyOf": [
                    {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 100,
                        "pattern": "\\S",
                    },
                    {"type": "null"},
                ]
            },
        },
        "required": ["kind", "id", "label"],
        "additionalProperties": False,
    }
    assert project["collection"]["anyOf"][0] == {"type": "null"}
    assert project["collection"]["anyOf"][1]["required"] == ["id", "label"]
    assert project["language"] == {
        "anyOf": [
            {
                "type": "string",
                "minLength": 1,
                "maxLength": 35,
                "pattern": "^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$",
            },
            {"type": "null"},
        ]
    }
    assert project["title"]["anyOf"][0]["maxLength"] == 200
    assert project["content"] == {
        "type": "string",
        "minLength": 1,
        "maxLength": 4000,
        "pattern": "\\S",
    }
    assert project["tags"]["minItems"] == 0
    assert project["tags"]["maxItems"] == 10
    assert project["tags"]["uniqueItems"] is True
    assert project["tags"]["items"]["maxLength"] == 50


def test_memory_remember_remains_callable_through_top_level_only_projection() -> None:
    schema = TOOL["inputSchema"]
    flattened = {
        "properties": schema["properties"],
        "required": schema["required"],
    }
    arguments = _arguments()
    projected = {
        name: value
        for name, value in arguments.items()
        if name in flattened["properties"]
    }

    assert set(flattened["required"]) == FIELDS
    assert projected == arguments
    assert _payload(handle(projected)) == {
        "status": "policy_error",
        "code": "mutation_disabled",
        "message": "memory remember is disabled",
    }


def test_memory_remember_package_reexports_definition_and_handler() -> None:
    assert TOOL is DEFINED_TOOL
    assert handle is handler_module.handle


def test_memory_remember_validates_without_persisting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory_root = tmp_path / "application" / "memory"
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(memory_root))

    result = handle(_arguments())

    assert result["isError"] is True
    assert _payload(result) == {
        "status": "policy_error",
        "code": "mutation_disabled",
        "message": "memory remember is disabled",
    }
    assert not memory_root.parent.exists()


@pytest.mark.parametrize(
    "origin",
    [None, "manual", "import", "missing", 42],
)
def test_memory_remember_rejects_non_public_origins(origin: object) -> None:
    arguments = _arguments()
    if origin is None:
        arguments.pop("origin")
    else:
        arguments["origin"] = origin

    result = handle(arguments)

    assert result["isError"] is True
    assert _payload(result) == {
        "status": "invalid_request",
        "code": "invalid_origin",
        "field": "origin",
        "message": "origin is invalid",
    }


@pytest.mark.parametrize(
    "origin",
    ["explicit_user_statement", "user_approved_proposal"],
)
def test_memory_remember_accepts_both_public_origins(origin: str) -> None:
    arguments = _arguments()
    arguments["origin"] = origin

    result = handle(arguments)

    assert result["isError"] is True
    assert _payload(result) == {
        "status": "policy_error",
        "code": "mutation_disabled",
        "message": "memory remember is disabled",
    }


@pytest.mark.parametrize(
    ("mutate", "code", "field", "message"),
    [
        (
            lambda value: value.update({"unexpected": True}),
            "invalid_record",
            "memory",
            "memory field is invalid",
        ),
        (
            lambda value: value.update({"scope": "missing"}),
            "invalid_scope",
            "scope",
            "scope is invalid",
        ),
        (
            lambda value: value["namespace"].update({"kind": "topic"}),
            "invalid_namespace",
            "namespace.kind",
            "namespace is invalid for scope",
        ),
        (
            lambda value: value["collection"].update({"id": "Bad ID"}),
            "invalid_collection",
            "collection.id",
            "collection is invalid",
        ),
        (
            lambda value: value.update({"kind": "attribute"}),
            "invalid_kind",
            "kind",
            "kind is invalid for scope",
        ),
        (
            lambda value: value.update({"language": "@"}),
            "invalid_record",
            "language",
            "memory field is invalid",
        ),
        (
            lambda value: value.update({"title": ""}),
            "invalid_record",
            "title",
            "memory field is invalid",
        ),
        (
            lambda value: value.update({"content": " "}),
            "invalid_record",
            "content",
            "memory field is invalid",
        ),
        (
            lambda value: value.update({"tags": ["Consent", "consent"]}),
            "invalid_record",
            "tags",
            "memory field is invalid",
        ),
    ],
)
def test_memory_remember_maps_validation_errors_without_input_values(
    mutate,
    code: str,
    field: str,
    message: str,
) -> None:
    arguments = deepcopy(_arguments())
    mutate(arguments)

    result = handle(arguments)

    assert result["isError"] is True
    assert _payload(result) == {
        "status": "invalid_request",
        "code": code,
        "field": field,
        "message": message,
    }


@pytest.mark.parametrize(
    "field",
    [
        "path",
        "id",
        "created_at",
        "updated_at",
        "lifecycle",
        "revision",
        "recorded_via",
        "confirmed",
        "approved",
        "consent",
    ],
)
def test_memory_remember_rejects_forbidden_operational_and_consent_fields(
    field: str,
) -> None:
    arguments = _arguments()
    arguments[field] = "forbidden"

    result = handle(arguments)

    assert _payload(result) == {
        "status": "invalid_request",
        "code": "invalid_record",
        "field": "memory",
        "message": "memory field is invalid",
    }


def test_memory_remember_persists_canonical_record_with_minimal_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))

    result = handle(_arguments(), mutations_enabled=True)

    assert "isError" not in result
    payload = _payload(result)
    assert payload["status"] == "remembered"
    reference = payload["reference"]
    assert reference["scope"] == "project"
    assert reference["namespace_id"] == "mnemosyne"
    assert reference["collection_id"] == "decisions"
    assert reference["id"].startswith("mem_")
    assert len(reference["id"]) == 36
    assert payload["lifecycle"] == {"state": "active", "revision": 1}
    assert set(payload) == {"status", "reference", "lifecycle"}

    files = list(tmp_path.rglob("*.json"))
    assert len(files) == 1
    stored = json.loads(files[0].read_text(encoding="utf-8"))
    assert stored["id"] == reference["id"]
    assert stored["provenance"]["recorded_via"] == "memory_remember"
    assert stored["lifecycle"] == {"state": "active", "revision": 1}


def test_memory_remember_initializes_an_absent_default_memory_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.delenv("MNEMOSYNE_MEMORY_ROOT", raising=False)
    monkeypatch.setattr(Path, "home", lambda: home)

    result = handle(_arguments(), mutations_enabled=True)

    assert _payload(result)["status"] == "remembered"
    memory_root = home / ".mnemosyne" / "memory"
    assert len(list(memory_root.rglob("*.json"))) == 1


def test_memory_remember_returns_active_duplicate_without_second_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))

    first = _payload(handle(_arguments(), mutations_enabled=True))
    second = _payload(handle(_arguments(), mutations_enabled=True))

    assert second == {
        "status": "already_exists",
        "reference": first["reference"],
        "lifecycle": {"state": "active", "revision": 1},
    }
    assert len(list(tmp_path.rglob("*.json"))) == 1


def test_memory_remember_returns_archived_duplicate_without_second_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    first = _payload(handle(_arguments(), mutations_enabled=True))
    reference = MemoryReference.from_dict(first["reference"])
    MemoryService(
        FilesystemMemoryStore(tmp_path),
        mutations_enabled=True,
    ).archive(reference, expected_revision=1)

    duplicate = _payload(handle(_arguments(), mutations_enabled=True))

    assert duplicate == {
        "status": "existing_archived",
        "reference": first["reference"],
        "lifecycle": {"state": "archived", "revision": 2},
    }
    assert len(list(tmp_path.rglob("*.json"))) == 1


def test_memory_remember_refuses_disallowed_content_without_writing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory_root = tmp_path / "application" / "memory"
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(memory_root))
    arguments = _arguments()
    arguments["content"] = "Authorization: Bearer synthetic-token"

    result = handle(arguments, mutations_enabled=True)

    assert result["isError"] is True
    assert _payload(result) == {
        "status": "refused",
        "code": "disallowed_content",
        "message": "memory contains content that Mnemosyne does not store",
    }
    assert not memory_root.parent.exists()


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            MutationDisabled(),
            {
                "status": "policy_error",
                "code": "mutation_disabled",
                "message": "memory remember is disabled",
            },
        ),
        (
            CandidateLimitExceeded(),
            {
                "status": "storage_error",
                "code": "candidate_limit_exceeded",
                "message": "memory scope contains more than 1000 candidate files",
            },
        ),
        (
            WriteConflict(),
            {
                "status": "conflict",
                "code": "write_conflict",
                "message": "generated memory identity conflicts with an existing record",
            },
        ),
        (
            UnsafeMemoryPath(),
            {
                "status": "storage_error",
                "code": "memory_source_unavailable",
                "message": "memory could not be stored",
            },
        ),
        (
            MemorySourceUnavailable(),
            {
                "status": "storage_error",
                "code": "memory_source_unavailable",
                "message": "memory could not be stored",
            },
        ),
        (
            OSError("/private/path"),
            {
                "status": "storage_error",
                "code": "memory_source_unavailable",
                "message": "memory could not be stored",
            },
        ),
        (
            RuntimeError("unexpected sensitive detail"),
            {
                "status": "internal_error",
                "code": "internal_error",
                "message": "memory could not be stored",
            },
        ),
    ],
)
def test_memory_remember_maps_service_failures_without_exception_details(
    error: Exception,
    expected: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_remember(*args: object) -> None:
        raise error

    monkeypatch.setattr(handler_module.MemoryService, "remember", fail_remember)

    result = handle(_arguments(), mutations_enabled=True)

    assert result["isError"] is True
    assert _payload(result) == expected
    if isinstance(error, (OSError, RuntimeError)):
        assert str(error) not in result["content"][0]["text"]


def test_memory_remember_logs_one_content_free_success_event(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    caplog.set_level(logging.INFO, logger="mcp.memory_remember")
    arguments = _arguments()

    handle(arguments, mutations_enabled=True)

    assert len(caplog.messages) == 1
    message = caplog.messages[0]
    assert message.startswith(
        "event=memory_remember outcome=remembered scope=project "
        "namespace_kind=project memory_kind=decision collection_present=True "
        "origin=user_approved_proposal memory_id=mem_"
    )
    assert message.endswith(" lifecycle_state=active revision=1")
    forbidden = [
        arguments["namespace"]["id"],
        arguments["namespace"]["label"],
        arguments["collection"]["id"],
        arguments["collection"]["label"],
        arguments["title"],
        arguments["content"],
        *arguments["tags"],
        str(tmp_path),
    ]
    assert all(value not in message for value in forbidden)


def test_memory_remember_logs_refusal_without_rejected_value_or_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    caplog.set_level(logging.WARNING, logger="mcp.memory_remember")
    rejected = "Authorization: Bearer synthetic-token"
    arguments = _arguments()
    arguments["content"] = rejected

    handle(arguments, mutations_enabled=True)

    assert caplog.messages == [
        "event=memory_remember outcome=refused code=disallowed_content "
        "scope=project namespace_kind=project memory_kind=decision "
        "collection_present=True origin=user_approved_proposal"
    ]
    assert rejected not in caplog.messages[0]
    assert str(tmp_path) not in caplog.messages[0]


@pytest.mark.parametrize(
    ("error", "level", "outcome", "code"),
    [
        (
            CandidateLimitExceeded(),
            logging.WARNING,
            "storage_error",
            "candidate_limit_exceeded",
        ),
        (WriteConflict(), logging.WARNING, "conflict", "write_conflict"),
        (
            OSError("/private/sensitive/path"),
            logging.WARNING,
            "storage_error",
            "memory_source_unavailable",
        ),
        (
            RuntimeError("unexpected sensitive detail"),
            logging.ERROR,
            "internal_error",
            "internal_error",
        ),
    ],
)
def test_memory_remember_logs_failures_without_exception_details(
    error: Exception,
    level: int,
    outcome: str,
    code: str,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fail_remember(*args: object) -> None:
        raise error

    monkeypatch.setattr(handler_module.MemoryService, "remember", fail_remember)
    caplog.set_level(logging.INFO, logger="mcp.memory_remember")

    handle(_arguments(), mutations_enabled=True)

    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == level
    assert caplog.messages == [
        f"event=memory_remember outcome={outcome} code={code} "
        "scope=project namespace_kind=project memory_kind=decision "
        "collection_present=True origin=user_approved_proposal"
    ]
    if isinstance(error, (OSError, RuntimeError)):
        assert str(error) not in caplog.messages[0]
