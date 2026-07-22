import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from mymcp.memory.errors import (
    CandidateLimitExceeded,
    InvalidMemoryListCursor,
    MemorySourceUnavailable,
    MemoryValidationError,
    StaleMemoryListCursor,
    UnsafeMemoryPath,
)
from mymcp.memory.listing import (
    MAX_MEMORY_LIST_CURSOR_LENGTH,
    MAX_MEMORY_LIST_PAGE_SIZE,
    MIN_MEMORY_LIST_PAGE_SIZE,
    MemoryCollectionSelector,
    MemoryListItem,
    MemoryListResult,
    MemoryListSelector,
)
from mymcp.memory.normalization import normalize_identifier
from mymcp.memory.records import LegacyMemoryRecordV1, MemoryRecordV2
from mymcp.memory.scopes import parse_scope
from mymcp.memory.service import MemoryService
from mymcp.memory.store import FilesystemMemoryStore
from mymcp.settings import get_memory_root


logger = logging.getLogger("mcp.memory_list")

ListOperation = Callable[
    [MemoryListSelector, int | None, str | None],
    MemoryListResult,
]
_REQUEST_FIELDS = {
    "scope",
    "namespace_id",
    "collection_id",
    "page_size",
    "cursor",
}


@dataclass(frozen=True)
class MemoryListRequest:
    selector: MemoryListSelector
    page_size: int | None
    cursor: str | None
    namespace_selector_present: bool
    collection_selector_present: bool


