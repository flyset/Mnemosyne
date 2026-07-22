import pytest

from mymcp.memory.errors import MemoryValidationError
from mymcp.memory.normalization import (
    normalize_identifier,
    normalize_language,
    normalize_optional_text,
    normalize_required_text,
    normalize_tags,
)


def test_text_normalization_uses_nfc_lf_and_outer_trimming() -> None:
    assert normalize_required_text(
        "  Cafe\u0301\r\nsecond line\r  ",
        field="content",
        maximum_length=100,
    ) == "Café\nsecond line"
    assert normalize_optional_text(
        " Cafe\u0301 ",
        field="title",
        maximum_length=100,
    ) == "Café"
    assert normalize_optional_text(
        None,
        field="title",
        maximum_length=100,
    ) is None


@pytest.mark.parametrize("value", [None, 1, "", "   ", "abcd"])
def test_required_text_rejects_invalid_or_excessive_values(value: object) -> None:
    with pytest.raises(MemoryValidationError) as error:
        normalize_required_text(value, field="content", maximum_length=3)

    assert error.value.code == "invalid_record"
    assert error.value.field == "content"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("mnemosyne", "mnemosyne"),
        ("person_01", "person_01"),
        ("decision-1", "decision-1"),
        ("a", "a"),
        ("a" * 64, "a" * 64),
    ],
)
def test_identifier_normalization_accepts_safe_canonical_values(
    value: str,
    expected: str,
) -> None:
    assert normalize_identifier(value, field="namespace.id") == expected


@pytest.mark.parametrize(
    "value",
    [None, 1, "", "A", "-name", "name-", "name.value", "../name", "a" * 65],
)
def test_identifier_normalization_rejects_unsafe_or_noncanonical_values(
    value: object,
) -> None:
    with pytest.raises(MemoryValidationError) as error:
        normalize_identifier(value, field="namespace.id")

    assert error.value.code == "invalid_namespace"
    assert error.value.field == "namespace.id"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("EN-us", "en-us"),
        ("el", "el"),
        ("und", "und"),
        ("mul", "mul"),
        (None, "und"),
    ],
)
def test_language_normalization(value: object, expected: str) -> None:
    assert normalize_language(value) == expected


@pytest.mark.parametrize("value", [1, "", "e", "en_US", "en--us", "x" * 36])
def test_language_normalization_rejects_invalid_values(value: object) -> None:
    with pytest.raises(MemoryValidationError) as error:
        normalize_language(value)

    assert error.value.code == "invalid_record"
    assert error.value.field == "language"


def test_tag_normalization_preserves_display_case_and_enforces_normalized_uniqueness() -> None:
    assert normalize_tags(["  Rainy\tDay ", "Cafe\u0301"]) == (
        "Rainy Day",
        "Café",
    )

    with pytest.raises(MemoryValidationError) as error:
        normalize_tags(["Rainy Day", " rainy   day "])

    assert error.value.code == "invalid_record"
    assert error.value.field == "tags"


@pytest.mark.parametrize(
    "value",
    [None, "tag", ["tag"] * 11, [""], [1], ["x" * 51]],
)
def test_tag_normalization_rejects_invalid_values(value: object) -> None:
    with pytest.raises(MemoryValidationError) as error:
        normalize_tags(value)

    assert error.value.code == "invalid_record"
    assert error.value.field == "tags"
