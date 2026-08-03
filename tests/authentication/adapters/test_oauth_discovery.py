import base64
import json
import ssl
import urllib.error
import urllib.request
from dataclasses import FrozenInstanceError

import pytest
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from mymcp.authentication.contracts import (
    AuthenticationEvidence,
    AuthenticationFailure,
    AuthenticationRequestContext,
    AuthenticationSuccess,
    EvidenceRoute,
)
from mymcp.authentication.adapters.oauth_jwt import (
    OAuthJwtAdapter,
    OAuthJwtConfig,
    RsaPublicKey,
    build_oauth_jwt_snapshot,
    project_subject,
)
from mymcp.authentication.adapters.oauth_discovery import (
    DEFAULT_FETCH_TIMEOUT_SECONDS,
    MAX_JWKS_BYTES,
    MAX_METADATA_BYTES,
    OAuthDiscoveryError,
    bounded_https_fetch,
    derive_oauth_metadata_url,
    load_oauth_validation_material,
)


ISSUER = "https://auth.example.com"
JWKS_URL = "https://auth.example.com/keys"
KID = "signing-key-1"
ROUTE = EvidenceRoute("authorization", "bearer", None)
CONTEXT = AuthenticationRequestContext("POST", "mcp")
AUDIENCE = "https://mcp.example.com"
NOW = 1_700_000_000
METADATA_URL = "https://auth.example.com/.well-known/oauth-authorization-server"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _generate_private(bits: int = 2048) -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=bits)


def _jwk(
    private: rsa.RSAPrivateKey,
    kid: str = KID,
    *,
    use: object = "sig",
    alg: object = "RS256",
    key_ops: object | None = None,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    numbers = private.public_key().public_numbers()
    n_bytes = numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")
    e_bytes = numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")
    jwk: dict[str, object] = {
        "kty": "RSA",
        "kid": kid,
        "n": _b64url(n_bytes),
        "e": _b64url(e_bytes),
    }
    if use is not None:
        jwk["use"] = use
    if alg is not None:
        jwk["alg"] = alg
    if key_ops is not None:
        jwk["key_ops"] = key_ops
    if extra:
        jwk.update(extra)
    return jwk


def _metadata(
    issuer: object = ISSUER,
    jwks_uri: object = JWKS_URL,
    **extra: object,
) -> bytes:
    doc: dict[str, object] = {"issuer": issuer, "jwks_uri": jwks_uri}
    doc.update(extra)
    return json.dumps(doc).encode("utf-8")


def _jwks(*jwk_objects: dict[str, object]) -> bytes:
    return json.dumps({"keys": list(jwk_objects)}).encode("utf-8")


def _inflate(doc: bytes, target: int) -> bytes:
    """Inflate a JSON object with an ignored 'pad' member to exactly ``target`` bytes."""
    prefix = doc[:-1]
    opening = b',"pad":"'
    closing = b'"}'
    padding = target - len(prefix) - len(opening) - len(closing)
    assert padding >= 0, (len(doc), target)
    return prefix + opening + b"x" * padding + closing


class _FakeFetch:
    """Records calls and serves fixture bodies or raises transport failures."""

    def __init__(self, routes: dict[str, bytes | Exception]) -> None:
        self.routes = dict(routes)
        self.calls: list[str] = []
        self.bounds: list[int] = []

    def __call__(self, url: str, max_bytes: int) -> bytes:
        self.calls.append(url)
        self.bounds.append(max_bytes)
        result = self.routes[url]
        if isinstance(result, Exception):
            raise result
        return result

    def count(self, url: str) -> int:
        return self.calls.count(url)


def _adapter(snapshot: object) -> OAuthJwtAdapter:
    config = OAuthJwtConfig(
        issuer=ISSUER,
        audience=AUDIENCE,
        snapshot=snapshot,
        clock=lambda: NOW,
    )
    return OAuthJwtAdapter(config)


def _evidence(token: str) -> AuthenticationEvidence:
    return AuthenticationEvidence(ROUTE, token.encode("utf-8"))


def _signed(private: rsa.RSAPrivateKey, kid: str = KID) -> str:
    payload = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "stable-subject",
        "exp": NOW + 240,
        "iat": NOW - 60,
        "client_id": "mcp-client",
        "jti": "jti-abc-123",
    }
    return jwt.encode(  # type: ignore[arg-type]
        payload, private, algorithm="RS256", headers={"typ": "at+jwt", "kid": kid}
    )


