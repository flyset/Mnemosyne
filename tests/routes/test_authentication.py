from dataclasses import dataclass
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient
from starlette.requests import Request

from mymcp.authentication.contracts import (
    AdapterId,
    AuthenticationEvidence,
    AuthenticationFailure,
    AuthenticationRequestContext,
    AuthenticationSuccess,
    EvidenceRoute,
    Principal,
)
from mymcp.authentication.router import AdapterRegistration, compose_authenticator
from mymcp.routes.mcp import create_router


@dataclass
class RecordingApplication:
    calls: list[tuple[Principal, object]]

    def dispatch(self, principal: Principal, message: object) -> dict[str, Any]:
        self.calls.append((principal, message))
        return {"jsonrpc": "2.0", "id": 1, "result": {}}


class SyntheticAdapter:
    def authenticate(
        self,
        evidence: AuthenticationEvidence,
        context: AuthenticationRequestContext,
    ) -> AuthenticationSuccess | AuthenticationFailure:
        return AuthenticationSuccess("registered-subject")


def _client(*, anonymous_enabled: bool, registered: bool = False):
    calls: list[tuple[Principal, object]] = []
    application = RecordingApplication(calls)
    registrations = (
        (
            AdapterRegistration(
                AdapterId("synthetic"),
                EvidenceRoute("authorization", "bearer", None),
                SyntheticAdapter(),
            ),
        )
        if registered
        else ()
    )
    authenticator = compose_authenticator(
        registrations,
        anonymous_enabled=anonymous_enabled,
    )
    app = FastAPI()
    app.include_router(create_router(application, authenticator))  # type: ignore[arg-type]
    return TestClient(app), calls


def test_anonymous_post_carries_fixed_principal_to_application() -> None:
    client, calls = _client(anonymous_enabled=True)

    response = client.post("/mcp", json={"id": 1, "method": "ping"})

    assert response.status_code == 200
    assert calls == [(Principal.anonymous(), {"id": 1, "method": "ping"})]


def test_registered_post_carries_namespaced_principal() -> None:
    client, calls = _client(anonymous_enabled=False, registered=True)

    response = client.post(
        "/mcp",
        headers={"Authorization": "Bearer opaque"},
        json={"id": 1, "method": "ping"},
    )

    assert response.status_code == 200
    assert calls[0][0].adapter_id == AdapterId("synthetic")
    assert calls[0][0].subject == "registered-subject"


@pytest.mark.parametrize("method", ["get", "post"])
def test_no_evidence_is_empty_401_before_mcp_when_anonymous_disabled(method: str) -> None:
    client, calls = _client(anonymous_enabled=False)

    response = getattr(client, method)(
        "/mcp",
        **({"content": b"not-json"} if method == "post" else {}),
    )

    assert response.status_code == 401
    assert response.content == b""
    assert calls == []


@pytest.mark.parametrize(
    "authorization",
    ["", "Bearer", "Basic opaque", "Bearer opaque extra"],
)
def test_malformed_or_unsupported_evidence_is_empty_401_without_fallback(
    authorization: str,
) -> None:
    client, calls = _client(anonymous_enabled=True, registered=True)

    response = client.post(
        "/mcp",
        headers={"Authorization": authorization},
        content=b"not-json",
    )

    assert response.status_code == 401
    assert response.content == b""
    assert calls == []


@pytest.mark.anyio
async def test_anonymous_get_preserves_stream_transport() -> None:
    authenticator = compose_authenticator((), anonymous_enabled=True)
    application = RecordingApplication([])
    router = create_router(application, authenticator)
    endpoint = next(route.endpoint for route in router.routes if "GET" in route.methods)
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/mcp",
            "headers": [],
        }
    )

    response = await endpoint(request)

    assert isinstance(response, StreamingResponse)
    assert response.media_type == "text/event-stream"
    assert application.calls == []
