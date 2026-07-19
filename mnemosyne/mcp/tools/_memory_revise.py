from copy import deepcopy
from dataclasses import dataclass
import logging
from collections.abc import Callable
from typing import Any

from mnemosyne.mcp.tools._memory_lifecycle import (
    lifecycle_input_schema,
    parse_lifecycle_request,
    text_result,
)
from mnemosyne.memory.errors import (
    DisallowedMemoryContent,
    MemoryNotFound,
    MemorySourceUnavailable,
    MemoryValidationError,
    MutationDisabled,
    ReplacementOutcomeUncertain,
    RevisionConflict,
    UnsafeMemoryPath,
    WriteConflict,
)
from mnemosyne.memory.records import MemoryReference, MemoryRevision
from mnemosyne.memory.service import MemoryResult


REPLACEMENT_FIELDS = {
    "namespace_label",
    "collection_label",
    "title",
    "content",
    "tags",
}
REQUEST_FIELDS = {"reference", "expected_revision"} | REPLACEMENT_FIELDS
REQUIRED_FIELDS = [
    "reference",
    "expected_revision",
    "namespace_label",
    "collection_label",
    "title",
    "content",
    "tags",
]


def _nullable_text(maximum_length: int) -> dict[str, object]:
    return {
        "anyOf": [
            {
                "type": "string",
                "minLength": 1,
                "maxLength": maximum_length,
                "pattern": "\\S",
            },
            {"type": "null"},
        ]
    }


def revise_input_schema() -> dict[str, object]:
    lifecycle_schema = lifecycle_input_schema()
    properties = deepcopy(lifecycle_schema["properties"])
    properties.update(
        {
            "namespace_label": _nullable_text(100),
            "collection_label": _nullable_text(100),
            "title": _nullable_text(200),
            "content": {
                "type": "string",
                "minLength": 1,
                "maxLength": 4_000,
                "pattern": "\\S",
            },
            "tags": {
                "type": "array",
                "items": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 50,
                    "pattern": "\\S",
                },
                "minItems": 0,
                "maxItems": 10,
                "uniqueItems": True,
            },
        }
    )
    return {
        "type": "object",
        "properties": properties,
        "required": REQUIRED_FIELDS,
        "additionalProperties": False,
    }


@dataclass(frozen=True)
class ReviseRequest:
    reference: MemoryReference
    revision: MemoryRevision


ReviseOperation = Callable[[MemoryReference, MemoryRevision], MemoryResult]


def _invalid_revision(field: str = "revision") -> MemoryValidationError:
    return MemoryValidationError(
        "invalid_record",
        field,
        "revision field is invalid",
    )


def parse_revise_request(arguments: object) -> ReviseRequest:
    if not isinstance(arguments, dict):
        raise _invalid_revision()
    if set(arguments) - REQUEST_FIELDS:
        raise _invalid_revision()
    if "reference" not in arguments:
        raise MemoryValidationError(
            "invalid_reference",
            "reference",
            "reference is invalid",
        )
    if "expected_revision" not in arguments:
        raise MemoryValidationError(
            "invalid_expected_revision",
            "expected_revision",
            "expected revision is invalid",
        )
    if not REPLACEMENT_FIELDS <= set(arguments):
        raise _invalid_revision()

    lifecycle_request = parse_lifecycle_request(
        {
            "reference": arguments["reference"],
            "expected_revision": arguments["expected_revision"],
        }
    )
    try:
        revision = MemoryRevision.from_dict(
            {
                "expected_revision": arguments["expected_revision"],
                **{field: arguments[field] for field in REPLACEMENT_FIELDS},
            }
        )
    except MemoryValidationError as error:
        fields = {
            "namespace.label": "namespace_label",
            "collection.label": "collection_label",
            "title": "title",
            "content": "content",
            "tags": "tags",
            "expected_revision": "expected_revision",
        }
        field = fields.get(error.field, "revision")
        if field == "expected_revision":
            raise MemoryValidationError(
                "invalid_expected_revision",
                field,
                "expected revision is invalid",
            ) from None
        raise _invalid_revision(field) from None
    return ReviseRequest(
        reference=lifecycle_request.reference,
        revision=revision,
    )


def _result_reference(result: MemoryResult) -> MemoryReference:
    memory = result.memory
    return MemoryReference(
        scope=memory.scope,
        namespace_id=memory.namespace.id,
        collection_id=memory.collection.id if memory.collection is not None else None,
        id=memory.id,
    )


def _validate_result(request: ReviseRequest, result: MemoryResult) -> None:
    if result.status not in {"revised", "already_current"}:
        raise TypeError("unexpected revise result status")
    memory = result.memory
    revision = request.revision
    expected_revision = revision.expected_revision + (
        1 if result.status == "revised" else 0
    )
    if (
        _result_reference(result) != request.reference
        or memory.namespace.label != revision.namespace_label
        or (
            memory.collection.label if memory.collection is not None else None
        )
        != revision.collection_label
        or memory.title != revision.title
        or memory.content != revision.content
        or memory.tags != revision.tags
        or memory.lifecycle.revision != expected_revision
    ):
        raise TypeError("unexpected revise result projection")


