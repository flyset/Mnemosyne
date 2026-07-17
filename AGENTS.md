# AGENTS.md

## Project Intent

Mnemosyne is a local-first MCP server for user-governed AI memory, awareness, reflection, and session context.

## Principles

- Read before changing.
- Prefer small, explicit MCP tools over broad access.
- Do not add shell-execution or unrestricted filesystem features.
- Do not store secrets, tokens, private keys, or sensitive personal data.
- Keep memory visible, consent-based, and easy to delete.
- Favor simple filesystem-backed schemas before infrastructure complexity.

## Current Scope

This is an early FastAPI MCP skeleton. Keep changes minimal and protocol-aware.

## Before Editing

- Inspect `README.md`, `VISION.md`, and `mnemosyne.py`.
- Preserve local-first and single-user assumptions unless explicitly changed.
- Add tests/protocol checks when behavior changes.
