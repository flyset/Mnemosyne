"""S6 focused route and application tests for operator-bearer evidence.

These tests exercise the real ``operator-bearer-v1`` adapter through the real
HTTP route and application seams to prove one-header exact bearer extraction,
duplicate and malformed rejection, registered-credential delivery,
evidence-free configured anonymous behavior, no downgrade/fallback, empty
pre-body HTTP 401, and the absence of any credential or raw evidence in
representations, logs, errors, and downstream calls.
"""

from base64 import urlsafe_b64encode
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient
from starlette.requests import Request

from mymcp.authentication.adapters.operator_bearer import (
    OperatorBearerAdapter,
    OperatorBearerVerifierRecord,
    build_operator_bearer_verifier,
)
from mymcp.authentication.contracts import (
    AdapterId,
    EvidenceRoute,
    Principal,
)
from mymcp.authentication.router import (
    AdapterRegistration,
    Authenticator,
    compose_authenticator,
)
from mymcp.host.mcp_application import PrincipalAwareMCPApplication
from mymcp.host.runtime import RuntimeGenerationId
from mymcp.host.sessions import MCP_PROTOCOL_VERSION, ProcessLocalSessionStore
from mymcp.mcp.dispatcher import MCPDispatcher
from mymcp.mcp.tool_registry import ToolRegistration, ToolRegistry
from mymcp.routes.mcp import create_router

OPERATOR_ROUTE = EvidenceRoute("authorization", "bearer", None)

CREDENTIAL_ID = "a" * 32
SECRET = bytes(range(32))
_CREDENTIAL_SECRET = urlsafe_b64encode(SECRET).rstrip(b"=").decode("ascii")
CREDENTIAL = f"mymcp1.{CREDENTIAL_ID}.{_CREDENTIAL_SECRET}"
SUBJECT = "stable-subject"
ADAPTER_ID = AdapterId("local-valid")


def _operator_authenticator(*, anonymous_enabled: bool = False) -> Authenticator:
    verifier = build_operator_bearer_verifier(
        (OperatorBearerVerifierRecord(CREDENTIAL_ID, SUBJECT, sha256(SECRET).digest()),)
    )
    adapter = OperatorBearerAdapter(verifier)
    return compose_authenticator(
        (AdapterRegistration(ADAPTER_ID, OPERATOR_ROUTE, adapter),),
        anonymous_enabled=anonymous_enabled,
    )


@dataclass
class RecordingApplication:
    calls: list[tuple[Principal, object]] = field(default_factory=list)

    def dispatch(self, principal: Principal, message: object) -> dict[str, Any]:
        self.calls.append((principal, message))
        return {"jsonrpc": "2.0", "id": 1, "result": {"ok": True}}


def _client(authenticator: Authenticator) -> tuple[TestClient, RecordingApplication]:
    application = RecordingApplication()
    app = FastAPI()
    app.include_router(create_router(application, authenticator))  # type: ignore[arg-type]
    return TestClient(app), application


def _post_endpoint(authenticator: Authenticator) -> Any:
    router = create_router(RecordingApplication(), authenticator)
    return next(route.endpoint for route in router.routes if "POST" in route.methods)


def _raw_post_request(headers: list[tuple[bytes, bytes]]) -> Request:
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/mcp",
            "raw_path": b"/mcp",
            "query_string": b"",
            "headers": headers,
            "body": b"not-json",
            "server": ("testserver", 80),
        }
    )


def test_valid_operator_bearer_post_delivers_registered_principal() -> None:
    client, application = _client(_operator_authenticator())

    response = client.post(
        "/mcp",
        headers={"Authorization": f"Bearer {CREDENTIAL}"},
        json={"id": 1, "method": "ping"},
    )

    assert response.status_code == 200
    assert len(application.calls) == 1
    principal, message = application.calls[0]
    assert principal == Principal.registered(ADAPTER_ID, SUBJECT)
    assert message == {"id": 1, "method": "ping"}


