import base64
import hashlib
import json
import os
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace

import pytest

import mymcp.authentication.adapters.operator_bearer as operator_bearer
from mymcp.authentication.adapters.operator_bearer import (
    OperatorBearerVerifier,
    OperatorBearerVerifierSourceError,
    load_operator_bearer_verifier_source,
    parse_operator_bearer_credential,
    parse_operator_bearer_verifier_source,
)

_VERIFIER_SOURCE_MAX_BYTES = 16 * 1024
_SECRET = bytes(range(32))
_CREDENTIAL_ID = "a" * 32
_SUBJECT = "stable-subject"
_VALID_CODES = {
    "unsafe",
    "unreadable",
    "excessive",
    "changed",
    "invalid_utf8",
    "invalid_format",
}


def _secret_text(secret: bytes = _SECRET) -> str:
    return (
        base64.urlsafe_b64encode(secret).rstrip(b"=").decode("ascii")
    )


def _digest_text(secret: bytes = _SECRET) -> str:
    return (
        base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
        .rstrip(b"=")
        .decode("ascii")
    )


def _credential_text(
    credential_id: str = _CREDENTIAL_ID,
    secret: bytes = _SECRET,
) -> str:
    return f"mymcp1.{credential_id}.{_secret_text(secret)}"


def _record_dict(
    credential_id: str = _CREDENTIAL_ID,
    subject: str = _SUBJECT,
    digest: str | None = None,
) -> dict[str, object]:
    return {
        "id": credential_id,
        "subject": subject,
        "digest": _digest_text() if digest is None else digest,
    }


def _snapshot_text(
    *records: dict[str, object],
    format_version: object = 1,
) -> str:
    return json.dumps(
        {"format_version": format_version, "credentials": list(records)}
    )


def _snapshot_bytes(
    *records: dict[str, object],
    format_version: object = 1,
) -> bytes:
    return _snapshot_text(*records, format_version=format_version).encode("utf-8")


def _write_source(tmp_path: Path, content: str, mode: int = 0o600) -> Path:
    source = tmp_path / "verifier.json"
    source.write_text(content, encoding="utf-8")
    os.chmod(source, mode)
    return source


def _assert_bounded_error(
    exc: OperatorBearerVerifierSourceError,
    code: str,
    *absent: str,
) -> None:
    assert exc.code == code
    assert exc.args == ()
    assert str(exc) == ""
    for value in absent:
        assert value not in repr(exc)


class _ReparseStat:
    """Wraps a real stat result and reports a reparse-point attribute."""

    def __init__(self, real: os.stat_result) -> None:
        object.__setattr__(self, "_real", real)
        object.__setattr__(self, "st_file_attributes", 0x400)

    def __getattr__(self, name: str) -> object:
        return getattr(self._real, name)


def test_verifier_source_accepts_exact_format_1_snapshot() -> None:
    verifier = parse_operator_bearer_verifier_source(
        _snapshot_bytes(_record_dict())
    )

    assert isinstance(verifier, OperatorBearerVerifier)
    assert len(verifier.records) == 1
    assert verifier.find(_CREDENTIAL_ID) is not None
    assert verifier.find(_CREDENTIAL_ID).subject == _SUBJECT  # type: ignore[union-attr]
    assert (
        verifier.find(_CREDENTIAL_ID).digest  # type: ignore[union-attr]
        == hashlib.sha256(_SECRET).digest()
    )
    assert verifier.verify(parse_operator_bearer_credential(_credential_text())) is True


def test_verifier_source_accepts_empty_credentials() -> None:
    verifier = parse_operator_bearer_verifier_source(_snapshot_bytes())

    assert verifier.records == ()
    assert verifier.find(_CREDENTIAL_ID) is None
    assert (
        verifier.verify(parse_operator_bearer_credential(_credential_text()))
        is False
    )


def test_verifier_source_accepts_up_to_32_records() -> None:
    records = [
        _record_dict(f"{index:032x}", f"subject-{index}") for index in range(32)
    ]

    verifier = parse_operator_bearer_verifier_source(_snapshot_bytes(*records))

    assert len(verifier.records) == 32


