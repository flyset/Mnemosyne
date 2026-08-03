"""Narrow offline RS256 ``at+jwt`` validation foundation (``oauth-jwt-jwks-v1``).

This module is the concrete OAuth adapter package and the only place in
``mymcp.authentication`` permitted to import the declared ``PyJWT[crypto]``
runtime dependency. MyMCP owns strict compact-token parsing, header and claim
validation, key selection, time and lifetime bounds, the opaque adapter-local
subject projection, and redaction. PyJWT supplies only the RS256
signature-verification primitive against one pre-selected, pre-validated RSA
public key from an immutable snapshot.

The foundation is dormant: no host-owned module imports or registers it, and it
must never be re-exported from ``mymcp.authentication``.
"""

import base64
import binascii
import hashlib
import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field as dataclass_field
from types import MappingProxyType
from typing import ClassVar, Mapping

import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPublicKey,
    RSAPublicNumbers,
)

from mymcp.authentication.contracts import (
    AuthenticationAdapter,
    AuthenticationEvidence,
    AuthenticationFailure,
    AuthenticationRequestContext,
    AuthenticationSuccess,
    EvidenceRoute,
    _validate_subject,
)
from mymcp.authentication.oauth import (
    OAUTH_JWT_PROFILE,
    validate_oauth_issuer,
)
SUBJECT_PREFIX = "oauth-jwt-v1:"
CLOCK_SKEW_SECONDS = 30
MAX_LIFETIME_SECONDS = 300
MAX_JWK_COUNT = 16
MIN_RSA_KEY_BITS = 2048
MAX_KID_LENGTH = 128
MAX_CLAIM_TEXT_LENGTH = 256
MAX_SEGMENT_CHARACTERS = 4096
MAX_JSON_DEPTH = 64

_RS256 = jwt.algorithms.get_default_algorithms()["RS256"]

_ALGORITHM = "RS256"
_TOKEN_TYPE = "at+jwt"
_HEADER_MEMBERS = frozenset({"alg", "typ", "kid"})
_REQUIRED_CLAIMS = frozenset({"iss", "aud", "sub", "exp", "iat", "client_id", "jti"})


class _OAuthJwtError(Exception):
    """Bounded content-free validation failure carrying only a stable code."""

    def __init__(self, code: str) -> None:
        if code not in {"malformed", "rejected"}:
            raise ValueError("invalid oauth jwt failure")
        super().__init__()
        self.code = code


def parse_compact_token(token_text: object) -> tuple[str, str, str]:
    """Split a compact JWS into header, payload, and signature segments."""
    if not isinstance(token_text, str) or not token_text.isascii():
        raise ValueError("invalid oauth jwt token")
    segments = token_text.split(".")
    if len(segments) != 3:
        raise ValueError("invalid oauth jwt token")
    header_segment, payload_segment, signature_segment = segments
    if not header_segment or not payload_segment or not signature_segment:
        raise ValueError("invalid oauth jwt token")
    if (
        len(header_segment) > MAX_SEGMENT_CHARACTERS
        or len(payload_segment) > MAX_SEGMENT_CHARACTERS
        or len(signature_segment) > MAX_SEGMENT_CHARACTERS
    ):
        raise ValueError("invalid oauth jwt token")
    return header_segment, payload_segment, signature_segment


def project_subject(issuer: str, subject: str) -> str:
    """Project exact UTF-8 issuer, one zero byte, and ``sub`` into the opaque
    ``oauth-jwt-v1:`` adapter-local subject."""
    digest = hashlib.sha256(
        issuer.encode("utf-8") + b"\x00" + subject.encode("utf-8")
    ).digest()
    return SUBJECT_PREFIX + base64.urlsafe_b64encode(digest).rstrip(b"=").decode(
        "ascii"
    )


def _valid_kid(value: object) -> bool:
    return (
        isinstance(value, str)
        and value.strip() != ""
        and value.isascii()
        and len(value) <= MAX_KID_LENGTH
        and all(ord(character) >= 0x20 and ord(character) != 0x7F for character in value)
    )


def _valid_bounded_ascii_text(value: object) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= MAX_CLAIM_TEXT_LENGTH
        and value.strip() != ""
        and value.isascii()
        and all(ord(character) >= 0x20 and ord(character) != 0x7F for character in value)
    )


