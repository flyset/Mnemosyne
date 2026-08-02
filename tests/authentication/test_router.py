from dataclasses import FrozenInstanceError

import pytest

from mymcp.authentication.contracts import (
    AdapterId,
    AuthenticationEvidence,
    AuthenticationFailure,
    AuthenticationRequestContext,
    AuthenticationSuccess,
    EvidenceRoute,
    PrincipalKind,
)
from mymcp.authentication.router import (
    AdapterRegistration,
    Authenticator,
    compose_authenticator,
)


class SyntheticAdapter:
    def __init__(
        self,
        result: AuthenticationSuccess | AuthenticationFailure | object,
    ) -> None:
        self.result = result
        self.calls: list[
            tuple[AuthenticationEvidence, AuthenticationRequestContext]
        ] = []

    def authenticate(
        self,
        evidence: AuthenticationEvidence,
        context: AuthenticationRequestContext,
    ) -> AuthenticationSuccess | AuthenticationFailure:
        self.calls.append((evidence, context))
        return self.result  # type: ignore[return-value]


LOCAL_ROUTE = EvidenceRoute("authorization", "bearer", "local")
OAUTH_ROUTE = EvidenceRoute("authorization", "bearer", "oauth")
CONTEXT = AuthenticationRequestContext("POST", "mcp")


def _registration(
    adapter_id: str,
    route: EvidenceRoute,
    adapter: SyntheticAdapter,
) -> AdapterRegistration:
    return AdapterRegistration(AdapterId(adapter_id), route, adapter)


def test_evidence_free_request_is_anonymous_only_when_enabled() -> None:
    enabled = compose_authenticator((), anonymous_enabled=True)
    disabled = compose_authenticator((), anonymous_enabled=False)

    principal = enabled.authenticate(None, CONTEXT)

    assert principal.kind is PrincipalKind.ANONYMOUS
    assert disabled.authenticate(None, CONTEXT) == AuthenticationFailure("no_evidence")


def test_two_exact_routes_select_one_adapter_and_namespace_subjects() -> None:
    local = SyntheticAdapter(AuthenticationSuccess("same-subject"))
    oauth = SyntheticAdapter(AuthenticationSuccess("same-subject"))
    authenticator = compose_authenticator(
        (
            _registration("local-client", LOCAL_ROUTE, local),
            _registration("external-oauth", OAUTH_ROUTE, oauth),
        ),
        anonymous_enabled=True,
    )
    evidence = AuthenticationEvidence(OAUTH_ROUTE, b"opaque")

    principal = authenticator.authenticate(evidence, CONTEXT)

    assert principal.adapter_id == AdapterId("external-oauth")
    assert principal.subject == "same-subject"
    assert principal.principal_id.startswith("registered:external-oauth:")
    assert local.calls == []
    assert oauth.calls == [(evidence, CONTEXT)]


def test_adapter_failure_never_falls_back_to_anonymous_or_another_adapter() -> None:
    rejected = SyntheticAdapter(AuthenticationFailure("rejected"))
    other = SyntheticAdapter(AuthenticationSuccess("other"))
    authenticator = compose_authenticator(
        (
            _registration("rejected", LOCAL_ROUTE, rejected),
            _registration("other", OAUTH_ROUTE, other),
        ),
        anonymous_enabled=True,
    )

    result = authenticator.authenticate(
        AuthenticationEvidence(LOCAL_ROUTE, b"bad"), CONTEXT
    )

    assert result == AuthenticationFailure("rejected")
    assert len(rejected.calls) == 1
    assert other.calls == []


def test_unsupported_evidence_invokes_no_adapter_and_never_becomes_anonymous() -> None:
    adapter = SyntheticAdapter(AuthenticationSuccess("subject"))
    authenticator = compose_authenticator(
        (_registration("local-client", LOCAL_ROUTE, adapter),),
        anonymous_enabled=True,
    )

    result = authenticator.authenticate(
        AuthenticationEvidence(EvidenceRoute("authorization", "basic", None), b"x"),
        CONTEXT,
    )

    assert result == AuthenticationFailure("unsupported")
    assert adapter.calls == []