def test_verifier_source_rejects_more_than_32_records() -> None:
    records = [
        _record_dict(f"{index:032x}", f"subject-{index}") for index in range(33)
    ]

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        parse_operator_bearer_verifier_source(_snapshot_bytes(*records))

    _assert_bounded_error(excinfo.value, "invalid_format")


def test_verifier_source_rejects_duplicate_top_level_json_keys() -> None:
    text = (
        '{"format_version":1,"format_version":2,"credentials":[{'
        f'"id":"{_CREDENTIAL_ID}","subject":"s","digest":"{_digest_text()}"'
        "}]}"
    )

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        parse_operator_bearer_verifier_source(text.encode("utf-8"))

    _assert_bounded_error(excinfo.value, "invalid_format")


def test_verifier_source_rejects_duplicate_record_json_keys() -> None:
    text = (
        '{"format_version":1,"credentials":[{'
        f'"id":"{_CREDENTIAL_ID}","id":"{_CREDENTIAL_ID}",'
        f'"subject":"s","digest":"{_digest_text()}"'
        "}]}"
    )

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        parse_operator_bearer_verifier_source(text.encode("utf-8"))

    _assert_bounded_error(excinfo.value, "invalid_format")


def test_verifier_source_rejects_invalid_utf8() -> None:
    data = _snapshot_bytes()
    invalid = data[:-1] + b"\xff"

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        parse_operator_bearer_verifier_source(invalid)

    _assert_bounded_error(excinfo.value, "invalid_utf8")


def test_verifier_source_rejects_non_bytes_input() -> None:
    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        parse_operator_bearer_verifier_source("not bytes")  # type: ignore[arg-type]

    _assert_bounded_error(excinfo.value, "invalid_format")


def test_verifier_source_accepts_exactly_16_kib() -> None:
    text = _snapshot_text(_record_dict())
    padded = text + " " * (_VERIFIER_SOURCE_MAX_BYTES - len(text))

    assert len(padded.encode("utf-8")) == _VERIFIER_SOURCE_MAX_BYTES
    verifier = parse_operator_bearer_verifier_source(padded.encode("utf-8"))

    assert verifier.find(_CREDENTIAL_ID) is not None


def test_verifier_source_rejects_over_16_kib() -> None:
    text = _snapshot_text(_record_dict())
    oversized = text + " " * (_VERIFIER_SOURCE_MAX_BYTES + 1 - len(text))

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        parse_operator_bearer_verifier_source(oversized.encode("utf-8"))

    _assert_bounded_error(excinfo.value, "excessive")


@pytest.mark.parametrize(
    "format_version",
    [0, 2, "1", 1.0, True, None, [1]],
)
def test_verifier_source_rejects_wrong_format_version(
    format_version: object,
) -> None:
    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        parse_operator_bearer_verifier_source(
            _snapshot_bytes(format_version=format_version)
        )

    _assert_bounded_error(excinfo.value, "invalid_format")


@pytest.mark.parametrize(
    "text",
    [
        '[{"format_version":1,"credentials":[]}]',
        '{"format_version":1}',
        '{"credentials":[]}',
        '{"format_version":1,"credentials":[],"extra":1}',
        '{"format_version":1,"credentials":{}}',
        '{"format_version":1,"credentials":null}',
    ],
)
def test_verifier_source_rejects_wrong_top_level_shape(text: str) -> None:
    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        parse_operator_bearer_verifier_source(text.encode("utf-8"))

    _assert_bounded_error(excinfo.value, "invalid_format")


@pytest.mark.parametrize(
    "record_text",
    [
        "42",
        '"a-string"',
        '{"id":"%s","subject":"s"}' % _CREDENTIAL_ID,
        '{"id":"%s","subject":"s","digest":"%s","extra":1}'
        % (_CREDENTIAL_ID, _digest_text()),
        '{"id":"%s","digest":"%s"}' % (_CREDENTIAL_ID, _digest_text()),
        '{"subject":"s","digest":"%s"}' % _digest_text(),
    ],
)
def test_verifier_source_rejects_wrong_record_shape(record_text: str) -> None:
    text = '{"format_version":1,"credentials":[' + record_text + "]}"

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        parse_operator_bearer_verifier_source(text.encode("utf-8"))

    _assert_bounded_error(excinfo.value, "invalid_format")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", "A" * 32),
        ("id", "a" * 31),
        ("id", "g" + "a" * 31),
        ("id", 1),
        ("subject", ""),
        ("subject", 1),
        ("subject", "with\x00control"),
        ("digest", 1),
        ("digest", "a" * 42),
        ("digest", "a" * 44),
        ("digest", _digest_text() + "="),
        ("digest", "!" * 43),
    ],
)
def test_verifier_source_rejects_invalid_record_fields(
    field: str,
    value: object,
) -> None:
    record = _record_dict()
    record[field] = value

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        parse_operator_bearer_verifier_source(_snapshot_bytes(record))

    _assert_bounded_error(excinfo.value, "invalid_format")


