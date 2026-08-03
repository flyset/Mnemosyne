import ast
import base64
import hashlib
import json
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

from mymcp.authentication.contracts import (
    AuthenticationAdapter,
    AuthenticationEvidence,
    AuthenticationFailure,
    AuthenticationRequestContext,
    AuthenticationSuccess,
    EvidenceRoute,
)
from mymcp.authentication.adapters.oauth_jwt import (
    MAX_LIFETIME_SECONDS,
    OAuthJwtAdapter,
    OAuthJwtConfig,
    OAuthJwtSnapshot,
    RsaPublicKey,
    SUBJECT_PREFIX,
    build_oauth_jwt_snapshot,
    parse_compact_token,
    project_subject,
    validate_oauth_issuer,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
AUTHENTICATION_PACKAGE = PROJECT_ROOT / "mymcp" / "authentication"
ADAPTERS_PACKAGE = AUTHENTICATION_PACKAGE / "adapters"

ISSUER = "https://auth.example.com"
AUDIENCE = "https://mcp.example.com"
KID = "signing-key-1"
ROUTE = EvidenceRoute("authorization", "bearer", None)
CONTEXT = AuthenticationRequestContext("POST", "mcp")
NOW = 1_700_000_000

ALLOWED_STDLIB = set(sys.stdlib_module_names)
ALLOWED_THIRD_PARTY = frozenset({"jwt", "cryptography"})


def _generate_private(bits: int = 2048) -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=bits)


def _public_key(private: rsa.RSAPrivateKey, kid: str = KID) -> RsaPublicKey:
    numbers = private.public_key().public_numbers()
    return RsaPublicKey(kid, numbers.n, numbers.e)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _signed(
    private: rsa.RSAPrivateKey,
    payload: object,
    kid: str = KID,
    **extra_header: object,
) -> str:
    headers: dict[str, object] = {"typ": "at+jwt", "kid": kid}
    headers.update(extra_header)
    return jwt.encode(payload, private, algorithm="RS256", headers=headers)  # type: ignore[arg-type]


def _payload(
    *,
    now: int = NOW,
    lifetime: int = 240,
    **overrides: object,
) -> dict[str, object]:
    iat_value = overrides.get("iat", now - 60)
    iat_for_exp = iat_value if isinstance(iat_value, int) else now - 60
    exp_value = overrides.get("exp", iat_for_exp + lifetime)
    claims: dict[str, object] = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "stable-subject",
        "exp": exp_value,
        "iat": iat_value,
        "client_id": "mcp-client",
        "jti": "jti-abc-123",
    }
    claims.update(overrides)
    return claims


def _adapter(
    public: RsaPublicKey,
    *,
    now: int = NOW,
    issuer: str = ISSUER,
    audience: str = AUDIENCE,
    keys: tuple[RsaPublicKey, ...] | None = None,
) -> OAuthJwtAdapter:
    selected = keys if keys is not None else (public,)
    config = OAuthJwtConfig(
        issuer=issuer,
        audience=audience,
        snapshot=build_oauth_jwt_snapshot(selected),
        clock=lambda: now,
    )
    return OAuthJwtAdapter(config)


def _evidence(token: str) -> AuthenticationEvidence:
    return AuthenticationEvidence(ROUTE, token.encode("utf-8"))


def _signed_raw(header_text: str, payload_text: str, private: rsa.RSAPrivateKey) -> str:
    signing_input = (
        f"{_b64url(header_text.encode('utf-8'))}.{_b64url(payload_text.encode('utf-8'))}"
    ).encode("ascii")
    signature = private.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    return signing_input.decode("ascii") + "." + _b64url(signature)


def _signed_segments(
    header_segment: str,
    payload_segment: str,
    private: rsa.RSAPrivateKey,
) -> str:
    message = f"{header_segment}.{payload_segment}".encode("ascii")
    signature = private.sign(message, padding.PKCS1v15(), hashes.SHA256())
    return f"{header_segment}.{payload_segment}.{_b64url(signature)}"


