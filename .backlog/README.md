# Tracks Backlog (canonical)

A Track is a large, outcome-driven line of work. It is the repository's self-contained engineering record: an engineer must be able to understand, plan, implement, validate, and complete the work without an external tracker.

## Status Taxonomy

- **DRAFT** — the problem, outcome, and plan are being shaped; no implementation.
- **ACTIVE** — scoped work is being executed.
- **BLOCKED** — work cannot proceed until a named decision or dependency lands.
- **COMPLETED** — acceptance passed; outcomes and evidence are captured.
- **DEPRECATED** — intentionally stopped or superseded; the reason is recorded.

## File Placement and Naming

- Assign each new Track the next immutable local identifier: `TRACK_001`, `TRACK_002`, and so on.
- Store it at `.backlog/<STATUS>/<YYYY>/TRACK_<id>_<STATUS>_<title>.md`.
- `<YYYY>` is the Track's last-modified year. Move the file when its year changes.
- `<title>` is a short, lowercase slug using underscores or hyphens.
- Synchronize status in the folder, filename, and title whenever it changes.

## Track Template

```md
# TRACK <id> [<STATUS>]: <title>

Track
- ID: TRACK_<id>
- Repository: MyMCP
- Branch: <branch>
- Current path: .backlog/<STATUS>/<YYYY>/TRACK_<id>_<STATUS>_<title>.md

Problems (PORE)
- P1: As a [role], I experience [problem], because [underlying reason or constraint].

Objective
- One-sentence outcome.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- State applicable safety and compatibility constraints.

Acceptance criteria
- [ ] A1) [P1] Observable check proving the problem is resolved.

Why now / impact
- Why this matters now.

Scope
- In scope:
  - ...
- Out of scope:
  - ...

Milestones
- [ ] M1) ...

Risks / decisions
- Risk: ...
- Decision: ...

Open questions
- [ ] Q1) ...

Decision log
- Decision (Q1): ...

Plan (execution steps)
- [ ] S1) Move Track <id> to ACTIVE (folder, filename, and title status).
- [ ] S2) ...

Current inventory
- Files, modules, contracts, and validation behavior under review.

Artifacts
- Designs, PRs, test evidence, or other durable references.
- For roadmap-derived work, cite the living roadmap and applicable phase.

Completion notes
- Outcomes, validation evidence, metrics, and lessons learned.
- For roadmap-derived work, record whether the roadmap was revised under user
  approval, has a revision proposal pending, or remains current.
```

## Workflow

1. Create a new Track in `DRAFT` with at least one PORE problem, an objective, acceptance criteria, scope, and a current inventory.
2. When a Track is roadmap-derived, inspect the current living roadmap during
   planning and cite the roadmap and applicable phase in the Track's Artifacts.
3. Planning is allowed while DRAFT; implementation is not.
4. Before implementation, move the Track to `ACTIVE` and check its explicit Move-to-ACTIVE plan step.
5. Execute only the next stated unchecked plan step or coherent TDD chunk unless the user explicitly requests batching.
6. For each implementation chunk: write a focused failing test, implement the smallest passing change, refactor, run validations, then update the Track immediately.
7. Update the Track's plan, inventory, and validation evidence after each meaningful chunk.
8. If new work falls outside scope, update the Track before proceeding or create a separate Track.
9. Before completing a roadmap-derived Track, inspect its linked roadmap. If the
   completed outcome or an approved decision materially changes the delivered
   baseline, current phase, sequencing, dependencies, intended outcomes, or next
   major step, propose revision of the living roadmap through its required user
   approval. Otherwise record in Completion notes that the roadmap remains
   current.
10. On acceptance, move the Track to `COMPLETED`, capture outcomes, and check the completion transition step.

## Implementation Gates (non-negotiable)

- No implementation—including tests intended to drive a code change—begins until the Track is ACTIVE and its Move-to-ACTIVE plan step is checked.
- Begin every implementation session by reading the Track and stating the next unchecked step(s).
- TDD is mandatory for implementation. Direct protocol checks supplement automated tests; they never substitute for them.
- Done means both validations have run and the Track has been updated.
- A roadmap-derived Track cannot complete until its linked roadmap has been
  inspected and the reconciliation outcome recorded; roadmap mutation remains
  user-approval-gated.
- Keep all Track notes, inventory, decisions, and completion evidence inside the Track file. Do not create auxiliary backlog notes.
