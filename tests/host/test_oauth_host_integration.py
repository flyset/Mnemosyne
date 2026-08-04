"""S4 focused host-integration tests for schema 5 / production OAuth composition.

This file covers TRACK_045 S4: exact schema-5 parsing and issuer intent,
schemas 1-4 compatibility, the mandatory disabled anonymous access for enabled
OAuth, loopback resource/audience derivation, bounded content-free failures,
immutable snapshot loading, and Authentication-before-plugin-runtime ordering.
The public metadata route and Bearer challenge are out of scope (S5).

All snapshot material comes from injected fetch doubles and injected clocks;
no network, provider, account, token, or credential is used.
"""

import base64
import json
import logging
from dataclasses import FrozenInstanceError

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

import mymcp.host.authentication as host_authentication
import mymcp.host.bootstrap as bootstrap
from mymcp import app as app_module
from mymcp.app import create_production_app
from mymcp.authentication.contracts import (
    AdapterId,
    AuthenticationEvidence,
    AuthenticationRequestContext,
    EvidenceRoute,
    Principal,
    PrincipalKind,
)
from mymcp.authentication.oauth import (
    derive_oauth_metadata_url,
    derive_oauth_resource,
    validate_oauth_issuer,
)
from mymcp.authentication.router import Authenticator
from mymcp.host.authentication import (
    HostAuthenticationCompositionError,
    build_production_authenticator,
)
from mymcp.host.configuration import (
    HostAuthenticationConfiguration,
    HostConfiguration,
    HostConfigurationError,
    HostConfigurationSchemaVersion,
    HostOAuthJwtConfiguration,
    HostServerConfiguration,
    OAUTH_JWT_ADAPTER_TYPE,
    SUPPORTED_HOST_CONFIGURATION_SCHEMA_VERSIONS,
    parse_host_configuration_toml,
)

AUTHENTICATION_LOGGER = "mymcp.host.authentication"
ISSUER = "https://auth.example.com"
JWKS_URL = "https://auth.example.com/keys"
METADATA_URL = "https://auth.example.com/.well-known/oauth-authorization-server"
KID = "signing-key-1"
NOW = 1_700_000_000
CONTEXT = AuthenticationRequestContext("POST", "mcp")
DEFAULT_RESOURCE = "http://127.0.0.1:8000/mcp"
OAUTH_ROUTE = EvidenceRoute("authorization", "bearer", None)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _generate_private(bits: int = 2048) -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=bits)


def _jwk_body(private: rsa.RSAPrivateKey, kid: str = KID) -> bytes:
    numbers = private.public_key().public_numbers()
    n_bytes = numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")
    e_bytes = numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")
    jwk = {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": kid,
        "n": _b64url(n_bytes),
        "e": _b64url(e_bytes),
    }
    return json.dumps({"keys": [jwk]}).encode("utf-8")


def _metadata_body(issuer: str = ISSUER, jwks_uri: str = JWKS_URL) -> bytes:
    return json.dumps({"issuer": issuer, "jwks_uri": jwks_uri}).encode("utf-8")


def _token(
    private: rsa.RSAPrivateKey,
    *,
    aud: str = DEFAULT_RESOURCE,
    iss: str = ISSUER,
    kid: str = KID,
    now: int = NOW,
) -> str:
    return jwt.encode(
        {
            "iss": iss,
            "aud": aud,
            "sub": "stable-subject",
            "exp": now + 240,
            "iat": now - 60,
            "client_id": "mcp-client",
            "jti": "jti-abc-123",
        },
        private,
        algorithm="RS256",
        headers={"typ": "at+jwt", "kid": kid},
    )


class _FakeFetch:
    def __init__(self, routes: dict[str, bytes]) -> None:
        self.routes = dict(routes)
        self.calls: list[str] = []

    def __call__(self, url: str, max_bytes: int) -> bytes:
        self.calls.append(url)
        return self.routes[url]


