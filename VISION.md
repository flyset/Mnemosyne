# Mnemosyne Vision

Mnemosyne is a personal, local-first MCP server that gives AI agents controlled
access to a user-governed memory substitute.

The goal is not to make an agent omniscient or pretend that a model possesses
durable personal memory. The goal is to provide a small, trustworthy local
notebook: the records the user has approved preserving and the safety boundaries
that govern them.

## Role

Mnemosyne acts as a thin bridge between MCP-compatible agents and local memory.

It should help agents:

- retrieve stable, user-approved facts and preferences when relevant
- retrieve prior context without dumping everything into the prompt
- operate under explicit consent and governance rules

## Notebook Model

Models do not have durable personal memory. During inference they operate on
temporary context supplied for the current interaction; any continuity across
sessions comes from an external system preserving and supplying state.

Mnemosyne is that kind of memory substitute, best understood as a user-kept
notebook rather than ambient memory. It stores approved records outside the
model and retrieves selected records into temporary context when an agent
deliberately consults it. "Guided" describes the direction of authority: the
user guides Mnemosyne's organization; Mnemosyne does not guess what the user's
information means.

The roles are deliberately distinct:

- the user is the keeper and remains the authority over meaning;
- the agent acts as a clerk that retrieves records and proposes bounded changes;
- Mnemosyne is the notebook that preserves only approved records and structure.

Structure is not decoration. Scope, namespace, collection, and kind make records
retrievable and provide the organizational neighborhood that constrains how they
should be interpreted. Poor placement can fail silently through missed retrieval
or, more dangerously, through confident misreading.

Mnemosyne should make sound organization intuitive, validate bounded choices,
and help agents reuse existing structure. It must stop short of silently
classifying, moving, or rewriting records based on its own interpretation. The
system may help with the interpretive act, but the user must decide it.

## Initial Scope

Version 0 is personal-only:

- single user
- local machine
- filesystem-backed storage is acceptable
- simple schemas over complex infrastructure
- explicit tools over broad ambient access
- transparent behavior over invisible automation

The server should expose small, composable tools rather than large autonomous workflows.

## Tool Focus

Mnemosyne's product domain is memory. Its tools should operate only on approved
memory records and their lifecycle:

- store approved facts and preferences
- recall, list, and inspect bounded records
- revise, archive, restore, or delete obsolete records under explicit consent
- separate temporary working context from durable on-demand records
- apply consent boundaries, record hygiene, auditability, and no-secret handling

## Non-Goals

Mnemosyne should not become:

- a general shell proxy
- an unrestricted filesystem bridge
- a place to store secrets, tokens, or private keys
- a business-logic layer for unrelated applications
- a multi-user product before the single-user model is reliable
- a vector database by default
- a hidden autonomous system that changes model context without transparency

## Safety Contract

Mnemosyne should prefer:

- read-only memory inspection before mutation
- explicit schemas and predictable errors
- least-privilege access
- user-approved durable records
- clear separation between personal facts and project facts
- small, explainable record changes
- local storage by default

It should refuse or constrain requests that risk exposing secrets, private data, or uncontrolled filesystem access.

## Future Expansion Seams

If Mnemosyne evolves into a reusable product, it should be ready for:

- versioned schemas
- pluggable storage backends
- configurable policy profiles
- audit logs
- optional encryption once the threat model is explicit
- migration from personal-only to product-grade packaging

The product path should not compromise the v0 principle: keep the user sovereign,
keep the tools small, and make external records and their use in model context
visible.
