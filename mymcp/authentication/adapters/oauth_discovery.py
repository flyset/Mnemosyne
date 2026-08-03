"""Bounded no-redirect HTTPS metadata/JWKS acquisition (``oauth-jwt-jwks-v1``).

This dormant startup loader acquires exactly one immutable validation snapshot:
it derives the RFC 8414 metadata URL from a canonical HTTPS issuer, fetches the
metadata body, then its declared same-origin HTTPS ``jwks_uri`` body, validates
every approved URI/body/key constraint, and builds one immutable
``OAuthJwtSnapshot``. The loader performs no runtime refresh or provider call;
rotation and key removal are visible only after restart, which acquires a new
snapshot through a fresh load.

The injected ``fetch`` seam owns the HTTPS transport boundary: it must enforce
certificate and hostname validation, reject redirects, bound request time and
streamed body size, and raise an exception on any transport failure. The
standard-library ``bounded_https_fetch`` is the concrete reference
implementation of that seam; doubles are also accepted for deterministic
startup tests. The loader validates URL shapes and consumes only seam
responses. Unknown metadata members are ignored; only ``issuer`` and
``jwks_uri`` are consumed, and no token-controlled URL is ever fetched.

This module is standard-library-only and imports only the concrete OAuth
adapter package. It is dormant and must never be re-exported from
``mymcp.authentication``.
"""

import base64
import binascii
import json
import math
import ssl
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from urllib.parse import urlsplit

from mymcp.authentication.adapters.oauth_jwt import (
    MAX_JWK_COUNT,
    OAuthJwtSnapshot,
    RsaPublicKey,
    build_oauth_jwt_snapshot,
    validate_oauth_issuer,
)

MAX_METADATA_BYTES = 16 * 1024
MAX_JWKS_BYTES = 64 * 1024
_OAUTH_WELL_KNOWN_PATH = "/.well-known/oauth-authorization-server"
_MAX_JSON_DEPTH = 64
DEFAULT_FETCH_TIMEOUT_SECONDS = 10.0
_READ_CHUNK = 64 * 1024

# Bounded fetch seam: (url, max_bytes) -> bytes. It owns certificate/hostname
# validation, redirect rejection, request time, and streaming body bounds.
FetchFn = Callable[[str, int], bytes]

_VALID_FAILURE_CODES = frozenset(
    {"metadata_unavailable", "metadata_invalid", "jwks_unavailable", "jwks_invalid"}
)


class OAuthDiscoveryError(Exception):
    """Bounded content-free discovery failure carrying only a stable code."""

    def __init__(self, code: str) -> None:
        if code not in _VALID_FAILURE_CODES:
            raise ValueError("invalid oauth discovery failure")
        super().__init__()
        self.code = code


