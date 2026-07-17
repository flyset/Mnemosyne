# AI Workflow

## Hard Gates

- Read-only actions may proceed without approval: inspect, list, search, read, and review Git status, diff, or log.
- Before any state-changing action, read the relevant scoped `AGENTS.md`, propose the exact commands and files that would change, and wait for an explicit **yes**.
- Treat an unclear action as state-changing.
- State-changing actions include edits, generated files, dependency installs, networked commands, environment changes, and Git history changes.

## Protocol and Contract Work

- Read `docs/GLOSSARY.md` before changing or discussing Mnemosyne terminology or public contracts.
- Read `docs/ARCHITECTURE.md` before changing package boundaries, routes, MCP dispatch, or tool registration.
- Preserve the local-first, single-user, least-privilege model unless the change explicitly revises it.
- Keep MCP tools small, explicit, and independently testable; never introduce general shell execution or unrestricted filesystem access.

## Verification and Documentation

- Implementation follows TDD: write a failing focused test, implement the smallest change that passes it, then refactor and run the relevant validation.
- Every behavior change requires automated test coverage. Direct MCP/client protocol checks complement automated tests; they do not replace them.
- Do not create ad-hoc MCP test scripts unless explicitly requested.
- When public MCP behavior, tool schemas, endpoints, or package boundaries change, update the applicable `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` in the same change.

## Backlog Work

- Use `.backlog/README.md` as the canonical local Track workflow and `.backlog/PORE.md` for problem statements.
- New Tracks begin in DRAFT; implementation begins only after the Track is ACTIVE and its Move-to-ACTIVE plan step is checked.
- Execute ACTIVE work one declared plan step or coherent TDD chunk at a time, then record inventory and validation evidence in the Track.
