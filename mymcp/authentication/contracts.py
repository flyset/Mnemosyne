import base64
import re
import unicodedata
from dataclasses import dataclass, field as dataclass_field
from enum import StrEnum
from typing import Protocol, runtime_checkable


_MAX_ADAPTER_ID_LENGTH = 64
_MAX_SUBJECT_CODE_POINTS = 256
_MAX_SUBJECT_BYTES = 1024
_MAX_ROUTE_PART_LENGTH = 64
_MAX_EVIDENCE_BYTES = 8192
_ADAPTER_ID_PATTERN = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
_ROUTE_PART_PATTERN = re.compile(r"[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*\Z")
_FAILURE_CODES = frozenset({"ambiguous", "malformed", "no_evidence", "rejected", "unsupported"})


@dataclass(frozen=True, slots=True)
class AdapterId:
    value: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.value, str)
            or len(self.value) > _MAX_ADAPTER_ID_LENGTH
            or _ADAPTER_ID_PATTERN.fullmatch(self.value) is None
        ):
            raise ValueError("invalid adapter id")


class PrincipalKind(StrEnum):
    ANONYMOUS = "anonymous"
    REGISTERED = "registered"


def _validate_subject(subject: object) -> str:
    if not isinstance(subject, str):
        raise ValueError("invalid principal subject")
    try:
        encoded = subject.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError("invalid principal subject") from None
    if (
        not subject.strip()
        or len(subject) > _MAX_SUBJECT_CODE_POINTS
        or len(encoded) > _MAX_SUBJECT_BYTES
        or unicodedata.normalize("NFC", subject) != subject
        or any(unicodedata.category(character).startswith("C") for character in subject)
    ):
        raise ValueError("invalid principal subject")
    return subject


@dataclass(frozen=True, slots=True, init=False)
class Principal:
    kind: PrincipalKind
    adapter_id: AdapterId | None
    subject: str | None
    principal_id: str

    @classmethod
    def anonymous(cls) -> "Principal":
        principal = object.__new__(cls)
        object.__setattr__(principal, "kind", PrincipalKind.ANONYMOUS)
        object.__setattr__(principal, "adapter_id", None)
        object.__setattr__(principal, "subject", None)
        object.__setattr__(principal, "principal_id", "anonymous")
        return principal

    @classmethod
    def registered(cls, adapter_id: AdapterId, subject: str) -> "Principal":
        if not isinstance(adapter_id, AdapterId):
            raise ValueError("invalid adapter id")
        validated_subject = _validate_subject(subject)
        token = base64.urlsafe_b64encode(validated_subject.encode("utf-8")).rstrip(b"=").decode("ascii")
        principal = object.__new__(cls)
        object.__setattr__(principal, "kind", PrincipalKind.REGISTERED)
        object.__setattr__(principal, "adapter_id", adapter_id)
        object.__setattr__(principal, "subject", validated_subject)
        object.__setattr__(
            principal,
            "principal_id",
            f"registered:{adapter_id.value}:{token}",
        )
        return principal


def _valid_route_part(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) <= _MAX_ROUTE_PART_LENGTH
        and _ROUTE_PART_PATTERN.fullmatch(value) is not None
    )


@dataclass(frozen=True, slots=True)
class EvidenceRoute:
    source: str
    scheme: str
    profile: str | None

    def __post_init__(self) -> None:
        if (
            self.source != "authorization"
            or not _valid_route_part(self.scheme)
            or (self.profile is not None and not _valid_route_part(self.profile))
        ):
            raise ValueError("invalid evidence route")


@dataclass(frozen=True, slots=True)
class AuthenticationEvidence:
    route: EvidenceRoute
    payload: bytes = dataclass_field(repr=False)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.route, EvidenceRoute)
            or type(self.payload) is not bytes
            or not 1 <= len(self.payload) <= _MAX_EVIDENCE_BYTES
        ):
            raise ValueError("invalid authentication evidence")


@dataclass(frozen=True, slots=True)
class AuthenticationRequestContext:
    http_method: str
    endpoint: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.http_method, str)
            or self.http_method not in {"GET", "POST"}
            or self.endpoint != "mcp"
        ):
            raise ValueError("invalid authentication request context")


@dataclass(frozen=True, slots=True)
class AuthenticationSuccess:
    subject: str

    def __post_init__(self) -> None:
        _validate_subject(self.subject)


@dataclass(frozen=True, slots=True)
class AuthenticationFailure:
    code: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or self.code not in _FAILURE_CODES:
            raise ValueError("invalid authentication failure")


@runtime_checkable
class AuthenticationAdapter(Protocol):
    def authenticate(
        self,
        evidence: AuthenticationEvidence,
        context: AuthenticationRequestContext,
    ) -> AuthenticationSuccess | AuthenticationFailure: ...
