from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from mymcp.memory.errors import MemoryValidationError
from mymcp.memory.records import (
    ALLOWED_KINDS,
    KIND_DEFINITIONS,
    KindDefinition,
    LegacyMemoryRecordV1,
    LegacyMemoryReference,
    LifecycleState,
    MemoryCollection,
    MemoryDraft,
    MemoryKind,
    MemoryLifecycle,
    MemoryNamespace,
    MemoryOrigin,
    MemoryProvenance,
    MemoryRecordV2,
    MemoryRecordedVia,
    MemoryReference,
    MemoryRevision,
    parse_memory_record,
    serialize_memory_record,
)
from mymcp.memory.scopes import MemoryScope


V2_PAYLOAD = {
    "schema_version": 2,
    "id": "mem_0123456789abcdef0123456789abcdef",
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
    "title": "Shared memory ownership",
    "content": "Canonical memory concepts belong to the shared memory domain.",
    "tags": ["architecture", "memory-domain"],
    "provenance": {
        "origin": "explicit_user_statement",
        "recorded_via": "memory_remember",
    },
    "lifecycle": {
        "state": "active",
        "revision": 1,
    },
    "created_at": "2026-07-18T12:00:00Z",
    "updated_at": "2026-07-18T12:00:00Z",
}
EVENT_OCCURRED_AT = "2026-07-17T09:30:00Z"
EVENT_V2_PAYLOAD = {
    **V2_PAYLOAD,
    "kind": "event",
    "occurred_at": EVENT_OCCURRED_AT,
}


EXPECTED_ALLOWED_KINDS = {
    MemoryScope.SELF: (MemoryKind.ATTRIBUTE,),
    MemoryScope.RELATIONSHIP: (
        MemoryKind.PERSPECTIVE,
        MemoryKind.SUMMARY,
    ),
    MemoryScope.PREFERENCE: (MemoryKind.PREFERENCE,),
    MemoryScope.PRACTICE: (MemoryKind.PRACTICE,),
    MemoryScope.PROJECT: (
        MemoryKind.DECISION,
        MemoryKind.CONSTRAINT,
        MemoryKind.STATE,
        MemoryKind.EVENT,
        MemoryKind.QUESTION,
        MemoryKind.REFERENCE,
        MemoryKind.SUMMARY,
    ),
    MemoryScope.KNOWLEDGE: (
        MemoryKind.REFERENCE,
        MemoryKind.SUMMARY,
    ),
}


def test_kind_definitions_are_canonical_complete_and_bounded() -> None:
    assert set(KIND_DEFINITIONS) == set(MemoryScope)
    assert {
        scope: tuple(definition.kind for definition in definitions)
        for scope, definitions in KIND_DEFINITIONS.items()
    } == EXPECTED_ALLOWED_KINDS
    assert ALLOWED_KINDS == EXPECTED_ALLOWED_KINDS

    definitions = [
        definition
        for scope_definitions in KIND_DEFINITIONS.values()
        for definition in scope_definitions
    ]
    assert len(definitions) == 14
    assert all(isinstance(definition, KindDefinition) for definition in definitions)
    assert all(
        definition.guidance == definition.guidance.strip()
        and 1 <= len(definition.guidance) <= 240
        for definition in definitions
    )

    with pytest.raises(FrozenInstanceError):
        definitions[0].guidance = "changed"  # type: ignore[misc]


def test_shared_kinds_have_scope_specific_guidance() -> None:
    guidance = {
        (scope, definition.kind): definition.guidance
        for scope, definitions in KIND_DEFINITIONS.items()
        for definition in definitions
    }

    assert len(
        {
            guidance[(MemoryScope.RELATIONSHIP, MemoryKind.SUMMARY)],
            guidance[(MemoryScope.PROJECT, MemoryKind.SUMMARY)],
            guidance[(MemoryScope.KNOWLEDGE, MemoryKind.SUMMARY)],
        }
    ) == 3
    assert (
        guidance[(MemoryScope.PROJECT, MemoryKind.REFERENCE)]
        != guidance[(MemoryScope.KNOWLEDGE, MemoryKind.REFERENCE)]
    )