@pytest.mark.parametrize(
    ("registrations", "message"),
    [
        (
            (
                _registration("duplicate", LOCAL_ROUTE, SyntheticAdapter(AuthenticationSuccess("a"))),
                _registration("duplicate", OAUTH_ROUTE, SyntheticAdapter(AuthenticationSuccess("b"))),
            ),
            "duplicate adapter id",
        ),
        (
            (
                _registration("first", LOCAL_ROUTE, SyntheticAdapter(AuthenticationSuccess("a"))),
                _registration("second", LOCAL_ROUTE, SyntheticAdapter(AuthenticationSuccess("b"))),
            ),
            "duplicate evidence route",
        ),
    ],
)
def test_composition_rejects_ambiguous_registrations_without_partial_result(
    registrations: tuple[AdapterRegistration, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=f"^{message}$"):
        compose_authenticator(registrations, anonymous_enabled=True)


def test_registration_and_authenticator_are_frozen_snapshots() -> None:
    adapter = SyntheticAdapter(AuthenticationSuccess("subject"))
    registrations = [_registration("local-client", LOCAL_ROUTE, adapter)]
    authenticator = compose_authenticator(registrations, anonymous_enabled=True)
    registrations.clear()

    assert authenticator.registrations[0].adapter is adapter
    with pytest.raises(FrozenInstanceError):
        authenticator.anonymous_enabled = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        authenticator.registrations[0].route = OAUTH_ROUTE  # type: ignore[misc]


def test_composition_requires_real_adapter_and_boolean() -> None:
    with pytest.raises(ValueError, match="^invalid adapter registration$"):
        AdapterRegistration(AdapterId("invalid"), LOCAL_ROUTE, object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="^invalid anonymous enablement$"):
        compose_authenticator((), anonymous_enabled=1)  # type: ignore[arg-type]

    class NonCallableAdapter:
        authenticate = None

    with pytest.raises(ValueError, match="^invalid adapter registration$"):
        AdapterRegistration(  # type: ignore[arg-type]
            AdapterId("invalid"), LOCAL_ROUTE, NonCallableAdapter()
        )


def test_invalid_adapter_result_fails_closed() -> None:
    adapter = SyntheticAdapter(object())
    authenticator = compose_authenticator(
        (_registration("local-client", LOCAL_ROUTE, adapter),),
        anonymous_enabled=True,
    )

    result = authenticator.authenticate(
        AuthenticationEvidence(LOCAL_ROUTE, b"opaque"), CONTEXT
    )

    assert result == AuthenticationFailure("rejected")


def test_adapter_exception_fails_closed_without_fallback() -> None:
    class FailingAdapter:
        def authenticate(
            self,
            evidence: AuthenticationEvidence,
            context: AuthenticationRequestContext,
        ) -> AuthenticationSuccess | AuthenticationFailure:
            raise RuntimeError("credential detail")

    authenticator = compose_authenticator(
        (AdapterRegistration(AdapterId("failing"), LOCAL_ROUTE, FailingAdapter()),),
        anonymous_enabled=True,
    )

    result = authenticator.authenticate(
        AuthenticationEvidence(LOCAL_ROUTE, b"opaque"), CONTEXT
    )

    assert result == AuthenticationFailure("rejected")


def test_authenticator_rejects_invalid_call_values() -> None:
    authenticator = compose_authenticator((), anonymous_enabled=True)

    with pytest.raises(ValueError, match="^invalid authentication request$"):
        authenticator.authenticate("evidence", CONTEXT)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="^invalid authentication request$"):
        authenticator.authenticate(None, "context")  # type: ignore[arg-type]


def test_authenticator_type_is_not_directly_constructible() -> None:
    with pytest.raises(TypeError):
        Authenticator(anonymous_enabled=True, registrations=())  # type: ignore[call-arg]
