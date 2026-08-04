import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mymcp.authentication.contracts import AdapterId, Principal
from mymcp.host.mcp_application import (
    MCPApplicationResult,
    PrincipalAwareMCPApplication,
)
from mymcp.host.runtime import RuntimeGenerationId
from mymcp.host.sessions import MCP_PROTOCOL_VERSION, ProcessLocalSessionStore
from mymcp.mcp.dispatcher import MCPDispatcher
from mymcp.mcp.tool_registry import ToolRegistration, ToolRegistry


REPOSITORY_ROOT = Path(__file__).parents[2]


@dataclass(frozen=True)
class SyntheticRuntime:
    registry: ToolRegistry


def _principal(subject: str = "client") -> Principal:
    return Principal.registered(AdapterId("local-client"), subject)


def _application(
    *,
    token_factory=lambda: "a" * 43,
    maximum_sessions: int = 128,
    strict_protocol_version: bool = True,
) -> tuple[PrincipalAwareMCPApplication, list[dict[str, Any]]]:
    calls: list[dict[str, Any]] = []

    def handler(arguments: dict[str, Any]) -> dict[str, Any]:
        calls.append(arguments)
        return {"content": []}

    dispatcher = MCPDispatcher(
        SyntheticRuntime(
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
    )
    generation = RuntimeGenerationId("application-generation")
    store = ProcessLocalSessionStore(
        generation,
        token_factory=token_factory,
        maximum_sessions=maximum_sessions,
    )
    return PrincipalAwareMCPApplication(
        dispatcher,
        generation,
        store,
        strict_protocol_version,
    ), calls


def _initialize(*, request_id: str | None = "initialize") -> dict[str, Any]:
    message: dict[str, Any] = {
        "method": "initialize",
        "params": {"protocolVersion": MCP_PROTOCOL_VERSION},
    }
    if request_id is not None:
        message["id"] = request_id
    return message


def test_registered_response_bearing_initialize_mints_one_session_header() -> None:
    application, _ = _application()

    result = application.handle(_principal(), _initialize())

    assert isinstance(result, MCPApplicationResult)
    assert result.status_code == 200
    assert result.body is not None
    assert result.body["result"]["protocolVersion"] == MCP_PROTOCOL_VERSION
    assert result.headers == {"MCP-Session-Id": "a" * 43}
    assert "a" * 43 not in repr(result)


def test_later_registered_request_requires_matching_session_context_without_exposing_it_to_tools() -> None:
    application, calls = _application()
    initialized = application.handle(_principal(), _initialize())
    identifier = initialized.headers["MCP-Session-Id"]

    missing = application.handle(_principal(), {"id": 2, "method": "tools/list"})
    mismatched = application.handle(
        _principal("other"),
        {"id": 3, "method": "tools/list"},
        session_id=identifier,
        protocol_version=MCP_PROTOCOL_VERSION,
    )
    accepted = application.handle(
        _principal(),
        {
            "id": 4,
            "method": "tools/call",
            "params": {"name": "synthetic", "arguments": {}},
        },
        session_id=identifier,
        protocol_version=MCP_PROTOCOL_VERSION,
    )

    assert missing.status_code == 400
    assert missing.body is None
    assert mismatched.status_code == 404
    assert mismatched.body is None
    assert accepted.status_code == 200
    assert accepted.headers == {}
    assert calls == [{}]


def test_compatibility_mode_uses_only_a_valid_registered_session_protocol_when_header_is_absent() -> None:
    application, calls = _application(strict_protocol_version=False)
    initialized = application.handle(_principal(), _initialize())
    identifier = initialized.headers["MCP-Session-Id"]

    accepted = application.handle(
        _principal(),
        {
            "id": 2,
            "method": "tools/call",
            "params": {"name": "synthetic", "arguments": {}},
        },
        session_id=identifier,
    )
    unsupported = application.handle(
        _principal(),
        {"id": 3, "method": "tools/list"},
        session_id=identifier,
        protocol_version="unsupported",
    )
    missing_session = application.handle(
        _principal(),
        {"id": 4, "method": "tools/list"},
    )
    anonymous = application.handle(Principal.anonymous(), {"id": 5, "method": "ping"})

    assert accepted.status_code == 200
    assert unsupported.status_code == 400
    assert unsupported.body is None
    assert missing_session.status_code == 400
    assert anonymous.status_code == 400
    assert calls == [{}]


def test_compatibility_mode_uses_the_validated_session_fallback_for_stream_and_termination() -> None:
    application, _ = _application(strict_protocol_version=False)
    identifier = application.handle(_principal(), _initialize()).headers["MCP-Session-Id"]

    stream = application.validate_stream(
        _principal(),
        session_id=identifier,
        protocol_version=None,
    )
    terminated = application.terminate_session(
        _principal(),
        session_id=identifier,
        protocol_version=None,
    )
    absent = application.validate_stream(
        _principal(),
        session_id=identifier,
        protocol_version=None,
    )

    assert stream.status_code == 200
    assert terminated.status_code == 204
    assert absent.status_code == 404


def test_registered_initialize_rejects_transport_context_and_bad_negotiation_without_minting() -> None:
    application, _ = _application()

    carrying_session = application.handle(
        _principal(),
        _initialize(),
        session_id="a" * 43,
    )
    unsupported = application.handle(
        _principal(),
        {"id": 2, "method": "initialize", "params": {"protocolVersion": "other"}},
    )
    no_session = application.handle(
        _principal(),
        {"id": 3, "method": "tools/list"},
        session_id="a" * 43,
        protocol_version=MCP_PROTOCOL_VERSION,
    )

    assert carrying_session.status_code == 400
    assert unsupported.status_code == 400
    assert no_session.status_code == 404


def test_anonymous_and_initialize_notification_requests_remain_stateless() -> None:
    application, _ = _application()

    anonymous = application.handle(Principal.anonymous(), _initialize())
    anonymous_followup = application.handle(
        Principal.anonymous(),
        {"id": 2, "method": "ping"},
        protocol_version=MCP_PROTOCOL_VERSION,
    )
    missing_anonymous_protocol = application.handle(
        Principal.anonymous(), {"id": 3, "method": "ping"}
    )
    notification = application.handle(_principal(), _initialize(request_id=None))

    assert anonymous.status_code == 200
    assert anonymous.headers == {}
    assert anonymous_followup.status_code == 200
    assert missing_anonymous_protocol.status_code == 400
    assert notification.status_code == 202
    assert notification.body is None
    assert notification.headers == {}


def test_application_returns_capacity_outcome_without_dispatching_initialize() -> None:
    tokens = iter(("a" * 43, "b" * 43))
    application, _ = _application(token_factory=lambda: next(tokens), maximum_sessions=1)

    first = application.handle(_principal(), _initialize())
    second = application.handle(_principal("other"), _initialize())

    assert first.status_code == 200
    assert second.status_code == 503
    assert second.body is None
    assert second.headers == {}


def test_session_module_is_host_owned_and_only_the_application_boundary_imports_it() -> None:
    session_importers: list[str] = []
    for package in ("mymcp/authentication", "mymcp/mcp", "mymcp/plugin", "mymcp/plugins"):
        for module in (REPOSITORY_ROOT / package).rglob("*.py"):
            tree = ast.parse(module.read_text(encoding="utf-8"))
            imports = {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            } | {
                node.module
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module is not None
            }
            if "mymcp.host.sessions" in imports:
                session_importers.append(str(module.relative_to(REPOSITORY_ROOT)))

    host_tree = ast.parse(
        (REPOSITORY_ROOT / "mymcp/host/mcp_application.py").read_text(encoding="utf-8")
    )
    host_imports = {
        node.module
        for node in ast.walk(host_tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert session_importers == []
    assert "mymcp.host.sessions" in host_imports
