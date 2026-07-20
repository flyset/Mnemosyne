import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, TypeVar

from mnemosyne.memory.errors import MemoryValidationError
from mnemosyne.memory.normalization import (
    normalize_identifier,
    normalize_language,
    normalize_memory_id,
    normalize_optional_text,
    normalize_required_text,
    normalize_tags,
    normalized_tag_key,
)
from mnemosyne.memory.scopes import (
    MemoryScope,
    get_scope_definition,
    parse_scope,
)


class MemoryKind(StrEnum):
    ATTRIBUTE = "attribute"
    PERSPECTIVE = "perspective"
    PREFERENCE = "preference"
    PRACTICE = "practice"
    DECISION = "decision"
    CONSTRAINT = "constraint"
    STATE = "state"
    EVENT = "event"
    QUESTION = "question"
    REFERENCE = "reference"
    SUMMARY = "summary"


@dataclass(frozen=True)
class KindDefinition:
    kind: MemoryKind
    guidance: str


class MemoryOrigin(StrEnum):
    EXPLICIT_USER_STATEMENT = "explicit_user_statement"
    USER_APPROVED_PROPOSAL = "user_approved_proposal"
    MANUAL = "manual"
    IMPORT = "import"


class MemoryRecordedVia(StrEnum):
    MEMORY_REMEMBER = "memory_remember"
    FILESYSTEM = "filesystem"
    MIGRATION = "migration"
    IMPORT = "import"


