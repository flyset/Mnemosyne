import json
import logging
from copy import deepcopy
from pathlib import Path

import pytest

from mymcp.mcp.tools.memory_remember import TOOL, handle as public_handle
from mymcp.mcp.tools.memory_remember import handler as handler_module
from mymcp.mcp.tools.memory_remember.definition import TOOL as DEFINED_TOOL
from mymcp.memory.errors import (
    CandidateLimitExceeded,
    MemorySourceUnavailable,
    MutationDisabled,
    UnsafeMemoryPath,
    WriteConflict,
)
from mymcp.memory.records import KIND_DEFINITIONS, MemoryDraft, MemoryReference
from mymcp.memory.scopes import SCOPE_DEFINITIONS
from mymcp.memory.service import MemoryService
from mymcp.memory.store import FilesystemMemoryStore
from mymcp.settings import get_memory_root


REQUIRED_FIELDS = {
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
TOP_LEVEL_FIELDS = REQUIRED_FIELDS | {"occurred_at"}
EXPECTED_KIND_ENUMS = {
    "self": ["attribute"],
    "relationship": ["perspective", "summary"],
    "preference": ["preference"],
    "practice": ["practice"],
    "project": [
        "decision",
        "constraint",
        "state",
        "event",
        "question",
        "reference",
        "summary",
    ],
    "knowledge": ["reference", "summary"],
}
EXPECTED_FLAT_KIND_ENUM = [
    "attribute",
    "perspective",
    "summary",
    "preference",
    "practice",
    "decision",
    "constraint",
    "state",
    "event",
    "question",
    "reference",
]


def _remember_operation(draft: MemoryDraft):
    return MemoryService(
        FilesystemMemoryStore(get_memory_root()),
        mutations_enabled=True,
    ).remember(draft)


def handle(
    arguments,
    *,
    mutations_enabled=False,
    remember_operation=None,
):
    return public_handle(
        arguments,
        remember_operation=(
            _remember_operation
            if remember_operation is None
            else remember_operation
        ),
        mutations_enabled=mutations_enabled,
    )


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


def _event_arguments(
    occurred_at: str = "2026-07-17T09:30:00Z",
) -> dict[str, object]:
    arguments = _arguments()
    arguments.update(
        {
            "collection": {"id": "events", "label": "Events"},
            "kind": "event",
            "title": "Track activated",
            "content": "Track 021 moved to active execution.",
            "tags": ["track-021"],
            "occurred_at": occurred_at,
        }
    )
    return arguments


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
    assert set(schema["properties"]) == TOP_LEVEL_FIELDS
    assert set(schema["required"]) == REQUIRED_FIELDS
    assert schema["additionalProperties"] is False
    assert schema["properties"]["scope"]["type"] == "string"
    assert schema["properties"]["scope"]["enum"] == [
        definition.scope.value for definition in SCOPE_DEFINITIONS
    ]
    assert schema["properties"]["kind"]["enum"] == EXPECTED_FLAT_KIND_ENUM
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
        expected_properties = (
            TOP_LEVEL_FIELDS
            if definition.scope.value == "project"
            else REQUIRED_FIELDS
        )
        assert set(properties) == expected_properties
        assert set(branch["required"]) == REQUIRED_FIELDS
        assert branch["additionalProperties"] is False
        assert properties["scope"] == {
            "const": definition.scope.value,
            "description": definition.description,
        }
        assert properties["namespace"]["properties"]["kind"]["enum"] == list(
            definition.namespace_kinds
        )
        assert properties["kind"]["enum"] == EXPECTED_KIND_ENUMS[
            definition.scope.value
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
    assert project["occurred_at"] == {
        "type": "string",
        "description": (
            "Required exactly for project event memory; omit it for every other "
            "memory kind. Use strict UTC-second form YYYY-MM-DDTHH:MM:SSZ."
        ),
        "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$",
    }
    assert branches_by_scope["project"]["allOf"] == [
        {
            "if": {"properties": {"kind": {"const": "event"}}},
            "then": {"required": ["occurred_at"]},
            "else": {"not": {"required": ["occurred_at"]}},
        }
    ]


def test_memory_remember_description_explains_safe_refusal_recovery() -> None:
    description = TOOL["description"]

    assert "disallowed_content" in description
    assert "bounded field and reason" in description
    assert "Do not obfuscate suspected sensitive data" in description
    assert (
        "retry only when the user confirms that the formatting is benign and "
        "approves the exact revised call"
    ) in description


def test_memory_remember_schema_renders_canonical_kind_guidance() -> None:
    schema = TOOL["inputSchema"]
    branches_by_scope = {
        branch["properties"]["scope"]["const"]: branch
        for branch in schema["oneOf"]
    }

    expected_groups: list[str] = []
    for scope_definition in SCOPE_DEFINITIONS:
        pairs = "; ".join(
            f"{definition.kind.value}: {definition.guidance}"
            for definition in KIND_DEFINITIONS[scope_definition.scope]
        )
        expected_groups.append(f"{scope_definition.scope.value}: {pairs}")
        assert branches_by_scope[scope_definition.scope.value]["properties"][
            "kind"
        ]["description"] == (
            f"Writing guidance for {scope_definition.scope.value} memory kinds: "
            f"{pairs}"
        )

    assert schema["properties"]["kind"]["description"] == (
        "Memory kind must match scope; the complete schema narrows this enum for "
        "each scope. Writing guidance by scope: " + " | ".join(expected_groups)
    )


def test_memory_remember_remains_callable_through_top_level_only_projection() -> None:
    schema = TOOL["inputSchema"]
    flattened = {
        "properties": schema["properties"],
        "required": schema["required"],
    }
    arguments = _event_arguments()
    projected = {
        name: value
        for name, value in arguments.items()
        if name in flattened["properties"]
    }

    assert set(flattened["required"]) == REQUIRED_FIELDS
    assert projected == arguments
    assert _payload(handle(projected)) == {
        "status": "policy_error",
        "code": "mutation_disabled",
        "message": "memory remember is disabled",
    }


@pytest.mark.parametrize(
    ("arguments", "code", "field"),
    [
        (
            {
                key: value
                for key, value in _event_arguments().items()
                if key != "occurred_at"
            },
            "invalid_record",
            "occurred_at",
        ),
        (
            _event_arguments("2026-07-17T09:30:00+00:00"),
            "invalid_record",
            "occurred_at",
        ),
        (
            {**_arguments(), "occurred_at": "2026-07-17T09:30:00Z"},
            "invalid_record",
            "occurred_at",
        ),
        (
            {
                **_event_arguments(),
                "scope": "preference",
                "namespace": {"kind": "domain", "id": "leisure", "label": None},
            },
            "invalid_kind",
            "kind",
        ),
    ],
)
def test_memory_remember_enforces_project_event_occurrence_contract(
    arguments: dict[str, object],
    code: str,
    field: str,
) -> None:
    result = handle(arguments)

    assert _payload(result) == {
        "status": "invalid_request",
        "code": code,
        "field": field,
        "message": (
            "memory field is invalid"
            if code == "invalid_record"
            else "kind is invalid for scope"
        ),
    }


def test_memory_remember_package_reexports_definition_and_handler() -> None:
    assert TOOL is DEFINED_TOOL
    assert public_handle is handler_module.handle


def test_memory_remember_adapts_a_valid_draft_to_the_supplied_operation() -> None:
    observed = []

    def remember_operation(draft: MemoryDraft):
        observed.append(draft)
        raise MutationDisabled

    result = handle(
        _arguments(),
        mutations_enabled=True,
        remember_operation=remember_operation,
    )

    assert len(observed) == 1
    assert observed[0].scope.value == "project"
    assert observed[0].namespace.id == "mnemosyne"
    assert observed[0].content == _arguments()["content"]
    assert _payload(result)["code"] == "mutation_disabled"


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


def test_memory_remember_persists_event_occurrence_without_returning_or_logging_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    caplog.set_level(logging.INFO, logger="mcp.memory_remember")
    arguments = _event_arguments()

    result = handle(arguments, mutations_enabled=True)

    payload = _payload(result)
    assert set(payload) == {"status", "reference", "lifecycle"}
    stored = json.loads(next(tmp_path.rglob("*.json")).read_text(encoding="utf-8"))
    assert stored["kind"] == "event"
    assert stored["occurred_at"] == arguments["occurred_at"]
    assert len(caplog.messages) == 1
    assert "memory_kind=event" in caplog.messages[0]
    assert arguments["occurred_at"] not in caplog.messages[0]


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
        "field": "content",
        "reason": "credential_shape",
        "message": (
            "memory field resembles content that Mnemosyne does not store; "
            "review the named field and retry only if the user confirms that "
            "the formatting is benign"
        ),
    }
    assert not memory_root.parent.exists()


@pytest.mark.parametrize(
    ("domain_field", "expected_public_field"),
    [
        ("namespace.id", "namespace"),
        ("namespace.label", "namespace"),
        ("collection.id", "collection"),
        ("collection.label", "collection"),
        ("title", "title"),
        ("content", "content"),
        ("tags", "tags"),
    ],
)
def test_memory_remember_maps_refusal_to_bounded_public_field(
    domain_field: str,
    expected_public_field: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory_root = tmp_path / "application" / "memory"
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(memory_root))
    arguments = _arguments()
    rejected = "sk-" + "a" * 20
    if domain_field == "namespace.id":
        arguments["namespace"]["id"] = rejected
    elif domain_field == "namespace.label":
        arguments["namespace"]["label"] = rejected
    elif domain_field == "collection.id":
        arguments["collection"]["id"] = rejected
    elif domain_field == "collection.label":
        arguments["collection"]["label"] = rejected
    elif domain_field == "tags":
        arguments["tags"] = [rejected]
    else:
        arguments[domain_field] = rejected

    result = handle(arguments, mutations_enabled=True)
    payload = _payload(result)

    assert result["isError"] is True
    assert payload["field"] == expected_public_field
    assert payload["reason"] == "credential_shape"
    assert rejected not in result["content"][0]["text"]
    assert not memory_root.parent.exists()


def test_memory_remember_classifies_dotted_version_without_source_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory_root = tmp_path / "application" / "memory"
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(memory_root))
    arguments = _arguments()
    arguments["content"] = "Compatibility build 0.1.0"

    result = handle(arguments, mutations_enabled=True)

    assert result["isError"] is True
    assert _payload(result) == {
        "status": "refused",
        "code": "disallowed_content",
        "field": "content",
        "reason": "compact_token_shape",
        "message": (
            "memory field resembles content that Mnemosyne does not store; "
            "review the named field and retry only if the user confirms that "
            "the formatting is benign"
        ),
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
) -> None:
    def fail_remember(*args: object) -> None:
        raise error

    result = handle(
        _arguments(),
        mutations_enabled=True,
        remember_operation=fail_remember,
    )

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
    assert "field=" not in caplog.messages[0]
    assert "credential_shape" not in caplog.messages[0]
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
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fail_remember(*args: object) -> None:
        raise error

    caplog.set_level(logging.INFO, logger="mcp.memory_remember")

    handle(
        _arguments(),
        mutations_enabled=True,
        remember_operation=fail_remember,
    )

    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == level
    assert caplog.messages == [
        f"event=memory_remember outcome={outcome} code={code} "
        "scope=project namespace_kind=project memory_kind=decision "
        "collection_present=True origin=user_approved_proposal"
    ]
    if isinstance(error, (OSError, RuntimeError)):
        assert str(error) not in caplog.messages[0]
