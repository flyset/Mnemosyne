# Project Memory

> The instructions in this file are the authoritative project-local rules for
> using Mnemosyne as this project's primary durable memory store. They are
> non-negotiable for every agent operating in this project.

## Discover the Available Interface

Before performing the first Mnemosyne operation in each session:

1. Review every Mnemosyne Tool currently exposed by the MCP client, including its
   name, description, and complete input schema.
2. Use `list_tools` to confirm the running server version and enabled Tool set.
3. Treat current Tool discovery as authoritative. Do not assume that a Tool is
   enabled or that its schema matches a previous session.
4. If a required Tool or schema is unavailable or unclear, stop and ask the user
   rather than guessing.

## Memory Map

### User

#### Professional

- **Scope:** `self`
- **Namespace:** `professional`
- **Collection:** `null`
- **Holds:** enduring factual context about the user's professional identity and
  circumstances.
- **Read when:** the task depends on what is currently true about the user's
  professional situation.
- **Write when:** an approved, enduring professional fact or circumstance should
  remain available across sessions.

### MyMCP Project

- **Scope:** `project`
- **Namespace:** `mymcp`
- **Collection:** `null`
- **Holds:** general MyMCP host-project state, constraints, questions, references,
  and summaries that do not belong in a more specific mapped collection.
- **Read when:** prior MyMCP project context could affect the current task.
- **Write when:** approved durable host-project context has no more specific
  mapped collection.

#### Overview

- **Scope:** `project`
- **Namespace:** `mymcp`
- **Collection:** `overview`
- **Holds:** the living high-level MyMCP identity, purpose, boundaries, and
  current shape.
- **Read when:** a task needs quick host-project orientation.
- **Write when:** MyMCP's high-level identity or capabilities materially change;
  revise the living overview.

#### Roadmaps

- **Scope:** `project`
- **Namespace:** `mymcp`
- **Collection:** `roadmaps`
- **Holds:** user-approved, long-range MyMCP roadmaps, including major phases,
  sequencing, dependencies, and intended outcomes; roadmaps guide direction but
  do not replace detailed Backlog Tracks.
- **Read when:** choosing or evaluating the next major project step, planning a
  roadmap-derived Track, determining how a Track fits the longer-term direction,
  and reconciling the roadmap when that Track completes.
- **Write when:** the user approves a durable roadmap or materially changes one,
  or when a completed Track or approved decision changes the delivered baseline,
  current phase, sequencing, dependencies, intended outcomes, or next major step.
  Revise the existing living roadmap rather than creating a near-duplicate. Do
  not revise it for individual TDD chunks or routine DRAFT/ACTIVE transitions;
  the Backlog Track owns that execution detail.

#### Decisions

- **Scope:** `project`
- **Namespace:** `mymcp`
- **Collection:** `decisions`
- **Holds:** durable MyMCP decisions with their rationale and consequences.
- **Read when:** current work may be constrained by an established choice.
- **Write when:** a durable host-project choice should guide future work.

#### Critiques

- **Scope:** `project`
- **Namespace:** `mymcp`
- **Collection:** `critiques`
- **Holds:** unresolved critiques and questions about MyMCP architecture,
  semantics, or product direction.
- **Read when:** evaluating project weaknesses or planning improvements.
- **Write when:** a concrete unresolved concern could change project direction.

#### Reviews

- **Scope:** `project`
- **Namespace:** `mymcp`
- **Collection:** `reviews`
- **Holds:** the living holistic assessment of MyMCP strengths, weaknesses,
  maturity, and priorities.
- **Read when:** assessing current project health or priorities.
- **Write when:** the overall assessment materially changes; revise the living
  review.

#### Ideas

- **Scope:** `project`
- **Namespace:** `mymcp`
- **Collection:** `ideas`
- **Holds:** proposed host capabilities or improvements, developed exploratory
  reasoning, deferred design possibilities, and their eventual disposition.
- **Read when:** exploring potential enhancements or future directions,
  reconsidering deferred concepts, or reviewing the rationale of prior ideas.
- **Write when:** a concrete possibility or exploration has durable value but
  is not yet planned or decided.

#### Issues

- **Scope:** `project`
- **Namespace:** `mymcp`
- **Collection:** `issues`
- **Holds:** concrete observed MyMCP defects or operational problems and their
  resolution status.
- **Read when:** diagnosing known or historical host-project problems.
- **Write when:** a concrete issue is observed that may require project work.

#### Checkpoints

- **Scope:** `project`
- **Namespace:** `mymcp`
- **Collection:** `checkpoints`
- **Holds:** temporary, user-requested snapshots of unfinished project or Track
  state, including the current position, blockers, and next action.
- **Read when:** resuming unfinished work for which the user explicitly requested
  a checkpoint.
- **Write when:** the user explicitly requests a temporary handoff snapshot;
  keep it concise and point to Git or the backlog instead of duplicating the
  engineering record.
- **Lifecycle:** revise a checkpoint while it remains useful; when the work is
  completed or the snapshot becomes obsolete, archive or forget it. Record a
  meaningful completed outcome in `changelog`, never as a checkpoint.

#### Changelog

- **Scope:** `project`
- **Namespace:** `mymcp`
- **Collection:** `changelog`
- **Holds:** concise MyMCP event records for meaningful completed Tracks or
  releases, including the commit, delivered outcome, validation evidence, and
  compatibility build when applicable; excludes minor commits.
- **Read when:** the task requires the history of completed MyMCP Tracks or
  releases.
- **Write when:** a completed MyMCP Track or release has been committed and
  pushed.

### Mnemosyne Domain and History

- **Scope:** `project`
- **Namespace:** `mnemosyne`
- **Collection:** omitted when listing; use the exact existing collection when
  inspecting or writing.
- **Holds:** Mnemosyne memory-domain context and existing project history,
  including pre-inversion decisions, critiques, reviews, ideas, plans, events,
  and the inspectable transition roadmap. It is not the default home for MyMCP
  host work.
- **Read when:** the task concerns Mnemosyne's memory behavior, public identity,
  domain-specific direction, or the history of the Mnemosyne-to-MyMCP
  transition.
- **Write when:** approved durable context is specifically about the Mnemosyne
  memory domain. Route MyMCP host orientation, plans, decisions, and outcomes to
  the `mymcp` namespace instead.
- **Lifecycle:** do not bulk-migrate, rewrite, relocate, archive, or forget
  existing Mnemosyne records merely because MyMCP is now the host-project
  identity.

#### Mnemosyne Changelog History

- **Scope:** `project`
- **Namespace:** `mnemosyne`
- **Collection:** `changelog`
- **Holds:** the existing historical changelog, including completed memory-domain
  work and the host-identity transition through Track 027.
- **Read when:** the task requires that historical delivery record.
- **Write when:** a future committed and pushed outcome is specifically
  Mnemosyne-domain work. Record future MyMCP host outcomes in
  `project/mymcp/changelog`.
- **Lifecycle:** preserve existing events in place; do not move or rewrite them
  during project-identity inversion.
