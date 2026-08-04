from dataclasses import FrozenInstanceError

import pytest

from mymcp.authentication.contracts import AdapterId, Principal
from mymcp.host.runtime import RuntimeGenerationId
from mymcp.host.sessions import (
    MCP_PROTOCOL_VERSION,
    MCPProtocolSession,
    ProcessLocalSessionStore,
    SessionCapacityError,
    SessionId,
)


def _principal(subject: str = "client") -> Principal:
    return Principal.registered(AdapterId("local-client"), subject)


def _store(
    *,
    now: list[float],
    generation: str = "generation-one",
    token_factory=lambda: "a" * 43,
) -> ProcessLocalSessionStore:
    return ProcessLocalSessionStore(
        RuntimeGenerationId(generation),
        monotonic_clock=lambda: now[0],
        token_factory=token_factory,
    )


def test_session_id_accepts_only_the_fixed_opaque_base64url_shape() -> None:
    identifier = SessionId("A" * 43)

    assert identifier.value == "A" * 43

    for value in ("", "a" * 42, "a" * 44, "a" * 42 + "/", "a" * 42 + " "):
        with pytest.raises(ValueError, match="^invalid MCP session id$"):
            SessionId(value)


def test_session_context_is_immutable_and_redacts_its_identifier_and_principal() -> None:
    now = [100.0]
    session = _store(now=now).create(_principal("private-subject"))

    assert isinstance(session, MCPProtocolSession)
    assert session.protocol_version == MCP_PROTOCOL_VERSION
    assert session.runtime_generation == RuntimeGenerationId("generation-one")
    assert session.created_at == 100.0
    assert session.last_valid_activity_at == 100.0
    assert session.absolute_expires_at == 28_900.0
    assert "a" * 43 not in repr(session)
    assert "private-subject" not in repr(session)
    with pytest.raises(FrozenInstanceError):
        session.protocol_version = "other"  # type: ignore[misc]


def test_session_creation_requires_a_registered_principal_and_unique_secure_id() -> None:
    now = [0.0]
    tokens = iter(("a" * 43, "a" * 43, "b" * 43))
    store = _store(now=now, token_factory=lambda: next(tokens))

    first = store.create(_principal())
    second = store.create(_principal("second"))

    assert first.identifier != second.identifier
    with pytest.raises(ValueError, match="^registered principal required for MCP session$"):
        store.create(Principal.anonymous())


def test_valid_session_lookup_binds_full_principal_generation_and_protocol_and_refreshes_activity() -> None:
    now = [10.0]
    store = _store(now=now)
    principal = _principal()
    session = store.create(principal)
    now[0] = 20.0

    validated = store.validate(
        session.identifier,
        principal,
        RuntimeGenerationId("generation-one"),
        MCP_PROTOCOL_VERSION,
    )

    assert validated is not None
    assert validated.last_valid_activity_at == 20.0
    assert store.validate(
        session.identifier,
        _principal("other"),
        RuntimeGenerationId("generation-one"),
        MCP_PROTOCOL_VERSION,
    ) is None
    assert store.validate(
        session.identifier,
        principal,
        RuntimeGenerationId("generation-two"),
        MCP_PROTOCOL_VERSION,
    ) is None
    assert store.validate(
        session.identifier,
        principal,
        RuntimeGenerationId("generation-one"),
        "other",
    ) is None


def test_session_expiry_is_bounded_by_inactivity_and_absolute_lifetime_without_background_cleanup() -> None:
    now = [0.0]
    tokens = iter(("a" * 43, "b" * 43))
    store = _store(now=now, token_factory=lambda: next(tokens))
    principal = _principal()
    inactive = store.create(principal)
    absolute = store.create(_principal("absolute"))

    now[0] = 1_799.0
    assert store.validate(
        absolute.identifier,
        _principal("absolute"),
        RuntimeGenerationId("generation-one"),
        MCP_PROTOCOL_VERSION,
    ) is not None
    now[0] = 1_801.0
    assert store.validate(
        inactive.identifier,
        principal,
        RuntimeGenerationId("generation-one"),
        MCP_PROTOCOL_VERSION,
    ) is None

    now[0] = 28_800.0
    assert store.validate(
        absolute.identifier,
        _principal("absolute"),
        RuntimeGenerationId("generation-one"),
        MCP_PROTOCOL_VERSION,
    ) is None


def test_session_store_is_process_local_terminates_exact_valid_session_and_refuses_capacity_eviction() -> None:
    now = [0.0]
    principal = _principal()
    store = ProcessLocalSessionStore(
        RuntimeGenerationId("generation-one"),
        monotonic_clock=lambda: now[0],
        token_factory=lambda: "a" * 43,
        maximum_sessions=1,
    )
    session = store.create(principal)

    with pytest.raises(SessionCapacityError, match="^MCP session capacity exhausted$"):
        store.create(_principal("second"))
    assert store.terminate(
        session.identifier,
        principal,
        RuntimeGenerationId("generation-one"),
        MCP_PROTOCOL_VERSION,
    ) is True
    assert store.validate(
        session.identifier,
        principal,
        RuntimeGenerationId("generation-one"),
        MCP_PROTOCOL_VERSION,
    ) is None

    restarted = _store(now=now)
    assert restarted.validate(
        session.identifier,
        principal,
        RuntimeGenerationId("generation-one"),
        MCP_PROTOCOL_VERSION,
    ) is None