@pytest.fixture(scope="module")
def rsa_pair() -> tuple[rsa.RSAPrivateKey, RsaPublicKey]:
    private = _generate_private()
    return private, _public_key(private)


# --------------------------------------------------------------------------- #
# Profile / issuer / projection primitives
# --------------------------------------------------------------------------- #

def test_subject_projection_is_sha256_of_exact_issuer_nul_sub() -> None:
    raw = ISSUER.encode("utf-8") + b"\x00" + "stable-subject".encode("utf-8")
    expected = "oauth-jwt-v1:" + _b64url(hashlib.sha256(raw).digest())

    assert project_subject(ISSUER, "stable-subject") == expected
    assert project_subject(ISSUER, "stable-subject").startswith(SUBJECT_PREFIX)
    assert "stable-subject" not in project_subject(ISSUER, "stable-subject")


@pytest.mark.parametrize(
    "value",
    [
        "https://auth.example.com",
        "https://auth.example.com/realms/prod",
        "https://auth.example.com:443",
        "https://auth.example.com/a/b",
        "https://sub.auth.example.com",
        "https://a-b.example.com",
        "https://auth.123.example.com",
        "https://123.example.com",
        "https://a1.123.example.com",
    ],
)
def test_validate_oauth_issuer_accepts_canonical_https(value: str) -> None:
    assert validate_oauth_issuer(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "http://auth.example.com",
        "https://AUTH.example.com",
        "https://auth.example.com?x=1",
        "https://auth.example.com#frag",
        "https://user:pass@auth.example.com",
        "https://127.0.0.1",
        "https://1.2.3.4",
        "https://0.0.0.0",
        "https://255.255.255.255",
        "https://192.168.1.1",
        "https://[::1]",
        "https://localhost",
        "https://auth.example.com:8443",
        "https://auth.example.com%2Fother",
        "https://auth.example.com/../escape",
        "https://auth.example.com/with-trailing/",
        "auth.example.com",
        "",
        "https://",
        "https://auth.example.com:",
        "https://auth.example.com:443:443",
        "https://auth_example.com",
        "https://auth.example.com.",
        "https://auth..example.com",
        "https://-auth.example.com",
        "https://auth-.example.com",
        "https://" + "a" * 64 + ".example.com",
    ],
)
def test_validate_oauth_issuer_rejects_noncanonical_value(value: str) -> None:
    with pytest.raises(ValueError, match="^invalid oauth issuer$"):
        validate_oauth_issuer(value)


# --------------------------------------------------------------------------- #
# Compact token parsing
# --------------------------------------------------------------------------- #

def test_parse_compact_token_accepts_exactly_three_segments() -> None:
    token = f"{_b64url(b'abc')}.{_b64url(b'def')}.{_b64url(b'g')}"

    assert parse_compact_token(token) == (_b64url(b"abc"), _b64url(b"def"), _b64url(b"g"))


@pytest.mark.parametrize(
    "token",
    [
        "",
        "a",
        "a.b",
        "a.b.c.d",
        ".b.c",
        "a..c",
        "a.b.",
    ],
)
def test_parse_compact_token_rejects_wrong_segment_count(token: str) -> None:
    with pytest.raises(ValueError, match="^invalid oauth jwt token$"):
        parse_compact_token(token)


@pytest.mark.parametrize(
    "token",
    [
        "héader.payload.signature",
        "a.b.\u00a0",
        "\u00e9.\u00e9.\u00e9",
    ],
)
def test_parse_compact_token_rejects_non_ascii(token: str) -> None:
    with pytest.raises(ValueError, match="^invalid oauth jwt token$"):
        parse_compact_token(token)


