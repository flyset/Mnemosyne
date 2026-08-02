import ast
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from mymcp.authentication.contracts import (
    AdapterId,
    AuthenticationAdapter,
    AuthenticationEvidence,
    AuthenticationFailure,
    AuthenticationRequestContext,
    AuthenticationSuccess,
    EvidenceRoute,
    Principal,
    PrincipalKind,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUTHENTICATION_PACKAGE = PROJECT_ROOT / "mymcp" / "authentication"


@pytest.mark.parametrize("value", ["a", "local-client", "oauth2"])
def test_adapter_id_accepts_bounded_lowercase_kebab_identity(value: str) -> None:
    assert AdapterId(value).value == value


@pytest.mark.parametrize(
    "value",
    ["", "Local", "local_client", "-local", "local-", "local--client", "a" * 65],
)
def test_adapter_id_rejects_invalid_identity(value: str) -> None:
    with pytest.raises(ValueError, match="^invalid adapter id$"):
        AdapterId(value)


def test_anonymous_principal_is_fixed_and_frozen() -> None:
    principal = Principal.anonymous()

    assert principal.kind is PrincipalKind.ANONYMOUS
    assert principal.adapter_id is None
    assert principal.subject is None
    assert principal.principal_id == "anonymous"
    with pytest.raises(FrozenInstanceError):
        principal.principal_id = "registered:x:eA"  # type: ignore[misc]


def test_registered_principal_is_host_constructed_and_namespaced() -> None:
    first = Principal.registered(AdapterId("first"), "same:subject")
    second = Principal.registered(AdapterId("second"), "same:subject")

    assert first.kind is PrincipalKind.REGISTERED
    assert first.adapter_id == AdapterId("first")
    assert first.subject == "same:subject"
    assert first.principal_id == "registered:first:c2FtZTpzdWJqZWN0"
    assert second.principal_id == "registered:second:c2FtZTpzdWJqZWN0"
    assert first.principal_id != second.principal_id


def test_principal_constructor_is_not_publicly_rewritable() -> None:
    with pytest.raises(TypeError):
        Principal(  # type: ignore[call-arg]
            kind=PrincipalKind.REGISTERED,
            adapter_id=AdapterId("first"),
            subject="subject",
            principal_id="attacker-selected",
        )


@pytest.mark.parametrize(
    "subject",
    ["", " ", "line\nfeed", "control\x00", "a" * 257, "e\u0301"],
)
def test_registered_principal_rejects_invalid_subject(subject: str) -> None:
    with pytest.raises(ValueError, match="^invalid principal subject$"):
        Principal.registered(AdapterId("first"), subject)


def test_registered_principal_accepts_bounded_unicode_subject_exactly() -> None:
    subject = "client-é-東京"

    principal = Principal.registered(AdapterId("first"), subject)

    assert principal.subject == subject


def test_registered_principal_enforces_utf8_byte_bound() -> None:
    subject = "😀" * 256

    assert len(subject.encode("utf-8")) == 1024
    assert Principal.registered(AdapterId("first"), subject).subject == subject
    with pytest.raises(ValueError, match="^invalid principal subject$"):
        Principal.registered(AdapterId("first"), subject + "a")


def test_evidence_route_is_immutable_and_strict() -> None:
    route = EvidenceRoute(source="authorization", scheme="bearer", profile="local")

    assert route.source == "authorization"
    with pytest.raises(FrozenInstanceError):
        route.scheme = "basic"  # type: ignore[misc]
    with pytest.raises(ValueError, match="^invalid evidence route$"):
        EvidenceRoute(source="Authorization", scheme="bearer", profile="local")
    with pytest.raises(ValueError, match="^invalid evidence route$"):
        EvidenceRoute(source="authorization", scheme="bearer", profile="x" * 65)


def test_evidence_and_context_are_bounded_immutable_values() -> None:
    route = EvidenceRoute("authorization", "bearer", None)
    evidence = AuthenticationEvidence(route=route, payload=b"opaque")
    context = AuthenticationRequestContext(http_method="POST", endpoint="mcp")

    assert evidence.payload == b"opaque"
    assert "opaque" not in repr(evidence)
    assert context.endpoint == "mcp"
    with pytest.raises(FrozenInstanceError):
        evidence.payload = b"changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="^invalid authentication evidence$"):
        AuthenticationEvidence(route=route, payload=b"")
    assert len(AuthenticationEvidence(route=route, payload=b"x" * 8192).payload) == 8192
    with pytest.raises(ValueError, match="^invalid authentication evidence$"):
        AuthenticationEvidence(route=route, payload=b"x" * 8193)
    with pytest.raises(ValueError, match="^invalid authentication request context$"):
        AuthenticationRequestContext(http_method="post", endpoint="mcp")


def test_adapter_outcomes_are_bounded_and_do_not_construct_principals() -> None:
    success = AuthenticationSuccess(subject="client-é")
    failure = AuthenticationFailure(code="rejected")

    assert success.subject == "client-é"
    assert failure.code == "rejected"
    with pytest.raises(ValueError, match="^invalid authentication failure$"):
        AuthenticationFailure(code="provider rejected token value")
    with pytest.raises(ValueError, match="^invalid authentication failure$"):
        AuthenticationFailure(code=[])  # type: ignore[arg-type]


def test_adapter_protocol_uses_only_authentication_contract_values() -> None:
    class SyntheticAdapter:
        def authenticate(
            self,
            evidence: AuthenticationEvidence,
            context: AuthenticationRequestContext,
        ) -> AuthenticationSuccess | AuthenticationFailure:
            return AuthenticationSuccess("subject")

    assert isinstance(SyntheticAdapter(), AuthenticationAdapter)


def test_authentication_package_imports_only_standard_library() -> None:
    imports: set[str] = set()
    for module in AUTHENTICATION_PACKAGE.glob("*.py"):
        tree = ast.parse(module.read_text(encoding="utf-8"))
        imports.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        imports.update(
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        )

    assert all(
        imported.startswith("mymcp.authentication")
        or not imported.startswith(("mymcp", "fastapi"))
        for imported in imports
    )
