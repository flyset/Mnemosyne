import asyncio
import logging
from collections.abc import AsyncIterator
from time import perf_counter
from typing import Any, Protocol, runtime_checkable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from mymcp.authentication.contracts import (
    AuthenticationEvidence,
    AuthenticationFailure,
    AuthenticationRequestContext,
    EvidenceRoute,
    Principal,
)
from mymcp.authentication.router import Authenticator
from mymcp.host.mcp_application import MCPApplicationResult


logger = logging.getLogger("mcp")


class PrincipalAwareDispatcher(Protocol):
    def dispatch(
        self,
        principal: Principal,
        message: Any,
    ) -> dict[str, Any] | None: ...


@runtime_checkable
class SessionAwareApplication(PrincipalAwareDispatcher, Protocol):
    def handle(
        self,
        principal: Principal,
        message: Any,
        *,
        session_id: str | None = None,
        protocol_version: str | None = None,
    ) -> MCPApplicationResult: ...

    def validate_stream(
        self,
        principal: Principal,
        *,
        session_id: str | None,
        protocol_version: str | None,
    ) -> MCPApplicationResult: ...

    def terminate_session(
        self,
        principal: Principal,
        *,
        session_id: str | None,
        protocol_version: str | None,
    ) -> MCPApplicationResult: ...


def _extract_evidence(
    request: Request,
) -> AuthenticationEvidence | AuthenticationFailure | None:
    authorization_values = [
        value.decode("latin-1")
        for key, value in request.headers.raw
        if key.decode("latin-1").lower() == "authorization"
    ]
    if not authorization_values:
        return None
    if len(authorization_values) != 1:
        return AuthenticationFailure("malformed")
    authorization = authorization_values[0]
    parts = authorization.split(" ")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return AuthenticationFailure("malformed")
    try:
        return AuthenticationEvidence(
            EvidenceRoute("authorization", parts[0].lower(), None),
            parts[1].encode("utf-8"),
        )
    except (UnicodeEncodeError, ValueError):
        return AuthenticationFailure("malformed")


def _authenticate(
    request: Request,
    authenticator: Authenticator,
) -> Principal | AuthenticationFailure:
    evidence = _extract_evidence(request)
    if isinstance(evidence, AuthenticationFailure):
        return evidence
    return authenticator.authenticate(
        evidence,
        AuthenticationRequestContext(
            "POST" if request.method == "DELETE" else request.method,
            "mcp",
        ),
    )


def _singleton_header(request: Request, name: str) -> str | None | object:
    values = [
        value
        for key, value in request.headers.raw
        if key.lower() == name.encode("ascii").lower()
    ]
    if not values:
        return None
    if len(values) != 1:
        return _INVALID_HEADER
    try:
        value = values[0].decode("ascii")
    except UnicodeDecodeError:
        return _INVALID_HEADER
    return value if value else _INVALID_HEADER


_INVALID_HEADER = object()


def _session_headers(request: Request) -> tuple[str | None, str | None] | None:
    session_id = _singleton_header(request, "mcp-session-id")
    protocol_version = _singleton_header(request, "mcp-protocol-version")
    if session_id is _INVALID_HEADER or protocol_version is _INVALID_HEADER:
        return None
    assert session_id is None or isinstance(session_id, str)
    assert protocol_version is None or isinstance(protocol_version, str)
    return session_id, protocol_version


def _serialize_application_result(result: MCPApplicationResult) -> Response:
    if result.body is None:
        return Response(status_code=result.status_code, headers=dict(result.headers))
    return JSONResponse(
        result.body,
        status_code=result.status_code,
        headers=dict(result.headers),
    )