@pytest.mark.parametrize(
    ("header", "payload", "signature"),
    [
        (_b64url(b"x" * 5000), _b64url(b"y"), _b64url(b"z")),
        (_b64url(b"x"), _b64url(b"y" * 5000), _b64url(b"z")),
        (_b64url(b"x"), _b64url(b"y"), _b64url(b"z" * 5000)),
    ],
)
def test_parse_compact_token_rejects_oversized_segment(
    header: str,
    payload: str,
    signature: str,
) -> None:
    with pytest.raises(ValueError, match="^invalid oauth jwt token$"):
        parse_compact_token(f"{header}.{payload}.{signature}")


@pytest.mark.parametrize(
    "token",
    [
        "one.two",
        "one.two.three.four",
        ".b.c",
        "a..c",
        "a.b.",
        "héader.payload.signature",
    ],
)
def test_adapter_maps_compact_parse_failures_to_malformed(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
    token: str,
) -> None:
    _, public = rsa_pair
    adapter = _adapter(public)

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "malformed"
    )


def test_adapter_rejects_oversized_signature_segment(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    _, public = rsa_pair
    adapter = _adapter(public)
    token = f"{_b64url(b'a')}.{_b64url(b'b')}.{_b64url(b'x' * 5000)}"

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "malformed"
    )


@pytest.mark.parametrize(
    "bad_segment",
    [
        "AAD",
        "A====",
        "A+B/=",
        "AA BD",
        "ab/c",
        "A",
    ],
)
def test_adapter_rejects_noncanonical_header_segment(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
    bad_segment: str,
) -> None:
    _, public = rsa_pair
    adapter = _adapter(public)
    payload_segment = _b64url(json.dumps(_payload()).encode("utf-8"))
    token = f"{bad_segment}.{payload_segment}.{_b64url(b'x' * 256)}"

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "malformed"
    )


@pytest.mark.parametrize(
    "bad_payload_segment",
    [
        "AAD",
        "A====",
        "A+B/=",
        "AA BD",
        "ab/c",
        "A",
    ],
)
def test_adapter_rejects_noncanonical_payload_segment(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
    bad_payload_segment: str,
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    header_segment = _b64url(
        b'{"alg":"RS256","typ":"at+jwt","kid":"signing-key-1"}'
    )
    token = _signed_segments(header_segment, bad_payload_segment, private)

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "malformed"
    )


# --------------------------------------------------------------------------- #
# Adapter contract and happy path
# --------------------------------------------------------------------------- #

