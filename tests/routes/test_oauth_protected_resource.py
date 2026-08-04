"""S5 focused route tests for OAuth protected-resource metadata and challenge.

TRACK_045 S5 adds the thin OAuth HTTP surface on top of the S4 composition:
exactly one GET ``/.well-known/oauth-protected-resource/mcp`` serving exact
RFC 9728-shaped JSON with ``Cache-Control: no-store`` only when OAuth is enabled,
and an OAuth-only body-free pre-MCP ``401`` carrying exactly
``WWW-Authenticate: Bearer resource_metadata="<metadata URL>"``. IPv4/IPv6
resource identity derives solely from validated server configuration, never from
request Host or forwarded headers. Operator/anonymous/default and disabled-OAuth
configurations stay route- and challenge-free, and MyMCP must not expose
authorization-server, OpenID, or registration routes.

App construction uses the injected discovery seam; no network, provider, token,
or credential is used. Tokens are deliberately bogus for challenge coverage and
only one real valid token proves successful routing through the unchanged OAuth
validator.
"""

import hashlib
import json
from base64 import urlsafe_b64encode
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

import mymcp.host.authentication as host_authentication
from mymcp.app import create_production_app

ISSUER = "https://auth.example.com"
JWKS_URL = "https://auth.example.com/keys"
METADATA_URL = "https://auth.example.com/.well-known/oauth-authorization-server"
KID = "signing-key-1"
NOW = 1_700_000_000
DEFAULT_RESOURCE = "http://127.0.0.1:8000/mcp"
DEFAULT_METADATA_URL = (
    "http://127.0.0.1:8000/.well-known/oauth-protected-resource/mcp"
)
PROTECTED_RESOURCE_PATH = "/.well-known/oauth-protected-resource/mcp"

_MEMORY_DISABLED_VARS = (
    "MNEMOSYNE_MEMORY_REMEMBER_ENABLED",
    "MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED",
    "MNEMOSYNE_MEMORY_REVISE_ENABLED",
    "MNEMOSYNE_MEMORY_FORGET_ENABLED",
)


def _b64url(data: bytes) -> str:
    return urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _jwk_body(private: rsa.RSAPrivateKey) -> bytes:
    numbers = private.public_key().public_numbers()
    n_bytes = numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")
    e_bytes = numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")
    jwk = {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": KID,
        "n": _b64url(n_bytes),
        "e": _b64url(e_bytes),
    }
    return json.dumps({"keys": [jwk]}).encode("utf-8")


def _metadata_body() -> bytes:
    return json.dumps({"issuer": ISSUER, "jwks_uri": JWKS_URL}).encode("utf-8")


def _install_oauth_seam(monkeypatch: pytest.MonkeyPatch) -> rsa.RSAPrivateKey:
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    routes = {
        METADATA_URL: _metadata_body(),
        JWKS_URL: _jwk_body(private),
    }
    monkeypatch.setattr(
        host_authentication,
        "_OAUTH_DISCOVERY_FETCH",
        lambda url, max_bytes: routes[url],
    )
    monkeypatch.setattr(host_authentication, "_OAUTH_CLOCK", lambda: NOW)
    return private


def _schema5_configuration(
    *,
    address: str | None = None,
    port: int | None = None,
    enabled: bool = True,
    anonymous_enabled: bool = False,
):
    from mymcp.host.configuration import parse_host_configuration_toml

    server_block = ""
    if address is not None or port is not None:
        lines = ["[server]"]
        if address is not None:
            lines.append(f'address = "{address}"')
        if port is not None:
            lines.append(f"port = {port}")
        server_block = "\n".join(lines) + "\n"
    return parse_host_configuration_toml(
        f"""schema_version = 5
{server_block}[authentication]
anonymous_enabled = {str(anonymous_enabled).lower()}
[[authentication.adapters]]
id = "external-oauth"
type = "oauth-jwt-jwks-v1"
enabled = {str(enabled).lower()}
route = {{source = "authorization", scheme = "bearer"}}
[authentication.oauth_jwt]
issuer = "{ISSUER}"
"""
    )


def _valid_token(
    private: rsa.RSAPrivateKey,
    *,
    aud: str = DEFAULT_RESOURCE,
) -> str:
    import jwt

    return jwt.encode(
        {
            "iss": ISSUER,
            "aud": aud,
            "sub": "stable-subject",
            "exp": NOW + 240,
            "iat": NOW - 60,
            "client_id": "mcp-client",
            "jti": "jti-abc-123",
        },
        private,
        algorithm="RS256",
        headers={"typ": "at+jwt", "kid": KID},
    )


