import pytest

from mnemosyne.settings import get_memory_remember_enabled


@pytest.mark.parametrize(
    ("configured_value", "expected"),
    [
        (None, False),
        ("false", False),
        ("true", True),
    ],
)
def test_memory_remember_enablement_uses_strict_boolean_values(
    configured_value: str | None,
    expected: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if configured_value is None:
        monkeypatch.delenv("MNEMOSYNE_MEMORY_REMEMBER_ENABLED", raising=False)
    else:
        monkeypatch.setenv(
            "MNEMOSYNE_MEMORY_REMEMBER_ENABLED",
            configured_value,
        )

    assert get_memory_remember_enabled() is expected


@pytest.mark.parametrize(
    "configured_value",
    ["", " true", "true ", "TRUE", "False", "1", "0", "yes"],
)
def test_memory_remember_enablement_fails_closed_without_echoing_invalid_value(
    configured_value: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "MNEMOSYNE_MEMORY_REMEMBER_ENABLED",
        configured_value,
    )

    with pytest.raises(ValueError) as error:
        get_memory_remember_enabled()

    assert str(error.value) == (
        "MNEMOSYNE_MEMORY_REMEMBER_ENABLED must be 'true' or 'false'"
    )