@pytest.fixture(scope="module")
def rsa_pair() -> tuple[rsa.RSAPrivateKey, RsaPublicKey]:
    private = _generate_private()
    numbers = private.public_key().public_numbers()
    return private, RsaPublicKey(KID, numbers.n, numbers.e)


# --------------------------------------------------------------------------- #
# RFC 8414 metadata URL derivation
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    ("issuer", "expected"),
    [
        ("https://auth.example.com", METADATA_URL),
        ("https://auth.example.com:443", "https://auth.example.com:443/.well-known/oauth-authorization-server"),
        (
            "https://auth.example.com/tenant",
            "https://auth.example.com/.well-known/oauth-authorization-server/tenant",
        ),
        (
            "https://auth.example.com/realms/prod",
            "https://auth.example.com/.well-known/oauth-authorization-server/realms/prod",
        ),
        (
            "https://auth.example.com/realms/prod/tenant",
            "https://auth.example.com/.well-known/oauth-authorization-server/realms/prod/tenant",
        ),
    ],
)
def test_derive_oauth_metadata_url_follows_rfc_8414(issuer: str, expected: str) -> None:
    assert derive_oauth_metadata_url(issuer) == expected


@pytest.mark.parametrize(
    "issuer",
    [
        "http://auth.example.com",
        "https://AUTH.example.com",
        "https://auth.example.com?x=1",
        "https://auth.example.com/../escape",
        "https://auth.example.com/path/",
        "https://auth.example.com/",
        "auth.example.com",
        "",
    ],
)
def test_derive_oauth_metadata_url_rejects_noncanonical_issuer(issuer: str) -> None:
    with pytest.raises(ValueError, match="^invalid oauth issuer$"):
        derive_oauth_metadata_url(issuer)


# --------------------------------------------------------------------------- #
# Successful bounded acquisition
# --------------------------------------------------------------------------- #

def test_load_fetches_metadata_and_jwks_exactly_once_each(rsa_pair: object) -> None:
    private, _ = rsa_pair
    fetch = _FakeFetch({METADATA_URL: _metadata(), JWKS_URL: _jwks(_jwk(private))})

    snapshot = load_oauth_validation_material(ISSUER, fetch)

    assert fetch.count(METADATA_URL) == 1
    assert fetch.count(JWKS_URL) == 1
    assert snapshot.find(KID) is not None
    assert snapshot.find("absent-key") is None


def test_load_derives_metadata_url_for_path_issuer(rsa_pair: object) -> None:
    private, _ = rsa_pair
    issuer = "https://auth.example.com/realms/prod"
    metadata_url = "https://auth.example.com/.well-known/oauth-authorization-server/realms/prod"
    fetch = _FakeFetch(
        {
            metadata_url: _metadata(issuer=issuer),
            "https://auth.example.com/keys": _jwks(_jwk(private)),
        }
    )

    snapshot = load_oauth_validation_material(issuer, fetch)

    assert fetch.count(metadata_url) == 1
    assert snapshot.find(KID) is not None


def test_load_accepts_https_jwks_with_default_port(rsa_pair: object) -> None:
    private, _ = rsa_pair
    fetch = _FakeFetch(
        {
            METADATA_URL: _metadata(jwks_uri="https://auth.example.com:443/keys"),
            "https://auth.example.com:443/keys": _jwks(_jwk(private)),
        }
    )

    snapshot = load_oauth_validation_material(ISSUER, fetch)

    assert snapshot.find(KID) is not None


def test_load_accepts_jwks_uri_with_query(rsa_pair: object) -> None:
    private, _ = rsa_pair
    jwks_url = "https://auth.example.com/keys?tenant=prod"
    fetch = _FakeFetch({METADATA_URL: _metadata(jwks_uri=jwks_url), jwks_url: _jwks(_jwk(private))})

    snapshot = load_oauth_validation_material(ISSUER, fetch)

    assert snapshot.find(KID) is not None


def test_load_ignores_unknown_metadata_members(rsa_pair: object) -> None:
    private, _ = rsa_pair
    metadata = _metadata(
        token_endpoint="https://auth.example.com/token",
        scopes_supported=["openid"],
        authorization_endpoint="https://auth.example.com/authorize",
    )
    fetch = _FakeFetch({METADATA_URL: metadata, JWKS_URL: _jwks(_jwk(private))})

    snapshot = load_oauth_validation_material(ISSUER, fetch)

    assert snapshot.find(KID) is not None


