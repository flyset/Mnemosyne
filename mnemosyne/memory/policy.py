import re
from collections.abc import Iterable

from mnemosyne.memory.errors import DisallowedMemoryContent
from mnemosyne.memory.records import MemoryDraft


SIGNATURE_PATTERNS = (
    re.compile(
        r"-----BEGIN (?:(?:RSA|EC|DSA|OPENSSH) )?PRIVATE KEY-----"
        r"|-----BEGIN PGP PRIVATE KEY BLOCK-----"
    ),
    re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])"),
    re.compile(
        r"(?<![A-Za-z0-9_])(?:gh[pousr]_[A-Za-z0-9]{20,}"
        r"|github_pat_[A-Za-z0-9_]{20,})(?![A-Za-z0-9_])"
    ),
    re.compile(r"(?<![A-Za-z0-9-])xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"(?<![A-Za-z0-9_])(?:sk|rk)_live_[A-Za-z0-9]{16,}"),
    re.compile(r"(?<![A-Za-z0-9_-])AIza[A-Za-z0-9_-]{35}(?![A-Za-z0-9_-])"),
    re.compile(r"(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"\bauthorization\s*:\s*(?:basic|bearer)\s+\S+", re.IGNORECASE),
    re.compile(
        r"\b(?:password|passwd|pwd|secret|api[_-]?key|apikey|access[_-]?token|"
        r"refresh[_-]?token|client[_-]?secret)\s*[:=]\s*\S{4,}",
        re.IGNORECASE,
    ),
    re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@"),
    re.compile(
        r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\."
        r"[A-Za-z0-9_-]+(?![A-Za-z0-9_-])"
    ),
    re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)"),
)
CARD_CANDIDATE_PATTERN = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")


def _text_values(draft: MemoryDraft) -> Iterable[str]:
    yield draft.namespace.id
    if draft.namespace.label is not None:
        yield draft.namespace.label
    if draft.collection is not None:
        yield draft.collection.id
        if draft.collection.label is not None:
            yield draft.collection.label
    if draft.title is not None:
        yield draft.title
    yield draft.content
    yield from draft.tags


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


def validate_remember_content(draft: MemoryDraft) -> None:
    for value in _text_values(draft):
        if any(pattern.search(value) is not None for pattern in SIGNATURE_PATTERNS):
            raise DisallowedMemoryContent
        if _contains_payment_card(value):
            raise DisallowedMemoryContent
