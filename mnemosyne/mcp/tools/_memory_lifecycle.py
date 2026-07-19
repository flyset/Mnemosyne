from dataclasses import dataclass
import json
import logging
from collections.abc import Callable
from typing import Any

from mnemosyne.memory.errors import (
    MemoryNotFound,
    MemorySourceUnavailable,
    MemoryValidationError,
    MutationDisabled,
    ReplacementOutcomeUncertain,
    RevisionConflict,
    UnsafeMemoryPath,
    WriteConflict,
)
from mnemosyne.memory.normalization import IDENTIFIER_PATTERN, MEMORY_ID_PATTERN
from mnemosyne.memory.records import MemoryReference
from mnemosyne.memory.scopes import SCOPE_DEFINITIONS
from mnemosyne.memory.service import MemoryResult


IDENTIFIER_SCHEMA = {
    "type": "string",
    "pattern": f"^{IDENTIFIER_PATTERN.pattern}$",
}


def _scope_schema() -> dict[str, object]:
    return {
        "oneOf": [
            {
                "const": definition.scope.value,
                "description": definition.description,
            }
            for definition in SCOPE_DEFINITIONS
        ]
    }


def lifecycle_input_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "reference": {
                "type": "object",
                "properties": {
                    "schema_version": {"const": 2},
                    "scope": _scope_schema(),
                    "namespace_id": IDENTIFIER_SCHEMA,
                    "collection_id": {
                        "oneOf": [IDENTIFIER_SCHEMA, {"type": "null"}]
                    },
                    "id": {
                        "type": "string",
                        "pattern": f"^{MEMORY_ID_PATTERN.pattern}$",
                    },
                },
                "required": [
                    "schema_version",
                    "scope",
                    "namespace_id",
                    "collection_id",
                    "id",
                ],
                "additionalProperties": False,
            },
            "expected_revision": {"type": "integer", "minimum": 1},
        },
        "required": ["reference", "expected_revision"],
        "additionalProperties": False,
    }


@dataclass(frozen=True)
class LifecycleRequest:
    reference: MemoryReference
    expected_revision: int


def _invalid_reference(field: str = "reference") -> MemoryValidationError:
    return MemoryValidationError(
        "invalid_reference",
        field,
        "reference is invalid",
    )


def _invalid_expected_revision() -> MemoryValidationError:
    return MemoryValidationError(
        "invalid_expected_revision",
        "expected_revision",
        "expected revision is invalid",
    )


def parse_lifecycle_request(arguments: object) -> LifecycleRequest:
    if not isinstance(arguments, dict):
        raise _invalid_reference()
    if set(arguments) - {"reference", "expected_revision"}:
        raise _invalid_reference()
    if "reference" not in arguments:
        raise _invalid_reference()
    if "expected_revision" not in arguments:
        raise _invalid_expected_revision()

    raw_reference = arguments["reference"]
    if (
        not isinstance(raw_reference, dict)
        or type(raw_reference.get("schema_version")) is not int
        or raw_reference["schema_version"] != 2
    ):
        raise _invalid_reference()
    reference_payload = dict(raw_reference)
    del reference_payload["schema_version"]
    try:
        reference = MemoryReference.from_dict(reference_payload)
    except MemoryValidationError as error:
        fields = {
            "scope": "reference.scope",
            "namespace.id": "reference.namespace_id",
            "collection.id": "reference.collection_id",
            "id": "reference.id",
        }
        raise _invalid_reference(fields.get(error.field, "reference")) from None

    expected_revision = arguments["expected_revision"]
    if type(expected_revision) is not int or expected_revision < 1:
        raise _invalid_expected_revision()
    return LifecycleRequest(
        reference=reference,
        expected_revision=expected_revision,
    )


def text_result(payload: dict[str, Any], *, is_error: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, separators=(",", ":")),
            }
        ]
    }
    if is_error:
        result["isError"] = True
    return result


LifecycleOperation = Callable[[MemoryReference, int], MemoryResult]


def _log_outcome(
    logger: logging.Logger,
    operation: str,
    level: int,
    outcome: str,
    *,
    code: str | None = None,
    field: str | None = None,
    request: LifecycleRequest | None = None,
    result: MemoryResult | None = None,
) -> None:
    message = f"event=memory_{operation} outcome={outcome}"
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