def test_adapter_is_protocol_adapter_claiming_exact_bearer_route(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    _, public = rsa_pair
    adapter = _adapter(public)

    assert isinstance(adapter, AuthenticationAdapter)
    assert adapter.route == EvidenceRoute("authorization", "bearer", None)


def test_valid_token_yields_opaque_projected_subject(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)

    result = adapter.authenticate(_evidence(_signed(private, _payload())), CONTEXT)

    assert result == AuthenticationSuccess(project_subject(ISSUER, "stable-subject"))
    assert isinstance(result, AuthenticationSuccess)
    assert "stable-subject" not in result.subject


def test_valid_token_allows_array_audience_membership(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)

    result = adapter.authenticate(
        _evidence(_signed(private, _payload(aud=[AUDIENCE, "https://other.example.com"]))),
        CONTEXT,
    )

    assert isinstance(result, AuthenticationSuccess)
    assert result.subject == project_subject(ISSUER, "stable-subject")


def test_valid_token_allows_unknown_extra_payload_claims(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)

    result = adapter.authenticate(
        _evidence(
            _signed(
                private,
                _payload(scope=["read"], azp="allowed-party", unknown="ignored"),
            )
        ),
        CONTEXT,
    )

    assert isinstance(result, AuthenticationSuccess)


def test_adapter_rejects_evidence_from_other_route(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    _, public = rsa_pair
    adapter = _adapter(public)

    result = adapter.authenticate(
        AuthenticationEvidence(EvidenceRoute("authorization", "basic", None), b"x"),
        CONTEXT,
    )

    assert result == AuthenticationFailure("unsupported")


def test_adapter_requires_evidence_value(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    _, public = rsa_pair
    adapter = _adapter(public)

    with pytest.raises(ValueError, match="^invalid authentication request$"):
        adapter.authenticate("not-evidence", CONTEXT)  # type: ignore[arg-type]


def test_adapter_rejects_non_ascii_token(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    _, public = rsa_pair
    adapter = _adapter(public)

    result = adapter.authenticate(
        AuthenticationEvidence(ROUTE, "a.b.\u00c3".encode("utf-8")),
        CONTEXT,
    )

    assert result == AuthenticationFailure("malformed")


# --------------------------------------------------------------------------- #
# Header validation
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    ("alg", "typ", "extra"),
    [
        ("HS256", "at+jwt", {}),
        ("none", "at+jwt", {}),
        ("ES256", "at+jwt", {}),
        ("RS256", "jwt", {}),
        ("RS256", "at_jwt", {}),
        ("RS256", "at+jwt", {"cty": "JWT"}),
        ("RS256", "at+jwt", {"enc": "A128CBC"}),
    ],
)
def test_adapter_rejects_invalid_or_overloaded_header(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
    alg: str,
    typ: str,
    extra: dict[str, object],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    header_text = json.dumps({"alg": alg, "typ": typ, "kid": KID, **extra})
    token = _signed_raw(header_text, json.dumps(_payload()), private)

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "malformed"
    )


@pytest.mark.parametrize(
    "header_text",
    [
        '{"typ":"at+jwt","kid":"signing-key-1"}',
        '{"alg":"RS256","kid":"signing-key-1"}',
        '{"alg":"RS256","typ":"at+jwt"}',
    ],
)
def test_adapter_rejects_missing_header_members(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
    header_text: str,
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed_raw(header_text, json.dumps(_payload()), private)

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "malformed"
    )


@pytest.mark.parametrize("bad_kid", ["", "   ", "héllo", "k" * 129, "kid\n2"])
def test_adapter_rejects_invalid_kid(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
    bad_kid: str,
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed_raw(
        json.dumps({"alg": "RS256", "typ": "at+jwt", "kid": bad_kid}),
        json.dumps(_payload()),
        private,
    )

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "malformed"
    )


def test_adapter_rejects_duplicate_header_object_keys(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    header_text = '{"alg":"RS256","alg":"RS256","typ":"at+jwt","kid":"signing-key-1"}'
    token = _signed_raw(header_text, json.dumps(_payload()), private)

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "malformed"
    )


# --------------------------------------------------------------------------- #
# Claim validation
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("claim", ["iss", "aud", "sub", "exp", "iat", "client_id", "jti"])
def test_adapter_requires_each_claim(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
    claim: str,
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    payload = _payload()
    del payload[claim]

    result = adapter.authenticate(_evidence(_signed(private, payload)), CONTEXT)

    assert result == AuthenticationFailure("malformed")


def test_adapter_rejects_wrong_issuer(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload(iss="https://evil.example.com"))

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "rejected"
    )


def test_adapter_rejects_wrong_string_audience(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload(aud="https://other.example.com"))

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "rejected"
    )


def test_adapter_rejects_audience_array_without_membership(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload(aud=["one.example.com", "two.example.com"]))

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "rejected"
    )


@pytest.mark.parametrize("bad_aud", [42, True, None])
def test_adapter_rejects_malformed_audience_type(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
    bad_aud: object,
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload(aud=bad_aud))

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "malformed"
    )


@pytest.mark.parametrize(
    "bad_member",
    [42, None, True, [AUDIENCE], {"name": "member"}, 1.5],
)
def test_adapter_rejects_audience_array_with_non_string_member(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
    bad_member: object,
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload(aud=[AUDIENCE, bad_member]))

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "malformed"
    )


def test_adapter_accepts_duplicate_audience_strings_containing_target(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload(aud=[AUDIENCE, AUDIENCE]))

    result = adapter.authenticate(_evidence(token), CONTEXT)

    assert isinstance(result, AuthenticationSuccess)
    assert result.subject == project_subject(ISSUER, "stable-subject")


