import ast
import base64
import hashlib
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import mymcp.authentication.adapters.operator_bearer as operator_bearer
from mymcp.authentication.contracts import (
    AuthenticationAdapter,
    AuthenticationEvidence,
    AuthenticationFailure,
    AuthenticationRequestContext,
    AuthenticationSuccess,
    EvidenceRoute,
)
from mymcp.authentication.adapters.operator_bearer import (
    DUMMY_DIGEST,
    OperatorBearerAdapter,
    OperatorBearerCredential,
    OperatorBearerVerifierRecord,
    build_operator_bearer_verifier,
    parse_operator_bearer_credential,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
OPERATOR_BEARER_MODULE = (
    PROJECT_ROOT / "mymcp" / "authentication" / "adapters" / "operator_bearer.py"
)

ROUTE = EvidenceRoute("authorization", "bearer", None)
CONTEXT = AuthenticationRequestContext("POST", "mcp")


def _secret() -> bytes:
    return bytes(range(32))


def _secret_text(secret: bytes | None = None) -> str:
    return (
        base64.urlsafe_b64encode(_secret() if secret is None else secret)
        .rstrip(b"=")
        .decode("ascii")
    )


def _credential_text(
    credential_id: str = "a" * 32,
    secret: bytes | None = None,
) -> str:
    return f"mymcp1.{credential_id}.{_secret_text(secret)}"


def _record(
    credential_id: str,
    subject: str,
    digest: bytes,
) -> OperatorBearerVerifierRecord:
    return OperatorBearerVerifierRecord(credential_id, subject, digest)


def _verifier(*records: OperatorBearerVerifierRecord) -> operator_bearer.OperatorBearerVerifier:
    return build_operator_bearer_verifier(records)


def _adapter() -> OperatorBearerAdapter:
    secret = _secret()
    return OperatorBearerAdapter(
        build_operator_bearer_verifier(
            [_record("a" * 32, "stable-subject", hashlib.sha256(secret).digest())]
        )
    )


def test_parse_credential_accepts_exact_grammar_and_redacts_secret() -> None:
    secret = _secret()

    credential = parse_operator_bearer_credential(_credential_text(secret=secret))

    assert isinstance(credential, OperatorBearerCredential)
    assert credential.credential_id == "a" * 32
    assert credential.secret == secret
    assert _secret_text(secret) not in repr(credential)
    assert _credential_text(secret=secret) not in repr(credential)
    with pytest.raises(FrozenInstanceError):
        credential.secret = b"\x00" * 32  # type: ignore[misc]


@pytest.mark.parametrize(
    "value",
    [
        "mymcp2." + "a" * 32 + "." + _secret_text(),
        "MYMCP1." + "a" * 32 + "." + _secret_text(),
        "mymcp1." + "A" * 32 + "." + _secret_text(),
        "mymcp1." + "a" * 31 + "." + _secret_text(),
        "mymcp1." + "a" * 33 + "." + _secret_text(),
        "mymcp1." + "a" * 31 + "g" + "." + _secret_text(),
        "mymcp1." + "a" * 32 + "." + _secret_text() + "a",
        "mymcp1." + "a" * 32 + "." + _secret_text()[:-1],
        "mymcp1." + "a" * 32 + "." + _secret_text() + "=",
        "mymcp1." + "a" * 32 + "." + _secret_text()[:-1] + "+",
        "mymcp1." + "a" * 32 + "." + _secret_text()[:-1] + "/",
        "mymcp1." + "a" * 32 + "." + _secret_text() + ".extra",
        "mymcp1.." + _secret_text(),
        "mymcp1." + "a" * 32 + ".",
        " " + _credential_text(),
        _credential_text() + " ",
        "mymcp1.\t" + "a" * 32 + "." + _secret_text(),
        "mymcp1." + "é" * 32 + "." + _secret_text(),
        "mymcp1",
        "",
    ],
)
def test_parse_credential_rejects_invalid_grammar(value: str) -> None:
    with pytest.raises(ValueError, match="^invalid operator bearer credential$"):
        parse_operator_bearer_credential(value)


def test_parse_credential_rejects_noncanonical_secret_encoding() -> None:
    secret_text = _secret_text()
    last = secret_text[-1]
    for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_":
        if ord(char) & 0x30 == ord(last) & 0x30 and char != last:
            noncanonical = secret_text[:-1] + char
            break
    else:
        raise AssertionError("no non-canonical base64url candidate found")

    with pytest.raises(ValueError, match="^invalid operator bearer credential$"):
        parse_operator_bearer_credential(f"mymcp1.{'a' * 32}.{noncanonical}")


@pytest.mark.parametrize(
    ("credential_id", "secret"),
    [
        ("a" * 31, b"\x00" * 32),
        ("A" * 32, b"\x00" * 32),
        ("a" * 32, b"\x00" * 31),
        ("a" * 32, b"\x00" * 33),
        ("a" * 32, "text-secret"),
        (123, b"\x00" * 32),
    ],
)
def test_credential_rejects_invalid_components(
    credential_id: object,
    secret: object,
) -> None:
    with pytest.raises(ValueError, match="^invalid operator bearer credential$"):
        OperatorBearerCredential(credential_id, secret)  # type: ignore[arg-type]


def test_verifier_record_is_immutable_and_secret_redacted() -> None:
    digest = hashlib.sha256(_secret()).digest()
    record = _record("a" * 32, "subject", digest)

    assert record.credential_id == "a" * 32
    assert record.subject == "subject"
    assert record.digest == digest
    assert digest.hex() not in repr(record)
    with pytest.raises(FrozenInstanceError):
        record.digest = b"\x00" * 32  # type: ignore[misc]


@pytest.mark.parametrize(
    ("credential_id", "subject", "digest"),
    [
        ("a" * 31, "subject", hashlib.sha256(b"x").digest()),
        ("A" * 32, "subject", hashlib.sha256(b"x").digest()),
        ("a" * 32, "", hashlib.sha256(b"x").digest()),
        ("a" * 32, "subject", b"short"),
        ("a" * 32, "subject", b"x" * 33),
        ("a" * 32, "subject", "not-bytes"),
        (123, "subject", hashlib.sha256(b"x").digest()),
    ],
)
def test_verifier_record_rejects_invalid_fields(
    credential_id: object,
    subject: object,
    digest: object,
) -> None:
    with pytest.raises(ValueError, match="^invalid operator bearer verifier record$"):
        OperatorBearerVerifierRecord(credential_id, subject, digest)  # type: ignore[arg-type]


def test_verifier_rejects_duplicate_credential_ids() -> None:
    with pytest.raises(ValueError, match="^duplicate operator bearer credential id$"):
        _verifier(
            _record("a" * 32, "first", hashlib.sha256(b"x").digest()),
            _record("a" * 32, "second", hashlib.sha256(b"y").digest()),
        )


def test_verifier_allows_duplicate_subjects_for_rotation() -> None:
    secret_a = _secret()
    secret_b = bytes([255]) * 32
    verifier = _verifier(
        _record("a" * 32, "shared-subject", hashlib.sha256(secret_a).digest()),
        _record("b" * 32, "shared-subject", hashlib.sha256(secret_b).digest()),
    )

    assert (
        verifier.verify(parse_operator_bearer_credential(_credential_text(secret=secret_a)))
        is True
    )
    assert (
        verifier.verify(
            parse_operator_bearer_credential(
                _credential_text(credential_id="b" * 32, secret=secret_b)
            )
        )
        is True
    )


def test_verifier_is_immutable_snapshot() -> None:
    records = [_record("a" * 32, "subject", hashlib.sha256(b"x").digest())]
    verifier = build_operator_bearer_verifier(records)
    records.clear()

    assert verifier.records[0].credential_id == "a" * 32
    assert verifier.records[0].subject == "subject"
    with pytest.raises(FrozenInstanceError):
        verifier.records = ()  # type: ignore[misc]


def test_verifier_verify_rejects_non_credential() -> None:
    verifier = build_operator_bearer_verifier(())

    with pytest.raises(ValueError, match="^invalid operator bearer credential$"):
        verifier.verify("text")  # type: ignore[arg-type]


def test_verifier_builder_rejects_non_record_input() -> None:
    with pytest.raises(ValueError, match="^invalid operator bearer verifier$"):
        build_operator_bearer_verifier([object()])  # type: ignore[list-item]


def test_verifier_accepts_exact_secret_and_rejects_wrong_secret() -> None:
    secret = _secret()
    digest = hashlib.sha256(secret).digest()
    verifier = _verifier(_record("a" * 32, "subject", digest))
    wrong_secret = bytes([1]) + secret[1:]

    assert verifier.verify(parse_operator_bearer_credential(_credential_text(secret=secret))) is True
    assert (
        verifier.verify(
            parse_operator_bearer_credential(_credential_text(secret=wrong_secret))
        )
        is False
    )


def test_verifier_digest_is_sha256_of_decoded_32_byte_secret() -> None:
    secret = _secret()
    credential = parse_operator_bearer_credential(_credential_text(secret=secret))
    assert credential.secret == secret
    expected = hashlib.sha256(secret).digest()
    verifier = _verifier(_record("a" * 32, "subject", expected))

    assert verifier.verify(credential) is True

    wrong_digest = hashlib.sha256(_credential_text(secret=secret).encode("utf-8")).digest()
    assert _verifier(_record("a" * 32, "subject", wrong_digest)).verify(credential) is False


def test_verifier_dummy_digest_is_fixed_32_byte_value() -> None:
    assert isinstance(DUMMY_DIGEST, bytes)
    assert len(DUMMY_DIGEST) == 32
    assert build_operator_bearer_verifier(()).find("unknown") is None


def test_verifier_unknown_id_performs_dummy_comparison_then_rejects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = _secret()
    digest = hashlib.sha256(secret).digest()
    verifier = _verifier(_record("a" * 32, "subject", digest))
    credential = parse_operator_bearer_credential(
        _credential_text(credential_id="b" * 32, secret=secret)
    )
    calls: list[tuple[bytes, bytes]] = []

    def recording_compare(left: bytes, right: bytes) -> bool:
        calls.append((bytes(left), bytes(right)))
        return True

    monkeypatch.setattr(operator_bearer, "compare_digest", recording_compare)

    assert verifier.verify(credential) is False
    assert calls == [(digest, DUMMY_DIGEST)]


def test_adapter_is_protocol_adapter_claiming_exact_route() -> None:
    adapter = _adapter()

    assert isinstance(adapter, AuthenticationAdapter)
    assert adapter.route == EvidenceRoute("authorization", "bearer", None)


def test_adapter_returns_registered_subject_for_valid_credential() -> None:
    adapter = _adapter()

    result = adapter.authenticate(
        AuthenticationEvidence(ROUTE, _credential_text().encode("utf-8")),
        CONTEXT,
    )

    assert result == AuthenticationSuccess("stable-subject")


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (b"opaque garbage", AuthenticationFailure("malformed")),
        (
            _credential_text(credential_id="b" * 32).encode("utf-8"),
            AuthenticationFailure("rejected"),
        ),
        (
            _credential_text(secret=bytes(32)).encode("utf-8"),
            AuthenticationFailure("rejected"),
        ),
        (
            "mymcp1.éééééééééééééééé.zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz".encode(
                "utf-8"
            ),
            AuthenticationFailure("malformed"),
        ),
    ],
)
def test_adapter_returns_bounded_failures(payload: bytes, expected: AuthenticationFailure) -> None:
    adapter = _adapter()

    assert adapter.authenticate(AuthenticationEvidence(ROUTE, payload), CONTEXT) == expected


def test_adapter_rejects_evidence_from_other_route() -> None:
    adapter = _adapter()

    result = adapter.authenticate(
        AuthenticationEvidence(EvidenceRoute("authorization", "basic", None), b"x"),
        CONTEXT,
    )

    assert result == AuthenticationFailure("unsupported")


def test_adapter_and_verifier_never_retain_plaintext_credential() -> None:
    secret_text = _secret_text()
    adapter = _adapter()
    adapter.authenticate(
        AuthenticationEvidence(ROUTE, _credential_text().encode("utf-8")),
        CONTEXT,
    )

    assert secret_text not in repr(adapter)
    assert secret_text not in str(adapter)
    assert secret_text not in repr(adapter.verifier)
    assert secret_text not in repr(adapter.verifier.records[0])


def test_operator_bearer_module_imports_only_standard_library_and_authentication() -> None:
    tree = ast.parse(OPERATOR_BEARER_MODULE.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)

    assert all(
        imported.startswith("mymcp.authentication")
        or not imported.startswith(("mymcp", "fastapi"))
        for imported in imports
    )