def test_load_accepts_jwks_without_use_or_alg(rsa_pair: object) -> None:
    private, _ = rsa_pair
    fetch = _FakeFetch(
        {
            METADATA_URL: _metadata(),
            JWKS_URL: _jwks(_jwk(private, use=None, alg=None)),
        }
    )

    snapshot = load_oauth_validation_material(ISSUER, fetch)

    assert snapshot.find(KID) is not None


def test_loaded_snapshot_is_immutable_and_redacted(rsa_pair: object) -> None:
    private, _ = rsa_pair
    fetch = _FakeFetch({METADATA_URL: _metadata(), JWKS_URL: _jwks(_jwk(private))})

    snapshot = load_oauth_validation_material(ISSUER, fetch)
    key = snapshot.find(KID)

    with pytest.raises(FrozenInstanceError):
        snapshot.keys = ()  # type: ignore[misc]
    assert key is not None
    assert str(key.modulus) not in repr(key)
    assert str(key.exponent) not in repr(key)
    assert ISSUER not in repr(snapshot)
    assert JWKS_URL not in repr(snapshot)


# --------------------------------------------------------------------------- #
# Metadata failure codes: unavailable vs invalid
# --------------------------------------------------------------------------- #

def test_metadata_fetch_failure_is_bounded_unavailable() -> None:
    fetch = _FakeFetch({METADATA_URL: ConnectionError("boom")})

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "metadata_unavailable"
    assert excinfo.value.args == ()
    assert str(excinfo.value) == ""
    assert "boom" not in repr(excinfo.value)
    assert METADATA_URL not in repr(excinfo.value)


def test_metadata_fetch_failure_never_touches_jwks() -> None:
    fetch = _FakeFetch({METADATA_URL: ConnectionError("boom")})

    with pytest.raises(OAuthDiscoveryError):
        load_oauth_validation_material(ISSUER, fetch)

    assert fetch.calls == [METADATA_URL]


@pytest.mark.parametrize(
    "bad_body",
    [
        b"",
        b"{not json",
        b'["not", "an", "object"]',
        b'{"issuer": 42, "jwks_uri": "https://auth.example.com/keys"}',
        b'{"issuer": "https://auth.example.com", "jwks_uri": "https://auth.example.com/keys", "issuer": "x"}',
        b"\xff\xfe{}",
    ],
)
def test_invalid_metadata_body_is_bounded_invalid(bad_body: bytes) -> None:
    fetch = _FakeFetch({METADATA_URL: bad_body, JWKS_URL: _jwks()})

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "metadata_invalid"
    assert excinfo.value.args == ()


def test_metadata_exceeding_16_kib_is_bounded_invalid() -> None:
    oversized = _inflate(_metadata(), MAX_METADATA_BYTES + 1)
    fetch = _FakeFetch({METADATA_URL: oversized, JWKS_URL: _jwks()})

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "metadata_invalid"


def test_metadata_exactly_16_kib_is_accepted(rsa_pair: object) -> None:
    private, _ = rsa_pair
    exact = _inflate(_metadata(), MAX_METADATA_BYTES)
    fetch = _FakeFetch({METADATA_URL: exact, JWKS_URL: _jwks(_jwk(private))})

    snapshot = load_oauth_validation_material(ISSUER, fetch)

    assert snapshot.find(KID) is not None


def test_metadata_issuer_mismatch_is_bounded_invalid() -> None:
    fetch = _FakeFetch(
        {
            METADATA_URL: _metadata(issuer="https://other.example.com"),
            JWKS_URL: _jwks(),
        }
    )

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "metadata_invalid"


def test_metadata_missing_jwks_uri_is_bounded_invalid() -> None:
    fetch = _FakeFetch(
        {
            METADATA_URL: json.dumps({"issuer": ISSUER}).encode("utf-8"),
            JWKS_URL: _jwks(),
        }
    )

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "metadata_invalid"


@pytest.mark.parametrize(
    "jwks_uri",
    [
        "http://auth.example.com/keys",
        "https://evil.example.com/keys",
        "https://user:pass@auth.example.com/keys",
        "https://auth.example.com/keys#frag",
        "https://auth.example.com:8443/keys",
        "https://auth.example.com%2F..",
        "https://AUTH.EXAMPLE.COM/keys",
        "https://auth.example.com:0443/keys",
        "https://%61uth.example.com/keys",
    ],
)
def test_nonconforming_jwks_uri_is_bounded_invalid(jwks_uri: str) -> None:
    fetch = _FakeFetch(
        {
            METADATA_URL: _metadata(jwks_uri=jwks_uri),
            JWKS_URL: _jwks(),
        }
    )

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "metadata_invalid"
    assert excinfo.value.args == ()