def test_adapter_rejects_duplicate_audience_strings_without_target(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload(aud=["x.example.com", "x.example.com"]))

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "rejected"
    )


@pytest.mark.parametrize("claim", ["exp", "iat", "nbf"])
@pytest.mark.parametrize("bad_value", ["not-a-number", 1.5, True, None, [], -1])
def test_adapter_rejects_malformed_numeric_dates(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
    claim: str,
    bad_value: object,
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload(**{claim: bad_value}))

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "malformed"
    )


@pytest.mark.parametrize("sub", [42, "", "   ", "e\u0301", "s" * 257, "with\ncontrol"])
def test_adapter_rejects_invalid_sub_claim(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
    sub: object,
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload(sub=sub))

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "malformed"
    )


@pytest.mark.parametrize("claim", ["client_id", "jti"])
@pytest.mark.parametrize("value", [None, "", " ", "abc\x00def", 42, "x" * 257])
def test_adapter_rejects_invalid_bound_claim(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
    claim: str,
    value: object,
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload(**{claim: value}))

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "malformed"
    )


def test_adapter_rejects_duplicate_payload_object_keys(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    payload_text = (
        '{"iss":"https://auth.example.com","iss":"x",'
        '"aud":"https://mcp.example.com","sub":"s","exp":2000000000,'
        '"iat":1999999700,"client_id":"c","jti":"j"}'
    )
    token = _signed_raw(
        '{"alg":"RS256","typ":"at+jwt","kid":"signing-key-1"}',
        payload_text,
        private,
    )

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "malformed"
    )


# --------------------------------------------------------------------------- #
# Time, skew, and lifetime validation
# --------------------------------------------------------------------------- #

def test_adapter_accepts_token_within_expiry_skew(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload(exp=NOW - 30, iat=NOW - 330))

    assert isinstance(
        adapter.authenticate(_evidence(token), CONTEXT), AuthenticationSuccess
    )


def test_adapter_rejects_expired_beyond_skew(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload(exp=NOW - 31, iat=NOW - 331))

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "rejected"
    )


def test_adapter_accepts_iat_within_future_skew(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload(iat=NOW + 30, exp=NOW + 330))

    assert isinstance(
        adapter.authenticate(_evidence(token), CONTEXT), AuthenticationSuccess
    )


def test_adapter_rejects_iat_beyond_future_skew(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload(iat=NOW + 31, exp=NOW + 331))

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "rejected"
    )


