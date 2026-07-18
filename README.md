# Mnemosyne

Mnemosyne is an experimental local MCP server.

Its intended direction is a personal memory and awareness layer for AI agents: a small local service that lets compatible models remember approved context, inspect safe environment signals, and operate under explicit user-governed boundaries.

## Current Status

This repository currently contains a minimal FastAPI-based MCP skeleton.

Implemented tools:

- `list_tools` — lists the tools exposed by the server
- `memory_recall` — retrieves bounded, relevant, user-approved JSON memory records from one allowlisted local scope directory

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

Memory scopes, records, paths, storage, retrieval, and lifecycle policy now live
in a shared `mnemosyne/memory/` domain rather than inside the recall Tool. The
domain includes mutation-disabled create, revise, archive, restore, and physical
delete primitives for future Tools, but `memory_recall` remains the only exposed
memory Tool. No MCP mutation endpoint is currently registered.

## Filesystem Memory

The default memory root is:

```text
~/.mnemosyne/memory
```

Set an explicit root for another local location:

```bash
export MNEMOSYNE_MEMORY_ROOT=/path/to/memory
```

Recall recognizes only the six fixed scope directories beneath the memory root:

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
tombstone. These lifecycle operations are domain primitives only until explicit
consent-gated MCP Tools are implemented.

All record files are limited to 64 KiB, content to 4,000 characters, and titles
to 200 characters. Invalid, oversized, too-deep, or unsafe records are skipped
and logged without their content.

Retrieval case-folds and tokenizes the query, relative path, title, content, and
record tags. Exact request-tag overlap has the strongest weight, followed by
title, path/record-tag, and content matches. Ties are resolved deterministically.
Symlinks are rejected, no more than 1,000 candidate files are accepted in one
scope, and no more than five records are returned. Files remain the source of
truth: inspect them directly and delete a record by deleting its file.

There is no required manifest or persistent content-bearing index. Future
mutation Tools must remain disabled unless the operator enables them and the MCP
client can require approval for every exact mutation call. A model-provided
confirmation field is not consent.

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

The included `opencode.json` registers this server as a remote MCP server:

```json
{
  "mcp": {
    "mnemosyne": {
      "type": "remote",
      "url": "http://127.0.0.1:8000/mcp",
      "enabled": true
    }
  }
}
```

## Roadmap Shape

Likely next steps:

1. Add explicit, consent-based memory creation and deletion tools.
2. Add read-only awareness tools.
3. Add governance rules for consent, hygiene, and no-secret handling.
4. Refine retrieval using observed local recall behavior.
5. Continue automated MCP coverage supplemented by direct protocol checks.

See `VISION.md` for the broader scope and boundaries.

See `docs/ARCHITECTURE.md` for the current code organization.

See `docs/AI_WORKFLOW.md` for contribution and verification gates, and
`docs/GLOSSARY.md` for canonical terms and public-contract language.