def _install_oauth_seam(
    monkeypatch: pytest.MonkeyPatch,
    private: rsa.RSAPrivateKey,
) -> _FakeFetch:
    fetch = _FakeFetch(
        {
            METADATA_URL: _metadata_body(),
            JWKS_URL: _jwk_body(private),
        }
    )
    monkeypatch.setattr(host_authentication, "_OAUTH_DISCOVERY_FETCH", fetch)
    monkeypatch.setattr(host_authentication, "_OAUTH_CLOCK", lambda: NOW)
    return fetch


def _schema5_oauth_configuration(
    *,
    enabled: bool = True,
    anonymous_enabled: bool = False,
    issuer: str = ISSUER,
    adapter_id: str = "external-oauth",
    include_oauth_table: bool = True,
    route: str = 'route = {source = "authorization", scheme = "bearer"}',
):
    oauth_table = (
        f"[authentication.oauth_jwt]\nissuer = \"{issuer}\"\n"
        if include_oauth_table
        else ""
    )
    return parse_host_configuration_toml(
        f"""
schema_version = 5
[authentication]
anonymous_enabled = {str(anonymous_enabled).lower()}
[[authentication.adapters]]
id = "{adapter_id}"
type = "oauth-jwt-jwks-v1"
enabled = {str(enabled).lower()}
{route}
{oauth_table}"""
    )


# --------------------------------------------------------------------------- #
# Schema 5 parsing and invariants
# --------------------------------------------------------------------------- #


def test_schema_v5_is_supported_alongside_schemas_one_through_four() -> None:
    assert SUPPORTED_HOST_CONFIGURATION_SCHEMA_VERSIONS == frozenset({1, 2, 3, 4, 5, 6})


def test_schema_v5_parses_exact_optional_oauth_issuer_intent() -> None:
    configuration = _schema5_oauth_configuration()

    assert configuration.schema_version == HostConfigurationSchemaVersion(5)
    assert configuration.authentication.anonymous_enabled is False
    assert configuration.authentication.oauth_jwt is not None
    assert configuration.authentication.oauth_jwt.issuer == ISSUER
    adapter = configuration.authentication.adapters[0]
    assert adapter.adapter_id == AdapterId("external-oauth")
    assert adapter.adapter_type == OAUTH_JWT_ADAPTER_TYPE
    assert adapter.route == EvidenceRoute("authorization", "bearer", None)
    assert isinstance(configuration.authentication.oauth_jwt, HostOAuthJwtConfiguration)
    with pytest.raises(FrozenInstanceError):
        configuration.authentication.oauth_jwt.issuer = "changed"  # type: ignore[misc]


def test_oauth_jwt_issuer_must_be_canonical_https_uri() -> None:
    assert validate_oauth_issuer(ISSUER) == ISSUER
    with pytest.raises(ValueError, match="^invalid oauth issuer$"):
        validate_oauth_issuer("http://auth.example.com")
    with pytest.raises(ValueError, match="^invalid oauth issuer$"):
        validate_oauth_issuer("https://localhost")
    with pytest.raises(ValueError, match="^invalid oauth issuer$"):
        validate_oauth_issuer("https://auth.example.com:8443")


@pytest.mark.parametrize("enabled", [False, True])
def test_schema_v5_requires_oauth_table_with_any_oauth_declaration(
    enabled: bool,
) -> None:
    with pytest.raises(HostConfigurationError) as captured:
        _schema5_oauth_configuration(enabled=enabled, include_oauth_table=False)

    assert captured.value.code == "invalid_schema"


def test_schema_v5_prohibits_oauth_table_without_oauth_declaration() -> None:
    with pytest.raises(HostConfigurationError) as captured:
        parse_host_configuration_toml(
            f"""
schema_version = 5
[authentication]
anonymous_enabled = false
[authentication.oauth_jwt]
issuer = "{ISSUER}"
"""
        )

    assert captured.value.code == "invalid_schema"


