# Mnemosyne

Mnemosyne is an experimental local MCP server.

Its intended direction is a personal memory and awareness layer for AI agents: a small local service that lets compatible models remember approved context, inspect safe environment signals, and operate under explicit user-governed boundaries.

## Current Status

This repository currently contains a minimal FastAPI-based MCP skeleton.

Implemented tools:

- `list_tools` — lists the tools exposed by the server
- `memory_recall` — retrieves bounded, relevant, user-approved JSON memory records from one allowlisted local scope directory
- `memory_remember` — when explicitly enabled, validates and atomically persists one approved canonical version-2 memory

This is not yet a full memory or awareness system. A `memory_recall` request
contains a free-form `query`, exactly one high-level scope (`self`,
`relationship`, `preference`, `practice`, `project`, or `knowledge`), and
optionally 1–10 unique free-form `tags`. Scope selects one fixed local directory.
Query terms and tags rank valid records from that directory; recall never searches
another scope or accepts a client-supplied path.

Matching calls return a normal Tool result with `status: ok` and at most five
memory records. Results include the record ID, scope, title, content, tags, and
matched terms/tags, but never include filesystem paths or internal scores. An
absent scope directory or no relevant record returns
`{"status":"no_matches","memories":[]}`. Invalid arguments retain stable Tool
errors with code `invalid_query`, `invalid_scope`, or `invalid_tags`; unreadable
or excessive sources return `memory_source_unavailable` or
`candidate_limit_exceeded` Tool errors.

Recall remains read-only. It does not create, update, delete, or automatically
extract memory, and it does not persist recall requests. Calls remain visible
through the MCP client's existing Tool-call/session representation.

Memory scopes, records, paths, storage, retrieval, content policy, and lifecycle
policy live in a shared `mnemosyne/memory/` domain rather than inside either MCP
Tool. The domain includes mutation-disabled revise, archive, restore, and
physical-delete primitives for future Tools. `memory_remember` is the only MCP
mutation Tool and is absent from discovery and dispatch unless the operator
enables it explicitly.

## Remembering Memory

Remember is disabled by default. With no setting, an accepted disabled setting,
or the exact environment value `false`, `tools/list` and `list_tools` omit
`memory_remember` and direct dispatch treats it as unknown.

Persist the operator's choice in the one fixed local settings file:

```text
~/.mnemosyne/config.toml
```

```toml
[memory]
remember_enabled = true
```

The file is optional and read-only to Mnemosyne. Startup does not create or
edit it or its parent. A missing file, empty document, absent or empty
`[memory]` table, absent key, or TOML boolean `false` all mean disabled. The
document may contain only the optional `[memory]` table, which may contain only
the optional TOML boolean `remember_enabled`; strings such as `"true"`, unknown
keys/tables, and malformed TOML fail startup closed.

For one process-level override, use:

```bash
export MNEMOSYNE_MEMORY_REMEMBER_ENABLED=true
```

A supplied environment value has precedence and prevents file access. Only
exact lowercase `true` and `false` are accepted; any other supplied value fails
startup closed without being echoed or falling back to the file. When the
variable is absent, Mnemosyne consults the fixed file and finally defaults to
false.

The server reads enablement once at startup, so restart it after changing either
source. Restart or reconnect the MCP client as well so it refreshes Tool
discovery. Enabling the server-side Tool does not establish user consent. A
compatible MCP client must separately show the complete arguments and require
user approval for every exact call.

The settings source is limited to 16 KiB of UTF-8 TOML. Mnemosyne rejects a
symlinked `.mnemosyne` directory or file, non-directory/non-regular source,
unreadable source, and—on POSIX—a directory or file writable by group or others.
Use mode `0700` for `~/.mnemosyne` and `0600` for `config.toml`; non-writable
`0755`/`0644` modes are also accepted because this file is not a secret store.
Configuration failures use stable bounded messages and do not expose supplied
values, file contents, parser details, underlying exception text, or the
absolute settings path.

All nine caller-owned fields are required, including nullable values:

```json
{
  "scope": "project",
  "namespace": {
    "kind": "project",
    "id": "mnemosyne",
    "label": "Mnemosyne"
  },
  "collection": {
    "id": "decisions",
    "label": "Decisions"
  },
  "kind": "decision",
  "language": "en",
  "title": "Remember consent boundary",
  "content": "Durable memory requires approval for each exact Tool call.",
  "tags": ["architecture", "consent"],
  "origin": "user_approved_proposal"
}
```

`namespace.label`, `collection`, `collection.label`, `language`, and `title`
may be null, but their keys remain required. Tags are a required zero-to-ten
item array. Namespace/collection IDs are 1–64 safe identifier characters,
labels are at most 100 characters, language tags at most 35, title at most 200,
content at most 4,000, and each tag at most 50. Unknown fields are rejected at
every level. The allowed dimensions are derived from the shared domain:

| Scope | Namespace kinds | Memory kinds |
| --- | --- | --- |
| `self` | `aspect` | `attribute` |
| `relationship` | `person`, `group`, `relationship` | `perspective`, `summary` |
| `preference` | `domain` | `preference` |
| `practice` | `domain` | `practice` |
| `project` | `project` | `decision`, `constraint`, `state`, `question`, `reference`, `summary` |
| `knowledge` | `topic` | `reference`, `summary` |

Public origin is either `explicit_user_statement` or
`user_approved_proposal`. Callers cannot supply a filesystem path, record ID,
timestamp, lifecycle state, revision, `recorded_via`, or model-authored
confirmation/consent field.

A new memory returns only its status, structured reference, and lifecycle:

```json
{
  "status": "remembered",
  "reference": {
    "scope": "project",
    "namespace_id": "mnemosyne",
    "collection_id": "decisions",
    "id": "mem_0123456789abcdef0123456789abcdef"
  },
  "lifecycle": {
    "state": "active",
    "revision": 1
  }
}
```

An exact active duplicate returns `already_exists`; an archived duplicate
returns `existing_archived`. Both identify the existing reference/lifecycle and
write no second file. Validation, content refusal, disabled mutation, candidate
overflow, generated-ID conflict, storage failure, and unexpected failure return
bounded Tool errors with stable codes and no path or submitted content.
Validation uses `invalid_scope`, `invalid_namespace`, `invalid_collection`,
`invalid_kind`, `invalid_record`, or `invalid_origin`; policy refusal uses
`disallowed_content`; disabled mutation uses `mutation_disabled`; bounded
discovery uses `candidate_limit_exceeded`; publication conflict uses
`write_conflict`; storage/path failures use `memory_source_unavailable`; and an
unexpected failure uses `internal_error`.

Before duplicate discovery or directory creation, the shared policy rejects
recognized private-key blocks, declared provider token/API-key prefixes,
Basic/Bearer authorization headers, credential assignments and
credential-bearing URLs, compact JWT-shaped values, Luhn-valid 13–19 digit
payment-card values, and SSN-shaped identifiers. It inspects
namespace/collection IDs and labels, title, content, and tags. This is
intentionally bounded signature detection, not semantic DLP: false positives
and false negatives remain possible. Unrecognized secrets and sensitive
personal facts remain prohibited, and the user must review the exact proposed
arguments before approval.

Remember logs one terminal event containing only outcome, stable error
code/field where applicable, scope, namespace kind, memory kind,
collection-present state, origin, and generated ID/lifecycle after a domain
result. Logs never include labels, title, content, tags, language, complete
arguments, rejected values, filesystem paths, exception messages, or
tracebacks.

## Filesystem Memory

The default memory root is:

```text
~/.mnemosyne/memory
```

No manual first-run initialization is required. When an enabled, valid,
policy-accepted `memory_remember` call reaches canonical creation, Mnemosyne
lazily creates any missing directories from the nearest existing ancestor
through the record directory. Every newly created directory uses private mode
`0700` on POSIX, and the record file uses mode `0600`. Existing directories are
left unchanged rather than chmodded.

Resolving either settings source, starting the server, recalling memory,
disabled or invalid remember calls, and content-policy refusals do not
initialize the memory root. Filesystem initialization therefore remains behind
the existing operator-enable and per-call consent boundaries.

Set an explicit root for another local location:

```bash
export MNEMOSYNE_MEMORY_ROOT=/path/to/memory
```

The memory domain recognizes only the six fixed scope directories beneath the
memory root:

```text
memory/
  self/
  relationship/
  preference/
  practice/
  project/
  knowledge/
```

Legacy version-1 records remain readable in their existing locations. Their
minimal format is:

```json
{
  "schema_version": 1,
  "id": "rainy-weekend",
  "title": "Rainy weekend activities",
  "content": "On rainy weekend afternoons, the user prefers museums or quiet cafés.",
  "tags": ["leisure", "rainy-day", "weekend"]
}
```

Version-1 `schema_version`, `id`, and `content` are required; `title` and `tags`
are optional. No background migration or rewrite occurs.

Canonical version-2 records are self-contained and use a deterministic path:

```text
<scope>/<namespace-id>/<collection-id?>/<memory-id>.json
```

For example:

```text
project/mnemosyne/decisions/mem_0123456789abcdef0123456789abcdef.json
```

```json
{
  "schema_version": 2,
  "id": "mem_0123456789abcdef0123456789abcdef",
  "scope": "project",
  "namespace": {
    "kind": "project",
    "id": "mnemosyne",
    "label": "Mnemosyne"
  },
  "collection": {
    "id": "decisions",
    "label": "Decisions"
  },
  "kind": "decision",
  "language": "en",
  "title": "Shared memory ownership",
  "content": "Canonical memory concepts belong to the shared memory domain.",
  "tags": ["architecture", "memory-domain"],
  "provenance": {
    "origin": "explicit_user_statement",
    "recorded_via": "memory_remember"
  },
  "lifecycle": {
    "state": "active",
    "revision": 1
  },
  "created_at": "2026-07-18T12:00:00Z",
  "updated_at": "2026-07-18T12:00:00Z"
}
```