def _error_payload(
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


def _serialize_result(result: MemoryResult) -> dict[str, Any]:
    memory = result.memory
    return text_result(
        {
            "status": result.status,
            "reference": {
                "schema_version": 2,
                "scope": memory.scope.value,
                "namespace_id": memory.namespace.id,
                "collection_id": (
                    memory.collection.id if memory.collection is not None else None
                ),
                "id": memory.id,
            },
            "lifecycle": {
                "state": memory.lifecycle.state.value,
                "revision": memory.lifecycle.revision,
            },
        }
    )


def _validate_result(
    operation: str,
    request: LifecycleRequest,
    result: MemoryResult,
) -> None:
    changed_status = "archived" if operation == "archive" else "restored"
    idempotent_status = (
        "already_archived" if operation == "archive" else "already_active"
    )
    expected_state = "archived" if operation == "archive" else "active"
    if result.status not in {changed_status, idempotent_status}:
        raise TypeError("unexpected lifecycle result status")
    memory = result.memory
    result_reference = MemoryReference(
        scope=memory.scope,
        namespace_id=memory.namespace.id,
        collection_id=(
            memory.collection.id if memory.collection is not None else None
        ),
        id=memory.id,
    )
    expected_revision = request.expected_revision + (
        1 if result.status == changed_status else 0
    )
    if (
        result_reference != request.reference
        or memory.lifecycle.state.value != expected_state
        or memory.lifecycle.revision != expected_revision
    ):
        raise TypeError("unexpected lifecycle result projection")


def execute_lifecycle(
    arguments: object,
    *,
    operation: str,
    mutations_enabled: bool,
    lifecycle_operation: LifecycleOperation,
    logger: logging.Logger,
) -> dict[str, Any]:
    try:
        request = parse_lifecycle_request(arguments)
    except MemoryValidationError as error:
        _log_outcome(
            logger,
            operation,
            logging.WARNING,
            "invalid_request",
            code=error.code,
            field=error.field,
        )
        return _error_payload(
            status="invalid_request",
            code=error.code,
            field=error.field,
            message=error.message,
        )

    disabled_message = f"memory {operation} is disabled"
    if not mutations_enabled:
        _log_outcome(
            logger,
            operation,
            logging.WARNING,
            "policy_error",
            code="mutation_disabled",
            request=request,
        )
        return _error_payload(
            status="policy_error",
            code="mutation_disabled",
            message=disabled_message,
        )

    past_tense = "archived" if operation == "archive" else "restored"
    try:
        result = lifecycle_operation(
            request.reference,
            request.expected_revision,
        )
        _validate_result(operation, request, result)
    except MemoryValidationError as error:
        field = "expected_revision" if error.field == "expected_revision" else "reference"
        code = (
            "invalid_expected_revision"
            if field == "expected_revision"
            else "invalid_reference"
        )
        message = (
            "expected revision is invalid"
            if field == "expected_revision"
            else "reference is invalid"
        )
        _log_outcome(logger, operation, logging.WARNING, "invalid_request", code=code, field=field, request=request)
        return _error_payload(status="invalid_request", code=code, field=field, message=message)
    except MutationDisabled:
        _log_outcome(logger, operation, logging.WARNING, "policy_error", code="mutation_disabled", request=request)
        return _error_payload(status="policy_error", code="mutation_disabled", message=disabled_message)
    except MemoryNotFound:
        _log_outcome(logger, operation, logging.WARNING, "not_found", code="not_found", request=request)
        return _error_payload(status="not_found", code="not_found", message=f"memory to {operation} was not found")
    except RevisionConflict:
        _log_outcome(logger, operation, logging.WARNING, "conflict", code="revision_conflict", request=request)
        return _error_payload(status="conflict", code="revision_conflict", message=f"memory to {operation} is not at the expected revision")
    except WriteConflict:
        _log_outcome(logger, operation, logging.WARNING, "conflict", code="write_conflict", request=request)
        return _error_payload(status="conflict", code="write_conflict", message=f"memory changed before it could be {past_tense}")
    except ReplacementOutcomeUncertain:
        _log_outcome(logger, operation, logging.WARNING, "uncertain", code="replacement_outcome_uncertain", request=request)
        return _error_payload(
            status="uncertain",
            code="replacement_outcome_uncertain",
            message=f"memory {operation} outcome is uncertain; inspect the same reference before any retry",
        )
    except (UnsafeMemoryPath, MemorySourceUnavailable, OSError):
        _log_outcome(logger, operation, logging.WARNING, "storage_error", code="memory_source_unavailable", request=request)
        return _error_payload(status="storage_error", code="memory_source_unavailable", message=f"memory could not be {past_tense}")
    except Exception:
        _log_outcome(logger, operation, logging.ERROR, "internal_error", code="internal_error", request=request)
        return _error_payload(status="internal_error", code="internal_error", message=f"memory could not be {past_tense}")

    _log_outcome(logger, operation, logging.INFO, result.status, request=request, result=result)
    return _serialize_result(result)
