from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from mymcp.authentication.contracts import (
    AdapterId,
    AuthenticationEvidence,
    AuthenticationFailure,
    AuthenticationRequestContext,
    AuthenticationSuccess,
    EvidenceRoute,
)
from mymcp.authentication.router import AdapterRegistration, compose_authenticator
from mymcp.host.mcp_application import PrincipalAwareMCPApplication
from mymcp.host.runtime import RuntimeGenerationId
from mymcp.host.sessions import MCP_PROTOCOL_VERSION, ProcessLocalSessionStore
from mymcp.mcp.dispatcher import MCPDispatcher
from mymcp.mcp.tool_registry import ToolRegistration, ToolRegistry
from mymcp.routes.mcp import create_router


@dataclass(frozen=True)
class SyntheticRuntime:
    registry: ToolRegistry


class SyntheticAdapter:
    def authenticate(
        self,
        evidence: AuthenticationEvidence,
        context: AuthenticationRequestContext,
    ) -> AuthenticationSuccess | AuthenticationFailure:
        return AuthenticationSuccess("session-client")


def _client() -> tuple[TestClient, list[dict[str, Any]]]:
    calls: list[dict[str, Any]] = []

    def handler(arguments: dict[str, Any]) -> dict[str, Any]:
        calls.append(arguments)
        return {"content": []}

    runtime = SyntheticRuntime(
        ToolRegistry(
            (
                ToolRegistration(
                    tool={
                        "name": "synthetic",
                        "description": "Synthetic Tool.",
                        "inputSchema": {"type": "object", "properties": {}},
                    },
                    handler=handler,
                ),
            )
        )
    )
    generation = RuntimeGenerationId("route-session-generation")
    application = PrincipalAwareMCPApplication(
        MCPDispatcher(runtime),
        generation,
        ProcessLocalSessionStore(generation, token_factory=lambda: "a" * 43),
    )
    authenticator = compose_authenticator(
        (
            AdapterRegistration(
                AdapterId("synthetic"),
                EvidenceRoute("authorization", "bearer", None),
                SyntheticAdapter(),
            ),
        ),
        anonymous_enabled=True,
    )
    app = FastAPI()
    app.include_router(create_router(application, authenticator))
    return TestClient(app), calls


def _initialize() -> dict[str, Any]:
    return {
        "id": "initialize",
        "method": "initialize",
        "params": {"protocolVersion": MCP_PROTOCOL_VERSION},
    }


def _registered_headers() -> dict[str, str]:
    return {"Authorization": "Bearer opaque"}


def test_registered_initialize_serializes_only_the_approved_session_header() -> None:
    client, _ = _client()

    response = client.post("/mcp", headers=_registered_headers(), json=_initialize())

    assert response.status_code == 200
    assert response.headers["mcp-session-id"] == "a" * 43
    assert "a" * 43 not in response.text


def test_registered_followup_requires_single_valid_headers_before_logging_or_dispatch(caplog) -> None:
    client, calls = _client()
    identifier = client.post(
        "/mcp", headers=_registered_headers(), json=_initialize()
    ).headers["mcp-session-id"]
    caplog.set_level("INFO", logger="mcp")
    caplog.clear()

    missing = client.post(
        "/mcp", headers=_registered_headers(), json={"id": 1, "method": "tools/list"}
    )
    duplicate = client.post(
        "/mcp",
        headers=[
            ("Authorization", "Bearer opaque"),
            ("MCP-Session-Id", identifier),
            ("MCP-Session-Id", identifier),
            ("MCP-Protocol-Version", MCP_PROTOCOL_VERSION),
        ],
        json={"id": 2, "method": "tools/list"},
    )
    unknown = client.post(
        "/mcp",
        headers={
            **_registered_headers(),
            "MCP-Session-Id": "b" * 43,
            "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
        },
        json={"id": 3, "method": "tools/list"},
    )
    accepted = client.post(
        "/mcp",
        headers={
            **_registered_headers(),
            "MCP-Session-Id": identifier,
            "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
        },
        json={"id": 2, "method": "tools/call", "params": {"name": "synthetic"}},
    )

    assert (missing.status_code, missing.content) == (400, b"")
    assert (duplicate.status_code, duplicate.content) == (400, b"")
    assert (unknown.status_code, unknown.content) == (404, b"")
    assert accepted.status_code == 200
    assert calls == [{}]
    assert identifier not in caplog.text
    assert "not-json" not in caplog.text
    assert caplog.messages == [
        "request id=2 method=tools/call",
        caplog.messages[1],
    ]
    assert caplog.messages[1].startswith(
        "response id=2 method=tools/call outcome=ok duration_ms="
    )


def test_registered_delete_terminates_only_the_valid_session_and_get_requires_it() -> None:
    client, _ = _client()
    identifier = client.post(
        "/mcp", headers=_registered_headers(), json=_initialize()
    ).headers["mcp-session-id"]
    headers = {
        **_registered_headers(),
        "MCP-Session-Id": identifier,
        "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
    }

    deleted = client.delete("/mcp", headers=headers)
    after_delete = client.post(
        "/mcp", headers=headers, json={"id": 3, "method": "tools/list"}
    )
    missing_get = client.get("/mcp", headers=_registered_headers())

    assert (deleted.status_code, deleted.content) == (204, b"")
    assert (after_delete.status_code, after_delete.content) == (404, b"")
    assert (missing_get.status_code, missing_get.content) == (400, b"")


def test_authentication_precedes_session_header_validation_and_anonymous_remains_compatible() -> None:
    client, _ = _client()

    unauthenticated = client.post(
        "/mcp",
        headers={"Authorization": "Bearer", "MCP-Session-Id": "not-a-session"},
        content=b"not-json",
    )
    anonymous = client.post("/mcp", json={"id": 1, "method": "ping"})
    anonymous_with_protocol = client.post(
        "/mcp",
        headers={"MCP-Protocol-Version": MCP_PROTOCOL_VERSION},
        json={"id": 2, "method": "ping"},
    )
    anonymous_session = client.post(
        "/mcp",
        headers={"MCP-Session-Id": "a" * 43},
        json={"id": 2, "method": "ping"},
    )

    assert (unauthenticated.status_code, unauthenticated.content) == (401, b"")
    assert (anonymous.status_code, anonymous.content) == (400, b"")
    assert anonymous_with_protocol.status_code == 200
    assert (anonymous_session.status_code, anonymous_session.content) == (404, b"")


def test_unknown_registered_session_is_rejected_before_invalid_json_body_parsing() -> None:
    client, _ = _client()

    response = client.post(
        "/mcp",
        headers={
            **_registered_headers(),
            "MCP-Session-Id": "b" * 43,
            "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
        },
        content=b"not-json",
    )

    assert (response.status_code, response.content) == (404, b"")