Scope, namespace, optional collection, kind, language, content, tags,
provenance, timestamps, and lifecycle are separate dimensions. IDs determine
paths; mutable labels do not. Record metadata must agree with its location.
Unknown fields or mismatched paths make a version-2 record invalid.

Version-2 records are either `active` or `archived`; normal recall excludes
archived records. Revision replaces the same file atomically without retaining
hidden prior content. Forgetting is designed as physical deletion with no
tombstone. Remember creation is exposed only behind its explicit gate; the other
lifecycle operations remain domain primitives until dedicated consent-gated MCP
Tools are implemented.

All record files are limited to 64 KiB, content to 4,000 characters, and titles
to 200 characters. Invalid, oversized, too-deep, or unsafe records are skipped
and logged without their content.

Retrieval case-folds and tokenizes the query, relative path, title, content, and
record tags. Exact request-tag overlap has the strongest weight, followed by
title, path/record-tag, and content matches. Ties are resolved deterministically.
Symlinks are rejected, no more than 1,000 candidate files are accepted in one
scope, and no more than five records are returned. Files remain the source of
truth: inspect them directly and delete a record by deleting its file.

There is no required manifest or persistent content-bearing index. Remember
remains disabled unless the operator enables it and the MCP client can require
approval for every exact call. Future lifecycle mutation Tools remain
unregistered. A model-provided confirmation field is not consent.

## MCP Validation

An MCP request envelope must be an object. Otherwise the server returns
JSON-RPC error `-32600` with the message `Invalid Request` and `id: null`.
When present, its `params` value must also be an object. Otherwise the server
returns JSON-RPC error `-32602` with the message `Invalid params` and preserves
the request ID.

MCP notifications omit `id` and receive HTTP `202` with no JSON-RPC response
body. `notifications/initialized` and `notifications/cancelled` are accepted;
cancellation is currently a no-op because tool handlers complete synchronously.

## Intended Role

Mnemosyne is meant to become a local-first MCP server that gives agents controlled access to:

- user-approved memory
- project and runtime awareness
- behavior/reflection configuration
- prior session context
- transparent governance rules

The design bias is personal-only first, with clean seams for a possible reusable product later.

## Non-Goals

Mnemosyne is not intended to be:

- a generic shell execution server
- an unrestricted filesystem API
- a secret store
- a multi-user platform in the initial version
- a hidden memory system that mutates context without visibility

## Running the Server

The MCP endpoint is exposed at:

```text
http://127.0.0.1:8000/mcp
```

Additional operational endpoints:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/version`

Create a local virtual environment and install the project in editable mode:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Start the development server with auto-reload:

```bash
mnemosyne-dev
```

Start the server without auto-reload:

```bash
mnemosyne
```

Run the test suite after installing the `test` extra:

```bash
mnemosyne-test
```

## OpenCode Configuration

The included `opencode.json` registers this server as a remote MCP server and
requires approval for the exact prefixed remember Tool. The agent-level rule is
also explicit because per-agent permissions can override top-level rules and
OpenCode uses the last matching Tool-name rule. It denies the broad server
prefix first, then allows the two read-only Tools and asks for remember:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "mnemosyne_memory_remember": "ask"
  },
  "mcp": {
    "mnemosyne": {
      "type": "remote",
      "url": "http://127.0.0.1:8000/mcp",
      "enabled": true
    }
  },
  "agent": {
    "mnemosyne": {
      "permission": {
        "mnemosyne_*": "deny",
        "mnemosyne_list_tools": "allow",
        "mnemosyne_memory_recall": "allow",
        "mnemosyne_memory_remember": "ask"
      }
    }
  }
}
```

This client permission does not enable mutation on the server. The operator
must separately set `MNEMOSYNE_MEMORY_REMEMBER_ENABLED=true` and restart the
server. After changing `opencode.json`, quit and restart OpenCode so it reloads
the configuration and Tool discovery.

For every proposed remember call, review the complete Tool arguments and choose
`once`. Choosing `reject` prevents the request from reaching Mnemosyne and
therefore produces no write. Do not choose session-wide `always`, start OpenCode
with `--auto`, or enable interactive auto-approval while memory mutation is
enabled: each bypasses approval on later exact calls. If any of those modes was
used, disable server mutation and restart both the server and OpenCode before
continuing. Any additional per-agent permission override must preserve
this order: broad `mnemosyne_*` denial first, explicit read-only allows next,
and `mnemosyne_memory_remember: ask` last.

## Roadmap Shape

Likely next steps:

1. Add explicit, consent-based memory inspection and deletion tools.
2. Add read-only awareness tools.
3. Add governance rules for consent, hygiene, and no-secret handling.
4. Refine retrieval using observed local recall behavior.
5. Continue automated MCP coverage supplemented by direct protocol checks.

See `VISION.md` for the broader scope and boundaries.

See `docs/ARCHITECTURE.md` for the current code organization.

See `docs/AI_WORKFLOW.md` for contribution and verification gates, and
`docs/GLOSSARY.md` for canonical terms and public-contract language.
