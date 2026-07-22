from collections.abc import Callable
import json
import logging
from typing import Any

from mymcp.memory.errors import (
    AmbiguousMemoryReference,
    CandidateLimitExceeded,
    MemoryNotFound,
    MemorySourceUnavailable,
    MemoryValidationError,
    UnsafeMemoryPath,
)
from mymcp.memory.records import (
    LegacyMemoryRecordV1,
    LegacyMemoryReference,
    MemoryRecordV2,
    MemoryReference,
    serialize_memory_record,
)


logger = logging.getLogger("mcp.memory_inspect")


InspectReference = MemoryReference | LegacyMemoryReference
InspectRecord = MemoryRecordV2 | LegacyMemoryRecordV1
InspectOperation = Callable[[InspectReference], InspectRecord]
VALIDATION_FIELDS = {
    "reference": "reference",
    "scope": "reference.scope",
    "namespace.id": "reference.namespace_id",
    "collection.id": "reference.collection_id",
    "id": "reference.id",
}


def _invalid_reference() -> MemoryValidationError:
    return MemoryValidationError(
        "invalid_record",
        "reference",
        "invalid reference",
    )


def _parse_reference(arguments: object) -> InspectReference:
    if not isinstance(arguments, dict) or set(arguments) != {"reference"}:
        raise _invalid_reference()

    raw_reference = arguments["reference"]
    if not isinstance(raw_reference, dict):
        raise _invalid_reference()

    schema_version = raw_reference.get("schema_version")
    if type(schema_version) is not int or schema_version not in {1, 2}:
        raise _invalid_reference()

    reference = dict(raw_reference)
    del reference["schema_version"]
    if schema_version == 2:
        return MemoryReference.from_dict(reference)
    return LegacyMemoryReference.from_dict(reference)


def _text_content(payload: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "type": "text",
            "text": json.dumps(payload, separators=(",", ":")),
        }
    ]


def _error(
    *,
    status: str,
    code: str,
    message: str,
    field: str | None = None,
) -> dict[str, Any]:
    payload = {"status": status, "code": code}
    if field is not None:
        payload["field"] = field
    payload["message"] = message
    return {"content": _text_content(payload), "isError": True}


def _log_outcome(
    level: int,
    outcome: str,
    *,
    code: str | None = None,
    field: str | None = None,
    reference: InspectReference | None = None,
) -> None:
    message = f"event=memory_inspect outcome={outcome}"
    values: list[object] = []
    if code is not None:
        message += " code=%s"
        values.append(code)
    if field is not None:
        message += " field=%s"
        values.append(field)
    if reference is not None:
        message += " schema_version=%s scope=%s"
        values.extend(
            [
                2 if isinstance(reference, MemoryReference) else 1,
                reference.scope.value,
            ]
        )
    logger.log(level, message, *values)


def _serialize_memory(
    reference: InspectReference,
    memory: InspectRecord,
) -> dict[str, Any]:
    if isinstance(reference, MemoryReference):
        if not isinstance(memory, MemoryRecordV2):
            raise TypeError("inspection reference and record versions differ")
        serialized = serialize_memory_record(memory)
        public_reference = {
            "schema_version": 2,
            "scope": memory.scope.value,
            "namespace_id": memory.namespace.id,
            "collection_id": (
                memory.collection.id if memory.collection is not None else None
            ),
            "id": memory.id,
        }
    else:
        if not isinstance(memory, LegacyMemoryRecordV1):
            raise TypeError("inspection reference and record versions differ")
        serialized = serialize_memory_record(memory)
        serialized["title"] = memory.title
        serialized["tags"] = list(memory.tags)
        public_reference = {
            "schema_version": 1,
            "scope": reference.scope.value,
            "id": memory.id,
        }
    return {"reference": public_reference, **serialized}


def handle(
    arguments: dict[str, Any],
    *,
    inspect_operation: InspectOperation,
) -> dict[str, Any]:
    try:
        reference = _parse_reference(arguments)
    except MemoryValidationError as error:
        field = VALIDATION_FIELDS.get(error.field, "reference")
        _log_outcome(
            logging.WARNING,
            "invalid_request",
            code="invalid_reference",
            field=field,
        )
        return _error(
            status="invalid_request",
            code="invalid_reference",
            field=field,
            message="reference is invalid",
        )

    try:
        memory = inspect_operation(reference)
        serialized = _serialize_memory(reference, memory)
    except MemoryValidationError as error:
        field = VALIDATION_FIELDS.get(error.field, "reference")
        _log_outcome(
            logging.WARNING,
            "invalid_request",
            code="invalid_reference",
            field=field,
            reference=reference,
        )
        return _error(
            status="invalid_request",
            code="invalid_reference",
            field=field,
            message="reference is invalid",
        )
    except MemoryNotFound:
        _log_outcome(
            logging.INFO,
            "not_found",
            code="not_found",
            reference=reference,
        )
        return _error(
            status="not_found",
            code="not_found",
            message="memory was not found",
        )
    except AmbiguousMemoryReference:
        _log_outcome(
            logging.WARNING,
            "conflict",
            code="ambiguous_reference",
            reference=reference,
        )
        return _error(
            status="conflict",
            code="ambiguous_reference",
            message="legacy memory reference is ambiguous",
        )
    except CandidateLimitExceeded:
        _log_outcome(
            logging.WARNING,
            "storage_error",
            code="candidate_limit_exceeded",
            reference=reference,
        )
        return _error(
            status="storage_error",
            code="candidate_limit_exceeded",
            message="memory scope contains more than 1000 candidate files",
        )
    except (UnsafeMemoryPath, MemorySourceUnavailable, OSError):
        _log_outcome(
            logging.WARNING,
            "storage_error",
            code="memory_source_unavailable",
            reference=reference,
        )
        return _error(
            status="storage_error",
            code="memory_source_unavailable",
            message="memory could not be inspected",
        )
    except Exception:
        _log_outcome(
            logging.ERROR,
            "internal_error",
            code="internal_error",
            reference=reference,
        )
        return _error(
            status="internal_error",
            code="internal_error",
            message="memory could not be inspected",
        )

    _log_outcome(logging.INFO, "ok", reference=reference)
    return {"content": _text_content({"status": "ok", "memory": serialized})}
