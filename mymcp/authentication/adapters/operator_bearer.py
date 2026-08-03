import base64
import binascii
import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass, field as dataclass_field
from hmac import compare_digest
from types import MappingProxyType
from typing import ClassVar, Iterable, Mapping

from mymcp.authentication.contracts import (
    AuthenticationAdapter,
    AuthenticationEvidence,
    AuthenticationFailure,
    AuthenticationRequestContext,
    AuthenticationSuccess,
    EvidenceRoute,
    _validate_subject,
)

_CREDENTIAL_ID_PATTERN = re.compile(r"[0-9a-f]{32}\Z")
_CREDENTIAL_PATTERN = re.compile(r"mymcp1\.([0-9a-f]{32})\.([A-Za-z0-9_-]{43})\Z")

# Fixed 32-byte in-memory dummy digest used for the unknown-ID constant-time
# comparison. It is a constant, never a stored credential digest.
DUMMY_DIGEST = bytes.fromhex(
    "6a09e667bb67ae853c6ef372a54ff53a510e527f9b05688c1f83d9ab5be0cd19"
)

_VERIFIER_SOURCE_MAX_BYTES = 16 * 1024
_MAX_VERIFIER_RECORDS = 32

# Established host pattern: descriptor-relative path operations are only used
# when the platform actually supports the dir_fd parameter.
_OPEN_SUPPORTS_DIR_FD = os.open in os.supports_dir_fd

_SOURCE_ERROR_CODES = frozenset(
    {"unsafe", "unreadable", "excessive", "changed", "invalid_utf8", "invalid_format"}
)


class OperatorBearerVerifierSourceError(Exception):
    """Bounded content-free verifier-source failure carrying a stable code."""

    def __init__(self, code: str) -> None:
        if not isinstance(code, str) or code not in _SOURCE_ERROR_CODES:
            raise ValueError("invalid operator bearer verifier source error")
        super().__init__()
        self.code = code


def _decode_secret(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    try:
        decoded = base64.b64decode(padded, altchars=b"-_")
    except (ValueError, binascii.Error):
        raise ValueError("invalid operator bearer credential") from None
    if (
        len(decoded) != 32
        or base64.urlsafe_b64encode(decoded).rstrip(b"=") != value.encode("ascii")
    ):
        raise ValueError("invalid operator bearer credential")
    return decoded


@dataclass(frozen=True, slots=True)
class OperatorBearerCredential:
    credential_id: str
    secret: bytes = dataclass_field(repr=False)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.credential_id, str)
            or _CREDENTIAL_ID_PATTERN.fullmatch(self.credential_id) is None
        ):
            raise ValueError("invalid operator bearer credential")
        if type(self.secret) is not bytes or len(self.secret) != 32:
            raise ValueError("invalid operator bearer credential")


def parse_operator_bearer_credential(value: str) -> OperatorBearerCredential:
    if not isinstance(value, str) or not value.isascii():
        raise ValueError("invalid operator bearer credential")
    match = _CREDENTIAL_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError("invalid operator bearer credential")
    return OperatorBearerCredential(
        match.group(1),
        _decode_secret(match.group(2)),
    )


@dataclass(frozen=True, slots=True)
class OperatorBearerVerifierRecord:
    credential_id: str
    subject: str
    digest: bytes = dataclass_field(repr=False)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.credential_id, str)
            or _CREDENTIAL_ID_PATTERN.fullmatch(self.credential_id) is None
        ):
            raise ValueError("invalid operator bearer verifier record")
        try:
            _validate_subject(self.subject)
        except ValueError:
            raise ValueError("invalid operator bearer verifier record") from None
        if type(self.digest) is not bytes or len(self.digest) != 32:
            raise ValueError("invalid operator bearer verifier record")