def test_verifier_source_rejects_noncanonical_digest_encoding() -> None:
    valid = _digest_text()
    last = valid[-1]
    for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_":
        if ord(char) & 0x30 == ord(last) & 0x30 and char != last:
            noncanonical = valid[:-1] + char
            break
    else:
        raise AssertionError("no non-canonical base64url candidate found")

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        parse_operator_bearer_verifier_source(
            _snapshot_bytes(_record_dict(digest=noncanonical))
        )

    _assert_bounded_error(excinfo.value, "invalid_format")


def test_verifier_source_rejects_duplicate_credential_ids() -> None:
    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        parse_operator_bearer_verifier_source(
            _snapshot_bytes(_record_dict(), _record_dict(subject="other"))
        )

    _assert_bounded_error(excinfo.value, "invalid_format")


def test_verifier_source_allows_duplicate_subjects_for_rotation() -> None:
    secret_b = bytes([255]) * 32
    digest_b = (
        base64.urlsafe_b64encode(hashlib.sha256(secret_b).digest())
        .rstrip(b"=")
        .decode("ascii")
    )
    verifier = parse_operator_bearer_verifier_source(
        _snapshot_bytes(
            _record_dict(credential_id="a" * 32, subject="shared"),
            _record_dict(credential_id="b" * 32, subject="shared", digest=digest_b),
        )
    )

    assert verifier.verify(parse_operator_bearer_credential(_credential_text())) is True
    assert (
        verifier.verify(
            parse_operator_bearer_credential(
                _credential_text(credential_id="b" * 32, secret=secret_b)
            )
        )
        is True
    )


def test_verifier_source_returns_immutable_snapshot() -> None:
    verifier = parse_operator_bearer_verifier_source(_snapshot_bytes(_record_dict()))

    with pytest.raises(FrozenInstanceError):
        verifier.records = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        verifier.records[0].digest = b"\x00" * 32  # type: ignore[misc]


@pytest.mark.parametrize(
    "data",
    [
        _snapshot_bytes(_record_dict(), _record_dict(subject="duplicate-id")),
        b"\xff\xfe",
        b"not json",
        _snapshot_bytes(_record_dict(digest="a" * 43)),
        _snapshot_bytes(_record_dict(digest="!" * 43)),
    ],
)
def test_verifier_source_errors_are_bounded_and_content_free(data: bytes) -> None:
    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        parse_operator_bearer_verifier_source(data)

    assert excinfo.value.code in _VALID_CODES
    assert excinfo.value.args == ()
    assert str(excinfo.value) == ""
    assert _digest_text() not in repr(excinfo.value)
    assert _CREDENTIAL_ID not in repr(excinfo.value)
    assert _SUBJECT not in repr(excinfo.value)


def test_loader_loads_valid_source_into_working_verifier(tmp_path: Path) -> None:
    source = _write_source(tmp_path, _snapshot_text(_record_dict()))

    verifier = load_operator_bearer_verifier_source(str(source))

    assert isinstance(verifier, OperatorBearerVerifier)
    assert verifier.verify(parse_operator_bearer_credential(_credential_text())) is True
    assert verifier.find(_CREDENTIAL_ID) is not None
    assert verifier.find(_CREDENTIAL_ID).subject == _SUBJECT  # type: ignore[union-attr]


@pytest.mark.parametrize(
    "path",
    [
        "relative/verifier.json",
        "/tmp/a\x00b.json",
        "/tmp/~verifier.json",
        "/tmp/$verifier.json",
        "/tmp/%verifier.json",
        "/tmp/a/../verifier.json",
        "/tmp/a/./verifier.json",
        "/tmp/a/..",
        123,
        None,
    ],
)
def test_loader_rejects_unsafe_paths(path: object) -> None:
    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        load_operator_bearer_verifier_source(path)  # type: ignore[arg-type]

    _assert_bounded_error(excinfo.value, "unsafe")


