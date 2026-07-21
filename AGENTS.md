# AGENTS.md

## Project Intent

Mnemosyne is a local-first MCP server for user-governed AI memory.

## Principles

- Read before changing.
- Prefer small, explicit MCP tools over broad access.
- Do not add shell-execution or unrestricted filesystem features.
- Do not store secrets, tokens, private keys, or sensitive personal data.
- Keep memory visible, consent-based, and easy to delete.
- Favor simple filesystem-backed schemas before infrastructure complexity.

## Current Scope

This is an early FastAPI MCP skeleton. Keep changes minimal and protocol-aware.

## Project Memory

- Read `MEMORY.md` before using Mnemosyne or assuming that prior project context
  is absent.
- Use the available Mnemosyne tools as the primary durable project record store.
- Follow every instruction in `MEMORY.md`; its project-local rules are
  non-negotiable.

## Before Editing

- Read `docs/AI_WORKFLOW.md` before planning any state-changing action.
- Inspect `README.md`, `VISION.md`, `docs/ARCHITECTURE.md`, and the affected package files.
- For terminology or public-contract work, read `docs/GLOSSARY.md` first.
- For backlog work, follow `.backlog/README.md`; implementation requires an ACTIVE Track and its implementation gates.
- Preserve local-first and single-user assumptions unless explicitly changed.
- Implementation follows TDD by default: write a failing focused test, make it pass with the smallest implementation, then refactor and validate.
- Every behavior change requires automated test coverage; direct MCP protocol checks complement automated tests and do not replace them.

## MCP Testing

- Test MCP access directly through available MCP/client connections and tools when possible.
- Avoid creating ad-hoc test scripts for MCP access unless explicitly requested.
- Prefer small direct protocol/tool checks over temporary files or broad automation.

## Project Documentation

- The `docs/` folder is the home for durable project documentation beyond the README.
- Use `README.md` for user-facing setup, status, and quick orientation.
- Use `docs/GETTING_STARTED.md` for user guidance on repository-level Mnemosyne
  integration through `MEMORY.md` and a project memory map.
- Use `docs/MANUAL.md` for operating guidance for agents using Mnemosyne memory
  Tools; read it before using Mnemosyne or analyzing its agent-integration workflow.
- Use `VISION.md` for product intent, boundaries, non-goals, and future direction.
- Use `docs/ARCHITECTURE.md` for current code organization and architectural rules.
- Use `docs/AI_WORKFLOW.md` for contribution gates and verification expectations.
- Use `docs/GLOSSARY.md` for canonical product and protocol terminology.
- Add new focused docs under `docs/` when a topic becomes too detailed for the README.
- Keep `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` updated when changing public MCP behavior, endpoints, package layout, or MCP structure.
- Put implementation-specific rules in the nearest scoped `AGENTS.md`; keep this root file focused on project-wide constraints.
- Use `.backlog/README.md` for local Track governance and `.backlog/PORE.md` for problem-oriented requirements.
