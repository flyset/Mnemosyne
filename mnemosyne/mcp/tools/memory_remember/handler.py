import json
import logging
from typing import Any

from mnemosyne.memory.errors import (
    CandidateLimitExceeded,
    DisallowedMemoryContent,
    MemorySourceUnavailable,
    MemoryValidationError,
    MutationDisabled,
    UnsafeMemoryPath,
    WriteConflict,
)
from mnemosyne.memory.records import MemoryDraft, MemoryOrigin, MemoryRecordV2
from mnemosyne.memory.service import MemoryResult, MemoryService
from mnemosyne.memory.store import FilesystemMemoryStore
from mnemosyne.settings import get_memory_root


logger = logging.getLogger("mcp.memory_remember")


PUBLIC_ORIGINS = {
    MemoryOrigin.EXPLICIT_USER_STATEMENT.value,
    MemoryOrigin.USER_APPROVED_PROPOSAL.value,
}
PUBLIC_FIELDS = {
    "scope",
    "namespace",
    "namespace.kind",
    "namespace.id",
    "namespace.label",
    "collection",
    "collection.id",
    "collection.label",
    "kind",
    "occurred_at",
    "language",
    "title",
    "content",
    "tags",
    "origin",
}
VALIDATION_MESSAGES = {
    "invalid_scope": "scope is invalid",
    "invalid_namespace": "namespace is invalid for scope",
    "invalid_collection": "collection is invalid",
    "invalid_kind": "kind is invalid for scope",
    "invalid_record": "memory field is invalid",
}


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
    payload = {
        "status": status,
        "code": code,
    }
    if field is not None:
        payload["field"] = field
    payload["message"] = message
    return {
        "content": _text_content(payload),
        "isError": True,
    }


def _log_outcome(
    level: int,
    outcome: str,
    *,
    code: str | None = None,
    field: str | None = None,
    draft: MemoryDraft | None = None,
    memory: MemoryRecordV2 | None = None,
) -> None:
    message = f"event=memory_remember outcome={outcome}"
    values: list[object] = []
    if code is not None:
        message += " code=%s"
        values.append(code)
    if field is not None:
        message += " field=%s"
        values.append(field)
    if draft is not None:
        message += (
            " scope=%s namespace_kind=%s memory_kind=%s "
            "collection_present=%s origin=%s"
        )
        values.extend(
            [
                draft.scope.value,
                draft.namespace.kind,
                draft.kind.value,
                draft.collection is not None,
                draft.origin.value,
            ]
        )
    if memory is not None:
        message += " memory_id=%s lifecycle_state=%s revision=%s"
        values.extend(
            [
                memory.id,
                memory.lifecycle.state.value,
                memory.lifecycle.revision,
            ]
        )
    logger.log(level, message, *values)


def _validation_error(error: MemoryValidationError) -> tuple[str, str, str]:
    code = error.code if error.code in VALIDATION_MESSAGES else "invalid_record"
    field = error.field if error.field in PUBLIC_FIELDS else "memory"
    return code, field, VALIDATION_MESSAGES[code]


def _serialize_result(result: MemoryResult) -> dict[str, Any]:
    memory = result.memory
    return {
        "content": _text_content(
            {
                "status": result.status,
                "reference": {
                    "scope": memory.scope.value,
                    "namespace_id": memory.namespace.id,
                    "collection_id": (
                        memory.collection.id
                        if memory.collection is not None
                        else None
                    ),
                    "id": memory.id,
                },
                "lifecycle": {
                    "state": memory.lifecycle.state.value,
                    "revision": memory.lifecycle.revision,
                },
            }
        )
    }


def handle(
    arguments: dict[str, Any],
    *,
    mutations_enabled: bool = False,
) -> dict[str, Any]:
    if arguments.get("origin") not in PUBLIC_ORIGINS:
        _log_outcome(
            logging.WARNING,
            "invalid_request",
            code="invalid_origin",
            field="origin",
        )
        return _error(
            status="invalid_request",
            code="invalid_origin",
            field="origin",
            message="origin is invalid",
        )

    try:
        draft = MemoryDraft.from_dict(arguments)
    except MemoryValidationError as error:
        code, field, message = _validation_error(error)
        _log_outcome(
            logging.WARNING,
            "invalid_request",
            code=code,
            field=field,
        )
        return _error(
            status="invalid_request",
            code=code,
            field=field,
            message=message,
        )

    if not mutations_enabled:
        _log_outcome(
            logging.WARNING,
            "policy_error",
            code="mutation_disabled",
            draft=draft,
        )
        return _error(
            status="policy_error",
            code="mutation_disabled",
            message="memory remember is disabled",
        )

    try:
        service = MemoryService(
            FilesystemMemoryStore(get_memory_root()),
            mutations_enabled=True,
        )
        result = service.remember(draft)
    except MemoryValidationError as error:
        code, field, message = _validation_error(error)
        _log_outcome(
            logging.WARNING,
            "invalid_request",
            code=code,
            field=field,
            draft=draft,
        )
        return _error(
            status="invalid_request",
            code=code,
            field=field,
            message=message,
        )
    except DisallowedMemoryContent:
        _log_outcome(
            logging.WARNING,
            "refused",
            code="disallowed_content",
            draft=draft,
        )
        return _error(
            status="refused",
            code="disallowed_content",
            message="memory contains content that Mnemosyne does not store",
        )
    except MutationDisabled:
        _log_outcome(
            logging.WARNING,
            "policy_error",
            code="mutation_disabled",
            draft=draft,
        )
        return _error(
            status="policy_error",
            code="mutation_disabled",
            message="memory remember is disabled",
        )
    except CandidateLimitExceeded:
        _log_outcome(
            logging.WARNING,
            "storage_error",
            code="candidate_limit_exceeded",
            draft=draft,
        )
        return _error(
            status="storage_error",
            code="candidate_limit_exceeded",
            message="memory scope contains more than 1000 candidate files",
        )
    except WriteConflict:
        _log_outcome(
            logging.WARNING,
            "conflict",
            code="write_conflict",
            draft=draft,
        )
        return _error(
            status="conflict",
            code="write_conflict",
            message="generated memory identity conflicts with an existing record",
        )
    except (UnsafeMemoryPath, MemorySourceUnavailable, OSError):
        _log_outcome(
            logging.WARNING,
            "storage_error",
            code="memory_source_unavailable",
            draft=draft,
        )
        return _error(
            status="storage_error",
            code="memory_source_unavailable",
            message="memory could not be stored",
        )
    except Exception:
        _log_outcome(
            logging.ERROR,
            "internal_error",
            code="internal_error",
            draft=draft,
        )
        return _error(
            status="internal_error",
            code="internal_error",
            message="memory could not be stored",
        )

    _log_outcome(
        logging.INFO,
        result.status,
        draft=draft,
        memory=result.memory,
    )
    return _serialize_result(result)