# --------------------------------------------------------------------------- #
# JWKS failure codes: unavailable vs invalid
# --------------------------------------------------------------------------- #

def test_jwks_fetch_failure_is_bounded_unavailable(rsa_pair: object) -> None:
    _, _ = rsa_pair
    fetch = _FakeFetch({METADATA_URL: _metadata(), JWKS_URL: ConnectionError("boom")})

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "jwks_unavailable"
    assert excinfo.value.args == ()
    assert "boom" not in repr(excinfo.value)
    assert JWKS_URL not in repr(excinfo.value)
    assert fetch.count(METADATA_URL) == 1


@pytest.mark.parametrize(
    "bad_body",
    [
        b"",
        b"{not json",
        b'{"keys": "not-a-list"}',
        b'{"keys": []}',
        b'{"keys": [42]}',
        b"\xff\xfe{}",
        b'{"keys": [{"kty": "RSA", "kid": "k", "n": "AA", "e": "AQAB"}]}',
    ],
)
def test_invalid_jwks_body_is_bounded_invalid(bad_body: bytes) -> None:
    fetch = _FakeFetch({METADATA_URL: _metadata(), JWKS_URL: bad_body})

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "jwks_invalid"
    assert excinfo.value.args == ()


def test_jwks_exceeding_64_kib_is_bounded_invalid(rsa_pair: object) -> None:
    private, _ = rsa_pair
    oversized = _inflate(_jwks(_jwk(private)), MAX_JWKS_BYTES + 1)
    fetch = _FakeFetch({METADATA_URL: _metadata(), JWKS_URL: oversized})

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "jwks_invalid"


def test_jwks_exactly_64_kib_is_accepted(rsa_pair: object) -> None:
    private, _ = rsa_pair
    exact = _inflate(_jwks(_jwk(private)), MAX_JWKS_BYTES)
    fetch = _FakeFetch({METADATA_URL: _metadata(), JWKS_URL: exact})

    snapshot = load_oauth_validation_material(ISSUER, fetch)

    assert snapshot.find(KID) is not None


def test_jwks_with_seventeen_keys_is_bounded_invalid() -> None:
    keys = tuple(_jwk(_generate_private(), kid=f"k-{index:02d}") for index in range(17))
    fetch = _FakeFetch({METADATA_URL: _metadata(), JWKS_URL: _jwks(*keys)})

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "jwks_invalid"


def test_jwks_duplicate_kid_is_bounded_invalid() -> None:
    first = _generate_private()
    second = _generate_private()
    fetch = _FakeFetch(
        {
            METADATA_URL: _metadata(),
            JWKS_URL: _jwks(_jwk(first, kid="dup"), _jwk(second, kid="dup")),
        }
    )

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "jwks_invalid"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda jwk: jwk.update({"kty": "EC"}),
        lambda jwk: jwk.update({"use": "enc"}),
        lambda jwk: jwk.update({"alg": "ES256"}),
        lambda jwk: jwk.pop("n"),
        lambda jwk: jwk.pop("e"),
        lambda jwk: jwk.update({"n": "AA=="}),
        lambda jwk: jwk.update({"n": "A+B/" }),
        lambda jwk: jwk.update({"key_ops": ["sign"]}),
    ],
)
def test_unsuitable_or_noncanonical_jwk_is_bounded_invalid(
    rsa_pair: object,
    mutate: object,
) -> None:
    private, _ = rsa_pair
    jwk = _jwk(private)
    mutate(jwk)  # type: ignore[operator]
    fetch = _FakeFetch({METADATA_URL: _metadata(), JWKS_URL: _jwks(jwk)})

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "jwks_invalid"


def test_weak_rsa_jwk_is_bounded_invalid() -> None:
    weak = _generate_private(bits=1024)
    fetch = _FakeFetch(
        {
            METADATA_URL: _metadata(),
            JWKS_URL: _jwks(_jwk(weak)),
        }
    )

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "jwks_invalid"


def test_discovery_error_rejects_unknown_codes() -> None:
    with pytest.raises(ValueError, match="^invalid oauth discovery failure$"):
        OAuthDiscoveryError("unknown")  # type: ignore[arg-type]


