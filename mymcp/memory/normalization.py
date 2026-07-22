import re
import unicodedata

from mymcp.memory.errors import MemoryValidationError


IDENTIFIER_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?")
LANGUAGE_PATTERN = re.compile(r"[a-z]{2,8}(?:-[a-z0-9]{1,8})*")
MEMORY_ID_PATTERN = re.compile(r"mem_[0-9a-f]{32}")


def _normalize_unicode(value: str) -> str:
    with_lf_endings = value.replace("\r\n", "\n").replace("\r", "\n")
    return unicodedata.normalize("NFC", with_lf_endings)


def normalize_required_text(
    value: object,
    *,
    field: str,
    maximum_length: int,
) -> str:
    if not isinstance(value, str):
        raise MemoryValidationError("invalid_record", field, f"invalid {field}")
    normalized = _normalize_unicode(value).strip()
    if not normalized or len(normalized) > maximum_length:
        raise MemoryValidationError("invalid_record", field, f"invalid {field}")
    return normalized


def normalize_optional_text(
    value: object,
    *,
    field: str,
    maximum_length: int,
) -> str | None:
    if value is None:
        return None
    return normalize_required_text(
        value,
        field=field,
        maximum_length=maximum_length,
    )


def normalize_identifier(value: object, *, field: str) -> str:
    code = "invalid_namespace" if field.startswith("namespace") else "invalid_collection"
    if not isinstance(value, str) or IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise MemoryValidationError(code, field, f"invalid {field}")
    return value


def normalize_memory_id(value: object, *, legacy: bool = False) -> str:
    if legacy:
        is_valid = (
            isinstance(value, str)
            and 1 <= len(value) <= 100
            and re.fullmatch(r"[A-Za-z0-9._-]+", value) is not None
        )
    else:
        is_valid = (
            isinstance(value, str)
            and MEMORY_ID_PATTERN.fullmatch(value) is not None
        )
    if not is_valid:
        raise MemoryValidationError("invalid_record", "id", "invalid id")
    return value


def normalize_language(value: object) -> str:
    if value is None:
        return "und"
    if not isinstance(value, str):
        raise MemoryValidationError(
            "invalid_record",
            "language",
            "invalid language",
        )
    normalized = value.strip().lower()
    if len(normalized) > 35 or LANGUAGE_PATTERN.fullmatch(normalized) is None:
        raise MemoryValidationError(
            "invalid_record",
            "language",
            "invalid language",
        )
    return normalized


def normalize_tags(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > 10:
        raise MemoryValidationError("invalid_record", "tags", "invalid tags")

    tags: list[str] = []
    normalized_keys: set[str] = set()
    for raw_tag in value:
        if not isinstance(raw_tag, str):
            raise MemoryValidationError("invalid_record", "tags", "invalid tags")
        tag = " ".join(_normalize_unicode(raw_tag).split())
        if not tag or len(tag) > 50:
            raise MemoryValidationError("invalid_record", "tags", "invalid tags")
        key = tag.casefold()
        if key in normalized_keys:
            raise MemoryValidationError("invalid_record", "tags", "invalid tags")
        normalized_keys.add(key)
        tags.append(tag)
    return tuple(tags)


def normalized_tag_key(tags: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(tag.casefold() for tag in tags))