def test_loader_rejects_missing_source(tmp_path: Path) -> None:
    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        load_operator_bearer_verifier_source(str(tmp_path / "missing.json"))

    _assert_bounded_error(excinfo.value, "unreadable")


def test_loader_rejects_directory_source(tmp_path: Path) -> None:
    directory = tmp_path / "verifier-dir"
    directory.mkdir()

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        load_operator_bearer_verifier_source(str(directory))

    _assert_bounded_error(excinfo.value, "unsafe")


def test_loader_rejects_symlink_source(tmp_path: Path) -> None:
    real = _write_source(tmp_path, _snapshot_text(_record_dict()))
    link = tmp_path / "verifier-link.json"
    os.symlink(real, link)

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        load_operator_bearer_verifier_source(str(link))

    _assert_bounded_error(excinfo.value, "unsafe")


def test_loader_rejects_symlink_parent(tmp_path: Path) -> None:
    real_dir = tmp_path / "real-dir"
    real_dir.mkdir()
    link_dir = tmp_path / "link-dir"
    os.symlink(real_dir, link_dir)

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        load_operator_bearer_verifier_source(str(link_dir / "verifier.json"))

    _assert_bounded_error(excinfo.value, "unsafe")


def test_loader_rejects_oversized_source(tmp_path: Path) -> None:
    text = _snapshot_text(_record_dict())
    source = _write_source(
        tmp_path,
        text + " " * (_VERIFIER_SOURCE_MAX_BYTES + 1 - len(text)),
    )

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        load_operator_bearer_verifier_source(str(source))

    _assert_bounded_error(excinfo.value, "excessive")


def test_loader_accepts_exactly_16_kib_source(tmp_path: Path) -> None:
    text = _snapshot_text(_record_dict())
    padded = text + " " * (_VERIFIER_SOURCE_MAX_BYTES - len(text))
    source = _write_source(tmp_path, padded)

    verifier = load_operator_bearer_verifier_source(str(source))

    assert verifier.find(_CREDENTIAL_ID) is not None


@pytest.mark.parametrize("mode", [0o777, 0o775, 0o770, 0o707])
def test_loader_rejects_group_or_world_writable_parent(
    tmp_path: Path,
    mode: int,
) -> None:
    source = _write_source(tmp_path, _snapshot_text(_record_dict()))
    os.chmod(tmp_path, mode)

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        load_operator_bearer_verifier_source(str(source))

    _assert_bounded_error(excinfo.value, "unsafe")


@pytest.mark.parametrize("mode", [0o644, 0o604, 0o640, 0o666, 0o601])
def test_loader_rejects_source_with_group_or_world_permission_bits(
    tmp_path: Path,
    mode: int,
) -> None:
    source = _write_source(tmp_path, _snapshot_text(_record_dict()), mode=mode)

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        load_operator_bearer_verifier_source(str(source))

    _assert_bounded_error(excinfo.value, "unsafe")


@pytest.mark.parametrize("mode", [0o600, 0o400])
def test_loader_accepts_source_without_group_or_world_bits(
    tmp_path: Path,
    mode: int,
) -> None:
    source = _write_source(tmp_path, _snapshot_text(_record_dict()), mode=mode)

    verifier = load_operator_bearer_verifier_source(str(source))

    assert verifier.find(_CREDENTIAL_ID) is not None


def test_loader_detects_replacement_during_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_source(tmp_path, _snapshot_text(_record_dict()))
    replacement = tmp_path / "replacement.json"
    replacement.write_text(
        _snapshot_text(
            _record_dict(credential_id="b" * 32, subject="replacement-subject")
        ),
        encoding="utf-8",
    )
    os.chmod(replacement, 0o600)

    original_read = os.read
    swapped = False

    def swapping_read(fd: int, count: int) -> bytes:
        nonlocal swapped
        chunk = original_read(fd, count)
        if not swapped and chunk:
            swapped = True
            replacement.replace(source)
        return chunk

    monkeypatch.setattr(os, "read", swapping_read)

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        load_operator_bearer_verifier_source(str(source))

    _assert_bounded_error(excinfo.value, "changed")