def test_adapter_accepts_exactly_five_minute_lifetime(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    assert MAX_LIFETIME_SECONDS == 5 * 60
    token = _signed(private, _payload(iat=NOW - 1, exp=NOW - 1 + MAX_LIFETIME_SECONDS))

    assert isinstance(
        adapter.authenticate(_evidence(token), CONTEXT), AuthenticationSuccess
    )


def test_adapter_rejects_lifetime_over_five_minutes(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(
        private, _payload(iat=NOW - 1, exp=NOW - 1 + MAX_LIFETIME_SECONDS + 1)
    )

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "rejected"
    )


def test_adapter_rejects_zero_or_reversed_lifetime(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    for token in (
        _signed(private, _payload(iat=NOW - 60, exp=NOW - 60)),
        _signed(private, _payload(exp=NOW - 60, iat=NOW - 30)),
    ):
        assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
            "rejected"
        )


def test_adapter_enforces_optional_nbf_within_skew(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    valid = _signed(private, _payload(nbf=NOW + 30, iat=NOW - 60, exp=NOW + 180))
    rejected = _signed(private, _payload(nbf=NOW + 31, iat=NOW - 60, exp=NOW + 181))

    assert isinstance(
        adapter.authenticate(_evidence(valid), CONTEXT), AuthenticationSuccess
    )
    assert adapter.authenticate(_evidence(rejected), CONTEXT) == AuthenticationFailure(
        "rejected"
    )


def test_clock_is_injected_and_compared_against_now(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    token = _signed(private, _payload(exp=NOW + 100, iat=NOW - 60))
    fresh = _adapter(public, now=NOW)
    stale = _adapter(public, now=NOW + 5000)

    assert isinstance(fresh.authenticate(_evidence(token), CONTEXT), AuthenticationSuccess)
    assert stale.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "rejected"
    )


# --------------------------------------------------------------------------- #
# Signature and key validation
# --------------------------------------------------------------------------- #

def test_adapter_rejects_unknown_kid(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload(), kid="other-key")

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "rejected"
    )


def test_adapter_rejects_token_signed_by_wrong_key(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    _, public = rsa_pair
    adapter = _adapter(public)
    wrong = _generate_private()
    token = _signed(wrong, _payload())

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "rejected"
    )


def test_adapter_rejects_tampered_signature(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload())
    header_b64, payload_b64, _ = token.split(".")
    tampered = (
        f"{header_b64}.{payload_b64}."
        f"{base64.urlsafe_b64encode(b'x' * 256).rstrip(b'=').decode('ascii')}"
    )

    assert adapter.authenticate(_evidence(tampered), CONTEXT) == AuthenticationFailure(
        "rejected"
    )


def test_adapter_rejects_payload_not_covered_by_signature(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload())
    header_b64, _, signature_b64 = token.split(".")
    forged_payload_b64 = _b64url(json.dumps(dict(_payload(), sub="forged")).encode("utf-8"))
    forged = f"{header_b64}.{forged_payload_b64}.{signature_b64}"

    assert adapter.authenticate(_evidence(forged), CONTEXT) == AuthenticationFailure(
        "rejected"
    )


def test_signature_is_verified_before_payload_claims(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload(exp="not-a-number"))
    header_b64, payload_b64, signature_b64 = token.split(".")
    # Flip the first signature character: it encodes six full base64 bits, so
    # the segment stays canonical and the tamper reaches signature verification.
    tampered_signature = (
        "A" if signature_b64[0] != "A" else "B"
    ) + signature_b64[1:]
    tampered = f"{header_b64}.{payload_b64}.{tampered_signature}"

    assert adapter.authenticate(_evidence(tampered), CONTEXT) == AuthenticationFailure(
        "rejected"
    )


def _nested_value(depth: int, *, use_object: bool = False) -> object:
    value: object = 1
    for _ in range(depth):
        value = {"x": value} if use_object else [value]
    return value


@pytest.mark.parametrize("use_object", [False, True])
def test_adapter_rejects_deeply_nested_extra_claim(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
    use_object: bool,
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload(extra=_nested_value(200, use_object=use_object)))

    assert adapter.authenticate(_evidence(token), CONTEXT) == AuthenticationFailure(
        "malformed"
    )


def test_adapter_accepts_shallow_nested_extra_claim(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload(extra=_nested_value(16)))

    result = adapter.authenticate(_evidence(token), CONTEXT)

    assert isinstance(result, AuthenticationSuccess)
    assert result.subject == project_subject(ISSUER, "stable-subject")


def test_rsa_snapshot_build_rejects_duplicate_kid() -> None:
    private = _generate_private()
    key = _public_key(private)

    with pytest.raises(ValueError, match="^invalid oauth jwt snapshot$"):
        build_oauth_jwt_snapshot((key, key))


def test_rsa_snapshot_build_rejects_more_than_sixteen_keys() -> None:
    private = _generate_private()
    numbers = private.public_key().public_numbers()
    keys = tuple(
        RsaPublicKey(f"k-{index:02d}", numbers.n, numbers.e) for index in range(17)
    )

    with pytest.raises(ValueError, match="^invalid oauth jwt snapshot$"):
        build_oauth_jwt_snapshot(keys)


def test_rsa_public_key_rejects_weak_or_invalid_key() -> None:
    for bits in (1024,):
        private = _generate_private(bits=bits)
        numbers = private.public_key().public_numbers()
        with pytest.raises(ValueError, match="^invalid oauth jwt key$"):
            RsaPublicKey(KID, numbers.n, numbers.e)
    numbers = _public_key(_generate_private())
    with pytest.raises(ValueError, match="^invalid oauth jwt key$"):
        RsaPublicKey(KID, numbers.modulus, 4)


def test_snapshot_is_frozen_and_keys_redacted() -> None:
    private = _generate_private()
    key = _public_key(private)
    snapshot = build_oauth_jwt_snapshot((key,))

    assert isinstance(snapshot, OAuthJwtSnapshot)
    assert snapshot.find(KID) is key
    with pytest.raises(FrozenInstanceError):
        snapshot.keys = ()  # type: ignore[misc]
    assert str(key.modulus) not in repr(key)
    assert str(key.exponent) not in repr(key)


# --------------------------------------------------------------------------- #
# Redaction
# --------------------------------------------------------------------------- #

def test_configuration_redacts_endpoints_and_key_material(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    _, public = rsa_pair
    config = OAuthJwtConfig(
        issuer=ISSUER,
        audience=AUDIENCE,
        snapshot=build_oauth_jwt_snapshot((public,)),
        clock=lambda: NOW,
    )

    assert ISSUER not in repr(config)
    assert AUDIENCE not in repr(config)
    assert str(public.modulus) not in repr(config)
    assert str(public.exponent) not in repr(config)
    assert repr(config) == "OAuthJwtConfig()"


def test_adapter_and_results_never_expose_raw_claims_or_secrets(
    rsa_pair: tuple[rsa.RSAPrivateKey, RsaPublicKey],
) -> None:
    private, public = rsa_pair
    adapter = _adapter(public)
    token = _signed(private, _payload())
    result = adapter.authenticate(AuthenticationEvidence(ROUTE, token.encode("utf-8")), CONTEXT)

    assert "stable-subject" not in repr(adapter)
    assert "stable-subject" not in str(adapter)
    assert "stable-subject" not in repr(result)
    assert "client_id" not in repr(result)
    assert "jti" not in repr(result)
    for attr in ("token", "claims", "evidence"):
        assert not hasattr(adapter, attr)


# --------------------------------------------------------------------------- #
# Dependency and import boundaries
# --------------------------------------------------------------------------- #

def test_only_oauth_adapter_imports_the_third_party_runtime_dependency() -> None:
    for module in ADAPTERS_PACKAGE.glob("*.py"):
        tree = ast.parse(module.read_text(encoding="utf-8"))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imports.add(node.module)
        for imported in imports:
            if imported.startswith("mymcp.authentication"):
                continue
            top_level = imported.split(".")[0]
            if top_level in ALLOWED_STDLIB:
                continue
            if module.name == "oauth_jwt.py":
                assert top_level in ALLOWED_THIRD_PARTY, (module.name, imported)
            else:
                raise AssertionError(f"{module.name} imports third-party {imported}")


def test_importing_adapters_package_does_not_load_oauth_runtime() -> None:
    import subprocess
    import sys

    probe = (
        "import sys;"
        "import mymcp.authentication.adapters as adapters;"
        "loaded = sorted(name for name in sys.modules "
        "if name == 'mymcp.authentication.adapters.oauth_jwt' "
        "or name == 'jwt' or name == 'cryptography' "
        "or name.startswith('cryptography.'));"
        "print(','.join(loaded));"
        "print(hasattr(adapters, 'OAuthJwtAdapter'))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        check=True,
    )
    lines = completed.stdout.splitlines()
    assert lines[0] == ""
    assert lines[1] == "False"


def test_authentication_contracts_and_router_remain_standard_library_only() -> None:
    for name in ("contracts.py", "router.py"):
        tree = ast.parse((AUTHENTICATION_PACKAGE / name).read_text(encoding="utf-8"))
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