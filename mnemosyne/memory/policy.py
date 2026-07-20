import re
from collections.abc import Iterable

from mnemosyne.memory.errors import ContentRefusalReason, DisallowedMemoryContent
from mnemosyne.memory.records import MemoryDraft, MemoryRevision


SIGNATURE_PATTERNS = (
    (
        ContentRefusalReason.PRIVATE_KEY_SHAPE,
        re.compile(
            r"-----BEGIN (?:(?:RSA|EC|DSA|OPENSSH) )?PRIVATE KEY-----"
            r"|-----BEGIN PGP PRIVATE KEY BLOCK-----"
        ),
    ),
    (
        ContentRefusalReason.CREDENTIAL_SHAPE,
        re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])"),
    ),
    (
        ContentRefusalReason.CREDENTIAL_SHAPE,
        re.compile(
            r"(?<![A-Za-z0-9_])(?:gh[pousr]_[A-Za-z0-9]{20,}"
            r"|github_pat_[A-Za-z0-9_]{20,})(?![A-Za-z0-9_])"
        ),
    ),
    (
        ContentRefusalReason.CREDENTIAL_SHAPE,
        re.compile(r"(?<![A-Za-z0-9-])xox[baprs]-[A-Za-z0-9-]{10,}"),
    ),
    (
        ContentRefusalReason.CREDENTIAL_SHAPE,
        re.compile(r"(?<![A-Za-z0-9_])(?:sk|rk)_live_[A-Za-z0-9]{16,}"),
    ),
    (
        ContentRefusalReason.CREDENTIAL_SHAPE,
        re.compile(
            r"(?<![A-Za-z0-9_-])AIza[A-Za-z0-9_-]{35}(?![A-Za-z0-9_-])"
        ),
    ),
    (
        ContentRefusalReason.CREDENTIAL_SHAPE,
        re.compile(r"(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{20,}"),
    ),
    (
        ContentRefusalReason.CREDENTIAL_SHAPE,
        re.compile(
            r"\bauthorization\s*:\s*(?:basic|bearer)\s+\S+", re.IGNORECASE
        ),
    ),
    (
        ContentRefusalReason.CREDENTIAL_SHAPE,
        re.compile(
            r"\b(?:password|passwd|pwd|secret|api[_-]?key|apikey|"
            r"access[_-]?token|refresh[_-]?token|client[_-]?secret)"
            r"\s*[:=]\s*\S{4,}",
            re.IGNORECASE,
        ),
    ),
    (
        ContentRefusalReason.CREDENTIAL_SHAPE,
        re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@"),
    ),
    (
        ContentRefusalReason.COMPACT_TOKEN_SHAPE,
        re.compile(
            r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\."
            r"[A-Za-z0-9_-]+(?![A-Za-z0-9_-])"
        ),
    ),
    (
        ContentRefusalReason.GOVERNMENT_IDENTIFIER_SHAPE,
        re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)"),
    ),
)
CARD_CANDIDATE_PATTERN = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")


def _remember_text_values(draft: MemoryDraft) -> Iterable[tuple[str, str]]:
    yield "namespace.id", draft.namespace.id
    if draft.namespace.label is not None:
        yield "namespace.label", draft.namespace.label
    if draft.collection is not None:
        yield "collection.id", draft.collection.id
        if draft.collection.label is not None:
            yield "collection.label", draft.collection.label
    if draft.title is not None:
        yield "title", draft.title
    yield "content", draft.content
    yield from (("tags", tag) for tag in draft.tags)


def _revision_text_values(revision: MemoryRevision) -> Iterable[tuple[str, str]]:
    if revision.namespace_label is not None:
        yield "namespace.label", revision.namespace_label
    if revision.collection_label is not None:
        yield "collection.label", revision.collection_label
    if revision.title is not None:
        yield "title", revision.title
    yield "content", revision.content
    yield from (("tags", tag) for tag in revision.tags)


def _passes_luhn(value: str) -> bool:
    total = 0
    for index, character in enumerate(reversed(value)):
        digit = int(character)
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def _contains_payment_card(value: str) -> bool:
    for match in CARD_CANDIDATE_PATTERN.finditer(value):
        digits = re.sub(r"[ -]", "", match.group())
        if 13 <= len(digits) <= 19 and _passes_luhn(digits):
            return True
    return False


def _validate_text_values(values: Iterable[tuple[str, str]]) -> None:
    for field, value in values:
        for reason, pattern in SIGNATURE_PATTERNS:
            if pattern.search(value) is not None:
                raise DisallowedMemoryContent(field, reason)
        if _contains_payment_card(value):
            raise DisallowedMemoryContent(
                field,
                ContentRefusalReason.PAYMENT_CARD_SHAPE,
            )


def validate_remember_content(draft: MemoryDraft) -> None:
    _validate_text_values(_remember_text_values(draft))


def validate_revision_content(revision: MemoryRevision) -> None:
    _validate_text_values(_revision_text_values(revision))