def test_non_callable_fetch_is_configuration_error() -> None:
    with pytest.raises(ValueError, match="^invalid oauth discovery fetch$"):
        load_oauth_validation_material(ISSUER, "not-callable")  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# No runtime refresh; restart-based rotation
# --------------------------------------------------------------------------- #

def test_validator_performs_no_runtime_provider_calls(rsa_pair: object) -> None:
    private, _ = rsa_pair
    fetch = _FakeFetch({METADATA_URL: _metadata(), JWKS_URL: _jwks(_jwk(private))})

    snapshot = load_oauth_validation_material(ISSUER, fetch)
    assert fetch.calls == [METADATA_URL, JWKS_URL]

    adapter = _adapter(snapshot)
    result = adapter.authenticate(_evidence(_signed(private)), CONTEXT)

    assert isinstance(result, AuthenticationSuccess)
    assert result.subject == project_subject(ISSUER, "stable-subject")
    assert fetch.calls == [METADATA_URL, JWKS_URL]


def test_restart_loads_new_snapshot_and_rotation_overlap() -> None:
    old_private = _generate_private()
    new_private = _generate_private()
    old_kid, new_kid = "key-old", "key-new"

    first_fetch = _FakeFetch(
        {
            METADATA_URL: _metadata(),
            JWKS_URL: _jwks(_jwk(old_private, kid=old_kid), _jwk(new_private, kid=new_kid)),
        }
    )
    old_snapshot = load_oauth_validation_material(ISSUER, first_fetch)
    assert first_fetch.count(METADATA_URL) == 1
    assert first_fetch.count(JWKS_URL) == 1

    second_fetch = _FakeFetch(
        {
            METADATA_URL: _metadata(),
            JWKS_URL: _jwks(_jwk(new_private, kid=new_kid)),
        }
    )
    new_snapshot = load_oauth_validation_material(ISSUER, second_fetch)
    assert second_fetch.count(METADATA_URL) == 1
    assert second_fetch.count(JWKS_URL) == 1

    old_adapter = _adapter(old_snapshot)
    new_adapter = _adapter(new_snapshot)

    # Overlap window: old key still validates under the old snapshot.
    assert isinstance(
        old_adapter.authenticate(_evidence(_signed(old_private, kid=old_kid)), CONTEXT),
        AuthenticationSuccess,
    )
    assert isinstance(
        old_adapter.authenticate(_evidence(_signed(new_private, kid=new_kid)), CONTEXT),
        AuthenticationSuccess,
    )

    # After rotation, the removed key is rejected and the new key validates.
    assert new_adapter.authenticate(
        _evidence(_signed(old_private, kid=old_kid)), CONTEXT
    ) == AuthenticationFailure("rejected")
    assert isinstance(
        new_adapter.authenticate(_evidence(_signed(new_private, kid=new_kid)), CONTEXT),
        AuthenticationSuccess,
    )


# --------------------------------------------------------------------------- #
# Concrete bounded HTTPS fetch seam
# --------------------------------------------------------------------------- #

def test_load_passes_explicit_max_bytes_to_fetch(rsa_pair: object) -> None:
    private, _ = rsa_pair
    fetch = _FakeFetch({METADATA_URL: _metadata(), JWKS_URL: _jwks(_jwk(private))})

    load_oauth_validation_material(ISSUER, fetch)

    assert fetch.bounds == [MAX_METADATA_BYTES, MAX_JWKS_BYTES]


class _HttpResponse:
    def __init__(self, status: int, payload: bytes = b"") -> None:
        self.status = status
        self.headers = {}
        self._payload = payload
        self.read_calls: list[int] = []

    def read(self, count: int) -> bytes:
        self.read_calls.append(count)
        data = self._payload[:count]
        self._payload = self._payload[count:]
        return data

    def close(self) -> None:
        return None

    def __enter__(self) -> "_HttpResponse":
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None


def _install_fake_opener(
    monkeypatch: object,
    response: object,
    record: dict[str, object] | None = None,
) -> None:
    class _FakeOpener:
        def open(self, request: object, timeout: object) -> object:
            if record is not None:
                record["timeout"] = timeout
            if isinstance(response, Exception):
                raise response
            return response

    monkeypatch.setattr(  # type: ignore[attr-defined]
        urllib.request, "build_opener", lambda *handlers: _FakeOpener()
    )


