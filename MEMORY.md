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

### Project

- **Scope:** `project`
- **Namespace:** `mnemosyne`
- **Collection:** `null`
- **Holds:** general project state, decisions, constraints, questions, references,
  and summaries that do not belong in a more specific mapped collection.
- **Read when:** prior Mnemosyne project context could affect the current task.
- **Write when:** approved durable project context has no more specific mapped
  collection.

#### Overview

- **Scope:** `project`
- **Namespace:** `mnemosyne`
- **Collection:** `overview`
- **Holds:** the living high-level project identity, purpose, boundaries, and
  current shape.
- **Read when:** a task needs quick project orientation.
- **Write when:** the project's high-level identity or capabilities materially
  change; revise the living overview.

#### Roadmaps

- **Scope:** `project`
- **Namespace:** `mnemosyne`
- **Collection:** `roadmaps`
- **Holds:** user-approved, long-range project roadmaps, including major phases,
  sequencing, dependencies, and intended outcomes; roadmaps guide direction
  but do not replace detailed Backlog Tracks.
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
- **Namespace:** `mnemosyne`
- **Collection:** `decisions`
- **Holds:** durable project decisions with their rationale and consequences.
- **Read when:** current work may be constrained by an established choice.
- **Write when:** a durable choice should guide future work.

#### Critiques

- **Scope:** `project`
- **Namespace:** `mnemosyne`
- **Collection:** `critiques`
- **Holds:** unresolved critiques and questions about project architecture,
  semantics, or product direction.
- **Read when:** evaluating project weaknesses or planning improvements.
- **Write when:** a concrete unresolved concern could change project direction.

#### Reviews

- **Scope:** `project`
- **Namespace:** `mnemosyne`
- **Collection:** `reviews`
- **Holds:** the living holistic assessment of project strengths, weaknesses,
  maturity, and priorities.
- **Read when:** assessing current project health or priorities.
- **Write when:** the overall assessment materially changes; revise the living
  review.

#### Ideas

- **Scope:** `project`
- **Namespace:** `mnemosyne`
- **Collection:** `ideas`
- **Holds:** proposed capabilities or improvements, developed exploratory
  reasoning, deferred design possibilities, and their eventual disposition.
- **Read when:** exploring potential enhancements or future directions,
  reconsidering deferred concepts, or reviewing the rationale of prior ideas.
- **Write when:** a concrete possibility or exploration has durable value but
  is not yet planned or decided.

#### Issues

- **Scope:** `project`
- **Namespace:** `mnemosyne`
- **Collection:** `issues`
- **Holds:** concrete observed defects or operational problems and their
  resolution status.
- **Read when:** diagnosing known or historical project problems.
- **Write when:** a concrete issue is observed that may require project work.

#### Checkpoints

- **Scope:** `project`
- **Namespace:** `mnemosyne`
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
- **Namespace:** `mnemosyne`
- **Collection:** `changelog`
- **Holds:** concise project event records for meaningful completed Tracks or
  releases, including the commit, delivered outcome, validation evidence, and
  compatibility build when applicable; excludes minor commits.
- **Read when:** the task requires the history of completed Tracks or releases.
- **Write when:** a completed Track or release has been committed and pushed.