def create_router(
    application: PrincipalAwareDispatcher,
    authenticator: Authenticator,
    *,
    oauth_resource_metadata_url: str | None = None,
) -> APIRouter:
    router = APIRouter()

    def unauthorized() -> Response:
        if oauth_resource_metadata_url is None:
            return Response(status_code=401)
        return Response(
            status_code=401,
            headers={
                "WWW-Authenticate": (
                    f'Bearer resource_metadata="{oauth_resource_metadata_url}"'
                )
            },
        )

    @router.get("/mcp")
    async def mcp_stream(request: Request) -> Response:
        principal = _authenticate(request, authenticator)
        if isinstance(principal, AuthenticationFailure):
            return unauthorized()
        headers = _session_headers(request)
        if headers is None:
            return Response(status_code=400)
        if isinstance(application, SessionAwareApplication):
            result = application.validate_stream(
                principal,
                session_id=headers[0],
                protocol_version=headers[1],
            )
            if result.status_code != 200:
                return _serialize_application_result(result)

        async def event_stream() -> AsyncIterator[str]:
            while True:
                yield ": keep-alive\n\n"
                await asyncio.sleep(15)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    @router.delete("/mcp")
    async def mcp_terminate(request: Request) -> Response:
        principal = _authenticate(request, authenticator)
        if isinstance(principal, AuthenticationFailure):
            return unauthorized()
        headers = _session_headers(request)
        if headers is None:
            return Response(status_code=400)
        if not isinstance(application, SessionAwareApplication):
            return Response(status_code=404)
        return _serialize_application_result(
            application.terminate_session(
                principal,
                session_id=headers[0],
                protocol_version=headers[1],
            )
        )

    @router.post("/mcp")
    async def mcp_endpoint(request: Request) -> Response:
        principal = _authenticate(request, authenticator)
        if isinstance(principal, AuthenticationFailure):
            return unauthorized()
        headers = _session_headers(request)
        if headers is None:
            return Response(status_code=400)
        if isinstance(application, SessionAwareApplication) and (
            headers[0] is not None or headers[1] is not None
        ):
            context = application.validate_stream(
                principal,
                session_id=headers[0],
                protocol_version=headers[1],
            )
            if context.status_code != 200:
                return _serialize_application_result(context)
        message = await request.json()
        request_id = message.get("id") if isinstance(message, dict) else None
        method = message.get("method") if isinstance(message, dict) else None
        is_notification = isinstance(message, dict) and "id" not in message
        if isinstance(application, SessionAwareApplication):
            if method == "initialize":
                if principal.kind.value == "anonymous" and (
                    headers[0] is not None or headers[1] is not None
                ):
                    return _serialize_application_result(
                        application.handle(
                            principal,
                            message,
                            session_id=headers[0],
                            protocol_version=headers[1],
                        )
                    )
                if headers[0] is not None or headers[1] is not None:
                    return _serialize_application_result(
                        application.handle(
                            principal,
                            message,
                            session_id=headers[0],
                            protocol_version=headers[1],
                        )
                    )
        started_at = perf_counter()
        if isinstance(application, SessionAwareApplication):
            result = application.handle(
                principal,
                message,
                session_id=headers[0],
                protocol_version=headers[1],
            )
        else:
            response_body = application.dispatch(principal, message)
            result = MCPApplicationResult(response_body, 202 if response_body is None else 200)
        duration_ms = round((perf_counter() - started_at) * 1000)
        if result.status_code not in {200, 202}:
            return _serialize_application_result(result)
        if not is_notification:
            logger.info("request id=%s method=%s", request_id, method)
        if result.body is None:
            logger.debug("notification method=%s duration_ms=%s", method, duration_ms)
            return _serialize_application_result(result)

        if "error" in result.body:
            logger.warning(
                "response id=%s method=%s outcome=error code=%s duration_ms=%s",
                request_id,
                method,
                result.body["error"]["code"],
                duration_ms,
            )
        else:
            logger.info(
                "response id=%s method=%s outcome=ok duration_ms=%s",
                request_id,
                method,
                duration_ms,
            )

        return _serialize_application_result(result)

    return router