def test_loader_detects_mutation_during_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_source(tmp_path, _snapshot_text(_record_dict()))
    original_read = os.read
    mutated = False

    def mutating_read(fd: int, count: int) -> bytes:
        nonlocal mutated
        chunk = original_read(fd, count)
        if not mutated and chunk:
            mutated = True
            source.write_text(
                _snapshot_text(
                    _record_dict(credential_id="b" * 32, subject="mutated-one"),
                    _record_dict(credential_id="c" * 32, subject="mutated-two"),
                ),
                encoding="utf-8",
            )
            os.chmod(source, 0o600)
        return chunk

    monkeypatch.setattr(os, "read", mutating_read)

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        load_operator_bearer_verifier_source(str(source))

    _assert_bounded_error(excinfo.value, "changed")


def test_loader_snapshot_is_immutable_and_not_reread(tmp_path: Path) -> None:
    source = _write_source(tmp_path, _snapshot_text(_record_dict()))

    verifier = load_operator_bearer_verifier_source(str(source))

    source.write_text(
        _snapshot_text(_record_dict(credential_id="b" * 32, subject="replacement")),
        encoding="utf-8",
    )
    os.chmod(source, 0o600)

    assert verifier.find(_CREDENTIAL_ID) is not None
    assert verifier.find("b" * 32) is None
    with pytest.raises(FrozenInstanceError):
        verifier.records = ()  # type: ignore[misc]


def test_loader_errors_are_bounded_and_content_free(tmp_path: Path) -> None:
    source = _write_source(tmp_path, _snapshot_text(_record_dict()))
    scenarios = [
        (str(tmp_path / "missing.json"), "unreadable"),
        (str(tmp_path / ".." / "verifier.json"), "unsafe"),
        (str(tmp_path), "unsafe"),
    ]

    for path, code in scenarios:
        with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
            load_operator_bearer_verifier_source(path)
        assert excinfo.value.code == code
        assert excinfo.value.args == ()
        assert str(excinfo.value) == ""
        assert path not in repr(excinfo.value)
        assert _digest_text() not in repr(excinfo.value)
        assert _CREDENTIAL_ID not in repr(excinfo.value)
        assert _SUBJECT not in repr(excinfo.value)


def test_operator_bearer_source_error_carries_only_stable_code() -> None:
    exc = operator_bearer.OperatorBearerVerifierSourceError("unsafe")

    assert exc.code == "unsafe"
    assert exc.args == ()
    assert str(exc) == ""
    assert repr(exc) == "OperatorBearerVerifierSourceError()"


