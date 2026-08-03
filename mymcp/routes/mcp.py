import asyncio
import logging
from collections.abc import AsyncIterator
from time import perf_counter
from typing import Any, Protocol

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


logger = logging.getLogger("mcp")


class PrincipalAwareDispatcher(Protocol):
    def dispatch(
        self,
        principal: Principal,
        message: Any,
    ) -> dict[str, Any] | None: ...


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
        AuthenticationRequestContext(request.method, "mcp"),
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

    @router.post("/mcp")
    async def mcp_endpoint(request: Request) -> Response:
        principal = _authenticate(request, authenticator)
        if isinstance(principal, AuthenticationFailure):
            return unauthorized()
        message = await request.json()
        request_id = message.get("id") if isinstance(message, dict) else None
        method = message.get("method") if isinstance(message, dict) else None
        is_notification = isinstance(message, dict) and "id" not in message
        if not is_notification:
            logger.info("request id=%s method=%s", request_id, method)

        started_at = perf_counter()
        response_body = application.dispatch(principal, message)
        duration_ms = round((perf_counter() - started_at) * 1000)
        if response_body is None:
            logger.debug("notification method=%s duration_ms=%s", method, duration_ms)
            return Response(status_code=202)

        if "error" in response_body:
            logger.warning(
                "response id=%s method=%s outcome=error code=%s duration_ms=%s",
                request_id,
                method,
                response_body["error"]["code"],
                duration_ms,
            )
        else:
            logger.info(
                "response id=%s method=%s outcome=ok duration_ms=%s",
                request_id,
                method,
                duration_ms,
            )

        return JSONResponse(response_body)

    return router