def test_bounded_https_fetch_returns_bytes_and_streams_limit_plus_one(
    monkeypatch: object,
) -> None:
    record: dict[str, object] = {}
    response = _HttpResponse(200, b"payload")
    _install_fake_opener(monkeypatch, response, record)

    result = bounded_https_fetch(
        "https://auth.example.com/meta", 8, _clock=lambda: 0.0
    )

    assert result == b"payload"
    assert all(limit <= 9 for limit in response.read_calls)
    assert record["timeout"] == DEFAULT_FETCH_TIMEOUT_SECONDS


def test_bounded_https_fetch_rejects_non_200(monkeypatch: object) -> None:
    _install_fake_opener(monkeypatch, _HttpResponse(204))

    with pytest.raises(urllib.error.HTTPError):
        bounded_https_fetch("https://auth.example.com/meta", 8)


def test_bounded_https_fetch_propagates_transport_and_redirect_errors(
    monkeypatch: object,
) -> None:
    errors = [
        urllib.error.HTTPError("https://x", 302, "Found", {}, None),
        ConnectionError("down"),
    ]
    for error in errors:
        _install_fake_opener(monkeypatch, error)
        with pytest.raises(type(error)):
            bounded_https_fetch("https://auth.example.com/meta", 8)


def test_bounded_https_fetch_passes_explicit_timeout(monkeypatch: object) -> None:
    record: dict[str, object] = {}
    _install_fake_opener(monkeypatch, _HttpResponse(200, b"ok"), record)

    bounded_https_fetch(
        "https://auth.example.com/meta", 8, timeout=3.5, _clock=lambda: 0.0
    )

    assert record["timeout"] == 3.5


def test_bounded_https_fetch_wires_verified_tls_no_proxy_and_no_redirect(
    monkeypatch: object,
) -> None:
    context = ssl.create_default_context()
    monkeypatch.setattr(ssl, "create_default_context", lambda: context)  # type: ignore[attr-defined]
    seen: list[object] = []

    def fake_build_opener(*handlers: object) -> object:
        seen.extend(handlers)

        class _FakeOpener:
            def open(self, request: object, timeout: object) -> object:
                return _HttpResponse(200, b"ok")

        return _FakeOpener()

    monkeypatch.setattr(urllib.request, "build_opener", fake_build_opener)  # type: ignore[attr-defined]

    result = bounded_https_fetch("https://auth.example.com/meta", 8)

    assert result == b"ok"
    https_handlers = [
        handler for handler in seen if isinstance(handler, urllib.request.HTTPSHandler)
    ]
    assert len(https_handlers) == 1
    http_context = https_handlers[0]._context  # type: ignore[attr-defined]
    assert http_context.verify_mode == ssl.CERT_REQUIRED
    assert http_context.check_hostname is True
    redirect_handlers = [
        handler for handler in seen if isinstance(handler, urllib.request.HTTPRedirectHandler)
    ]
    assert len(redirect_handlers) == 1
    assert redirect_handlers[0].redirect_request(None, None, 302, "", {}, None) is None
    proxy_handlers = [
        handler for handler in seen if isinstance(handler, urllib.request.ProxyHandler)
    ]
    assert len(proxy_handlers) == 1
    assert proxy_handlers[0].proxies == {}


def test_bounded_https_fetch_rejects_downgraded_tls_context(monkeypatch: object) -> None:
    weak_context = ssl.create_default_context()
    weak_context.check_hostname = False
    weak_context.verify_mode = ssl.CERT_NONE
    monkeypatch.setattr(ssl, "create_default_context", lambda: weak_context)  # type: ignore[attr-defined]

    with pytest.raises(RuntimeError, match="^oauth discovery tls context is not verified$"):
        bounded_https_fetch("https://auth.example.com/meta", 8)


@pytest.mark.parametrize(
    "bad_url",
    [
        "http://auth.example.com/meta",
        "https://user:pass@auth.example.com/meta",
        "https://auth.example.com/meta#frag",
        "https://auth.example.com%2Fmeta",
        "",
        "auth.example.com",
    ],
)
def test_bounded_https_fetch_validates_url(bad_url: str) -> None:
    with pytest.raises(ValueError, match="^invalid oauth discovery url$"):
        bounded_https_fetch(bad_url, 8)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "bad_limit",
    [0, -1, None, True, 1.5, "8"],
)
def test_bounded_https_fetch_validates_max_bytes(bad_limit: object) -> None:
    with pytest.raises(ValueError, match="^invalid oauth discovery fetch limit$"):
        bounded_https_fetch("https://auth.example.com/meta", bad_limit)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "bad_timeout",
    [0, -1, float("nan"), float("inf"), "10", True],
)
def test_bounded_https_fetch_validates_timeout(bad_timeout: object) -> None:
    with pytest.raises(ValueError, match="^invalid oauth discovery fetch timeout$"):
        bounded_https_fetch("https://auth.example.com/meta", 8, timeout=bad_timeout)  # type: ignore[arg-type]