def _serialize_result(result: MemoryResult) -> dict[str, Any]:
    memory = result.memory
    reference = _result_reference(result)
    return text_result(
        {
            "status": result.status,
            "reference": {
                "schema_version": 2,
                "scope": reference.scope.value,
                "namespace_id": reference.namespace_id,
                "collection_id": reference.collection_id,
                "id": reference.id,
            },
            "lifecycle": {
                "state": memory.lifecycle.state.value,
                "revision": memory.lifecycle.revision,
            },
        }
    )


def _log_outcome(
    logger: logging.Logger,
    level: int,
    outcome: str,
    *,
    code: str | None = None,
    field: str | None = None,
    request: ReviseRequest | None = None,
    result: MemoryResult | None = None,
) -> None:
    message = f"event=memory_revise outcome={outcome}"
    values: list[object] = []
    if code is not None:
        message += " code=%s"
        values.append(code)
    if field is not None:
        message += " field=%s"
        values.append(field)
    if request is not None:
        message += " schema_version=2 scope=%s"
        values.append(request.reference.scope.value)
    if result is not None:
        message += " lifecycle_state=%s revision=%s"
        values.extend(
            [
                result.memory.lifecycle.state.value,
                result.memory.lifecycle.revision,
            ]
        )
    logger.log(level, message, *values)


def _error_result(
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
    return text_result(payload, is_error=True)


def _validation_error(error: MemoryValidationError) -> tuple[str, str, str]:
    if error.code == "invalid_collection":
        return (
            "invalid_collection",
            "collection_label",
            "collection label is invalid for memory",
        )
    fields = {
        "namespace.label": "namespace_label",
        "collection.label": "collection_label",
        "title": "title",
        "content": "content",
        "tags": "tags",
        "expected_revision": "expected_revision",
    }
    field = fields.get(error.field, "revision")
    if field == "expected_revision":
        return (
            "invalid_expected_revision",
            field,
            "expected revision is invalid",
        )
    return ("invalid_record", field, "revision field is invalid")


def execute_revise(
    arguments: object,
    *,
    mutations_enabled: bool,
    revise_operation: ReviseOperation,
    logger: logging.Logger,
) -> dict[str, Any]:
    try:
        request = parse_revise_request(arguments)
    except MemoryValidationError as error:
        _log_outcome(
            logger,
            logging.WARNING,
            "invalid_request",
            code=error.code,
            field=error.field,
        )
        return _error_result(
            status="invalid_request",
            code=error.code,
            field=error.field,
            message=error.message,
        )

    if not mutations_enabled:
        _log_outcome(
            logger,
            logging.WARNING,
            "policy_error",
            code="mutation_disabled",
            request=request,
        )
        return _error_result(
            status="policy_error",
            code="mutation_disabled",
            message="memory revise is disabled",
        )

    try:
        result = revise_operation(request.reference, request.revision)
        _validate_result(request, result)
    except MemoryValidationError as error:
        code, field, message = _validation_error(error)
        _log_outcome(
            logger,
            logging.WARNING,
            "invalid_request",
            code=code,
            field=field,
            request=request,
        )
        return _error_result(
            status="invalid_request",
            code=code,
            field=field,
            message=message,
        )
    except DisallowedMemoryContent:
        _log_outcome(logger, logging.WARNING, "refused", code="disallowed_content", request=request)
        return _error_result(
            status="refused",
            code="disallowed_content",
            message="memory contains content that Mnemosyne does not store",
        )
    except MutationDisabled:
        _log_outcome(logger, logging.WARNING, "policy_error", code="mutation_disabled", request=request)
        return _error_result(
            status="policy_error",
            code="mutation_disabled",
            message="memory revise is disabled",
        )
    except MemoryNotFound:
        _log_outcome(logger, logging.WARNING, "not_found", code="not_found", request=request)
        return _error_result(
            status="not_found",
            code="not_found",
            message="memory to revise was not found",
        )
    except RevisionConflict:
        _log_outcome(logger, logging.WARNING, "conflict", code="revision_conflict", request=request)
        return _error_result(
            status="conflict",
            code="revision_conflict",
            message="memory to revise is not at the expected revision",
        )
    except WriteConflict:
        _log_outcome(logger, logging.WARNING, "conflict", code="write_conflict", request=request)
        return _error_result(
            status="conflict",
            code="write_conflict",
            message="memory changed before it could be revised",
        )
    except ReplacementOutcomeUncertain:
        _log_outcome(
            logger,
            logging.WARNING,
            "uncertain",
            code="replacement_outcome_uncertain",
            request=request,
        )
        return _error_result(
            status="uncertain",
            code="replacement_outcome_uncertain",
            message=(
                "memory revise outcome is uncertain; inspect the same reference "
                "before any retry"
            ),
        )
    except (UnsafeMemoryPath, MemorySourceUnavailable, OSError):
        _log_outcome(
            logger,
            logging.WARNING,
            "storage_error",
            code="memory_source_unavailable",
            request=request,
        )
        return _error_result(
            status="storage_error",
            code="memory_source_unavailable",
            message="memory could not be revised",
        )
    except Exception:
        _log_outcome(
            logger,
            logging.ERROR,
            "internal_error",
            code="internal_error",
            request=request,
        )
        return _error_result(
            status="internal_error",
            code="internal_error",
            message="memory could not be revised",
        )

    _log_outcome(
        logger,
        logging.INFO,
        result.status,
        request=request,
        result=result,
    )
    return _serialize_result(result)
