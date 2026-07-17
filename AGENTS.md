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

## MCP Testing

- Test MCP access directly through available MCP/client connections and tools when possible.
- Avoid creating ad-hoc test scripts for MCP access unless explicitly requested.
- Prefer small direct protocol/tool checks over temporary files or broad automation.

## Project Documentation

- The `docs/` folder is the home for durable project documentation beyond the README.
- Use `README.md` for user-facing setup, status, and quick orientation.
- Use `VISION.md` for product intent, boundaries, non-goals, and future direction.
- Use `docs/ARCHITECTURE.md` for current code organization and architectural rules.
- Add new focused docs under `docs/` when a topic becomes too detailed for the README.
- Keep documentation updated when changing public endpoints, package layout, or MCP structure.
