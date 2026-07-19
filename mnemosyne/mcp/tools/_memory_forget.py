from collections.abc import Callable
import logging
from typing import Any

from mnemosyne.memory.errors import (
    DeletionOutcomeUncertain,
    MemoryNotArchived,
    MemoryNotFound,
    MemorySourceUnavailable,
    MemoryValidationError,
    MutationDisabled,
    RevisionConflict,
    UnsafeMemoryPath,
    WriteConflict,
)
from mnemosyne.memory.records import MemoryReference
from mnemosyne.memory.service import ForgetResult
from mnemosyne.mcp.tools._memory_lifecycle import (
    LifecycleRequest,
    parse_lifecycle_request,
    text_result,
)


ForgetOperation = Callable[[MemoryReference, int], ForgetResult]


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


def _log_outcome(
    logger: logging.Logger,
    level: int,
    outcome: str,
    *,
    code: str | None = None,
    field: str | None = None,
    request: LifecycleRequest | None = None,
) -> None:
    message = f"event=memory_forget outcome={outcome}"
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
    logger.log(level, message, *values)


def _serialize_reference(reference: MemoryReference) -> dict[str, object]:
    return {
        "schema_version": 2,
        "scope": reference.scope.value,
        "namespace_id": reference.namespace_id,
        "collection_id": reference.collection_id,
        "id": reference.id,
    }


def _validate_result(request: LifecycleRequest, result: ForgetResult) -> None:
    if result.status != "forgotten" or result.reference != request.reference:
        raise TypeError("unexpected forget result")


def execute_forget(
    arguments: object,
    *,
    mutations_enabled: bool,
    forget_operation: ForgetOperation,
    logger: logging.Logger,
) -> dict[str, Any]:
    try:
        request = parse_lifecycle_request(arguments)
    except MemoryValidationError as error:
        _log_outcome(
            logger,
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

    if not mutations_enabled:
        _log_outcome(
            logger,
            logging.WARNING,
            "policy_error",
            code="mutation_disabled",
            request=request,
        )
        return _error_payload(
            status="policy_error",
            code="mutation_disabled",
            message="memory forget is disabled",
        )

    try:
        result = forget_operation(request.reference, request.expected_revision)
        _validate_result(request, result)
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
        _log_outcome(
            logger,
            logging.WARNING,
            "invalid_request",
            code=code,
            field=field,
            request=request,
        )
        return _error_payload(
            status="invalid_request",
            code=code,
            field=field,
            message=message,
        )
    except MutationDisabled:
        _log_outcome(
            logger,
            logging.WARNING,
            "policy_error",
            code="mutation_disabled",
            request=request,
        )
        return _error_payload(
            status="policy_error",
            code="mutation_disabled",
            message="memory forget is disabled",
        )
    except MemoryNotArchived:
        _log_outcome(
            logger,
            logging.WARNING,
            "conflict",
            code="not_archived",
            request=request,
        )
        return _error_payload(
            status="conflict",
            code="not_archived",
            message="memory must be archived before it can be forgotten",
        )
    except MemoryNotFound:
        _log_outcome(
            logger,
            logging.WARNING,
            "not_found",
            code="not_found",
            request=request,
        )
        return _error_payload(
            status="not_found",
            code="not_found",
            message="memory to forget was not found",
        )
    except RevisionConflict:
        _log_outcome(
            logger,
            logging.WARNING,
            "conflict",
            code="revision_conflict",
            request=request,
        )
        return _error_payload(
            status="conflict",
            code="revision_conflict",
            message="memory to forget is not at the expected revision",
        )
    except WriteConflict:
        _log_outcome(
            logger,
            logging.WARNING,
            "conflict",
            code="write_conflict",
            request=request,
        )
        return _error_payload(
            status="conflict",
            code="write_conflict",
            message="memory changed before it could be forgotten",
        )
    except DeletionOutcomeUncertain:
        _log_outcome(
            logger,
            logging.WARNING,
            "uncertain",
            code="deletion_outcome_uncertain",
            request=request,
        )
        return _error_payload(
            status="uncertain",
            code="deletion_outcome_uncertain",
            message=(
                "memory deletion outcome is uncertain; inspect the same "
                "reference before any retry"
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
        return _error_payload(
            status="storage_error",
            code="memory_source_unavailable",
            message="memory could not be forgotten",
        )
    except Exception:
        _log_outcome(
            logger,
            logging.ERROR,
            "internal_error",
            code="internal_error",
            request=request,
        )
        return _error_payload(
            status="internal_error",
            code="internal_error",
            message="memory could not be forgotten",
        )

    _log_outcome(logger, logging.INFO, "forgotten", request=request)
    return text_result(
        {
            "status": "forgotten",
            "reference": _serialize_reference(result.reference),
        }
    )