@pytest.mark.parametrize(
    "oauth_jwt_source",
    [
        "[authentication.oauth_jwt]",
        "[authentication.oauth_jwt]\nissuer = 1",
        (
            "[authentication.oauth_jwt]\n"
            'issuer = "https://auth.example.com"\nunknown = true'
        ),
        '[authentication.oauth_jwt]\nother = "https://auth.example.com"',
    ],
)
def test_schema_v5_oauth_jwt_table_shape_is_strict(oauth_jwt_source: str) -> None:
    with pytest.raises(HostConfigurationError) as captured:
        parse_host_configuration_toml(
            """
schema_version = 5
[authentication]
anonymous_enabled = false
[[authentication.adapters]]
id = "external-oauth"
type = "oauth-jwt-jwks-v1"
enabled = false
route = {source = "authorization", scheme = "bearer"}
"""
            + oauth_jwt_source
        )

    assert captured.value.code == "invalid_schema"


@pytest.mark.parametrize(
    "issuer",
    [
        "http://auth.example.com",
        "not-a-url",
        "https://host",
        "https://127.0.0.1",
        "https://localhost",
        "https://auth.example.com:8443",
        "https://auth.example.com/path/",
        "https://auth.example.com?query=1",
        "https://auth.example.com#frag",
        "https://user@auth.example.com",
    ],
)
def test_schema_v5_rejects_invalid_oauth_issuers(issuer: str) -> None:
    with pytest.raises(HostConfigurationError) as captured:
        _schema5_oauth_configuration(issuer=issuer)

    assert captured.value.code == "invalid_schema"


def test_schema_v5_supports_operator_bearer_alone_without_oauth() -> None:
    configuration = parse_host_configuration_toml(
        f"""
schema_version = 5
[authentication]
anonymous_enabled = true
[[authentication.adapters]]
id = "local-client"
type = "operator-bearer-v1"
enabled = false
route = {{source = "authorization", scheme = "bearer"}}
[authentication.operator_bearer]
verifier_path = "/etc/mymcp/verifier.json"
"""
    )

    assert configuration.authentication.operator_bearer is not None
    assert configuration.authentication.oauth_jwt is None


def test_schema_v5_rejects_oauth_and_operator_co_declaration_jwt() -> None:
    with pytest.raises(HostConfigurationError) as captured:
        parse_host_configuration_toml(
            f"""
schema_version = 5
[authentication]
anonymous_enabled = false
[[authentication.adapters]]
id = "oauth-client"
type = "oauth-jwt-jwks-v1"
enabled = false
route = {{source = "authorization", scheme = "bearer"}}
[[authentication.adapters]]
id = "operator-client"
type = "operator-bearer-v1"
enabled = false
route = {{source = "authorization", scheme = "bearer"}}
[authentication.operator_bearer]
verifier_path = "/etc/mymcp/verifier.json"
[authentication.oauth_jwt]
issuer = "{ISSUER}"
"""
        )

    assert captured.value.code == "invalid_schema"


def test_schema_v4_rejects_oauth_jwt_table() -> None:
    with pytest.raises(HostConfigurationError) as captured:
        parse_host_configuration_toml(
            f"""
schema_version = 4
[authentication]
anonymous_enabled = false
[authentication.oauth_jwt]
issuer = "{ISSUER}"
"""
        )

    assert captured.value.code == "invalid_schema"


def test_schema_v5_snapshot_requires_consistent_oauth_values() -> None:
    adapter = _schema5_oauth_configuration().authentication.adapters[0]
    with pytest.raises(ValueError, match="^invalid host configuration$"):
        HostConfiguration(
            HostConfigurationSchemaVersion(5),
            HostServerConfiguration(),
            (),
            HostAuthenticationConfiguration(False, (adapter,)),
        )
    with pytest.raises(
        ValueError, match="^invalid host operator oauth configuration$"
    ):
        HostOAuthJwtConfiguration("http://auth.example.com")


# --------------------------------------------------------------------------- #
# Loopback resource derivation
# --------------------------------------------------------------------------- #


def test_derive_oauth_resource_ipv4_loopback() -> None:
    assert derive_oauth_resource("127.0.0.1", 8000) == "http://127.0.0.1:8000/mcp"
    assert derive_oauth_resource("127.0.0.2", 9000) == "http://127.0.0.2:9000/mcp"