def test_bounded_https_fetch_fails_closed_on_elapsed_deadline(monkeypatch: object) -> None:
    now = [0.0]

    def fake_clock() -> float:
        return now[0]

    class _SlowResponse(_HttpResponse):
        def read(self, count: int) -> bytes:
            now[0] += 5.0
            return super().read(count)

    class _FakeOpener:
        def open(self, request: object, timeout: object) -> object:
            return _SlowResponse(200, b"x")

    monkeypatch.setattr(urllib.request, "build_opener", lambda *handlers: _FakeOpener())  # type: ignore[attr-defined]

    with pytest.raises(TimeoutError, match="^oauth discovery deadline exceeded$"):
        bounded_https_fetch(
            "https://auth.example.com/meta", 1, timeout=1, _clock=fake_clock
        )


# --------------------------------------------------------------------------- #
# JWKS candidate filtering (ignore irrelevant, strict candidates)
# --------------------------------------------------------------------------- #

def test_jwks_ignores_irrelevant_ec_other_alg_and_encryption_keys(
    rsa_pair: object,
) -> None:
    private, _ = rsa_pair
    ec = {"kty": "EC", "kid": "ec-1", "use": "sig", "alg": "ES256"}
    other_alg = _jwk(_generate_private(), kid="rsa384", alg="RS384")
    enc = _jwk(_generate_private(), kid="enc-1", use="enc")
    fetch = _FakeFetch(
        {METADATA_URL: _metadata(), JWKS_URL: _jwks(ec, other_alg, enc, _jwk(private))}
    )

    snapshot = load_oauth_validation_material(ISSUER, fetch)

    assert snapshot.find(KID) is not None
    assert snapshot.find("ec-1") is None
    assert snapshot.find("rsa384") is None
    assert snapshot.find("enc-1") is None


def test_jwks_only_irrelevant_keys_is_bounded_invalid() -> None:
    ec = {"kty": "EC", "kid": "ec-1"}
    enc = _jwk(_generate_private(), kid="enc-1", use="enc")
    other_alg = _jwk(_generate_private(), kid="rsa384", alg="RS384")
    fetch = _FakeFetch({METADATA_URL: _metadata(), JWKS_URL: _jwks(ec, enc, other_alg)})

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "jwks_invalid"


def test_jwks_with_seventeen_mixed_keys_is_bounded_invalid() -> None:
    keys = [_jwk(_generate_private(), kid=f"k-{index:02d}") for index in range(16)]
    keys.append({"kty": "EC", "kid": "ec-1"})
    fetch = _FakeFetch({METADATA_URL: _metadata(), JWKS_URL: _jwks(*keys)})

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "jwks_invalid"


def test_jwks_duplicate_kid_on_irrelevant_key_is_accepted(rsa_pair: object) -> None:
    private, _ = rsa_pair
    ec = {"kty": "EC", "kid": "dup", "alg": "ES256"}
    fetch = _FakeFetch(
        {METADATA_URL: _metadata(), JWKS_URL: _jwks(ec, _jwk(private, kid="dup"))}
    )

    snapshot = load_oauth_validation_material(ISSUER, fetch)

    assert snapshot.find("dup") is not None


# --------------------------------------------------------------------------- #
# base64urlUInt minimality (no leading zero octets, no zero value)
# --------------------------------------------------------------------------- #

def test_jwks_rejects_redundant_leading_zero_modulus(rsa_pair: object) -> None:
    private, _ = rsa_pair
    numbers = private.public_key().public_numbers()
    n_bytes = numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")
    jwk = _jwk(private)
    jwk["n"] = _b64url(b"\x00" + n_bytes)
    fetch = _FakeFetch({METADATA_URL: _metadata(), JWKS_URL: _jwks(jwk)})

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "jwks_invalid"