@dataclass(frozen=True, slots=True, init=False)
class OperatorBearerVerifier:
    records: tuple[OperatorBearerVerifierRecord, ...]
    _by_id: Mapping[str, OperatorBearerVerifierRecord]

    def verify(self, credential: OperatorBearerCredential) -> bool:
        if not isinstance(credential, OperatorBearerCredential):
            raise ValueError("invalid operator bearer credential")
        digest = hashlib.sha256(credential.secret).digest()
        record = self._by_id.get(credential.credential_id)
        if record is None:
            compare_digest(digest, DUMMY_DIGEST)
            return False
        return compare_digest(digest, record.digest)

    def find(self, credential_id: str) -> OperatorBearerVerifierRecord | None:
        return self._by_id.get(credential_id)


def build_operator_bearer_verifier(
    records: Iterable[OperatorBearerVerifierRecord],
) -> OperatorBearerVerifier:
    selected = tuple(records)
    if any(not isinstance(item, OperatorBearerVerifierRecord) for item in selected):
        raise ValueError("invalid operator bearer verifier")
    by_id: dict[str, OperatorBearerVerifierRecord] = {}
    for record in selected:
        if record.credential_id in by_id:
            raise ValueError("duplicate operator bearer credential id")
        by_id[record.credential_id] = record
    verifier = object.__new__(OperatorBearerVerifier)
    object.__setattr__(verifier, "records", selected)
    object.__setattr__(verifier, "_by_id", MappingProxyType(by_id))
    return verifier


@dataclass(frozen=True, slots=True)
class OperatorBearerAdapter:
    verifier: OperatorBearerVerifier

    route: ClassVar[EvidenceRoute] = EvidenceRoute("authorization", "bearer", None)

    def __post_init__(self) -> None:
        if not isinstance(self.verifier, OperatorBearerVerifier):
            raise ValueError("invalid operator bearer adapter")

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
            text = evidence.payload.decode("ascii")
        except UnicodeDecodeError:
            return AuthenticationFailure("malformed")
        try:
            credential = parse_operator_bearer_credential(text)
        except ValueError:
            return AuthenticationFailure("malformed")
        if not self.verifier.verify(credential):
            return AuthenticationFailure("rejected")
        record = self.verifier.find(credential.credential_id)
        if record is None:
            return AuthenticationFailure("rejected")
        return AuthenticationSuccess(record.subject)


