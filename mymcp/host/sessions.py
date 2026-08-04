import re
import secrets
from dataclasses import dataclass, field
from time import monotonic
from typing import Callable

from mymcp.authentication.contracts import Principal, PrincipalKind
from mymcp.host.runtime import RuntimeGenerationId


MCP_PROTOCOL_VERSION = "2025-11-25"
_SESSION_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{43}\Z")
_INACTIVITY_TIMEOUT_SECONDS = 30 * 60
_ABSOLUTE_LIFETIME_SECONDS = 8 * 60 * 60
_MAXIMUM_SESSIONS = 128
_TOKEN_ATTEMPTS = 8


@dataclass(frozen=True, slots=True)
class SessionId:
    value: str = field(repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or _SESSION_ID_PATTERN.fullmatch(self.value) is None:
            raise ValueError("invalid MCP session id")


@dataclass(frozen=True, slots=True)
class MCPProtocolSession:
    identifier: SessionId = field(repr=False)
    principal: Principal = field(repr=False)
    runtime_generation: RuntimeGenerationId
    protocol_version: str
    created_at: float
    last_valid_activity_at: float
    absolute_expires_at: float


class SessionCapacityError(RuntimeError):
    pass


class ProcessLocalSessionStore:
    def __init__(
        self,
        runtime_generation: RuntimeGenerationId,
        *,
        monotonic_clock: Callable[[], float] = monotonic,
        token_factory: Callable[[], str] = lambda: secrets.token_urlsafe(32),
        maximum_sessions: int = _MAXIMUM_SESSIONS,
    ) -> None:
        if (
            not isinstance(runtime_generation, RuntimeGenerationId)
            or not callable(monotonic_clock)
            or not callable(token_factory)
            or type(maximum_sessions) is not int
            or maximum_sessions < 1
        ):
            raise ValueError("invalid MCP session store")
        self._runtime_generation = runtime_generation
        self._monotonic_clock = monotonic_clock
        self._token_factory = token_factory
        self._maximum_sessions = maximum_sessions
        self._sessions: dict[SessionId, MCPProtocolSession] = {}

    def create(self, principal: Principal) -> MCPProtocolSession:
        if not isinstance(principal, Principal) or principal.kind is not PrincipalKind.REGISTERED:
            raise ValueError("registered principal required for MCP session")
        now = self._monotonic_clock()
        self._discard_expired(now)
        if len(self._sessions) >= self._maximum_sessions:
            raise SessionCapacityError("MCP session capacity exhausted")
        for _ in range(_TOKEN_ATTEMPTS):
            identifier = SessionId(self._token_factory())
            if identifier not in self._sessions:
                session = MCPProtocolSession(
                    identifier=identifier,
                    principal=principal,
                    runtime_generation=self._runtime_generation,
                    protocol_version=MCP_PROTOCOL_VERSION,
                    created_at=now,
                    last_valid_activity_at=now,
                    absolute_expires_at=now + _ABSOLUTE_LIFETIME_SECONDS,
                )
                self._sessions[identifier] = session
                return session
        raise RuntimeError("MCP session identifier generation failed")

    def validate(
        self,
        identifier: SessionId,
        principal: Principal,
        runtime_generation: RuntimeGenerationId,
        protocol_version: str,
    ) -> MCPProtocolSession | None:
        session = self._lookup(identifier, principal, runtime_generation, protocol_version)
        if session is None:
            return None
        now = self._monotonic_clock()
        if self._expired(session, now):
            self._sessions.pop(identifier, None)
            return None
        refreshed = MCPProtocolSession(
            identifier=session.identifier,
            principal=session.principal,
            runtime_generation=session.runtime_generation,
            protocol_version=session.protocol_version,
            created_at=session.created_at,
            last_valid_activity_at=now,
            absolute_expires_at=session.absolute_expires_at,
        )
        self._sessions[identifier] = refreshed
        return refreshed

    def terminate(
        self,
        identifier: SessionId,
        principal: Principal,
        runtime_generation: RuntimeGenerationId,
        protocol_version: str,
    ) -> bool:
        session = self.validate(identifier, principal, runtime_generation, protocol_version)
        if session is None:
            return False
        self._sessions.pop(identifier, None)
        return True

    def _lookup(
        self,
        identifier: SessionId,
        principal: Principal,
        runtime_generation: RuntimeGenerationId,
        protocol_version: str,
    ) -> MCPProtocolSession | None:
        if (
            not isinstance(identifier, SessionId)
            or not isinstance(principal, Principal)
            or not isinstance(runtime_generation, RuntimeGenerationId)
            or protocol_version != MCP_PROTOCOL_VERSION
        ):
            return None
        session = self._sessions.get(identifier)
        if (
            session is None
            or session.principal != principal
            or session.runtime_generation != runtime_generation
            or session.protocol_version != protocol_version
        ):
            return None
        return session

    def _discard_expired(self, now: float) -> None:
        for identifier, session in tuple(self._sessions.items()):
            if self._expired(session, now):
                self._sessions.pop(identifier, None)

    @staticmethod
    def _expired(session: MCPProtocolSession, now: float) -> bool:
        return (
            now - session.last_valid_activity_at > _INACTIVITY_TIMEOUT_SECONDS
            or now >= session.absolute_expires_at
        )