def test_event_kind_follows_state_and_is_project_only() -> None:
    assert list(MemoryKind).index(MemoryKind.EVENT) == list(MemoryKind).index(
        MemoryKind.STATE
    ) + 1
    assert MemoryKind.EVENT in ALLOWED_KINDS[MemoryScope.PROJECT]
    assert all(
        MemoryKind.EVENT not in kinds
        for scope, kinds in ALLOWED_KINDS.items()
        if scope is not MemoryScope.PROJECT
    )
    event_guidance = next(
        definition.guidance
        for definition in KIND_DEFINITIONS[MemoryScope.PROJECT]
        if definition.kind is MemoryKind.EVENT
    )
    assert "occurrence" in event_guidance
    assert "state" in event_guidance


def test_version_one_record_parsing_preserves_the_existing_contract() -> None:
    payload = {
        "schema_version": 1,
        "id": "rainy-weekend",
        "title": " Rainy weekend ",
        "content": " User prefers cafés. ",
        "tags": ["Leisure", "rainy-day"],
    }

    record = parse_memory_record(payload)

    assert record == LegacyMemoryRecordV1(
        id="rainy-weekend",
        title=" Rainy weekend ",
        content=" User prefers cafés. ",
        tags=("Leisure", "rainy-day"),
    )
    assert serialize_memory_record(record) == payload


def test_version_one_record_allows_omitted_title_and_tags() -> None:
    record = parse_memory_record(
        {"schema_version": 1, "id": "legacy", "content": "Legacy memory"}
    )

    assert record == LegacyMemoryRecordV1(
        id="legacy",
        title=None,
        content="Legacy memory",
        tags=(),
    )
    assert serialize_memory_record(record) == {
        "schema_version": 1,
        "id": "legacy",
        "content": "Legacy memory",
    }


def test_version_two_record_round_trips_the_canonical_shape() -> None:
    record = parse_memory_record(V2_PAYLOAD)

    assert record == MemoryRecordV2(
        id="mem_0123456789abcdef0123456789abcdef",
        scope=MemoryScope.PROJECT,
        namespace=MemoryNamespace(
            kind="project",
            id="mnemosyne",
            label="Mnemosyne",
        ),
        collection=MemoryCollection(id="decisions", label="Decisions"),
        kind=MemoryKind.DECISION,
        language="en",
        title="Shared memory ownership",
        content="Canonical memory concepts belong to the shared memory domain.",
        tags=("architecture", "memory-domain"),
        provenance=MemoryProvenance(
            origin=MemoryOrigin.EXPLICIT_USER_STATEMENT,
            recorded_via=MemoryRecordedVia.MEMORY_REMEMBER,
        ),
        lifecycle=MemoryLifecycle(state=LifecycleState.ACTIVE, revision=1),
        created_at=datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc),
    )
    assert serialize_memory_record(record) == V2_PAYLOAD


def test_event_record_round_trips_structural_occurrence_time() -> None:
    record = parse_memory_record(EVENT_V2_PAYLOAD)

    assert isinstance(record, MemoryRecordV2)
    assert record.kind is MemoryKind.EVENT
    assert record.occurred_at == datetime(2026, 7, 17, 9, 30, tzinfo=timezone.utc)
    assert serialize_memory_record(record) == EVENT_V2_PAYLOAD


@pytest.mark.parametrize(
    "payload",
    [
        {key: value for key, value in EVENT_V2_PAYLOAD.items() if key != "occurred_at"},
        {**EVENT_V2_PAYLOAD, "occurred_at": None},
        {**EVENT_V2_PAYLOAD, "occurred_at": "2026-07-17T09:30:00+00:00"},
        {**EVENT_V2_PAYLOAD, "occurred_at": "2026-07-17T09:30:00.000Z"},
        {**EVENT_V2_PAYLOAD, "occurred_at": "2026-02-30T09:30:00Z"},
        {**V2_PAYLOAD, "occurred_at": EVENT_OCCURRED_AT},
    ],
)
def test_record_occurrence_time_is_required_exactly_for_events(
    payload: dict[str, object],
) -> None:
    with pytest.raises(MemoryValidationError) as error:
        parse_memory_record(payload)

    assert error.value.code == "invalid_record"
    assert error.value.field == "occurred_at"