def _object_pairs_reject_duplicates(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise OperatorBearerVerifierSourceError("invalid_format")
        result[key] = value
    return result


def _parse_verifier_source_record(item: object) -> OperatorBearerVerifierRecord:
    if type(item) is not dict:
        raise OperatorBearerVerifierSourceError("invalid_format")
    if set(item) != {"id", "subject", "digest"}:
        raise OperatorBearerVerifierSourceError("invalid_format")
    credential_id = item["id"]
    subject = item["subject"]
    digest_text = item["digest"]
    if (
        not isinstance(credential_id, str)
        or not isinstance(subject, str)
        or not isinstance(digest_text, str)
    ):
        raise OperatorBearerVerifierSourceError("invalid_format")
    try:
        digest = _decode_secret(digest_text)
    except ValueError:
        raise OperatorBearerVerifierSourceError("invalid_format") from None
    try:
        return OperatorBearerVerifierRecord(credential_id, subject, digest)
    except ValueError:
        raise OperatorBearerVerifierSourceError("invalid_format") from None


def parse_operator_bearer_verifier_source(data: bytes) -> OperatorBearerVerifier:
    if type(data) is not bytes:
        raise OperatorBearerVerifierSourceError("invalid_format")
    if len(data) > _VERIFIER_SOURCE_MAX_BYTES:
        raise OperatorBearerVerifierSourceError("excessive")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise OperatorBearerVerifierSourceError("invalid_utf8") from None
    try:
        parsed = json.loads(text, object_pairs_hook=_object_pairs_reject_duplicates)
    except OperatorBearerVerifierSourceError:
        raise
    except json.JSONDecodeError:
        raise OperatorBearerVerifierSourceError("invalid_format") from None
    if type(parsed) is not dict:
        raise OperatorBearerVerifierSourceError("invalid_format")
    if set(parsed) != {"format_version", "credentials"}:
        raise OperatorBearerVerifierSourceError("invalid_format")
    if type(parsed["format_version"]) is not int or parsed["format_version"] != 1:
        raise OperatorBearerVerifierSourceError("invalid_format")
    credentials = parsed["credentials"]
    if type(credentials) is not list:
        raise OperatorBearerVerifierSourceError("invalid_format")
    if len(credentials) > _MAX_VERIFIER_RECORDS:
        raise OperatorBearerVerifierSourceError("invalid_format")
    records = tuple(_parse_verifier_source_record(item) for item in credentials)
    try:
        return build_operator_bearer_verifier(records)
    except ValueError:
        raise OperatorBearerVerifierSourceError("invalid_format") from None


def _is_reparse_point(metadata: os.stat_result) -> bool:
    file_attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(file_attributes & reparse_attribute)


def _same_file(expected: os.stat_result, observed: os.stat_result) -> bool:
    return expected.st_dev == observed.st_dev and expected.st_ino == observed.st_ino


def _same_source_state(expected: os.stat_result, observed: os.stat_result) -> bool:
    return (
        _same_file(expected, observed)
        and expected.st_size == observed.st_size
        and expected.st_mtime_ns == observed.st_mtime_ns
        and expected.st_ctime_ns == observed.st_ctime_ns
        and expected.st_mode == observed.st_mode
    )


def _safe_source_path(path: object) -> str:
    if not isinstance(path, str):
        raise OperatorBearerVerifierSourceError("unsafe")
    if (
        "\x00" in path
        or "~" in path
        or "$" in path
        or "%" in path
        or not os.path.isabs(path)
        or any(part in {".", ".."} for part in path.split("/"))
    ):
        raise OperatorBearerVerifierSourceError("unsafe")
    return path


def load_operator_bearer_verifier_source(path: object) -> OperatorBearerVerifier:
    source_path = _safe_source_path(path)
    parent_path = os.path.dirname(source_path)
    try:
        parent_stat = os.lstat(parent_path)
    except OSError:
        raise OperatorBearerVerifierSourceError("unreadable") from None
    if (
        stat.S_ISLNK(parent_stat.st_mode)
        or _is_reparse_point(parent_stat)
        or not stat.S_ISDIR(parent_stat.st_mode)
    ):
        raise OperatorBearerVerifierSourceError("unsafe")
    if os.name == "posix" and stat.S_IMODE(parent_stat.st_mode) & 0o022:
        raise OperatorBearerVerifierSourceError("unsafe")
    try:
        source_stat = os.lstat(source_path)
    except OSError:
        raise OperatorBearerVerifierSourceError("unreadable") from None
    if (
        stat.S_ISLNK(source_stat.st_mode)
        or _is_reparse_point(source_stat)
        or not stat.S_ISREG(source_stat.st_mode)
    ):
        raise OperatorBearerVerifierSourceError("unsafe")
    if os.name == "posix" and stat.S_IMODE(source_stat.st_mode) & 0o077:
        raise OperatorBearerVerifierSourceError("unsafe")
    if source_stat.st_size > _VERIFIER_SOURCE_MAX_BYTES:
        raise OperatorBearerVerifierSourceError("excessive")

    parent_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(
        os, "O_NOFOLLOW", 0
    )
    source_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    parent_fd = -1
    source_fd = -1
    try:
        try:
            parent_fd = os.open(parent_path, parent_flags)
        except OSError:
            raise OperatorBearerVerifierSourceError("unreadable") from None
        try:
            opened_parent_stat = os.fstat(parent_fd)
        except OSError:
            raise OperatorBearerVerifierSourceError("unreadable") from None
        if _is_reparse_point(opened_parent_stat) or not stat.S_ISDIR(
            opened_parent_stat.st_mode
        ):
            raise OperatorBearerVerifierSourceError("unsafe")
        if not _same_file(parent_stat, opened_parent_stat):
            raise OperatorBearerVerifierSourceError("changed")
        if os.name == "posix" and stat.S_IMODE(opened_parent_stat.st_mode) & 0o022:
            raise OperatorBearerVerifierSourceError("unsafe")
        try:
            if _OPEN_SUPPORTS_DIR_FD:
                source_fd = os.open(
                    os.path.basename(source_path),
                    source_flags,
                    dir_fd=parent_fd,
                )
            else:
                source_fd = os.open(source_path, source_flags)
        except OSError:
            raise OperatorBearerVerifierSourceError("unreadable") from None
        try:
            opened_source_stat = os.fstat(source_fd)
        except OSError:
            raise OperatorBearerVerifierSourceError("unreadable") from None
        if _is_reparse_point(opened_source_stat):
            raise OperatorBearerVerifierSourceError("unsafe")
        if not stat.S_ISREG(opened_source_stat.st_mode):
            raise OperatorBearerVerifierSourceError("unsafe")
        if not _same_file(source_stat, opened_source_stat):
            raise OperatorBearerVerifierSourceError("changed")
        if os.name == "posix" and stat.S_IMODE(opened_source_stat.st_mode) & 0o077:
            raise OperatorBearerVerifierSourceError("unsafe")
        if opened_source_stat.st_size > _VERIFIER_SOURCE_MAX_BYTES:
            raise OperatorBearerVerifierSourceError("excessive")

        chunks: list[bytes] = []
        total = 0
        while total <= _VERIFIER_SOURCE_MAX_BYTES:
            try:
                chunk = os.read(source_fd, _VERIFIER_SOURCE_MAX_BYTES + 1 - total)
            except OSError:
                raise OperatorBearerVerifierSourceError("unreadable") from None
            if not chunk:
                break
            total += len(chunk)
            chunks.append(chunk)
        data = b"".join(chunks)
        if len(data) > _VERIFIER_SOURCE_MAX_BYTES:
            raise OperatorBearerVerifierSourceError("excessive")

        # Re-validate the source entry at its path after the read.
        try:
            if _OPEN_SUPPORTS_DIR_FD:
                current_source_stat = os.stat(
                    os.path.basename(source_path),
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            else:
                current_source_stat = os.lstat(source_path)
        except OSError:
            raise OperatorBearerVerifierSourceError("changed") from None
        if not _same_source_state(opened_source_stat, current_source_stat):
            raise OperatorBearerVerifierSourceError("changed")
        if _is_reparse_point(current_source_stat):
            raise OperatorBearerVerifierSourceError("unsafe")
        if not stat.S_ISREG(current_source_stat.st_mode):
            raise OperatorBearerVerifierSourceError("unsafe")
        if os.name == "posix" and stat.S_IMODE(current_source_stat.st_mode) & 0o077:
            raise OperatorBearerVerifierSourceError("unsafe")

        # Re-validate the parent directory at its path after the read.
        try:
            current_parent_stat = os.lstat(parent_path)
        except OSError:
            raise OperatorBearerVerifierSourceError("changed") from None
        if not _same_source_state(parent_stat, current_parent_stat):
            raise OperatorBearerVerifierSourceError("changed")
        if _is_reparse_point(current_parent_stat):
            raise OperatorBearerVerifierSourceError("unsafe")
        if not stat.S_ISDIR(current_parent_stat.st_mode):
            raise OperatorBearerVerifierSourceError("unsafe")
        if os.name == "posix" and stat.S_IMODE(current_parent_stat.st_mode) & 0o022:
            raise OperatorBearerVerifierSourceError("unsafe")
    finally:
        if source_fd != -1:
            try:
                os.close(source_fd)
            except OSError:
                pass
        if parent_fd != -1:
            try:
                os.close(parent_fd)
            except OSError:
                pass
    return parse_operator_bearer_verifier_source(data)