class LifecycleState(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


KIND_DEFINITIONS: dict[MemoryScope, tuple[KindDefinition, ...]] = {
    MemoryScope.SELF: (
        KindDefinition(
            kind=MemoryKind.ATTRIBUTE,
            guidance=(
                "Record a stable fact about who the user is or an enduring "
                "circumstance; do not use it for preferences or temporary project "
                "state."
            ),
        ),
    ),
    MemoryScope.RELATIONSHIP: (
        KindDefinition(
            kind=MemoryKind.PERSPECTIVE,
            guidance=(
                "Record the user's viewpoint, feeling, or assessment about a person, "
                "group, or relationship."
            ),
        ),
        KindDefinition(
            kind=MemoryKind.SUMMARY,
            guidance=(
                "Summarize durable context about a person, group, or relationship "
                "from the user's perspective; do not present it as objective biography."
            ),
        ),
    ),
    MemoryScope.PREFERENCE: (
        KindDefinition(
            kind=MemoryKind.PREFERENCE,
            guidance=(
                "Record a choice the user explicitly wants respected, including what "
                "they prefer or avoid."
            ),
        ),
    ),
    MemoryScope.PRACTICE: (
        KindDefinition(
            kind=MemoryKind.PRACTICE,
            guidance=(
                "Record a routine, method, habit, or actual way the user works; "
                "describe stated or observed practice rather than an aspiration."
            ),
        ),
    ),
    MemoryScope.PROJECT: (
        KindDefinition(
            kind=MemoryKind.DECISION,
            guidance=(
                "Record a choice made for the project and the rationale or "
                "consequences that should guide later work."
            ),
        ),
        KindDefinition(
            kind=MemoryKind.CONSTRAINT,
            guidance=(
                "Record a project boundary, requirement, limitation, or "
                "non-negotiable that restricts valid choices."
            ),
        ),
        KindDefinition(
            kind=MemoryKind.STATE,
            guidance=(
                "Record the project's current condition or status; revise it when "
                "that condition changes."
            ),
        ),
        KindDefinition(
            kind=MemoryKind.EVENT,
            guidance=(
                "Record a completed project occurrence at its known occurrence time; "
                "use state for a current condition."
            ),
        ),
        KindDefinition(
            kind=MemoryKind.QUESTION,
            guidance=(
                "Record an unresolved project question whose answer could change "
                "direction or implementation."
            ),
        ),
        KindDefinition(
            kind=MemoryKind.REFERENCE,
            guidance=(
                "Record project-specific approved reference material needed to "
                "execute or understand this project."
            ),
        ),
        KindDefinition(
            kind=MemoryKind.SUMMARY,
            guidance=(
                "Summarize the project's durable context, progress, or design "
                "without replacing more precise decisions, constraints, states, or "
                "questions."
            ),
        ),
    ),
    MemoryScope.KNOWLEDGE: (
        KindDefinition(
            kind=MemoryKind.REFERENCE,
            guidance=(
                "Record user-approved reusable reference material for a topic beyond "
                "one project; do not store ordinary general knowledge."
            ),
        ),
        KindDefinition(
            kind=MemoryKind.SUMMARY,
            guidance=(
                "Summarize user-approved reusable material about a topic beyond one "
                "project; do not store ordinary general knowledge."
            ),
        ),
    ),
}
ALLOWED_KINDS = {
    scope: tuple(definition.kind for definition in definitions)
    for scope, definitions in KIND_DEFINITIONS.items()
}

V1_FIELDS = {"schema_version", "id", "title", "content", "tags"}
V2_FIELDS = {
    "schema_version",
    "id",
    "scope",
    "namespace",
    "collection",
    "kind",
    "language",
    "title",
    "content",
    "tags",
    "provenance",
    "lifecycle",
    "created_at",
    "updated_at",
    "occurred_at",
}
V2_REQUIRED_FIELDS = V2_FIELDS - {"occurred_at"}
TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
EnumValue = TypeVar("EnumValue", bound=StrEnum)


def _invalid(field: str) -> MemoryValidationError:
    return MemoryValidationError("invalid_record", field, f"invalid {field}")


def _expect_object(
    value: object,
    *,
    field: str,
    fields: set[str],
    required: set[str] | None = None,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _invalid(field)
    keys = set(value)
    if keys - fields or (required is not None and not required <= keys):
        raise _invalid(field)
    return value


def _parse_enum(
    enum_type: type[EnumValue],
    value: object,
    field: str,
) -> EnumValue:
    if not isinstance(value, str):
        raise _invalid(field)
    try:
        return enum_type(value)
    except ValueError as error:
        raise _invalid(field) from error


def _parse_timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str) or TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise _invalid(field)
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise _invalid(field) from error
    return parsed.replace(tzinfo=timezone.utc)


def _serialize_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class LegacyMemoryRecordV1:
    id: str
    title: str | None
    content: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class MemoryNamespace:
    kind: str
    id: str
    label: str | None


@dataclass(frozen=True)
class MemoryCollection:
    id: str
    label: str | None


@dataclass(frozen=True)
class MemoryProvenance:
    origin: MemoryOrigin
    recorded_via: MemoryRecordedVia


@dataclass(frozen=True)
class MemoryLifecycle:
    state: LifecycleState
    revision: int


DuplicateKey = tuple[
    str,
    str,
    str,
    str | None,
    str,
    datetime | None,
    str | None,
    str,
    tuple[str, ...],
]


def _duplicate_key(
    *,
    scope: MemoryScope,
    namespace: MemoryNamespace,
    collection: MemoryCollection | None,
    kind: MemoryKind,
    occurred_at: datetime | None,
    title: str | None,
    content: str,
    tags: tuple[str, ...],
) -> DuplicateKey:
    return (
        scope.value,
        namespace.kind,
        namespace.id,
        collection.id if collection is not None else None,
        kind.value,
        occurred_at,
        title,
        content,
        normalized_tag_key(tags),
    )


@dataclass(frozen=True)
class MemoryRecordV2:
    id: str
    scope: MemoryScope
    namespace: MemoryNamespace
    collection: MemoryCollection | None
    kind: MemoryKind
    language: str
    title: str | None
    content: str
    tags: tuple[str, ...]
    provenance: MemoryProvenance
    lifecycle: MemoryLifecycle
    created_at: datetime
    updated_at: datetime
    occurred_at: datetime | None = None

    def duplicate_key(self) -> DuplicateKey:
        return _duplicate_key(
            scope=self.scope,
            namespace=self.namespace,
            collection=self.collection,
            kind=self.kind,
            occurred_at=self.occurred_at,
            title=self.title,
            content=self.content,
            tags=self.tags,
        )


@dataclass(frozen=True)
class MemoryReference:
    scope: MemoryScope
    namespace_id: str
    collection_id: str | None
    id: str

    @classmethod
    def from_dict(cls, value: object) -> "MemoryReference":
        payload = _expect_object(
            value,
            field="reference",
            fields={"scope", "namespace_id", "collection_id", "id"},
            required={"scope", "namespace_id", "collection_id", "id"},
        )
        return cls(
            scope=parse_scope(payload["scope"]),
            namespace_id=normalize_identifier(
                payload["namespace_id"],
                field="namespace.id",
            ),
            collection_id=(
                None
                if payload["collection_id"] is None
                else normalize_identifier(
                    payload["collection_id"],
                    field="collection.id",
                )
            ),
            id=normalize_memory_id(payload["id"]),
        )


@dataclass(frozen=True)
class LegacyMemoryReference:
    scope: MemoryScope
    id: str

    @classmethod
    def from_dict(cls, value: object) -> "LegacyMemoryReference":
        payload = _expect_object(
            value,
            field="reference",
            fields={"scope", "id"},
            required={"scope", "id"},
        )
        return cls(
            scope=parse_scope(payload["scope"]),
            id=normalize_memory_id(payload["id"], legacy=True),
        )


@dataclass(frozen=True)
class MemoryDraft:
    scope: MemoryScope
    namespace: MemoryNamespace
    collection: MemoryCollection | None
    kind: MemoryKind
    language: str
    title: str | None
    content: str
    tags: tuple[str, ...]
    origin: MemoryOrigin
    occurred_at: datetime | None = None

    @classmethod
    def from_dict(cls, value: object) -> "MemoryDraft":
        payload = _expect_object(
            value,
            field="draft",
            fields={
                "scope",
                "namespace",
                "collection",
                "kind",
                "language",
                "title",
                "content",
                "tags",
                "origin",
                "occurred_at",
            },
            required={
                "scope",
                "namespace",
                "collection",
                "kind",
                "language",
                "title",
                "content",
                "tags",
                "origin",
            },
        )
        scope = parse_scope(payload["scope"])
        namespace = _parse_namespace(payload["namespace"])
        collection = _parse_collection(payload["collection"])
        kind = _parse_kind(payload["kind"])
        _validate_scope_dimensions(scope, namespace, kind)
        occurred_at = _parse_occurrence(payload, kind)
        origin = _parse_enum(MemoryOrigin, payload["origin"], "origin")
        return cls(
            scope=scope,
            namespace=namespace,
            collection=collection,
            kind=kind,
            language=normalize_language(payload["language"]),
            title=normalize_optional_text(
                payload["title"], field="title", maximum_length=200
            ),
            content=normalize_required_text(
                payload["content"], field="content", maximum_length=4_000
            ),
            tags=normalize_tags(payload["tags"]),
            origin=origin,
            occurred_at=occurred_at,
        )

    def duplicate_key(self) -> DuplicateKey:
        return _duplicate_key(
            scope=self.scope,
            namespace=self.namespace,
            collection=self.collection,
            kind=self.kind,
            occurred_at=self.occurred_at,
            title=self.title,
            content=self.content,
            tags=self.tags,
        )


@dataclass(frozen=True)
class MemoryRevision:
    expected_revision: int
    namespace_label: str | None
    collection_label: str | None
    title: str | None
    content: str
    tags: tuple[str, ...]

    @classmethod
    def from_dict(cls, value: object) -> "MemoryRevision":
        fields = {
            "expected_revision",
            "namespace_label",
            "collection_label",
            "title",
            "content",
            "tags",
        }
        payload = _expect_object(
            value,
            field="revision",
            fields=fields,
            required=fields,
        )
        expected_revision = payload["expected_revision"]
        if type(expected_revision) is not int or expected_revision < 1:
            raise _invalid("expected_revision")
        return cls(
            expected_revision=expected_revision,
            namespace_label=normalize_optional_text(
                payload["namespace_label"],
                field="namespace.label",
                maximum_length=100,
            ),
            collection_label=normalize_optional_text(
                payload["collection_label"],
                field="collection.label",
                maximum_length=100,
            ),
            title=normalize_optional_text(
                payload["title"], field="title", maximum_length=200
            ),
            content=normalize_required_text(
                payload["content"], field="content", maximum_length=4_000
            ),
            tags=normalize_tags(payload["tags"]),
        )


def _parse_namespace(value: object) -> MemoryNamespace:
    payload = _expect_object(
        value,
        field="namespace",
        fields={"kind", "id", "label"},
        required={"kind", "id", "label"},
    )
    kind = payload["kind"]
    if not isinstance(kind, str):
        raise MemoryValidationError(
            "invalid_namespace",
            "namespace.kind",
            "invalid namespace.kind",
        )
    return MemoryNamespace(
        kind=kind,
        id=normalize_identifier(payload["id"], field="namespace.id"),
        label=normalize_optional_text(
            payload["label"],
            field="namespace.label",
            maximum_length=100,
        ),
    )


def _parse_collection(value: object) -> MemoryCollection | None:
    if value is None:
        return None
    payload = _expect_object(
        value,
        field="collection",
        fields={"id", "label"},
        required={"id", "label"},
    )
    return MemoryCollection(
        id=normalize_identifier(payload["id"], field="collection.id"),
        label=normalize_optional_text(
            payload["label"],
            field="collection.label",
            maximum_length=100,
        ),
    )


def _parse_kind(value: object) -> MemoryKind:
    try:
        return MemoryKind(value)
    except (TypeError, ValueError) as error:
        raise MemoryValidationError(
            "invalid_kind",
            "kind",
            "invalid kind",
        ) from error


def _parse_occurrence(
    payload: dict[str, Any],
    kind: MemoryKind,
) -> datetime | None:
    present = "occurred_at" in payload
    if kind is MemoryKind.EVENT:
        if not present:
            raise _invalid("occurred_at")
        return _parse_timestamp(payload["occurred_at"], "occurred_at")
    if present:
        raise _invalid("occurred_at")
    return None


def _validate_scope_dimensions(
    scope: MemoryScope,
    namespace: MemoryNamespace,
    kind: MemoryKind,
) -> None:
    if namespace.kind not in get_scope_definition(scope).namespace_kinds:
        raise MemoryValidationError(
            "invalid_namespace",
            "namespace.kind",
            "namespace kind is invalid for scope",
        )
    if kind not in ALLOWED_KINDS[scope]:
        raise MemoryValidationError(
            "invalid_kind",
            "kind",
            "memory kind is invalid for scope",
        )


def _parse_v1(payload: dict[str, Any]) -> LegacyMemoryRecordV1:
    if set(payload) - V1_FIELDS or not {"schema_version", "id", "content"} <= set(
        payload
    ):
        raise _invalid("record")
    record_id = normalize_memory_id(payload["id"], legacy=True)
    content = payload["content"]
    if not isinstance(content, str) or not content.strip() or len(content) > 4_000:
        raise _invalid("content")
    title = payload.get("title")
    if title is not None and (
        not isinstance(title, str) or not title.strip() or len(title) > 200
    ):
        raise _invalid("title")
    raw_tags = payload.get("tags", [])
    if (
        not isinstance(raw_tags, list)
        or ("tags" in payload and not 1 <= len(raw_tags) <= 10)
        or any(
            not isinstance(tag, str) or not tag.strip() or len(tag) > 50
            for tag in raw_tags
        )
        or len(set(raw_tags)) != len(raw_tags)
    ):
        raise _invalid("tags")
    return LegacyMemoryRecordV1(
        id=record_id,
        title=title,
        content=content,
        tags=tuple(raw_tags),
    )


def _parse_v2(payload: dict[str, Any]) -> MemoryRecordV2:
    if set(payload) - V2_FIELDS or not V2_REQUIRED_FIELDS <= set(payload):
        raise _invalid("record")
    scope = parse_scope(payload["scope"])
    namespace = _parse_namespace(payload["namespace"])
    collection = _parse_collection(payload["collection"])
    kind = _parse_kind(payload["kind"])
    _validate_scope_dimensions(scope, namespace, kind)
    occurred_at = _parse_occurrence(payload, kind)

    provenance_payload = _expect_object(
        payload["provenance"],
        field="provenance",
        fields={"origin", "recorded_via"},
        required={"origin", "recorded_via"},
    )
    lifecycle_payload = _expect_object(
        payload["lifecycle"],
        field="lifecycle",
        fields={"state", "revision"},
        required={"state", "revision"},
    )
    origin = _parse_enum(
        MemoryOrigin,
        provenance_payload["origin"],
        "provenance.origin",
    )
    recorded_via = _parse_enum(
        MemoryRecordedVia,
        provenance_payload["recorded_via"],
        "provenance.recorded_via",
    )
    state = _parse_enum(
        LifecycleState,
        lifecycle_payload["state"],
        "lifecycle.state",
    )
    revision = lifecycle_payload["revision"]
    if type(revision) is not int or revision < 1:
        raise _invalid("lifecycle.revision")
    created_at = _parse_timestamp(payload["created_at"], "created_at")
    updated_at = _parse_timestamp(payload["updated_at"], "updated_at")
    if updated_at < created_at:
        raise _invalid("updated_at")

    return MemoryRecordV2(
        id=normalize_memory_id(payload["id"]),
        scope=scope,
        namespace=namespace,
        collection=collection,
        kind=kind,
        language=normalize_language(payload["language"]),
        title=normalize_optional_text(
            payload["title"], field="title", maximum_length=200
        ),
        content=normalize_required_text(
            payload["content"], field="content", maximum_length=4_000
        ),
        tags=normalize_tags(payload["tags"]),
        provenance=MemoryProvenance(
            origin=origin,
            recorded_via=recorded_via,
        ),
        lifecycle=MemoryLifecycle(state=state, revision=revision),
        created_at=created_at,
        updated_at=updated_at,
        occurred_at=occurred_at,
    )


def parse_memory_record(payload: object) -> LegacyMemoryRecordV1 | MemoryRecordV2:
    record = _expect_object(
        payload,
        field="record",
        fields=V1_FIELDS | V2_FIELDS,
    )
    schema_version = record.get("schema_version")
    if type(schema_version) is not int:
        raise _invalid("schema_version")
    if schema_version == 1:
        return _parse_v1(record)
    if schema_version == 2:
        return _parse_v2(record)
    raise _invalid("schema_version")


def serialize_memory_record(
    record: LegacyMemoryRecordV1 | MemoryRecordV2,
) -> dict[str, Any]:
    if isinstance(record, LegacyMemoryRecordV1):
        payload: dict[str, Any] = {
            "schema_version": 1,
            "id": record.id,
        }
        if record.title is not None:
            payload["title"] = record.title
        payload["content"] = record.content
        if record.tags:
            payload["tags"] = list(record.tags)
        return payload

    payload: dict[str, Any] = {
        "schema_version": 2,
        "id": record.id,
        "scope": record.scope.value,
        "namespace": {
            "kind": record.namespace.kind,
            "id": record.namespace.id,
            "label": record.namespace.label,
        },
        "collection": (
            None
            if record.collection is None
            else {
                "id": record.collection.id,
                "label": record.collection.label,
            }
        ),
        "kind": record.kind.value,
        "language": record.language,
        "title": record.title,
        "content": record.content,
        "tags": list(record.tags),
        "provenance": {
            "origin": record.provenance.origin.value,
            "recorded_via": record.provenance.recorded_via.value,
        },
        "lifecycle": {
            "state": record.lifecycle.state.value,
            "revision": record.lifecycle.revision,
        },
        "created_at": _serialize_timestamp(record.created_at),
        "updated_at": _serialize_timestamp(record.updated_at),
    }
    if record.occurred_at is not None:
        payload["occurred_at"] = _serialize_timestamp(record.occurred_at)
    return payload