def test_jwks_rejects_redundant_leading_zero_exponent(rsa_pair: object) -> None:
    private, _ = rsa_pair
    jwk = _jwk(private)
    jwk["e"] = _b64url(b"\x00\x01\x00\x01")
    fetch = _FakeFetch({METADATA_URL: _metadata(), JWKS_URL: _jwks(jwk)})

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "jwks_invalid"


# --------------------------------------------------------------------------- #
# Strict key_ops: exactly ["verify"]
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "key_ops",
    [
        ["sign"],
        [],
        ["verify", "verify"],
        ["verify", "sign", "verify"],
        [None],
        [42],
        "verify",
        {"verify": True},
    ],
)
def test_jwks_sign_only_or_malformed_key_ops_on_single_key_is_invalid(
    rsa_pair: object,
    key_ops: object,
) -> None:
    private, _ = rsa_pair
    fetch = _FakeFetch(
        {METADATA_URL: _metadata(), JWKS_URL: _jwks(_jwk(private, key_ops=key_ops))}
    )

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "jwks_invalid"


@pytest.mark.parametrize(
    "key_ops",
    [["verify"], ["verify", "sign"], ["sign", "verify"]],
)
def test_jwks_accepts_well_formed_key_ops_containing_verify(
    rsa_pair: object,
    key_ops: object,
) -> None:
    private, _ = rsa_pair
    fetch = _FakeFetch(
        {METADATA_URL: _metadata(), JWKS_URL: _jwks(_jwk(private, key_ops=key_ops))}
    )

    snapshot = load_oauth_validation_material(ISSUER, fetch)

    assert snapshot.find(KID) is not None


def test_jwks_sign_only_key_is_ignored_alongside_verify_key(rsa_pair: object) -> None:
    private, _ = rsa_pair
    sign_only = _jwk(_generate_private(), kid="sign-only", key_ops=["sign"])
    fetch = _FakeFetch(
        {METADATA_URL: _metadata(), JWKS_URL: _jwks(_jwk(private), sign_only)}
    )

    snapshot = load_oauth_validation_material(ISSUER, fetch)

    assert snapshot.find(KID) is not None
    assert snapshot.find("sign-only") is None


def test_jwks_sign_only_set_yields_no_candidates() -> None:
    sign_only = _jwk(_generate_private(), kid="sign-only", key_ops=["sign"])
    fetch = _FakeFetch({METADATA_URL: _metadata(), JWKS_URL: _jwks(sign_only)})

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "jwks_invalid"


def test_jwks_malformed_key_ops_rejects_entire_set(rsa_pair: object) -> None:
    private, _ = rsa_pair
    malformed = _jwk(_generate_private(), kid="bad", key_ops=["verify", "verify"])
    fetch = _FakeFetch(
        {METADATA_URL: _metadata(), JWKS_URL: _jwks(_jwk(private), malformed)}
    )

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "jwks_invalid"


# --------------------------------------------------------------------------- #
# Strict JSON: NaN and Infinity rejected
# --------------------------------------------------------------------------- #

def test_metadata_with_nan_is_bounded_invalid() -> None:
    body = json.dumps({"issuer": ISSUER, "jwks_uri": JWKS_URL, "x": float("nan")}).encode(
        "utf-8"
    )
    fetch = _FakeFetch({METADATA_URL: body, JWKS_URL: _jwks()})

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "metadata_invalid"


def test_metadata_with_infinity_is_bounded_invalid() -> None:
    body = json.dumps({"issuer": ISSUER, "jwks_uri": JWKS_URL, "x": float("inf")}).encode(
        "utf-8"
    )
    fetch = _FakeFetch({METADATA_URL: body, JWKS_URL: _jwks()})

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "metadata_invalid"


def test_jwks_with_nan_is_bounded_invalid(rsa_pair: object) -> None:
    private, _ = rsa_pair
    jwk = _jwk(private)
    jwk["x"] = float("nan")
    body = json.dumps({"keys": [jwk]}).encode("utf-8")
    fetch = _FakeFetch({METADATA_URL: _metadata(), JWKS_URL: body})

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "jwks_invalid"


def test_jwks_with_huge_integer_is_bounded_invalid() -> None:
    huge = b"9" * 5000
    body = b'{"keys":[{"kty":"RSA","kid":"k","n":' + huge + b',"e":"AQAB"}]}'
    fetch = _FakeFetch({METADATA_URL: _metadata(), JWKS_URL: body})

    with pytest.raises(OAuthDiscoveryError) as excinfo:
        load_oauth_validation_material(ISSUER, fetch)

    assert excinfo.value.code == "jwks_invalid"
