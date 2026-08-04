from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from mymcp.authentication.contracts import Principal, PrincipalKind
from mymcp.host.runtime import RuntimeGenerationId
from mymcp.host.sessions import (
    MCP_PROTOCOL_VERSION,
    ProcessLocalSessionStore,
    SessionCapacityError,
    SessionId,
)
from mymcp.mcp.dispatcher import MCPDispatcher


_DEFAULT_RUNTIME_GENERATION = RuntimeGenerationId("application-default")


@dataclass(frozen=True, slots=True)
class MCPApplicationResult:
    body: dict[str, Any] | None
    status_code: int
    headers: Mapping[str, str] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if (
            (self.body is not None and not isinstance(self.body, dict))
            or self.status_code not in {200, 202, 204, 400, 404, 503}
            or not isinstance(self.headers, Mapping)
            or any(
                not isinstance(name, str) or not isinstance(value, str)
                for name, value in self.headers.items()
            )
        ):
            raise ValueError("invalid MCP application result")
        object.__setattr__(self, "headers", MappingProxyType(dict(self.headers)))


@dataclass(frozen=True, slots=True)
class PrincipalAwareMCPApplication:
    dispatcher: MCPDispatcher
    runtime_generation: RuntimeGenerationId = _DEFAULT_RUNTIME_GENERATION
    sessions: ProcessLocalSessionStore = field(
        default_factory=lambda: ProcessLocalSessionStore(_DEFAULT_RUNTIME_GENERATION),
        repr=False,
    )
    strict_protocol_version: bool = True

    def __post_init__(self) -> None:
        if (
            not isinstance(self.dispatcher, MCPDispatcher)
            or not isinstance(self.runtime_generation, RuntimeGenerationId)
            or not isinstance(self.sessions, ProcessLocalSessionStore)
            or type(self.strict_protocol_version) is not bool
        ):
            raise ValueError("invalid principal-aware MCP application")

    def dispatch(
        self,
        principal: Principal,
        message: Any,
    ) -> dict[str, Any] | None:
        if not isinstance(principal, Principal):
            raise ValueError("invalid authenticated principal")
        return self.dispatcher.dispatch(message)

    def handle(
        self,
        principal: Principal,
        message: Any,
        *,
        session_id: str | None = None,
        protocol_version: str | None = None,
    ) -> MCPApplicationResult:
        if not isinstance(principal, Principal):
            raise ValueError("invalid authenticated principal")
        is_initialize = (
            isinstance(message, dict) and message.get("method") == "initialize"
        )
        is_response_bearing = isinstance(message, dict) and "id" in message
        if principal.kind is PrincipalKind.ANONYMOUS:
            if session_id is not None:
                return MCPApplicationResult(None, 404)
            if not is_initialize and protocol_version != MCP_PROTOCOL_VERSION:
                return MCPApplicationResult(None, 400)
            if is_initialize and protocol_version is not None:
                return MCPApplicationResult(None, 400)
            return self._dispatch_result(message)
        if is_initialize:
            if session_id is not None or protocol_version is not None:
                return MCPApplicationResult(None, 400)
            if not is_response_bearing:
                return self._dispatch_result(message)
            if not self._offers_protocol_version(message):
                return MCPApplicationResult(None, 400)
            response = self.dispatcher.dispatch(message)
            if response is None:
                return MCPApplicationResult(None, 202)
            if "result" not in response:
                return MCPApplicationResult(response, 200)
            try:
                session = self.sessions.create(principal)
            except SessionCapacityError:
                return MCPApplicationResult(None, 503)
            return MCPApplicationResult(
                response,
                200,
                {"MCP-Session-Id": session.identifier.value},
            )
        if session_id is None or (
            protocol_version is None and self.strict_protocol_version
        ):
            return MCPApplicationResult(None, 400)
        if protocol_version is not None and protocol_version != MCP_PROTOCOL_VERSION:
            return MCPApplicationResult(None, 400)
        try:
            identifier = SessionId(session_id)
        except ValueError:
            return MCPApplicationResult(None, 400)
        session = self.sessions.validate(
            identifier,
            principal,
            self.runtime_generation,
            protocol_version,
            allow_missing_protocol_version=not self.strict_protocol_version,
        )
        if session is None:
            return MCPApplicationResult(None, 404)
        return self._dispatch_result(message)

    def validate_stream(
        self,
        principal: Principal,
        *,
        session_id: str | None,
        protocol_version: str | None,
    ) -> MCPApplicationResult:
        return self._validate_session_context(
            principal,
            session_id=session_id,
            protocol_version=protocol_version,
        )

    def terminate_session(
        self,
        principal: Principal,
        *,
        session_id: str | None,
        protocol_version: str | None,
    ) -> MCPApplicationResult:
        context = self._validate_session_context(
            principal,
            session_id=session_id,
            protocol_version=protocol_version,
        )
        if context.status_code != 200:
            return context
        if principal.kind is PrincipalKind.ANONYMOUS:
            return MCPApplicationResult(None, 404)
        assert session_id is not None
        terminated = self.sessions.terminate(
            SessionId(session_id),
            principal,
            self.runtime_generation,
            protocol_version,
            allow_missing_protocol_version=not self.strict_protocol_version,
        )
        return MCPApplicationResult(None, 204 if terminated else 404)

    def _validate_session_context(
        self,
        principal: Principal,
        *,
        session_id: str | None,
        protocol_version: str | None,
    ) -> MCPApplicationResult:
        if not isinstance(principal, Principal):
            raise ValueError("invalid authenticated principal")
        if principal.kind is PrincipalKind.ANONYMOUS:
            if session_id is not None:
                return MCPApplicationResult(None, 404)
            return MCPApplicationResult(
                None,
                200 if protocol_version == MCP_PROTOCOL_VERSION else 400,
            )
        if session_id is None or (
            protocol_version is None and self.strict_protocol_version
        ):
            return MCPApplicationResult(None, 400)
        if protocol_version is not None and protocol_version != MCP_PROTOCOL_VERSION:
            return MCPApplicationResult(None, 400)
        try:
            identifier = SessionId(session_id)
        except ValueError:
            return MCPApplicationResult(None, 400)
        session = self.sessions.validate(
            identifier,
            principal,
            self.runtime_generation,
            protocol_version,
            allow_missing_protocol_version=not self.strict_protocol_version,
        )
        return MCPApplicationResult(None, 200 if session is not None else 404)

    @staticmethod
    def _offers_protocol_version(message: dict[str, Any]) -> bool:
        params = message.get("params")
        return isinstance(params, dict) and params.get("protocolVersion") == MCP_PROTOCOL_VERSION

    def _dispatch_result(self, message: Any) -> MCPApplicationResult:
        body = self.dispatcher.dispatch(message)
        return MCPApplicationResult(body, 202 if body is None else 200)
