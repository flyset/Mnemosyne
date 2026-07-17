# Backlog Scope Rules

- Root guidance lives in `AGENTS.md`; canonical local backlog rules live in `.backlog/README.md`.
- Use the Track template and local ID convention for every new Track.
- Keep Track status synchronized across its folder, filename, and title.
- Require PORE problems, acceptance criteria traceability, current inventory, and implementation gates for every Track.
- Do not implement DRAFT work. ACTIVE work proceeds one declared TDD chunk at a time: failing focused test, smallest passing change, refactor, validation, then Track update.
- Require automated tests for behavior changes; direct MCP checks supplement and never replace them.
- Keep all Track notes inside the Track file; `.backlog/` contains only this file, `README.md`, `PORE.md`, and Track files in status/year directories.