def test_derive_oauth_resource_ipv6_loopback_is_compressed_bracketed() -> None:
    assert derive_oauth_resource("::1", 8000) == "http://[::1]:8000/mcp"


def test_derive_oauth_resource_rejects_non_loopback_or_invalid() -> None:
    for address, port in (("192.168.1.1", 8000), ("example.com", 8000), ("::", 8000)):
        with pytest.raises(ValueError, match="^invalid oauth resource$"):
            derive_oauth_resource(address, port)
    with pytest.raises(ValueError, match="^invalid oauth resource$"):
        derive_oauth_resource("127.0.0.1", 0)


def test_derive_oauth_metadata_url_ipv4() -> None:
    assert (
        derive_oauth_metadata_url("127.0.0.1", 8000)
        == "http://127.0.0.1:8000/.well-known/oauth-protected-resource/mcp"
    )


def test_derive_oauth_metadata_url_ipv6_is_compressed_bracketed() -> None:
    assert (
        derive_oauth_metadata_url("::1", 8000)
        == "http://[::1]:8000/.well-known/oauth-protected-resource/mcp"
    )


def test_derive_oauth_metadata_url_rejects_invalid_resource() -> None:
    for address, port in (("192.168.1.1", 8000), ("example.com", 8000), ("::", 8000)):
        with pytest.raises(ValueError, match="^invalid oauth resource$"):
            derive_oauth_metadata_url(address, port)
    with pytest.raises(ValueError, match="^invalid oauth resource$"):
        derive_oauth_metadata_url("127.0.0.1", 0)


# --------------------------------------------------------------------------- #
# Production composition
# --------------------------------------------------------------------------- #


def test_enabled_oauth_adapter_composes_with_exact_route_and_anonymous_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_oauth_seam(monkeypatch, _generate_private())
    configuration = _schema5_oauth_configuration()

    authenticator = build_production_authenticator(configuration)

    assert isinstance(authenticator, Authenticator)
    assert authenticator.anonymous_enabled is False
    assert len(authenticator.registrations) == 1
    registration = authenticator.registrations[0]
    assert registration.adapter_id == AdapterId("external-oauth")
    assert registration.route == OAUTH_ROUTE


def test_enabled_oauth_valid_token_yields_registered_principal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private = _generate_private()
    _install_oauth_seam(monkeypatch, private)
    configuration = _schema5_oauth_configuration()

    authenticator = build_production_authenticator(configuration)
    principal = authenticator.authenticate(
        AuthenticationEvidence(OAUTH_ROUTE, _token(private).encode("ascii")),
        CONTEXT,
    )

    assert isinstance(principal, Principal)
    assert principal.kind is PrincipalKind.REGISTERED
    assert principal.adapter_id == AdapterId("external-oauth")
    assert principal.subject.startswith("oauth-jwt-v1:")
    assert "stable-subject" not in principal.subject
    assert principal.principal_id.startswith("registered:external-oauth:")


def test_enabled_oauth_requires_anonymous_access_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_oauth_seam(monkeypatch, _generate_private())
    configuration = _schema5_oauth_configuration(anonymous_enabled=True)

    with pytest.raises(HostAuthenticationCompositionError) as captured:
        build_production_authenticator(configuration)

    assert captured.value.code == "anonymous_access_enabled"


def test_enabled_oauth_declaration_requires_the_exact_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_oauth_seam(monkeypatch, _generate_private())
    configuration = _schema5_oauth_configuration(
        route='route = {source = "authorization", scheme = "bearer", profile = "oauth"}'
    )

    with pytest.raises(HostAuthenticationCompositionError) as captured:
        build_production_authenticator(configuration)

    assert captured.value.code == "oauth_route_invalid"