class _NoRedirectHTTPRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Turn every 3xx into an error instead of following the redirect."""

    def redirect_request(
        self,
        req: object,
        fp: object,
        code: int,
        msg: str,
        headers: object,
        newurl: object,
    ) -> None:
        return None


def _underlying_socket(response: object) -> object | None:
    """Return the raw socket for a urllib response when reachable, else ``None``.

    ``http.client`` and ``urllib.response`` do not expose a public socket
    accessor, so this is a best-effort walk over the version-dependent private
    attributes. It must never raise.
    """
    for path in ("fp.raw._sock", "fp._sock", "_fp._sock", "_sock"):
        node = response
        try:
            for attribute in path.split("."):
                node = getattr(node, attribute)
        except (AttributeError, OSError):
            continue
        if node is not None:
            return node
    return None


def _set_socket_timeout(response: object, seconds: float) -> None:
    """Push the remaining deadline onto the underlying socket when accessible.

    urllib reads the body through the connection socket, so refreshing
    ``settimeout`` before each bounded chunk bounds each individual receive by
    the *total* remaining time rather than a fresh budget. Fails silently when
    the transport does not expose a socket (for example, injected doubles).
    """
    try:
        sock = _underlying_socket(response)
    except Exception:  # pragma: no cover - defensive
        return
    if sock is None:
        return
    try:
        sock.settimeout(seconds)
    except (AttributeError, OSError, ValueError):
        pass


def _read_bounded(
    response: object,
    limit: int,
    deadline: float,
    clock: Callable[[], float],
) -> bytes:
    """Read at most ``limit + 1`` bytes, bounded by one absolute deadline."""
    total = bytearray()
    chunk = min(_READ_CHUNK, limit + 1)
    while len(total) < limit + 1:
        remaining = deadline - clock()
        if remaining <= 0:
            raise TimeoutError("oauth discovery deadline exceeded")
        _set_socket_timeout(response, remaining)
        part = response.read(chunk)  # type: ignore[attr-defined]
        if not part:
            break
        total.extend(part)
    return bytes(total)


def _validate_fetch_url(url: object) -> str:
    if not isinstance(url, str) or not url or not url.isascii():
        raise ValueError("invalid oauth discovery url")
    try:
        parts = urlsplit(url)
    except ValueError:
        raise ValueError("invalid oauth discovery url") from None
    if (
        parts.scheme != "https"
        or parts.username is not None
        or parts.password is not None
        or parts.fragment
        or parts.hostname is None
        or "%" in parts.netloc
    ):
        raise ValueError("invalid oauth discovery url")
    return url


def bounded_https_fetch(
    url: str,
    max_bytes: int,
    *,
    timeout: float = DEFAULT_FETCH_TIMEOUT_SECONDS,
    _clock: Callable[[], float] = time.monotonic,
) -> bytes:
    """Concrete bounded no-redirect HTTPS fetch.

    Always builds a fresh verified default TLS context (never accepts an
    injected or downgraded context), disables environment proxies, blocks every
    redirect, and bounds the whole exchange by one monotonic absolute deadline
    set across connect, headers, and the streamed body.

    Enforceable stdlib boundary: ``urllib.request`` exposes no absolute
    deadline for returning the response headers; the only lease the caller can
    set is the per-operation socket timeout. This implementation sets that
    timeout to the full remaining deadline before open and re-applies it before
    each body read (when the underlying socket is reachable), then *fails
    closed* whenever an elapsed monotonic deadline is observed. A single
    low-level ``recv`` inside one ``read()`` call can still block up to the
    current socket timeout, which the chunked read refreshals keeps shrinking.
    """
    _validate_fetch_url(url)
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ValueError("invalid oauth discovery fetch limit")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise ValueError("invalid oauth discovery fetch timeout")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("invalid oauth discovery fetch timeout")

    context = ssl.create_default_context()
    if (
        getattr(context, "verify_mode", None) != ssl.CERT_REQUIRED
        or getattr(context, "check_hostname", None) is not True
    ):
        raise RuntimeError("oauth discovery tls context is not verified")

    # ``ProxyHandler({})`` replaces the environment-proxy default and keeps the
    # request on the direct network path.
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        _NoRedirectHTTPRedirectHandler(),
        urllib.request.HTTPSHandler(context=context),
    )
    request = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "MyMCP/oauth-jwt-jwks-v1"}
    )
    start = _clock()
    deadline = start + float(timeout)
    remaining = deadline - _clock()
    if remaining <= 0:
        raise TimeoutError("oauth discovery deadline exceeded")
    response = opener.open(request, timeout=remaining)  # type: ignore[call-overload]
    try:
        status = getattr(response, "status", None)
        if status != 200:
            raise urllib.error.HTTPError(
                url, status, "http status", getattr(response, "headers", None), None  # type: ignore[arg-type]
            )
        return _read_bounded(response, max_bytes, deadline, _clock)
    finally:
        try:
            response.close()  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover - best-effort close
            pass


def derive_oauth_metadata_url(issuer: str) -> str:
    """Derive the RFC 8414 metadata URL for one canonical HTTPS issuer.

    The well-known path is inserted between the authority and any issuer path:
    ``https://host/path`` becomes
    ``https://host/.well-known/oauth-authorization-server/path``.
    """
    validate_oauth_issuer(issuer)
    parts = urlsplit(issuer)
    netloc = parts.netloc
    path = parts.path
    if not path or path == "/":
        return f"https://{netloc}{_OAUTH_WELL_KNOWN_PATH}"
    return f"https://{netloc}{_OAUTH_WELL_KNOWN_PATH}{path}"


def _same_origin_https_jwks_uri(uri: object, issuer: str) -> bool:
    if not isinstance(uri, str) or not uri or not uri.isascii():
        return False
    try:
        target = urlsplit(uri)
        base = urlsplit(issuer)
    except ValueError:
        return False
    if target.scheme != "https":
        return False
    if target.username is not None or target.password is not None:
        return False
    if target.fragment:
        return False
    if target.hostname is None or target.hostname != base.hostname:
        return False
    if "%" in target.netloc:
        return False
    # Canonical authority: lowercase host with no explicit port or exactly "443".
    port_text: str | None = None
    if ":" in target.netloc:
        _, _, port_text = target.netloc.rpartition(":")
        if not port_text or port_text != "443":
            return False
    canonical = target.hostname + (f":{port_text}" if port_text else "")
    if target.netloc != canonical:
        return False
    return True


def _reject_duplicate_pairs(code: str) -> Callable[[list[tuple[str, object]]], dict[str, object]]:
    def _hook(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise OAuthDiscoveryError(code)
            result[key] = value
        return result

    return _hook


def _reject_deeper_than(limit: int, root: object, code: str) -> None:
    stack: list[tuple[object, int]] = [(root, 0)]
    while stack:
        value, depth = stack.pop()
        if depth > limit:
            raise OAuthDiscoveryError(code)
        if isinstance(value, dict):
            stack.extend((item, depth + 1) for item in value.values())
        elif isinstance(value, list):
            stack.extend((item, depth + 1) for item in value)


def _reject_constants(code: str) -> Callable[[str], object]:
    def _hook(constant: str) -> object:
        raise OAuthDiscoveryError(code)

    return _hook


def _parse_bounded_json_object(data: bytes, max_bytes: int, code: str) -> dict[str, object]:
    if type(data) is not bytes:
        raise OAuthDiscoveryError(code)
    if len(data) > max_bytes:
        raise OAuthDiscoveryError(code)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise OAuthDiscoveryError(code) from None
    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs(code),
            parse_constant=_reject_constants(code),
        )
    except OAuthDiscoveryError:
        raise
    except (json.JSONDecodeError, RecursionError, ValueError, OverflowError):
        raise OAuthDiscoveryError(code) from None
    if type(parsed) is not dict:
        raise OAuthDiscoveryError(code)
    _reject_deeper_than(_MAX_JSON_DEPTH, parsed, code)
    return parsed


def _decode_bigint(text: object, code: str) -> int:
    if not isinstance(text, str) or not text or not text.isascii():
        raise OAuthDiscoveryError(code)
    padded = text + "=" * (-len(text) % 4)
    try:
        raw = base64.b64decode(padded, altchars=b"-_")
    except (ValueError, binascii.Error):
        raise OAuthDiscoveryError(code) from None
    if base64.urlsafe_b64encode(raw).rstrip(b"=") != text.encode("ascii"):
        raise OAuthDiscoveryError(code)
    # base64urlUInt minimality: the unsigned big-endian octets must carry no
    # redundant leading zero octet and must not be the zero value.
    if not raw or raw[0] == 0:
        raise OAuthDiscoveryError(code)
    return int.from_bytes(raw, "big")


def _parse_jwk_set(keys: list[object]) -> list[RsaPublicKey]:
    if not keys or len(keys) > MAX_JWK_COUNT:
        raise OAuthDiscoveryError("jwks_invalid")
    candidates: list[RsaPublicKey] = []
    for item in keys:
        if type(item) is not dict:
            raise OAuthDiscoveryError("jwks_invalid")
        # Ignore obviously irrelevant keys: non-RSA, encryption-only
        # (``use=enc``), other-``use``, and other-algorithm keys. Candidate keys
        # (RSA signing RS256 verify) are parsed strictly below; a malformed
        # candidate rejects the entire set.
        if item.get("kty") != "RSA":
            continue
        if item.get("use") not in (None, "sig"):
            continue
        if item.get("alg") is not None and item.get("alg") != "RS256":
            continue
        key_ops = item.get("key_ops")
        if key_ops is not None:
            # A candidate-shaped RSA/RS256 signing key with a malformed
            # ``key_ops`` (wrong type, non-string entries, or duplicates)
            # rejects the entire set.
            if type(key_ops) is not list:
                raise OAuthDiscoveryError("jwks_invalid")
            if not all(isinstance(operation, str) for operation in key_ops):
                raise OAuthDiscoveryError("jwks_invalid")
            if len(key_ops) != len(set(key_ops)):
                raise OAuthDiscoveryError("jwks_invalid")
            # A well-formed list that lacks ``verify`` marks a signing-only key:
            # unsuitable for validation, so it is ignored rather than rejected.
            if "verify" not in key_ops:
                continue
        kid = item.get("kid")
        if not isinstance(kid, str):
            raise OAuthDiscoveryError("jwks_invalid")
        modulus = _decode_bigint(item.get("n"), "jwks_invalid")
        exponent = _decode_bigint(item.get("e"), "jwks_invalid")
        try:
            candidates.append(RsaPublicKey(kid, modulus, exponent))
        except ValueError:
            raise OAuthDiscoveryError("jwks_invalid") from None
    if not candidates:
        raise OAuthDiscoveryError("jwks_invalid")
    return candidates


def load_oauth_validation_material(issuer: str, fetch: FetchFn) -> OAuthJwtSnapshot:
    """Acquire one immutable startup snapshot from exactly two bounded fetches.

    Fetches RFC 8414 metadata for the canonical ``issuer``, then its declared
    same-origin HTTPS ``jwks_uri``, each exactly once. Transport failures map to
    ``*_unavailable``; content, size, URI, and key-suitability violations map to
    ``*_invalid``. Never called at runtime by the validator.
    """
    if not callable(fetch):
        raise ValueError("invalid oauth discovery fetch")
    metadata_url = derive_oauth_metadata_url(issuer)
    try:
        metadata_body = fetch(metadata_url, MAX_METADATA_BYTES)
    except Exception:
        raise OAuthDiscoveryError("metadata_unavailable") from None
    metadata = _parse_bounded_json_object(
        metadata_body, MAX_METADATA_BYTES, "metadata_invalid"
    )
    if metadata.get("issuer") != issuer:
        raise OAuthDiscoveryError("metadata_invalid")
    jwks_uri = metadata.get("jwks_uri")
    if not _same_origin_https_jwks_uri(jwks_uri, issuer):
        raise OAuthDiscoveryError("metadata_invalid")
    try:
        jwks_body = fetch(jwks_uri, MAX_JWKS_BYTES)  # type: ignore[arg-type]
    except Exception:
        raise OAuthDiscoveryError("jwks_unavailable") from None
    jwks = _parse_bounded_json_object(jwks_body, MAX_JWKS_BYTES, "jwks_invalid")
    keys_value = jwks.get("keys")
    if type(keys_value) is not list:
        raise OAuthDiscoveryError("jwks_invalid")
    parsed_keys = _parse_jwk_set(keys_value)
    try:
        return build_oauth_jwt_snapshot(parsed_keys)
    except ValueError:
        raise OAuthDiscoveryError("jwks_invalid") from None