def test_loader_uses_descriptor_relative_open_when_supported(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_source(tmp_path, _snapshot_text(_record_dict()))
    original_open = operator_bearer.os.open
    observed: list[tuple[object, dict[str, object]]] = []

    def recording_open(
        target: object,
        flags: int,
        *args: object,
        **kwargs: object,
    ) -> int:
        observed.append((target, kwargs))
        return original_open(target, flags, *args, **kwargs)

    monkeypatch.setattr(operator_bearer.os, "open", recording_open)

    verifier = load_operator_bearer_verifier_source(str(source))

    assert verifier.find(_CREDENTIAL_ID) is not None
    assert observed[0] == (str(tmp_path), {})
    if operator_bearer._OPEN_SUPPORTS_DIR_FD:
        assert observed[1][0] == "verifier.json"
        assert "dir_fd" in observed[1][1]
        assert isinstance(observed[1][1]["dir_fd"], int)


def test_loader_falls_back_to_absolute_path_open_without_dir_fd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_source(tmp_path, _snapshot_text(_record_dict()))
    monkeypatch.setattr(operator_bearer, "_OPEN_SUPPORTS_DIR_FD", False)
    original_open = operator_bearer.os.open
    observed: list[tuple[object, dict[str, object]]] = []

    def recording_open(
        target: object,
        flags: int,
        *args: object,
        **kwargs: object,
    ) -> int:
        observed.append((target, kwargs))
        return original_open(target, flags, *args, **kwargs)

    monkeypatch.setattr(operator_bearer.os, "open", recording_open)

    verifier = load_operator_bearer_verifier_source(str(source))

    assert verifier.find(_CREDENTIAL_ID) is not None
    assert observed == [(str(tmp_path), {}), (str(source), {})]


def test_reparse_point_detection_uses_platform_file_attribute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = 0x400
    monkeypatch.setattr(
        operator_bearer.stat,
        "FILE_ATTRIBUTE_REPARSE_POINT",
        marker,
        raising=False,
    )

    assert operator_bearer._is_reparse_point(
        SimpleNamespace(st_file_attributes=marker)
    )


def test_reparse_point_detection_is_false_without_platform_attribute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = 0x400
    monkeypatch.setattr(
        operator_bearer.stat,
        "FILE_ATTRIBUTE_REPARSE_POINT",
        marker,
        raising=False,
    )

    assert not operator_bearer._is_reparse_point(
        SimpleNamespace(st_file_attributes=0)
    )
    assert not operator_bearer._is_reparse_point(SimpleNamespace())


def test_loader_rejects_reparse_point_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_source(tmp_path, _snapshot_text(_record_dict()))
    original_lstat = operator_bearer.os.lstat

    def reparse_lstat(target: str) -> object:
        real = original_lstat(target)
        if target == str(source):
            return _ReparseStat(real)
        return real

    monkeypatch.setattr(operator_bearer.os, "lstat", reparse_lstat)

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        load_operator_bearer_verifier_source(str(source))

    _assert_bounded_error(excinfo.value, "unsafe")


def test_loader_rejects_reparse_point_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_source(tmp_path, _snapshot_text(_record_dict()))
    original_lstat = operator_bearer.os.lstat

    def reparse_lstat(target: str) -> object:
        real = original_lstat(target)
        if target == str(tmp_path):
            return _ReparseStat(real)
        return real

    monkeypatch.setattr(operator_bearer.os, "lstat", reparse_lstat)

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        load_operator_bearer_verifier_source(str(source))

    _assert_bounded_error(excinfo.value, "unsafe")


def test_loader_detects_same_size_restored_mtime_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_text = _snapshot_text(_record_dict())
    source = _write_source(tmp_path, original_text)
    original_atime_ns = source.stat().st_atime_ns
    original_mtime_ns = source.stat().st_mtime_ns
    original_read = os.read
    mutated = False

    def mutating_read(fd: int, count: int) -> bytes:
        nonlocal mutated
        chunk = original_read(fd, count)
        if not mutated and chunk:
            mutated = True
            replacement = _snapshot_text(
                _record_dict(credential_id="b" * 32, subject="mutated-one")
            )
            source.write_text(
                replacement + " " * (len(original_text) - len(replacement)),
                encoding="utf-8",
            )
            os.chmod(source, 0o600)
            os.utime(source, ns=(original_atime_ns, original_mtime_ns))
        return chunk

    monkeypatch.setattr(os, "read", mutating_read)

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        load_operator_bearer_verifier_source(str(source))

    _assert_bounded_error(excinfo.value, "changed")


def test_loader_detects_permission_change_during_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_source(tmp_path, _snapshot_text(_record_dict()))
    original_read = os.read
    mutated = False

    def mutating_read(fd: int, count: int) -> bytes:
        nonlocal mutated
        chunk = original_read(fd, count)
        if not mutated and chunk:
            mutated = True
            os.chmod(source, 0o666)
        return chunk

    monkeypatch.setattr(os, "read", mutating_read)

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        load_operator_bearer_verifier_source(str(source))

    _assert_bounded_error(excinfo.value, "changed")


def test_loader_detects_parent_replacement_during_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = tmp_path / "parent-dir"
    parent.mkdir()
    os.chmod(parent, 0o700)
    source = _write_source(parent, _snapshot_text(_record_dict()))
    original_read = os.read
    mutated = False

    def mutating_read(fd: int, count: int) -> bytes:
        nonlocal mutated
        chunk = original_read(fd, count)
        if not mutated and chunk:
            mutated = True
            moved = tmp_path / "moved-parent"
            parent.rename(moved)
            parent.mkdir()
        return chunk

    monkeypatch.setattr(os, "read", mutating_read)

    with pytest.raises(OperatorBearerVerifierSourceError) as excinfo:
        load_operator_bearer_verifier_source(str(source))

    _assert_bounded_error(excinfo.value, "changed")