def test_version_two_record_normalizes_user_text_and_nullable_fields() -> None:
    payload = {
        **V2_PAYLOAD,
        "namespace": {"kind": "project", "id": "mnemosyne", "label": None},
        "collection": None,
        "language": "EL",
        "title": None,
        "content": "  Cafe\u0301\r\nnotes  ",
        "tags": [],
    }

    record = parse_memory_record(payload)

    assert isinstance(record, MemoryRecordV2)
    assert record.namespace.label is None
    assert record.collection is None
    assert record.language == "el"
    assert record.title is None
    assert record.content == "Café\nnotes"
    assert record.tags == ()


@pytest.mark.parametrize(
    "payload",
    [
        {**V2_PAYLOAD, "unexpected": True},
        {**V2_PAYLOAD, "namespace": {**V2_PAYLOAD["namespace"], "extra": True}},
        {**V2_PAYLOAD, "collection": {**V2_PAYLOAD["collection"], "extra": True}},
        {**V2_PAYLOAD, "provenance": {**V2_PAYLOAD["provenance"], "extra": True}},
        {**V2_PAYLOAD, "lifecycle": {**V2_PAYLOAD["lifecycle"], "extra": True}},
    ],
)
def test_version_two_record_rejects_unknown_fields(payload: dict[str, object]) -> None:
    with pytest.raises(MemoryValidationError) as error:
        parse_memory_record(payload)

    assert error.value.code == "invalid_record"


@pytest.mark.parametrize(
    ("scope", "namespace_kind", "kind"),
    [
        ("self", "domain", "attribute"),
        ("project", "topic", "decision"),
        ("project", "project", "preference"),
        ("relationship", "person", "attribute"),
        ("relationship", "person", "event"),
    ],
)
def test_version_two_record_rejects_scope_dimension_mismatches(
    scope: str,
    namespace_kind: str,
    kind: str,
) -> None:
    payload = {
        **V2_PAYLOAD,
        "scope": scope,
        "namespace": {**V2_PAYLOAD["namespace"], "kind": namespace_kind},
        "kind": kind,
    }

    with pytest.raises(MemoryValidationError) as error:
        parse_memory_record(payload)

    assert error.value.code in {"invalid_namespace", "invalid_kind"}


@pytest.mark.parametrize(
    "payload",
    [
        {**V2_PAYLOAD, "schema_version": True},
        {**V2_PAYLOAD, "id": "memory-1"},
        {**V2_PAYLOAD, "created_at": "2026-07-18T12:00:00+00:00"},
        {**V2_PAYLOAD, "updated_at": "2026-07-18T11:00:00Z"},
        {**V2_PAYLOAD, "lifecycle": {"state": "active", "revision": 0}},
    ],
)
def test_version_two_record_rejects_invalid_identity_time_or_lifecycle(
    payload: dict[str, object],
) -> None:
    with pytest.raises(MemoryValidationError) as error:
        parse_memory_record(payload)

    assert error.value.code == "invalid_record"


def test_memory_reference_and_legacy_reference_are_structured_and_validated() -> None:
    assert MemoryReference.from_dict(
        {
            "scope": "project",
            "namespace_id": "mnemosyne",
            "collection_id": "decisions",
            "id": "mem_0123456789abcdef0123456789abcdef",
        }
    ) == MemoryReference(
        scope=MemoryScope.PROJECT,
        namespace_id="mnemosyne",
        collection_id="decisions",
        id="mem_0123456789abcdef0123456789abcdef",
    )
    assert LegacyMemoryReference.from_dict(
        {"scope": "preference", "id": "rainy-weekend"}
    ) == LegacyMemoryReference(
        scope=MemoryScope.PREFERENCE,
        id="rainy-weekend",
    )