@dataclass(frozen=True, slots=True)
class RsaPublicKey:
    """One immutable RSA public signing JWK selected by a bounded ``kid``."""

    kid: str
    modulus: int = dataclass_field(repr=False)
    exponent: int = dataclass_field(repr=False)
    _crypto_key: RSAPublicKey = dataclass_field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not _valid_kid(self.kid):
            raise ValueError("invalid oauth jwt key")
        if type(self.modulus) is not int or type(self.exponent) is not int:
            raise ValueError("invalid oauth jwt key")
        if self.exponent < 3 or self.exponent % 2 == 0:
            raise ValueError("invalid oauth jwt key")
        if self.modulus < 1 or self.modulus.bit_length() < MIN_RSA_KEY_BITS:
            raise ValueError("invalid oauth jwt key")
        try:
            crypto_key = RSAPublicNumbers(self.exponent, self.modulus).public_key()
        except ValueError:
            raise ValueError("invalid oauth jwt key") from None
        object.__setattr__(self, "_crypto_key", crypto_key)


@dataclass(frozen=True, slots=True, init=False)
class OAuthJwtSnapshot:
    """Immutable startup snapshot of RSA signing keys addressed by unique ``kid``."""

    keys: tuple[RsaPublicKey, ...]
    _by_kid: Mapping[str, RsaPublicKey]

    def find(self, kid: str) -> RsaPublicKey | None:
        return self._by_kid.get(kid)


def build_oauth_jwt_snapshot(keys: Iterable[RsaPublicKey]) -> OAuthJwtSnapshot:
    selected = tuple(keys)
    if any(not isinstance(item, RsaPublicKey) for item in selected):
        raise ValueError("invalid oauth jwt snapshot")
    if len(selected) > MAX_JWK_COUNT:
        raise ValueError("invalid oauth jwt snapshot")
    by_kid: dict[str, RsaPublicKey] = {}
    for key in selected:
        if key.kid in by_kid:
            raise ValueError("invalid oauth jwt snapshot")
        by_kid[key.kid] = key
    snapshot = object.__new__(OAuthJwtSnapshot)
    object.__setattr__(snapshot, "keys", selected)
    object.__setattr__(snapshot, "_by_kid", MappingProxyType(by_kid))
    return snapshot


@dataclass(frozen=True, slots=True)
class OAuthJwtConfig:
    """One validated, bounded validation profile for one external issuer."""

    issuer: str = dataclass_field(repr=False)
    audience: str = dataclass_field(repr=False)
    snapshot: OAuthJwtSnapshot = dataclass_field(repr=False)
    clock: Callable[[], int] = dataclass_field(repr=False)

    def __post_init__(self) -> None:
        validate_oauth_issuer(self.issuer)
        if not _valid_bounded_ascii_text(self.audience):
            raise ValueError("invalid oauth jwt configuration")
        if not isinstance(self.snapshot, OAuthJwtSnapshot):
            raise ValueError("invalid oauth jwt configuration")
        if not callable(self.clock):
            raise ValueError("invalid oauth jwt configuration")


def _decode_segment(segment: str) -> bytes:
    if not segment.isascii():
        raise _OAuthJwtError("malformed")
    padded = segment + "=" * (-len(segment) % 4)
    try:
        decoded = base64.b64decode(padded, altchars=b"-_")
    except (ValueError, binascii.Error):
        raise _OAuthJwtError("malformed") from None
    if base64.urlsafe_b64encode(decoded).rstrip(b"=") != segment.encode("ascii"):
        raise _OAuthJwtError("malformed")
    return decoded