def test_operator_bearer_registered_session_lifecycle_uses_the_common_transport_contract() -> None:
    runtime = type(
        "Runtime",
        (),
        {
            "registry": ToolRegistry(
                (
                    ToolRegistration(
                        tool={
                            "name": "synthetic",
                            "description": "Synthetic Tool.",
                            "inputSchema": {"type": "object", "properties": {}},
                        },
                        handler=lambda _arguments: {"content": []},
                    ),
                )
            )
        },
    )()
    generation = RuntimeGenerationId("operator-session-generation")
    application = PrincipalAwareMCPApplication(
        MCPDispatcher(runtime),
        generation,
        ProcessLocalSessionStore(generation, token_factory=lambda: "a" * 43),
    )
    app = FastAPI()
    app.include_router(create_router(application, _operator_authenticator()))
    client = TestClient(app)
    authorization = {"Authorization": f"Bearer {CREDENTIAL}"}

    initialized = client.post(
        "/mcp",
        headers=authorization,
        json={
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": MCP_PROTOCOL_VERSION},
        },
    )
    session_headers = {
        **authorization,
        "MCP-Session-Id": initialized.headers["mcp-session-id"],
        "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
    }
    followed = client.post("/mcp", headers=session_headers, json={"id": 2, "method": "ping"})
    terminated = client.delete("/mcp", headers=session_headers)

    assert initialized.status_code == 200
    assert followed.status_code == 200
    assert (terminated.status_code, terminated.content) == (204, b"")


def test_operator_bearer_compatibility_session_accepts_absent_protocol_header() -> None:
    runtime = type("Runtime", (), {"registry": ToolRegistry(())})()
    generation = RuntimeGenerationId("operator-compatibility-session-generation")
    application = PrincipalAwareMCPApplication(
        MCPDispatcher(runtime),
        generation,
        ProcessLocalSessionStore(generation, token_factory=lambda: "a" * 43),
        strict_protocol_version=False,
    )
    app = FastAPI()
    app.include_router(create_router(application, _operator_authenticator()))
    client = TestClient(app)
    authorization = {"Authorization": f"Bearer {CREDENTIAL}"}
    initialized = client.post(
        "/mcp",
        headers=authorization,
        json={
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": MCP_PROTOCOL_VERSION},
        },
    )

    followed = client.post(
        "/mcp",
        headers={**authorization, "MCP-Session-Id": initialized.headers["mcp-session-id"]},
        json={"id": 2, "method": "ping"},
    )

    assert initialized.status_code == 200
    assert followed.status_code == 200


def test_credential_and_raw_evidence_absent_from_downstream_and_response() -> None:
    client, application = _client(_operator_authenticator())

    response = client.post(
        "/mcp",
        headers={"Authorization": f"Bearer {CREDENTIAL}"},
        json={"id": 1, "method": "ping"},
    )

    assert response.status_code == 200
    assert CREDENTIAL not in response.text
    assert "mymcp1" not in response.text
    assert f"Bearer {CREDENTIAL}" not in response.text
    principal, _message = application.calls[0]
    for representation in (repr(principal), str(principal), principal.principal_id):
        assert CREDENTIAL not in representation
        assert _CREDENTIAL_SECRET not in representation


def test_duplicate_authorization_headers_is_empty_401() -> None:
    client, application = _client(_operator_authenticator(anonymous_enabled=True))

    response = client.post(
        "/mcp",
        headers=[
            ("Authorization", f"Bearer {CREDENTIAL}"),
            ("Authorization", f"Bearer {CREDENTIAL}"),
        ],
        content=b"not-json",
    )

    assert response.status_code == 401
    assert response.content == b""
    assert application.calls == []


@pytest.mark.parametrize(
    "authorization",
    [
        f"Bearer {CREDENTIAL} extra",
        f"Bearer  {CREDENTIAL}",
        f"bearer {CREDENTIAL} ",
        CREDENTIAL,
        "Bearer ",
        "",
        f"Basic {CREDENTIAL}",
        f"Digest {CREDENTIAL}",
        "bearer\t" + CREDENTIAL,
    ],
)
def test_malformed_or_wrong_scheme_evidence_is_empty_401(authorization: str) -> None:
    client, application = _client(_operator_authenticator(anonymous_enabled=True))

    response = client.post(
        "/mcp",
        headers={"Authorization": authorization},
        content=b"not-json",
    )

    assert response.status_code == 401
    assert response.content == b""
    assert application.calls == []