@pytest.fixture
def isolated_env(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    for var in _MEMORY_DISABLED_VARS:
        monkeypatch.setenv(var, "false")
    monkeypatch.delenv("MNEMOSYNE_MEMORY_ROOT", raising=False)


def _oauth_client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    address: str | None = None,
    port: int | None = None,
) -> TestClient:
    _install_oauth_seam(monkeypatch)
    configuration = _schema5_configuration(address=address, port=port)
    return TestClient(create_production_app(configuration))


# --------------------------------------------------------------------------- #
# Protected-resource metadata (enabled OAuth only)
# --------------------------------------------------------------------------- #


def test_oauth_metadata_route_serves_exact_shape_with_no_store(
    isolated_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _oauth_client(monkeypatch)

    response = client.get(PROTECTED_RESOURCE_PATH)

    assert response.status_code == 200
    assert response.headers.get("cache-control") == "no-store"
    body = response.json()
    assert set(body) == {"resource", "authorization_servers", "bearer_methods_supported"}
    assert body == {
        "resource": DEFAULT_RESOURCE,
        "authorization_servers": [ISSUER],
        "bearer_methods_supported": ["header"],
    }


@pytest.mark.parametrize("method", ["post", "put", "delete"])
def test_metadata_route_is_get_only(
    method: str,
    isolated_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _oauth_client(monkeypatch)

    response = client.request(method, PROTECTED_RESOURCE_PATH)

    assert response.status_code == 405


def test_oauth_ipv6_metadata_resource_is_compressed_bracketed(
    isolated_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _oauth_client(monkeypatch, address="::1")

    body = client.get(PROTECTED_RESOURCE_PATH).json()

    assert body["resource"] == "http://[::1]:8000/mcp"
    assert body["authorization_servers"] == [ISSUER]
    assert body["bearer_methods_supported"] == ["header"]


def test_metadata_ignores_hostile_host_and_forwarded_headers(
    isolated_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _oauth_client(monkeypatch)

    response = client.get(
        PROTECTED_RESOURCE_PATH,
        headers={
            "Host": "evil.example.com",
            "X-Forwarded-Host": "evil.example.com",
            "X-Forwarded-Proto": "https",
        },
    )

    assert response.json()["resource"] == DEFAULT_RESOURCE


# --------------------------------------------------------------------------- #
# OAuth Bearer challenge on /mcp (enabled OAuth only)
# --------------------------------------------------------------------------- #


def test_oauth_invalid_bearer_is_body_free_401_with_exact_challenge(
    isolated_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _oauth_client(monkeypatch)

    response = client.post(
        "/mcp",
        headers={"Authorization": "Bearer not-a-token"},
        content=b"not-json",
    )

    assert response.status_code == 401
    assert response.content == b""
    assert response.headers["www-authenticate"] == (
        'Bearer resource_metadata="%s"' % DEFAULT_METADATA_URL
    )


@pytest.mark.parametrize("method", ["get", "post"])
def test_oauth_missing_evidence_carries_same_challenge(
    method: str,
    isolated_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _oauth_client(monkeypatch)

    response = client.request(method, "/mcp", content=b"not-json")

    assert response.status_code == 401
    assert response.content == b""
    assert response.headers["www-authenticate"] == (
        'Bearer resource_metadata="%s"' % DEFAULT_METADATA_URL
    )


def test_oauth_challenge_has_no_token_derived_distinction(
    isolated_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _oauth_client(monkeypatch)

    missing = client.post("/mcp", content=b"ignored")
    invalid = client.post(
        "/mcp", headers={"Authorization": "Bearer expired"}, content=b"ignored"
    )

    assert (
        missing.headers["www-authenticate"]
        == invalid.headers["www-authenticate"]
        == 'Bearer resource_metadata="%s"' % DEFAULT_METADATA_URL
    )
    assert missing.content == invalid.content == b""


def test_oauth_challenge_ignores_hostile_host_header(
    isolated_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _oauth_client(monkeypatch)

    response = client.post(
        "/mcp",
        headers={"Authorization": "Bearer bad", "Host": "evil.example.com"},
        content=b"ignored",
    )

    assert response.headers["www-authenticate"] == (
        'Bearer resource_metadata="%s"' % DEFAULT_METADATA_URL
    )


def test_oauth_valid_token_reaches_app_without_challenge(
    isolated_env: None,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    import logging

    private = _install_oauth_seam(monkeypatch)
    client = TestClient(create_production_app(_schema5_configuration()))

    import jwt

    token = _valid_token(private)
    with caplog.at_level(logging.DEBUG):
        response = client.post(
            "/mcp", headers={"Authorization": f"Bearer {token}"}, json={}
        )

    assert "www-authenticate" not in {k.lower() for k in response.headers}
    assert response.status_code in {200, 202, 400}
    assert "WWW-Authenticate" not in caplog.text


def test_oauth_registered_session_lifecycle_uses_the_common_transport_contract(
    isolated_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private = _install_oauth_seam(monkeypatch)
    client = TestClient(create_production_app(_schema5_configuration()))
    authorization = {"Authorization": f"Bearer {_valid_token(private)}"}

    initialized = client.post(
        "/mcp",
        headers=authorization,
        json={
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-11-25"},
        },
    )
    session_headers = {
        **authorization,
        "MCP-Session-Id": initialized.headers["mcp-session-id"],
        "MCP-Protocol-Version": "2025-11-25",
    }
    followed = client.post("/mcp", headers=session_headers, json={"id": 2, "method": "ping"})
    terminated = client.delete("/mcp", headers=session_headers)

    assert initialized.status_code == 200
    assert followed.status_code == 200
    assert (terminated.status_code, terminated.content) == (204, b"")


# --------------------------------------------------------------------------- #
# Operator / anonymous / default / disabled-OAuth stay challenge- and route-free
# --------------------------------------------------------------------------- #


def test_operator_bearer_configuration_has_no_metadata_route_or_challenge(
    isolated_env: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
) -> None:
    verifier = tmp_path / "verifier.json"
    verifier.write_text(
        json.dumps(
            {
                "format_version": 1,
                "credentials": [
                    {
                        "id": "a" * 32,
                        "subject": "stable-subject",
                        "digest": urlsafe_b64encode(
                            hashlib.sha256(bytes(range(32))).digest()
                        )
                        .rstrip(b"=")
                        .decode("ascii"),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    verifier.chmod(0o600)
    from mymcp.host.configuration import parse_host_configuration_toml

    configuration = parse_host_configuration_toml(
        f"""schema_version = 4
[authentication]
anonymous_enabled = false
[[authentication.adapters]]
id = "local-client"
type = "operator-bearer-v1"
enabled = true
route = {{source = "authorization", scheme = "bearer"}}
[authentication.operator_bearer]
verifier_path = "{verifier}"
"""
    )
    client = TestClient(create_production_app(configuration))

    assert client.get(PROTECTED_RESOURCE_PATH).status_code == 404
    denied = client.post(
        "/mcp", headers={"Authorization": "Bearer invalid"}, content=b"ignored"
    )
    assert denied.status_code == 401
    assert "www-authenticate" not in {k.lower() for k in denied.headers}


def test_default_anonymous_configuration_has_no_metadata_route_or_challenge(
    isolated_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from mymcp.host.configuration import HostConfiguration

    client = TestClient(create_production_app(HostConfiguration.default()))

    assert client.get(PROTECTED_RESOURCE_PATH).status_code == 404
    # Evidence-free default is anonymous, so force a 401 via malformed evidence.
    denied = client.post(
        "/mcp", headers={"Authorization": "Bearer "}, content=b"ignored"
    )
    assert denied.status_code == 401
    assert "www-authenticate" not in {k.lower() for k in denied.headers}


def test_disabled_oauth_declaration_has_no_metadata_route_or_challenge(
    isolated_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_oauth_seam(monkeypatch)
    configuration = _schema5_configuration(enabled=False)
    client = TestClient(create_production_app(configuration))

    assert client.get(PROTECTED_RESOURCE_PATH).status_code == 404
    denied = client.post("/mcp", content=b"ignored")
    assert denied.status_code == 401
    assert "www-authenticate" not in {k.lower() for k in denied.headers}


# --------------------------------------------------------------------------- #
# No authorization-server / OIDC / registration routes, even when OAuth enabled
# --------------------------------------------------------------------------- #

_FORBIDDEN_OAUTH_PATHS = (
    "/.well-known/oauth-authorization-server",
    "/.well-known/openid-configuration",
    "/register",
    "/.well-known/oauth-protected-resource",
)


@pytest.mark.parametrize("path", _FORBIDDEN_OAUTH_PATHS)
def test_enabled_oauth_does_not_expose_authorization_server_or_register(
    path: str,
    isolated_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _oauth_client(monkeypatch)

    for method in ("get", "post"):
        response = client.request(method, path)
        assert response.status_code == 404, (method, path)