def _reject_duplicate_pairs(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _OAuthJwtError("malformed")
        result[key] = value
    return result


def _parse_json_object(data: bytes) -> dict[str, object]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise _OAuthJwtError("malformed") from None
    try:
        parsed = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
    except _OAuthJwtError:
        raise
    except (json.JSONDecodeError, RecursionError):
        raise _OAuthJwtError("malformed") from None
    if type(parsed) is not dict:
        raise _OAuthJwtError("malformed")
    _reject_deeper_than(MAX_JSON_DEPTH, parsed)
    return parsed


def _reject_deeper_than(limit: int, root: object) -> None:
    """Reject unboundedly nested JSON with an explicit, recursion-free walk."""
    stack: list[tuple[object, int]] = [(root, 0)]
    while stack:
        value, depth = stack.pop()
        if depth > limit:
            raise _OAuthJwtError("malformed")
        if isinstance(value, dict):
            stack.extend((item, depth + 1) for item in value.values())
        elif isinstance(value, list):
            stack.extend((item, depth + 1) for item in value)


def _validate_header(header: Mapping[str, object]) -> str:
    if set(header) != _HEADER_MEMBERS:
        raise _OAuthJwtError("malformed")
    if header["alg"] != _ALGORITHM or header["typ"] != _TOKEN_TYPE:
        raise _OAuthJwtError("malformed")
    kid = header["kid"]
    if not _valid_kid(kid):
        raise _OAuthJwtError("malformed")
    return kid  # type: ignore[return-value]


def _numeric_date(value: object) -> int:
    if type(value) is not int or value < 0:
        raise _OAuthJwtError("malformed")
    return value


def _audience_matches(audience: object, expected: str) -> bool:
    if isinstance(audience, str):
        return audience == expected
    if isinstance(audience, list):
        if not audience or not all(isinstance(item, str) for item in audience):
            raise _OAuthJwtError("malformed")
        return expected in audience
    raise _OAuthJwtError("malformed")


def _validate_claims(
    payload: Mapping[str, object],
    issuer: str,
    audience: str,
    now: int,
) -> str:
    if not _REQUIRED_CLAIMS.issubset(payload.keys()):
        raise _OAuthJwtError("malformed")
    if payload["iss"] != issuer:
        raise _OAuthJwtError("rejected")
    if not _audience_matches(payload["aud"], audience):
        raise _OAuthJwtError("rejected")
    exp = _numeric_date(payload["exp"])
    iat = _numeric_date(payload["iat"])
    if now - exp > CLOCK_SKEW_SECONDS:
        raise _OAuthJwtError("rejected")
    if iat - now > CLOCK_SKEW_SECONDS:
        raise _OAuthJwtError("rejected")
    lifetime = exp - iat
    if lifetime <= 0 or lifetime > MAX_LIFETIME_SECONDS:
        raise _OAuthJwtError("rejected")
    if "nbf" in payload:
        nbf = _numeric_date(payload["nbf"])
        if nbf - now > CLOCK_SKEW_SECONDS:
            raise _OAuthJwtError("rejected")
    sub = payload["sub"]
    if not isinstance(sub, str):
        raise _OAuthJwtError("malformed")
    try:
        validated_sub = _validate_subject(sub)
    except ValueError:
        raise _OAuthJwtError("malformed") from None
    if not _valid_bounded_ascii_text(payload["client_id"]):
        raise _OAuthJwtError("malformed")
    if not _valid_bounded_ascii_text(payload["jti"]):
        raise _OAuthJwtError("malformed")
    return validated_sub


def _verify_rs256(message: bytes, signature: bytes, key: RsaPublicKey) -> bool:
    try:
        return _RS256.verify(message, key._crypto_key, signature) is True
    except Exception:
        return False


def validate_access_token(token_text: str, config: OAuthJwtConfig) -> str:
    """Validate one compact RS256 ``at+jwt`` token and return its opaque subject."""
    try:
        header_segment, payload_segment, signature_segment = parse_compact_token(token_text)
    except ValueError:
        raise _OAuthJwtError("malformed") from None
    signature = _decode_segment(signature_segment)
    header = _parse_json_object(_decode_segment(header_segment))
    kid = _validate_header(header)
    key = config.snapshot.find(kid)
    if key is None:
        raise _OAuthJwtError("rejected")
    now = config.clock()
    if type(now) is not int:
        raise ValueError("invalid oauth jwt clock")
    message = header_segment.encode("ascii") + b"." + payload_segment.encode("ascii")
    if not _verify_rs256(message, signature, key):
        raise _OAuthJwtError("rejected")
    payload = _parse_json_object(_decode_segment(payload_segment))
    subject = _validate_claims(payload, config.issuer, config.audience, now)
    return project_subject(config.issuer, subject)


@dataclass(frozen=True, slots=True)
class OAuthJwtAdapter:
    """Dormant ``oauth-jwt-jwks-v1`` adapter over one immutable profile."""

    config: OAuthJwtConfig

    # The HTTP boundary cannot distinguish token shapes, so the OAuth adapter
    # claims the same exact Authorization/Bearer route as ``operator-bearer-v1``.
    # Configuration exclusion prevents both Bearer methods from ever being
    # composed together, so the shared exact route never collides at runtime.
    route: ClassVar[EvidenceRoute] = EvidenceRoute("authorization", "bearer", None)

    def __post_init__(self) -> None:
        if not isinstance(self.config, OAuthJwtConfig):
            raise ValueError("invalid oauth jwt adapter")

    def authenticate(
        self,
        evidence: AuthenticationEvidence,
        context: AuthenticationRequestContext,
    ) -> AuthenticationSuccess | AuthenticationFailure:
        if not isinstance(evidence, AuthenticationEvidence):
            raise ValueError("invalid authentication request")
        if evidence.route != self.route:
            return AuthenticationFailure("unsupported")
        try:
            token = evidence.payload.decode("ascii")
        except UnicodeDecodeError:
            return AuthenticationFailure("malformed")
        try:
            subject = validate_access_token(token, self.config)
        except _OAuthJwtError as exc:
            return AuthenticationFailure(exc.code)
        return AuthenticationSuccess(subject)
