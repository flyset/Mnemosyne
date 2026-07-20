# Mnemosyne Manual

> Operating guidance for AI agents using Mnemosyne's user-governed notebook.

## Read this first: Mnemosyne is a memory substitute

Models do not have durable personal memory. During inference, a model works with
temporary context supplied for the current interaction. Some host systems create
the appearance of memory by automatically injecting previously stored context,
without a deliberate retrieval call.

**Mnemosyne is instead a deliberate memory substitute in the form of a user-kept
notebook.** It stores approved records outside the model and retrieves selected
records into temporary context. It is external, passive, on-demand, and guided.
A closed notebook pushes nothing into your context. If you do not deliberately
consult Mnemosyne, none of its stored context enters the interaction.

The public `memory_*` Tool names use memory as a protocol and product category.
In this guide, **notebook** means Mnemosyne as a system, **record** means one
stored item, and **stored context** means information retrieved for the model's
temporary context. None of these terms implies that the model itself remembers.

Treat this as the governing fact. Almost every rule below is a consequence of it:

- Because it is **passive**, the timing is your responsibility. Recall when
  stored user-specific context could materially improve or change the current
  response; nothing will remind you.
- Because it is **on-demand**, an empty recall may mean the request did not match
  an existing record, or that no matching record exists. Refine the request or
  use bounded listing when completeness matters.
- Because it is **guided**, the user guides the notebook's organization. You may
  propose placement and lifecycle changes, but you do not decide what the user's
  information means. Nothing self-organizes.
- Because mutations are **consent-gated**, you *propose*; the user decides. You
  never authorize your own mutations.

The user is the keeper, you are the clerk, and Mnemosyne is the notebook. If you
internalize only one thing: **the notebook does nothing on its own. You must
consult it, and if you don't, none of its stored context is available to you.**

## The loop this implies

1. **Before assuming you lack relevant user-specific context**, recall the
   relevant records, or list the relevant bounded scope or container when you need
   complete discovery. Do not recall for ordinary general-knowledge questions.
2. **While working**, when the current interaction reveals something durable and
   reusable beyond the current turn, *propose* preserving it as a record. The
   notebook is not a scratchpad for the answer you're writing now.
3. **Don't narrate the mechanics** to the user ("let me query the notebook"). Use
   retrieved context the way a colleague uses shared notes.

## Reading — three tools, three jobs

Read tools are read-only and carry no mutation-approval burden. Still apply
least privilege: retrieve only context relevant to the current task.

- **`memory_recall`** — *"I need user-specific records to answer this well."*
  Ranked and tag-driven. Best when you can name the content words. It is **not
  exhaustive** and can miss records. An empty recall may justify a more precise
  request or bounded listing, but it can also mean no matching record exists. Do
  not use recall for ordinary general-knowledge questions.
- **`memory_list`** — *"What exists here?"* Complete, bounded enumeration over a
  scope (optionally a namespace or collection), with counts and truncation
  signals. Use it for discovery ("what are my projects?") and **before writing**,
  to find the right home and avoid duplicates.
- **`memory_inspect`** — *"Give me this one record's full content."* Call it on a
  reference returned by list or recall.

Typical pattern: **recall or list → inspect the promising reference(s).**

## Placing a record

Placement is an interpretive act. You propose where a record belongs; the user
remains the authority over its meaning and approves the exact mutation. A record
is not read in isolation: its scope, namespace, collection, and kind form an
organizational neighborhood that helps constrain its interpretation.

Placement has four dimensions:

**Scope** — chosen by what the record is *about*, not how you encountered it. One
scope per record; use separate recall calls per scope.

| scope          | holds                                                        |
|----------------|--------------------------------------------------------------|
| `self`         | who the user is and their enduring circumstances             |
| `relationship` | people, and the user's perspective on them                   |
| `preference`   | choices the user explicitly wants respected                  |
| `practice`     | routines, methods, habits, ways of working                   |
| `project`      | goals, state, decisions, constraints of a bounded endeavor   |
| `knowledge`    | user-approved reference material useful beyond one project   |

**Namespace** is the required subject and routing identity (a project, topic,
relationship subject, preference domain, and so on). **Collection** is an
optional organizational partition within it (`overview`, `decisions`,
`changelog`, …). Namespace and collection IDs are stable; their display labels
are mutable. Prefer lowercase-kebab IDs, and **reuse existing IDs** — list first
rather than inventing a near-duplicate.

**Kind** is the shape of the claim, constrained by scope:

| scope          | allowed kinds                                                                 |
|----------------|-------------------------------------------------------------------------------|
| `self`         | `attribute`                                                                   |
| `relationship` | `perspective`, `summary`                                                      |
| `preference`   | `preference`                                                                  |
| `practice`     | `practice`                                                                    |
| `project`      | `decision`, `constraint`, `state`, `event`, `question`, `reference`, `summary` |
| `knowledge`    | `reference`, `summary`                                                        |

Use the structure the user has already established. You may help by finding
existing placements and proposing the narrowest fitting choice, but do not
silently classify, move, or rewrite a record from your own guess at its meaning.

## Writing — you propose, the user disposes

Mutation tools are `memory_remember`, `memory_revise`, `memory_archive`,
`memory_restore`, and `memory_forget`. These capabilities are disabled by
default; record creation, revision, the archive/restore pair, and deletion have
independent startup gates. Tools appear in discovery only when their gate is
enabled. Server enablement does not establish user consent.

- **Every mutation call requires explicit, per-call user approval in the
  client.** A confirmation field *you* fill in is not consent. Never
  self-authorize a mutation, and do not call one when the client cannot require
  approval for that exact invocation.
- Propose **one bounded, non-sensitive record at a time.** Do not dump the
  conversation into a record.
- **Never store** secrets, credentials, tokens, or sensitive personal data.
- `memory_revise` replaces namespace label, the label of an existing collection,
  title, content, and tags. Scope, IDs, kind, language, provenance, event
  occurrence time, and lifecycle state remain unchanged. Pass
  `expected_revision`; stale writes are rejected (optimistic concurrency), so
  re-inspect before revising if you might be out of date.
- `memory_archive` is reversible via `memory_restore`. `memory_forget` is
  **physical deletion with no tombstone — irreversible.** Treat it with
  corresponding caution.

## Hygiene

- List the target namespace/collection before calling `memory_remember`, to avoid
  duplicates.
- Prefer **revising a living record** over spawning near-duplicates.
- Keep records atomic, with a clear title.
- Interpret a record together with its scope, namespace, collection, and kind;
  do not discard the neighborhood that gives it context.
- **Reuse tags exactly.** Tag matching is exact-string, so consistent tagging is
  what makes recall work across sessions and across different writers.

## The short version

- Mnemosyne is a notebook-like memory substitute — **consult it or none of its
  stored context enters the interaction.**
- The user is the keeper; you are the clerk. Help with interpretation, then stop.
- Read before you assume; preserve only what is durable.
- An empty recall may require a better request or bounded listing; it can also
  mean no matching record exists.
- You propose mutations; the user approves them. Never mutate unapproved.
- Never store sensitive data.
- `memory_forget` is permanent.
