from copy import deepcopy

import pytest

from mnemosyne.memory.errors import DisallowedMemoryContent
from mnemosyne.memory.policy import validate_remember_content
from mnemosyne.memory.records import MemoryDraft


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


@pytest.mark.parametrize(
    "disallowed",
    [
        "-----BEGIN PRIVATE KEY-----",
        "-----BEGIN RSA PRIVATE KEY-----",
        "-----BEGIN PGP PRIVATE KEY BLOCK-----",
        "AKIA" + "A" * 16,
        "ASIA" + "1" * 16,
        "ghp_" + "a" * 20,
        "github_pat_" + "a" * 20,
        "xoxb-" + "a" * 10,
        "sk_live_" + "a" * 16,
        "rk_live_" + "a" * 16,
        "AIza" + "a" * 35,
        "sk-" + "a" * 20,
        "Authorization: Bearer synthetic-token",
        "authorization: basic synthetic-token",
        "client_secret=synthetic-value",
        "postgresql://user:synthetic-password@localhost/db",
        "eyJhbGciOiJub25lIn0.c3ludGhldGlj.c2lnbmF0dXJl",
        "4242 4242 4242 4242",
        "123-45-6789",
    ],
)
def test_remember_policy_rejects_declared_sensitive_signatures(
    disallowed: str,
) -> None:
    with pytest.raises(DisallowedMemoryContent):
        validate_remember_content(_draft_with_content(disallowed))


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

    with pytest.raises(DisallowedMemoryContent):
        validate_remember_content(MemoryDraft.from_dict(arguments))