def test_disabled_oauth_declaration_never_loads_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_fetch(url: str, max_bytes: int) -> bytes:
        pytest.fail("disabled OAuth accessed the discovery fetch")

    monkeypatch.setattr(host_authentication, "_OAUTH_DISCOVERY_FETCH", fail_fetch)
    configuration = _schema5_oauth_configuration(enabled=False)

    authenticator = build_production_authenticator(configuration)

    assert authenticator.registrations == ()
    assert authenticator.anonymous_enabled is False


def test_oauth_snapshot_failure_is_bounded_and_content_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_fetch(url: str, max_bytes: int) -> bytes:
        raise RuntimeError("provider outage")

    monkeypatch.setattr(host_authentication, "_OAUTH_DISCOVERY_FETCH", fail_fetch)
    monkeypatch.setattr(host_authentication, "_OAUTH_CLOCK", lambda: NOW)
    configuration = _schema5_oauth_configuration()

    with pytest.raises(HostAuthenticationCompositionError) as captured:
        build_production_authenticator(configuration)

    assert captured.value.code == "oauth_validation_source"
    assert str(captured.value) == "OAuth validation material is unavailable"
    assert ISSUER not in str(captured.value)
    assert ISSUER not in repr(captured.value)


def test_composition_oauth_emits_one_bounded_error_event(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fail_fetch(url: str, max_bytes: int) -> bytes:
        raise RuntimeError("outage")

    monkeypatch.setattr(host_authentication, "_OAUTH_DISCOVERY_FETCH", fail_fetch)
    monkeypatch.setattr(host_authentication, "_OAUTH_CLOCK", lambda: NOW)
    configuration = _schema5_oauth_configuration()

    with caplog.at_level(logging.ERROR, logger=AUTHENTICATION_LOGGER):
        with pytest.raises(HostAuthenticationCompositionError) as captured:
            build_production_authenticator(configuration)

    records = [
        record.getMessage()
        for record in caplog.records
        if record.name == AUTHENTICATION_LOGGER
    ]
    assert records == [
        "authentication_composition outcome=error code=oauth_validation_source"
    ]
    assert ISSUER not in records[0]


# --------------------------------------------------------------------------- #
# Authentication before plugin runtime publication
# --------------------------------------------------------------------------- #


def test_production_app_loads_oauth_snapshot_before_runtime_publication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private = _generate_private()
    fetch = _install_oauth_seam(monkeypatch, private)
    configuration = _schema5_oauth_configuration()
    sentinel = object()
    calls: list[str] = []
    oauth_surfaces: list[object] = []

    def build_runtime(_configuration) -> object:
        calls.append("runtime")
        return sentinel

    def build_app(_runtime, _authenticator, **kwargs) -> object:
        calls.append("app")
        oauth_surfaces.append(kwargs.get("oauth_protected_resource"))
        return sentinel

    monkeypatch.setattr(bootstrap, "build_production_runtime", build_runtime)
    monkeypatch.setattr(app_module, "create_app", build_app)

    assert create_production_app(configuration) is sentinel
    assert calls == ["runtime", "app"]
    assert len(fetch.calls) == 2
    surface = oauth_surfaces[0]
    assert surface is not None
    assert surface.resource == DEFAULT_RESOURCE
    assert surface.authorization_servers == (ISSUER,)
    assert surface.metadata_url == (
        "http://127.0.0.1:8000/.well-known/oauth-protected-resource/mcp"
    )


def test_production_app_oauth_failure_rejects_before_runtime_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_fetch(url: str, max_bytes: int) -> bytes:
        raise RuntimeError("outage")

    monkeypatch.setattr(host_authentication, "_OAUTH_DISCOVERY_FETCH", fail_fetch)
    monkeypatch.setattr(host_authentication, "_OAUTH_CLOCK", lambda: NOW)
    configuration = _schema5_oauth_configuration()
    monkeypatch.setattr(
        bootstrap,
        "build_production_runtime",
        lambda _config: pytest.fail("runtime composition must follow Authentication"),
    )

    with pytest.raises(HostAuthenticationCompositionError) as captured:
        create_production_app(configuration)

    assert captured.value.code == "oauth_validation_source"
