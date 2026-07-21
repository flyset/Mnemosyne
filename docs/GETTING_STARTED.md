# Getting Started: Project Memory Integration

Mnemosyne is a user-governed, notebook-like memory substitute. It stores approved
records outside a model and returns selected records only when an agent uses a
memory Tool. It does not automatically inject context or give a model durable
personal memory.

This guide shows how to integrate that capability with one repository. It assumes
that Mnemosyne is already available to the AI client as Tools. Client connection
and approval configuration vary by client; follow the client-specific setup in the
main [README](../README.md).

## The integration pattern

Use a repository-local `MEMORY.md` file as an operating contract for agents that
work in the repository. The file explains which project context is worth
retrieving, where durable records belong, and when records should be created,
revised, archived, or forgotten.

The layers have distinct responsibilities:

| Layer | Responsibility |
| --- | --- |
| Mnemosyne Manual | General operating guidance for an agent using memory Tools. |
| `MEMORY.md` | Repository-specific workflow and memory map. |
| Tool descriptions and schemas | The actions a model may request and their valid argument shapes. |
| Mnemosyne server | Validation, local persistence, record identity, revision and lifecycle rules, and consent-gated mutation. |
| Repository, Git, backlog, and docs | Authoritative engineering record. |

The model sees Tools, their descriptions, and their input schemas. MCP is the
protocol that makes those Tools available; it is not the model-facing abstraction.

`MEMORY.md` guides placement and workflow. Tool schemas enforce the supported
structural dimensions, such as scope, namespace shape, allowed kinds, references,
and mutation fields. They do not decide whether a project-specific collection name
or a proposed record is the best semantic choice; that remains user-guided.

## Build a small memory map

Start with one `project` namespace for the repository. Add collections only when
they support a recurring workflow. A useful initial map is:

| Location | Use it for |
| --- | --- |
| `project / <project-id> / overview` | A living description of purpose, boundaries, and current shape. |
| `project / <project-id> / decisions` | Durable choices, their rationale, and consequences. |
| `project / <project-id> / issues` | Concrete observed problems and their resolution state. |
| `project / <project-id> / changelog` | Meaningful completed work, including commit and validation evidence. |

Use the scope that describes what a record is *about*, not how it was discovered.
For example, an enduring user choice belongs in `preference`, not `project`.
Namespace IDs identify the bounded subject or owner; collection IDs are optional
organizational partitions within that namespace. Reuse established IDs rather than
creating near-duplicates.

Keep the map small. Collections are useful when they change agent behavior—for
example, when an agent should read `decisions` before changing an established
design—not merely as labels for every possible topic.

## Add `MEMORY.md`

Place `MEMORY.md` at the repository root and tell agents to read it before using
Mnemosyne. The following is a minimal starting point; replace `example-project`
and adapt the collections to the project's workflow.

```md
# Project Memory

Before the first Mnemosyne operation in each session:

1. Review the available Mnemosyne Tools and their current input schemas.
2. Use `list_tools` to confirm the enabled Tool set.
3. Treat current Tool discovery as authoritative.

## Project

- Scope: `project`
- Namespace: `example-project`
- Collection: `overview`
- Holds: the living project purpose, boundaries, and current shape.
- Read when: work needs project orientation.
- Write when: those high-level facts materially change; revise the living record.

## Decisions

- Scope: `project`
- Namespace: `example-project`
- Collection: `decisions`
- Holds: durable choices, rationale, and consequences.
- Read when: work may be constrained by an existing choice.
- Write when: a durable choice should guide later work.

## Changelog

- Scope: `project`
- Namespace: `example-project`
- Collection: `changelog`
- Holds: meaningful completed work, including the commit and validation evidence.
- Read when: work needs completed-delivery history.
- Write when: a meaningful outcome is complete and committed.
```

The important parts are the read and write triggers. They keep memory from
becoming either an unused archive or a transcript dump.

## Use the Tools deliberately

The normal read pattern is:

1. Use `memory_recall` when relevant user-specific context could materially
   change the current response.
2. Use `memory_list` when complete, bounded discovery is needed, such as finding
   established namespace or collection IDs before a write.
3. Use `memory_inspect` on an exact reference returned by recall or listing.

Use mutations only for one bounded, durable, non-sensitive record at a time.
`memory_remember` creates a record; `memory_revise` updates its mutable content;
`memory_archive` and `memory_restore` manage reversible lifecycle state; and
`memory_forget` permanently deletes an archived record. Mutation capabilities are
disabled by default and each enabled mutation call still requires the client's
explicit, per-call user approval.

Never use Mnemosyne for secrets, credentials, tokens, private keys, or sensitive
personal data.

## Keep memory and the repository aligned

Memory should preserve concise orientation, rationale, and history that help a
later agent find the right repository evidence. It should not duplicate source
code, full discussions, generated output, or the complete backlog.

Use living records for current material and revise them as it changes. Use a
changelog record for a meaningful completed outcome. If a temporary handoff or
checkpoint is no longer useful, archive or forget it according to the project's
policy. This keeps retrieved context current and prevents stale records from
silently steering later work.

## Next reading

- [Mnemosyne Manual](MANUAL.md) — detailed guidance for agents using memory Tools.
- [README](../README.md) — installation, configuration, and Tool reference.
- [Glossary](GLOSSARY.md) — canonical terminology and public-contract language.