class _RequestError(ValueError):
    def __init__(
        self,
        code: str,
        field: str,
        message: str,
        *,
        scope: str | None = None,
        namespace_selector_present: bool = False,
        collection_selector_present: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
        self.message = message
        self.scope = scope
        self.namespace_selector_present = namespace_selector_present
        self.collection_selector_present = collection_selector_present


def _request_error(
    code: str,
    field: str,
    message: str,
    *,
    scope: str | None = None,
    namespace_selector_present: bool = False,
    collection_selector_present: bool = False,
) -> _RequestError:
    return _RequestError(
        code,
        field,
        message,
        scope=scope,
        namespace_selector_present=namespace_selector_present,
        collection_selector_present=collection_selector_present,
    )


def _parse_request(arguments: object) -> MemoryListRequest:
    if not isinstance(arguments, dict) or set(arguments) - _REQUEST_FIELDS:
        raise _request_error(
            "invalid_request",
            "request",
            "request is invalid",
        )

    namespace_present = "namespace_id" in arguments
    collection_present = "collection_id" in arguments
    try:
        scope = parse_scope(arguments.get("scope"))
    except MemoryValidationError as error:
        raise _request_error(
            "invalid_scope",
            "scope",
            "scope is invalid",
            namespace_selector_present=namespace_present,
            collection_selector_present=collection_present,
        ) from error

    if namespace_present:
        try:
            namespace_id = normalize_identifier(
                arguments["namespace_id"],
                field="namespace.id",
            )
        except MemoryValidationError as error:
            raise _request_error(
                "invalid_namespace",
                "namespace_id",
                "namespace_id is invalid",
                scope=scope.value,
                namespace_selector_present=True,
                collection_selector_present=collection_present,
            ) from error
    else:
        namespace_id = None

    if collection_present and not namespace_present:
        raise _request_error(
            "invalid_collection",
            "collection_id",
            "collection_id is invalid",
            scope=scope.value,
            collection_selector_present=True,
        )
    try:
        if not collection_present:
            collection = MemoryCollectionSelector.all()
        elif arguments["collection_id"] is None:
            collection = MemoryCollectionSelector.collectionless()
        else:
            collection = MemoryCollectionSelector.exact(
                arguments["collection_id"]
            )
    except MemoryValidationError as error:
        raise _request_error(
            "invalid_collection",
            "collection_id",
            "collection_id is invalid",
            scope=scope.value,
            namespace_selector_present=namespace_present,
            collection_selector_present=collection_present,
        ) from error

    cursor_present = "cursor" in arguments
    page_size_present = "page_size" in arguments
    if cursor_present:
        cursor = arguments["cursor"]
        if (
            page_size_present
            or not isinstance(cursor, str)
            or not cursor
            or len(cursor) > MAX_MEMORY_LIST_CURSOR_LENGTH
        ):
            raise _request_error(
                "invalid_cursor",
                "cursor",
                "cursor is invalid",
                scope=scope.value,
                namespace_selector_present=namespace_present,
                collection_selector_present=collection_present,
            )
        page_size = None
    else:
        cursor = None
        if page_size_present:
            page_size = arguments["page_size"]
            if (
                type(page_size) is not int
                or page_size < MIN_MEMORY_LIST_PAGE_SIZE
                or page_size > MAX_MEMORY_LIST_PAGE_SIZE
            ):
                raise _request_error(
                    "invalid_page_size",
                    "page_size",
                    "page_size must be an integer from 1 through 100",
                    scope=scope.value,
                    namespace_selector_present=namespace_present,
                    collection_selector_present=collection_present,
                )
        else:
            page_size = None

    return MemoryListRequest(
        selector=MemoryListSelector(
            scope=scope,
            namespace_id=namespace_id,
            collection=collection,
        ),
        page_size=page_size,
        cursor=cursor,
        namespace_selector_present=namespace_present,
        collection_selector_present=collection_present,
    )


def _text_result(
    payload: dict[str, Any],
    *,
    is_error: bool = False,
) -> dict[str, Any]:
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
    return _text_result(payload, is_error=True)


def _log_outcome(
    level: int,
    outcome: str,
    *,
    code: str | None = None,
    field: str | None = None,
    scope: str | None = None,
    namespace_selector_present: bool | None = None,
    collection_selector_present: bool | None = None,
    result: MemoryListResult | None = None,
) -> None:
    message = f"event=memory_list outcome={outcome}"
    values: list[object] = []
    if code is not None:
        message += " code=%s"
        values.append(code)
    if field is not None:
        message += " field=%s"
        values.append(field)
    if scope is not None:
        message += " scope=%s"
        values.append(scope)
    if namespace_selector_present is not None:
        message += " namespace_selector_present=%s"
        values.append(namespace_selector_present)
    if collection_selector_present is not None:
        message += " collection_selector_present=%s"
        values.append(collection_selector_present)
    if result is not None:
        message += (
            " returned_count=%s total_count=%s page_number=%s truncated=%s"
        )
        values.extend(
            [
                result.page.count,
                result.page.total_count,
                result.page.number,
                result.page.truncated,
            ]
        )
    logger.log(level, message, *values)


def _serialize_item(item: MemoryListItem) -> dict[str, Any]:
    record = item.memory.record
    if isinstance(record, LegacyMemoryRecordV1):
        return {
            "reference": {
                "schema_version": 1,
                "scope": item.memory.scope.value,
                "id": record.id,
            },
            "title": record.title,
            "inspectability": item.inspectability.value,
        }
    if not isinstance(record, MemoryRecordV2):
        raise TypeError("unsupported listed memory version")
    return {
        "reference": {
            "schema_version": 2,
            "scope": record.scope.value,
            "namespace_id": record.namespace.id,
            "collection_id": (
                record.collection.id if record.collection is not None else None
            ),
            "id": record.id,
        },
        "title": record.title,
        "inspectability": item.inspectability.value,
        "kind": record.kind.value,
        "lifecycle": {"state": record.lifecycle.state.value},
    }


def _serialize_result(result: MemoryListResult) -> dict[str, Any]:
    if not isinstance(result, MemoryListResult):
        raise TypeError("invalid memory list result")
    if result.page.count != len(result.memories):
        raise TypeError("memory list count mismatch")
    return {
        "status": "ok",
        "memories": [_serialize_item(item) for item in result.memories],
        "page": {
            "number": result.page.number,
            "count": result.page.count,
            "total_count": result.page.total_count,
            "total_pages": result.page.total_pages,
            "truncated": result.page.truncated,
            "next_cursor": result.page.next_cursor,
        },
    }


def _list_memories(
    selector: MemoryListSelector,
    page_size: int | None,
    cursor: str | None,
) -> MemoryListResult:
    service = MemoryService(FilesystemMemoryStore(get_memory_root()))
    return service.list_memories(
        selector,
        page_size=page_size,
        cursor=cursor,
    )


def handle(
    arguments: object,
    *,
    list_operation: ListOperation | None = None,
) -> dict[str, Any]:
    try:
        request = _parse_request(arguments)
    except _RequestError as error:
        _log_outcome(
            logging.WARNING,
            "invalid_request",
            code=error.code,
            field=error.field,
            scope=error.scope,
            namespace_selector_present=error.namespace_selector_present,
            collection_selector_present=error.collection_selector_present,
        )
        return _error(
            status="invalid_request",
            code=error.code,
            field=error.field,
            message=error.message,
        )

    operation = list_operation or _list_memories
    log_context = {
        "scope": request.selector.scope.value,
        "namespace_selector_present": request.namespace_selector_present,
        "collection_selector_present": request.collection_selector_present,
    }
    try:
        result = operation(
            request.selector,
            request.page_size,
            request.cursor,
        )
        payload = _serialize_result(result)
    except InvalidMemoryListCursor:
        _log_outcome(
            logging.WARNING,
            "invalid_request",
            code="invalid_cursor",
            field="cursor",
            **log_context,
        )
        return _error(
            status="invalid_request",
            code="invalid_cursor",
            field="cursor",
            message="cursor is invalid",
        )
    except StaleMemoryListCursor:
        _log_outcome(
            logging.WARNING,
            "conflict",
            code="stale_cursor",
            **log_context,
        )
        return _error(
            status="conflict",
            code="stale_cursor",
            message="cursor is stale; start a new listing",
        )
    except MemoryValidationError as error:
        code = (
            "invalid_page_size"
            if error.field == "page_size"
            else "invalid_request"
        )
        field = "page_size" if error.field == "page_size" else "request"
        message = (
            "page_size must be an integer from 1 through 100"
            if field == "page_size"
            else "request is invalid"
        )
        _log_outcome(
            logging.WARNING,
            "invalid_request",
            code=code,
            field=field,
            **log_context,
        )
        return _error(
            status="invalid_request",
            code=code,
            field=field,
            message=message,
        )
    except CandidateLimitExceeded:
        _log_outcome(
            logging.WARNING,
            "storage_error",
            code="candidate_limit_exceeded",
            **log_context,
        )
        return _error(
            status="storage_error",
            code="candidate_limit_exceeded",
            message=(
                "selected memory container contains more than 1000 candidate files"
            ),
        )
    except (UnsafeMemoryPath, MemorySourceUnavailable, OSError):
        _log_outcome(
            logging.WARNING,
            "storage_error",
            code="memory_source_unavailable",
            **log_context,
        )
        return _error(
            status="storage_error",
            code="memory_source_unavailable",
            message="memory could not be listed",
        )
    except Exception:
        _log_outcome(
            logging.ERROR,
            "internal_error",
            code="internal_error",
            **log_context,
        )
        return _error(
            status="internal_error",
            code="internal_error",
            message="memory could not be listed",
        )

    _log_outcome(logging.INFO, "ok", result=result, **log_context)
    return _text_result(payload)