def test_memory_draft_normalizes_fields_and_calculates_duplicate_identity() -> None:
    draft = MemoryDraft.from_dict(
        {
            "scope": "preference",
            "namespace": {"kind": "domain", "id": "leisure", "label": " Leisure "},
            "collection": None,
            "kind": "preference",
            "language": None,
            "title": " Rainy weekends ",
            "content": " Cafe\u0301 visits ",
            "tags": ["Rainy Day", "Leisure"],
            "origin": "explicit_user_statement",
        }
    )

    assert draft.language == "und"
    assert draft.namespace.label == "Leisure"
    assert draft.title == "Rainy weekends"
    assert draft.content == "Café visits"
    assert draft.tags == ("Rainy Day", "Leisure")
    assert draft.duplicate_key() == (
        "preference",
        "domain",
        "leisure",
        None,
        "preference",
        None,
        "Rainy weekends",
        "Café visits",
        ("leisure", "rainy day"),
    )


def test_event_draft_requires_occurrence_time_and_includes_it_in_duplicate_identity(
) -> None:
    arguments = {
        "scope": "project",
        "namespace": {"kind": "project", "id": "mnemosyne", "label": None},
        "collection": {"id": "events", "label": "Events"},
        "kind": "event",
        "language": "en",
        "title": "Track activated",
        "content": "Track 021 moved to active execution.",
        "tags": ["track-021"],
        "origin": "explicit_user_statement",
        "occurred_at": EVENT_OCCURRED_AT,
    }

    draft = MemoryDraft.from_dict(arguments)
    same = MemoryDraft.from_dict(arguments)
    later = MemoryDraft.from_dict(
        {**arguments, "occurred_at": "2026-07-17T09:31:00Z"}
    )

    assert draft.occurred_at == datetime(2026, 7, 17, 9, 30, tzinfo=timezone.utc)
    assert draft.duplicate_key() == same.duplicate_key()
    assert draft.duplicate_key() != later.duplicate_key()
    assert draft.duplicate_key()[5] == draft.occurred_at

    for invalid in (
        {key: value for key, value in arguments.items() if key != "occurred_at"},
        {**arguments, "occurred_at": "2026-07-17T09:30:00+00:00"},
        {
            **arguments,
            "kind": "state",
            "occurred_at": EVENT_OCCURRED_AT,
        },
    ):
        with pytest.raises(MemoryValidationError) as error:
            MemoryDraft.from_dict(invalid)
        assert error.value.field == "occurred_at"


def test_record_duplicate_identity_ignores_generated_and_operational_fields() -> None:
    record = parse_memory_record(V2_PAYLOAD)
    changed = parse_memory_record(
        {
            **V2_PAYLOAD,
            "id": "mem_ffffffffffffffffffffffffffffffff",
            "namespace": {**V2_PAYLOAD["namespace"], "label": "New label"},
            "collection": {**V2_PAYLOAD["collection"], "label": "New collection"},
            "provenance": {"origin": "manual", "recorded_via": "filesystem"},
            "lifecycle": {"state": "archived", "revision": 4},
            "created_at": "2026-07-17T12:00:00Z",
            "updated_at": "2026-07-19T12:00:00Z",
        }
    )

    assert isinstance(record, MemoryRecordV2)
    assert isinstance(changed, MemoryRecordV2)
    assert record.duplicate_key() == changed.duplicate_key()


def test_memory_revision_contains_only_complete_mutable_state() -> None:
    revision = MemoryRevision.from_dict(
        {
            "expected_revision": 2,
            "namespace_label": " Mnemosyne ",
            "collection_label": None,
            "title": " Revised title ",
            "content": " Revised content ",
            "tags": ["Architecture"],
        }
    )

    assert revision == MemoryRevision(
        expected_revision=2,
        namespace_label="Mnemosyne",
        collection_label=None,
        title="Revised title",
        content="Revised content",
        tags=("Architecture",),
    )

    with pytest.raises(MemoryValidationError):
        MemoryRevision.from_dict(
            {
                "expected_revision": 2,
                "namespace_label": "Mnemosyne",
                "collection_label": None,
                "title": "Revised title",
                "content": "Revised content",
                "tags": ["Architecture"],
                "occurred_at": EVENT_OCCURRED_AT,
            }
        )