def test_post_rejects_evidence_before_body_parsing() -> None:
    client, application = _client(_operator_authenticator(anonymous_enabled=True))

    response = client.post(
        "/mcp",
        headers={"Authorization": f"Bearer {CREDENTIAL} extra"},
        content=b"this is definitely not valid json",
    )

    assert response.status_code == 401
    assert response.content == b""
    assert application.calls == []


def test_failed_credential_never_downgrades_to_anonymous() -> None:
    client, application = _client(_operator_authenticator(anonymous_enabled=True))
    secret = urlsafe_b64encode(bytes(range(32, 64))).rstrip(b"=").decode("ascii")
    wrong_credential = f"mymcp1.{'b' * 32}.{secret}"

    response = client.post(
        "/mcp",
        headers={"Authorization": f"Bearer {wrong_credential}"},
        json={"id": 1, "method": "ping"},
    )

    assert response.status_code == 401
    assert response.content == b""
    assert application.calls == []


def test_evidence_free_configured_anonymous_delivers_anonymous_principal() -> None:
    client, application = _client(_operator_authenticator(anonymous_enabled=True))

    response = client.post(
        "/mcp",
        json={"id": 1, "method": "ping"},
    )

    assert response.status_code == 200
    assert len(application.calls) == 1
    principal, _message = application.calls[0]
    assert principal == Principal.anonymous()


def test_evidence_free_with_anonymous_disabled_is_empty_401() -> None:
    client, application = _client(_operator_authenticator(anonymous_enabled=False))

    response = client.post(
        "/mcp",
        content=b"not-json",
    )

    assert response.status_code == 401
    assert response.content == b""
    assert application.calls == []


@pytest.mark.anyio
async def test_non_ascii_evidence_is_rejected_as_empty_401() -> None:
    endpoint = _post_endpoint(_operator_authenticator(anonymous_enabled=True))
    # 0xE9 is not ASCII; it must not pass exact bearer grammar.
    request = _raw_post_request(
        [(b"authorization", b"Bearer mymcp1" + bytes([0xE9]) + b"abaaba")]
    )

    response = await endpoint(request)

    assert response.status_code == 401
    assert response.body == b""


def _get_endpoint(authenticator: Authenticator) -> Any:
    router = create_router(RecordingApplication(), authenticator)
    return next(route.endpoint for route in router.routes if "GET" in route.methods)


def _raw_get_request(headers: list[tuple[bytes, bytes]]) -> Request:
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/mcp",
            "raw_path": b"/mcp",
            "query_string": b"",
            "headers": headers,
            "server": ("testserver", 80),
        }
    )


@pytest.mark.anyio
async def test_valid_credential_get_authenticates_and_streams_without_principal() -> None:
    endpoint = _get_endpoint(_operator_authenticator())
    request = _raw_get_request(
        [(b"authorization", f"Bearer {CREDENTIAL}".encode("ascii"))]
    )

    response = await endpoint(request)

    assert isinstance(response, StreamingResponse)
    assert response.status_code == 200
    assert response.media_type == "text/event-stream"


@pytest.mark.anyio
async def test_invalid_credential_get_is_empty_401_before_stream() -> None:
    endpoint = _get_endpoint(_operator_authenticator(anonymous_enabled=True))
    request = _raw_get_request([(b"authorization", b"Bearer invalid")])

    response = await endpoint(request)

    assert response.status_code == 401
    assert response.body == b""


def test_credential_never_appears_in_failure_or_success_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    import logging

    client, application = _client(_operator_authenticator())
    with caplog.at_level(logging.DEBUG):
        client.post(
            "/mcp",
            headers={"Authorization": "Bearer invalid"},
            json={"id": 1, "method": "ping"},
        )
        client.post(
            "/mcp",
            headers={"Authorization": f"Bearer {CREDENTIAL}"},
            json={"id": 1, "method": "ping"},
        )

    emitted = " ".join(record.getMessage() for record in caplog.records)
    assert CREDENTIAL not in emitted
    assert _CREDENTIAL_SECRET not in emitted
