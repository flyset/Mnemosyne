from copy import deepcopy

import pytest

from mnemosyne.memory.errors import (
    ContentRefusalReason,
    DisallowedMemoryContent,
)
from mnemosyne.memory.policy import (
    validate_remember_content,
    validate_revision_content,
)
from mnemosyne.memory.records import MemoryDraft, MemoryRevision


def _arguments() -> dict[str, object]:
    return {
        "scope": "project",
        "namespace": {
            "kind": "project",
            "id": "mnemosyne",
            "label": "Mnemosyne",
        },
        "collection": {
            "id": "decisions",
            "label": "Decisions",
        },
        "kind": "decision",
        "language": "en",
        "title": "Remember boundary",
        "content": "Memory creation requires exact per-call approval.",
        "tags": ["architecture", "consent"],
        "origin": "user_approved_proposal",
    }


def _draft_with_content(content: str) -> MemoryDraft:
    arguments = _arguments()
    arguments["content"] = content
    return MemoryDraft.from_dict(arguments)


def _revision_arguments() -> dict[str, object]:
    return {
        "expected_revision": 1,
        "namespace_label": "Tea",
        "collection_label": "Favorites",
        "title": "Japanese green tea",
        "content": "The user enjoys Japanese green tea.",
        "tags": ["tea", "preference"],
    }


@pytest.mark.parametrize(
    ("disallowed", "expected_reason"),
    [
        ("-----BEGIN PRIVATE KEY-----", ContentRefusalReason.PRIVATE_KEY_SHAPE),
        ("-----BEGIN RSA PRIVATE KEY-----", ContentRefusalReason.PRIVATE_KEY_SHAPE),
        (
            "-----BEGIN PGP PRIVATE KEY BLOCK-----",
            ContentRefusalReason.PRIVATE_KEY_SHAPE,
        ),
        ("AKIA" + "A" * 16, ContentRefusalReason.CREDENTIAL_SHAPE),
        ("ASIA" + "1" * 16, ContentRefusalReason.CREDENTIAL_SHAPE),
        ("ghp_" + "a" * 20, ContentRefusalReason.CREDENTIAL_SHAPE),
        ("github_pat_" + "a" * 20, ContentRefusalReason.CREDENTIAL_SHAPE),
        ("xoxb-" + "a" * 10, ContentRefusalReason.CREDENTIAL_SHAPE),
        ("sk_live_" + "a" * 16, ContentRefusalReason.CREDENTIAL_SHAPE),
        ("rk_live_" + "a" * 16, ContentRefusalReason.CREDENTIAL_SHAPE),
        ("AIza" + "a" * 35, ContentRefusalReason.CREDENTIAL_SHAPE),
        ("sk-" + "a" * 20, ContentRefusalReason.CREDENTIAL_SHAPE),
        (
            "Authorization: Bearer synthetic-token",
            ContentRefusalReason.CREDENTIAL_SHAPE,
        ),
        (
            "authorization: basic synthetic-token",
            ContentRefusalReason.CREDENTIAL_SHAPE,
        ),
        ("client_secret=synthetic-value", ContentRefusalReason.CREDENTIAL_SHAPE),
        (
            "postgresql://user:synthetic-password@localhost/db",
            ContentRefusalReason.CREDENTIAL_SHAPE,
        ),
        (
            "eyJhbGciOiJub25lIn0.c3ludGhldGlj.c2lnbmF0dXJl",
            ContentRefusalReason.COMPACT_TOKEN_SHAPE,
        ),
        ("4242 4242 4242 4242", ContentRefusalReason.PAYMENT_CARD_SHAPE),
        ("123-45-6789", ContentRefusalReason.GOVERNMENT_IDENTIFIER_SHAPE),
    ],
)
def test_remember_policy_rejects_declared_sensitive_signatures(
    disallowed: str,
    expected_reason: ContentRefusalReason,
) -> None:
    with pytest.raises(DisallowedMemoryContent) as caught:
        validate_remember_content(_draft_with_content(disallowed))

    assert caught.value.field == "content"
    assert caught.value.reason is expected_reason


@pytest.mark.parametrize(
    "allowed",
    [
        "-----BEGIN PUBLIC KEY-----",
        "AKIA" + "A" * 15,
        "ghp_short",
        "xoxb-short",
        "sk_live_short",
        "AIza" + "a" * 34,
        "sk-short",
        "Use an Authorization header without recording its value.",
        "password: no",
        "postgresql://localhost/db",
        "two.segments",
        "4242 4242 4242 4241",
        "123456789",
        "Memory creation requires exact per-call approval.",
    ],
)
def test_remember_policy_allows_near_misses(allowed: str) -> None:
    validate_remember_content(_draft_with_content(allowed))


def test_remember_policy_classifies_dotted_version_as_compact_token_shape() -> None:
    with pytest.raises(DisallowedMemoryContent) as caught:
        validate_remember_content(_draft_with_content("Compatibility build 0.1.0"))

    assert caught.value.field == "content"
    assert caught.value.reason is ContentRefusalReason.COMPACT_TOKEN_SHAPE


def test_remember_policy_reports_only_first_match_without_retaining_value() -> None:
    rejected = "client_secret=aaa.bbb.ccc"

    with pytest.raises(DisallowedMemoryContent) as caught:
        validate_remember_content(_draft_with_content(rejected))

    assert caught.value.field == "content"
    assert caught.value.reason is ContentRefusalReason.CREDENTIAL_SHAPE
    assert caught.value.args == ("disallowed_content",)
    assert vars(caught.value) == {
        "field": "content",
        "reason": ContentRefusalReason.CREDENTIAL_SHAPE,
    }
    assert rejected not in repr(caught.value)


@pytest.mark.parametrize(
    "field",
    [
        "namespace.id",
        "namespace.label",
        "collection.id",
        "collection.label",
        "title",
        "content",
        "tags",
    ],
)
def test_remember_policy_inspects_every_caller_owned_free_form_field(
    field: str,
) -> None:
    arguments = deepcopy(_arguments())
    signal = "sk-" + "a" * 20
    if field == "namespace.id":
        arguments["namespace"]["id"] = signal
    elif field == "namespace.label":
        arguments["namespace"]["label"] = signal
    elif field == "collection.id":
        arguments["collection"]["id"] = signal
    elif field == "collection.label":
        arguments["collection"]["label"] = signal
    elif field == "tags":
        arguments["tags"] = [signal]
    else:
        arguments[field] = signal

    with pytest.raises(DisallowedMemoryContent) as caught:
        validate_remember_content(MemoryDraft.from_dict(arguments))

    assert caught.value.field == field
    assert caught.value.reason is ContentRefusalReason.CREDENTIAL_SHAPE


@pytest.mark.parametrize(
    ("field", "expected_domain_field"),
    [
        ("namespace_label", "namespace.label"),
        ("collection_label", "collection.label"),
        ("title", "title"),
        ("content", "content"),
        ("tags", "tags"),
    ],
)
def test_revision_policy_inspects_every_replacement_text_field(
    field: str,
    expected_domain_field: str,
) -> None:
    arguments = _revision_arguments()
    signal = "sk-" + "a" * 20
    arguments[field] = [signal] if field == "tags" else signal

    with pytest.raises(DisallowedMemoryContent) as caught:
        validate_revision_content(MemoryRevision.from_dict(arguments))

    assert caught.value.field == expected_domain_field
    assert caught.value.reason is ContentRefusalReason.CREDENTIAL_SHAPE
