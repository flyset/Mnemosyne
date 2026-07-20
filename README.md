# Mnemosyne

Mnemosyne is an experimental local MCP server.

Its intended direction is a personal, notebook-like memory substitute and
awareness layer for AI agents: a small local service that preserves approved
records outside the model, retrieves selected context when requested, exposes
safe environment signals, and operates under explicit user-governed boundaries.

## Current Status

This repository currently contains a minimal FastAPI-based MCP skeleton.

Implemented tools:

- `list_tools` — reports the server version and lists the exposed tools
- `memory_recall` — retrieves bounded, relevant, user-approved JSON memory records from one allowlisted local scope directory
- `memory_list` — completely and deterministically inventories valid memories in one bounded scope or canonical container without returning record content
- `memory_inspect` — returns one exact canonical or legacy memory selected by a versioned structured reference
- `memory_remember` — when explicitly enabled, validates and atomically persists one approved canonical version-2 memory
- `memory_revise` — when independently enabled, revision-checks and atomically replaces the complete caller-mutable state of one exact canonical version-2 memory
- `memory_archive` — when explicitly enabled, revision-checks and archives one exact canonical version-2 memory
- `memory_restore` — when explicitly enabled, revision-checks and restores one exact archived canonical version-2 memory
- `memory_forget` — when independently enabled, permanently deletes one exact archived canonical version-2 memory at its expected revision

This is not yet a full memory substitute or awareness system. A
`memory_recall` request contains a free-form `query`, exactly one high-level
scope (`self`, `relationship`, `preference`, `practice`, `project`, or
`knowledge`), and
optionally 1–10 unique free-form `tags`. Scope selects one fixed local directory.
Query terms and tags rank valid records from that directory; recall never searches
another scope or accepts a client-supplied path. The Tool schema publishes scope
as an explicit string enum so clients can discover the complete vocabulary.

Matching calls return a normal Tool result with `status: ok` and at most five
memory records. Results include an inspect-compatible versioned reference, the
record ID, scope, title, content, tags, and matched terms/tags, but never include
filesystem paths or internal scores. A legacy reference contains schema version,
scope, and ID. A canonical reference additionally contains namespace ID and the
nullable collection ID. An absent scope directory or no relevant record returns
`{"status":"no_matches","memories":[]}`. Invalid arguments retain stable Tool
errors with code `invalid_query`, `invalid_scope`, or `invalid_tags`; unreadable
or excessive sources return `memory_source_unavailable` or
`candidate_limit_exceeded` Tool errors.

Recall remains read-only. It does not create, update, delete, or automatically
extract memory, and it does not persist recall requests. Calls remain visible
through the MCP client's existing Tool-call/session representation.

## Listing Memory

`memory_list` is registered by default as a read-only Tool for complete bounded
discovery. It is distinct from both other read operations:

- recall ranks records by a query, excludes non-matches and archived canonical
  records, and returns at most five results;
- listing enumerates every valid selected record without a query or relevance
  score, includes archived canonical records, and returns compact metadata in
  deterministic pages;
- inspection retrieves the complete user-visible contents of one exact listed
  or recalled reference.

Every list request requires exactly one scope. Its Tool schema exposes `scope`,
`namespace_id`, `collection_id`, `page_size`, and `cursor` as top-level object
properties for clients that do not project properties nested in composition
branches. Scope uses the same explicit six-value string enum as recall. Four
mutually exclusive conditional branches retain the strict scope-wide/namespace
and initial/continuation request variants. Tool and property descriptions repeat
those combination rules for clients that retain the flat properties but discard
composition constraints. A scope-wide request includes compatible legacy and
canonical records:

```json
{"scope":"project"}
```

Supplying `namespace_id` selects canonical records only. With a namespace,
collection selection is omission-sensitive:

```json
{"scope":"project","namespace_id":"mnemosyne"}
```

Omitted `collection_id` means collectionless records and every collection in
the namespace. Native JSON null means collectionless records only:

```json
{
  "scope": "project",
  "namespace_id": "mnemosyne",
  "collection_id": null
}
```

A string selects one exact collection:

```json
{
  "scope": "project",
  "namespace_id": "mnemosyne",
  "collection_id": "decisions"
}
```

The string `"null"` is the literal collection ID `null`; clients must send an
actual JSON null for collectionless selection. A collection selector without a
namespace is invalid. Requests never accept a path, root, filename, query, tag,
sort key, arbitrary filter, content field, or cross-scope selector.

Initial requests may include `page_size` from 1 through 100; the default is 50.
When more selected records remain, repeat the exact selector with the returned
opaque cursor and omit `page_size`:

```json
{
  "scope": "project",
  "namespace_id": "mnemosyne",
  "collection_id": "decisions",
  "cursor": "<opaque cursor>"
}
```

A successful response is always `status: ok`, including an empty inventory:

```json
{
  "status": "ok",
  "memories": [
    {
      "reference": {
        "schema_version": 2,
        "scope": "project",
        "namespace_id": "mnemosyne",
        "collection_id": "decisions",
        "id": "mem_0123456789abcdef0123456789abcdef"
      },
      "title": "Discovery contract",
      "inspectability": "exact",
      "kind": "decision",
      "lifecycle": {"state": "archived"}
    }
  ],
  "page": {
    "number": 1,
    "count": 1,
    "total_count": 1,
    "total_pages": 1,
    "truncated": false,
    "next_cursor": null
  }
}
```

Legacy items contain only their version-1 reference, nullable title, and
`inspectability`. Canonical items additionally contain kind and lifecycle state,
but not lifecycle revision. Listing never returns content, tags, labels,
language, provenance, timestamps, paths, fingerprints, retrieval scores, or
match evidence.

Ordering is fixed: schema version first, then public identity. Collectionless
canonical records precede collected records within a namespace. Duplicate
legacy sources remain separate countable items and use their unexposed relative
paths only as a final ordering tie-breaker. Their shared reference is marked
`inspectability: ambiguous`; exact inspection continues to return
`ambiguous_reference` for that reference.

Cursors are authenticated, bound to the exact selector and complete selected
valid-record snapshot, and fixed to the original page size. Selected additions,
removals, relocations, byte rewrites, lifecycle changes, or valid/invalid
transitions return `status: conflict`, code `stale_cursor`. Cursors also become
stale after a server restart because their key and process marker are not
persisted. Malformed, current-process-tampered, selector-mismatched, or otherwise
incompatible cursors return `status: invalid_request`, code `invalid_cursor`.
Start a fresh listing after either cursor error.

Other stable errors are `invalid_request`, `invalid_scope`,
`invalid_namespace`, `invalid_collection`, `invalid_page_size`,
`candidate_limit_exceeded`, `memory_source_unavailable`, and `internal_error`.
Candidate overflow and unsafe or unavailable selected sources fail without a
partial inventory. Listing does not initialize a missing memory root, create an
index or snapshot store, persist cursors, or change any record. Its one terminal
log event contains only bounded outcome, selector-presence, count, page, and
error metadata; it omits selector values, IDs, titles, cursors, content, paths,
fingerprints, exception details, and tracebacks.

## Inspecting Memory

`memory_inspect` is registered by default as a read-only Tool. It accepts exactly
one `reference` object and no path, memory root, filename, query, lifecycle
selector, or broad list selector. Use the versioned reference returned by
`memory_recall` or add `schema_version: 2` to the canonical identity returned by
`memory_remember`:

```json
{
  "reference": {
    "schema_version": 2,
    "scope": "project",
    "namespace_id": "mnemosyne",
    "collection_id": "decisions",
    "id": "mem_0123456789abcdef0123456789abcdef"
  }
}
```

A legacy selector is limited to its actual identity:

```json
{
  "reference": {
    "schema_version": 1,
    "scope": "preference",
    "id": "rainy-weekend"
  }
}
```

Canonical success returns `status: ok`, the versioned structured reference, and
the complete user-visible version-2 record: scope, namespace, optional
collection, kind, language, nullable title, content, tags, provenance,
lifecycle, and timestamps. Active and archived records use the same result
shape; exact inspection does not filter archived memory. Legacy success returns
only its versioned reference and fields that version 1 can represent: schema
version, ID, nullable title, content, and tags. It does not invent namespace,
collection, kind, language, provenance, lifecycle, or timestamps.

Invalid references, missing records, ambiguous legacy IDs, excessive legacy
candidates, unsafe or unavailable sources, and unexpected failures return
bounded Tool errors with stable codes: `invalid_reference`, `not_found`,
`ambiguous_reference`, `candidate_limit_exceeded`,
`memory_source_unavailable`, or `internal_error`. Results never include paths,
fingerprints, retrieval scores, storage wrappers, or unrelated records.

Inspection never creates, changes, migrates, archives, restores, or deletes a
record and does not initialize a missing memory root. Its one terminal log event
contains only the outcome, stable code/field where applicable, reference schema
version, and scope. It omits IDs, memory text and metadata, complete arguments,
paths, exception details, and tracebacks. Shared skipped-record warnings likewise
contain only scope and a bounded reason.

Memory scopes, records, paths, storage, retrieval, listing selection, ordering,
pagination, cursor policy, content policy, and lifecycle policy live in a shared
`mnemosyne/memory/` domain rather than inside individual MCP Tools. The domain
includes mutation-disabled revise, archive, restore, and physical-delete
primitives. `memory_remember`, `memory_revise`, paired
`memory_archive` / `memory_restore`, and `memory_forget` are absent from
discovery and dispatch unless their independent operator gates enable them.
Enabling one gate does not enable another capability.

## Revising Memory

Revision is disabled by default and has an independent gate. Persist it in the
fixed settings file or use the process override:

```toml
[memory]
revise_enabled = true
```

```bash
export MNEMOSYNE_MEMORY_REVISE_ENABLED=true
```

Only exact lowercase `true` and `false` are accepted. Restart the server and
reconnect or restart the MCP client after changing enablement. Clients that
cannot require approval for every complete exact replacement must leave
revision disabled.

Inspect the record immediately before proposing revision. Recall returns an
inspect-compatible reference, but inspection supplies the complete current
record, lifecycle state, and revision needed for review and approval. Every
revision request contains six unconditional fields plus `collection_label` when
the reference identifies an existing collection:

```json
{
  "reference": {
    "schema_version": 2,
    "scope": "preference",
    "namespace_id": "tea",
    "collection_id": "favorites",
    "id": "mem_0123456789abcdef0123456789abcdef"
  },
  "expected_revision": 3,
  "namespace_label": "Tea",
  "collection_label": "Favorites",
  "title": "Japanese green tea",
  "content": "The user enjoys sencha and gyokuro.",
  "tags": ["tea", "japanese-green-tea"]
}
```

`namespace_label` and `title` may be null, but their keys remain required. When
`reference.collection_id` is a string, `collection_label` is also required and
may be either a replacement string or native JSON null. When
`reference.collection_id` is null, the record has no collection and
`collection_label` may be omitted; an explicit native JSON null remains accepted.
The literal string `"null"` is text, not JSON null. Content is nonblank and at
most 4,000 characters; tags contain zero to ten unique normalized items of at
most 50 characters. Unknown fields, legacy references, paths, patches, language
or identity changes, provenance, lifecycle targets, timestamps, and model
confirmation/consent fields are rejected.

Clients that stringify structured Tool fields receive the existing one-layer
compatibility normalization: a JSON-encoded reference object, tags array, or
integer revision is decoded where its schema position disallows strings. A
nullable text position permits real strings, so string `"null"` is deliberately
not coerced. Collectionless callers that cannot emit top-level JSON null should
omit `collection_label`.

The caller replaces only namespace label, the label of an existing collection,
title, content, and tags. Mnemosyne preserves schema version, record ID, scope,
namespace kind/ID, collection presence/ID, memory kind, language, provenance,
lifecycle state, and `created_at`. On change, the server increments lifecycle
revision once and updates `updated_at`. Labels never rename directories or
relocate the record. Revision atomically replaces the same source file and
creates no second record, patch history, backup, diff, or tombstone.

Success returns only status, canonical versioned reference, and lifecycle:

```json
{
  "status": "revised",
  "reference": {
    "schema_version": 2,
    "scope": "preference",
    "namespace_id": "tea",
    "collection_id": "favorites",
    "id": "mem_0123456789abcdef0123456789abcdef"
  },
  "lifecycle": {"state": "active", "revision": 4}
}
```

`revised` means one atomic replacement occurred. A current-revision normalized
no-op returns `already_current` without a write, timestamp update, or revision
increment; stale revision conflicts before no-op detection. Archived memory may
be revised but remains archived, inspectable, and excluded from normal recall.
Active memory remains recall-eligible.

The shared bounded content policy checks every replacement label, title,
content value, and tag before storage access. It refuses recognized private-key,
credential, authorization-header, JWT-shaped, payment-card, and SSN-shaped
values with `disallowed_content`. This is signature detection, not complete
semantic DLP; secrets and sensitive personal data remain prohibited.

Stable bounded error codes are `invalid_reference`,
`invalid_expected_revision`, `invalid_record`, `invalid_collection`,
`disallowed_content`, `mutation_disabled`, `not_found`, `revision_conflict`,
`write_conflict`, `memory_source_unavailable`,
`replacement_outcome_uncertain`, and `internal_error`. Error statuses are,
as applicable, `invalid_request`, `refused`, `policy_error`, `not_found`,
`conflict`, `storage_error`, `uncertain`, or `internal_error`.

`replacement_outcome_uncertain` means the atomic replacement may already be
visible, but parent-directory durability was not confirmed. Do not retry
blindly: inspect the same reference first. If the requested replacement is
already present, do not retry; otherwise use the inspected current revision and
obtain new exact per-call approval. If inspection is unavailable, the outcome
remains uncertain.

Logger `mcp.memory_revise` emits one terminal event containing only outcome,
stable code/field where applicable, schema version, scope, and successful
lifecycle state/revision. It omits IDs, labels, title, content, tags, complete
arguments, paths, fingerprints, exception details, and tracebacks.

`list_tools` prefixes the discovered Tool names with the same static server
version exposed by MCP initialize and `/version`, for example
`Server: mnemosyne 0.1.2.`. Restart the server and reconnect the client after an
upgrade; a prior marker identifies a stale process.

## Archiving and Restoring Memory

Archive and restore are disabled by default and are enabled together. Persist
the operator choice in the same fixed settings file:

```toml
[memory]
archive_restore_enabled = true
```

Or use the process override:

```bash
export MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED=true
```

Only exact lowercase `true` and `false` are accepted. This gate is independent
of `remember_enabled`; enabling either capability does not enable the other.
Restart the server and MCP client after changing enablement.

Each lifecycle request contains exactly the canonical version-2 reference from
`memory_inspect` and its current positive revision:

```json
{
  "reference": {
    "schema_version": 2,
    "scope": "project",
    "namespace_id": "mnemosyne",
    "collection_id": "decisions",
    "id": "mem_0123456789abcdef0123456789abcdef"
  },
  "expected_revision": 1
}
```

The request accepts no legacy reference, path, root, filename, query, content,
target state, timestamp, or consent field. Inspect immediately before proposing
the mutation so the complete exact reference and current revision can be shown
for approval. A stale revision always returns `revision_conflict`, even if the
record has since reached the requested state.

Archive changes `active` to `archived`, increments revision once, updates
`updated_at`, and atomically replaces the same file. Archived memory is excluded
from normal recall but remains available through exact inspection. Restore
performs the inverse transition and returns the record to recall. A
current-revision archive of archived memory returns `already_archived`; a
current-revision restore of active memory returns `already_active`. Idempotent
outcomes do not write, increment revision, or update metadata.

Success contains only status, canonical versioned reference, and lifecycle:

```json
{
  "status": "archived",
  "reference": {
    "schema_version": 2,
    "scope": "project",
    "namespace_id": "mnemosyne",
    "collection_id": "decisions",
    "id": "mem_0123456789abcdef0123456789abcdef"
  },
  "lifecycle": {"state": "archived", "revision": 2}
}
```

The four normal statuses are `archived`, `already_archived`, `restored`, and
`already_active`. Stable bounded error codes are `invalid_reference`,
`invalid_expected_revision`, `mutation_disabled`, `not_found`,
`revision_conflict`, `write_conflict`, `memory_source_unavailable`,
`replacement_outcome_uncertain`, and `internal_error`. Results never expose
record content, paths, fingerprints, or storage wrappers.

For archive and restore, `replacement_outcome_uncertain` means the new
lifecycle state may already be visible but directory durability was not
confirmed. Inspect the same reference before any newly approved retry. This is
distinct from forget's deletion-specific uncertain outcome.

Each server call logs one terminal event under `mcp.memory_archive` or
`mcp.memory_restore`. Logs contain only outcome, stable code/field where
applicable, schema version, scope, and successful lifecycle state/revision. They
omit IDs, namespace/collection identity, labels, title, content, tags, complete
arguments, paths, exception details, and tracebacks.

## Permanently Forgetting Memory

Forget is disabled by default and has its own gate. It is not enabled by
remember or archive/restore. Persist the operator choice in the fixed settings
file:

```toml
[memory]
forget_enabled = true
```

Or use the exact process override:

```bash
export MNEMOSYNE_MEMORY_FORGET_ENABLED=true
```

Only lowercase `true` and `false` are accepted. Restart the server and MCP
client after changing either source. Clients that cannot require approval for
every exact call must leave forget disabled.

Forget accepts the same exact canonical version-2 reference and positive
`expected_revision` request shape shown above for lifecycle mutation. It accepts
no legacy reference, path, content, fingerprint, target state, timestamp, or
confirmation field. The record must already be archived at that current
revision. A stale request returns `revision_conflict` before state eligibility;
a current active record returns `not_archived` unchanged. Inspect immediately
before proposing forget so the complete record, archived state, reference, and
current revision can be reviewed for per-call approval.

Success physically removes the one source file, leaves organizational
directories intact, creates no tombstone, hidden history, backup, retained hash,
or deletion manifest, and returns only:

```json
{
  "status": "forgotten",
  "reference": {
    "schema_version": 2,
    "scope": "project",
    "namespace_id": "mnemosyne",
    "collection_id": "decisions",
    "id": "mem_0123456789abcdef0123456789abcdef"
  }
}
```

A second call returns `not_found`; Mnemosyne cannot fabricate idempotent proof
without a tombstone. Stable bounded codes are `invalid_reference`,
`invalid_expected_revision`, `mutation_disabled`, `not_archived`, `not_found`,
`revision_conflict`, `write_conflict`, `memory_source_unavailable`,
`deletion_outcome_uncertain`, and `internal_error`.

`deletion_outcome_uncertain` means unlink may have succeeded but directory
durability was not confirmed. Do not retry blindly. Inspect the same reference:
if it is absent, do not retry; if it is present, review it again, require it to
remain archived, use its current revision, and obtain new per-call approval. If
inspection is unavailable, the outcome remains uncertain.

Forgetting is irreversible within Mnemosyne: restore cannot recover a forgotten
record. Physical source deletion is not secure erasure and does not remove
filesystem journal data, snapshots, backups, MCP-client history, logs outside
Mnemosyne, or external copies. Logger `mcp.memory_forget` emits one terminal
content-free event with only bounded outcome/code/field, schema version, and
scope metadata.

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
the optional TOML booleans `remember_enabled`, `archive_restore_enabled`,
`forget_enabled`, and `revise_enabled`;
strings such as `"true"`, unknown keys/tables, and malformed TOML fail startup
closed.

For one process-level override, use:

```bash
export MNEMOSYNE_MEMORY_REMEMBER_ENABLED=true
```

Each environment variable overrides only its matching setting. Mnemosyne parses
all four mutation environment values first; an invalid supplied value fails
startup before file access without being echoed. If any setting remains
unresolved, Mnemosyne reads the strict file at most once for unresolved values.
The file is bypassed only when all four environment variables are supplied.
Every unresolved setting finally defaults to false.

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

Nine caller-owned fields are always required, including nullable values. The
Tool schema publishes those nine plus optional `occurred_at` in top-level
`properties`, while retaining the nine-field top-level required list, so clients
that keep only a flat object schema can construct both ordinary memories and
events. Six scope-specific `oneOf` branches additionally narrow namespace kind
and memory kind for clients that support composition:

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

For a completed project occurrence, use `kind: "event"` and include its known
occurrence instant separately from persistence time:

```json
{
  "scope": "project",
  "namespace": {"kind": "project", "id": "mnemosyne", "label": "Mnemosyne"},
  "collection": {"id": "events", "label": "Events"},
  "kind": "event",
  "language": "en",
  "title": "Track activated",
  "content": "Track 021 moved to active execution.",
  "tags": ["track-021"],
  "origin": "explicit_user_statement",
  "occurred_at": "2026-07-20T15:00:00Z"
}
```

`occurred_at` is required exactly for `event`, rejected for every other kind,
and uses strict UTC-second form `YYYY-MM-DDTHH:MM:SSZ`. It is immutable after
creation: revision has no occurrence replacement field, and archive/restore
preserve it. Existing non-event version-2 records remain valid without the
field and serialize without an invented null value.

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
| `project` | `project` | `decision`, `constraint`, `state`, `event`, `question`, `reference`, `summary` |
| `knowledge` | `topic` | `reference`, `summary` |

The shared domain defines writing guidance for every allowed `(scope, kind)`
pair. Complete scope branches publish only their applicable guidance, while the
top-level `kind` description groups all guidance by scope for clients that
discard schema composition. Shared kinds such as `summary` and `reference`
therefore retain scope-specific meaning.

Public `origin` is caller-supplied provenance context: use
`explicit_user_statement` for a direct user statement or
`user_approved_proposal` for an approved proposed memory. Origin is not consent;
consent remains the MCP client's approval of the complete exact call.
`recorded_via` is instead server-assigned. Callers cannot supply a filesystem
path, record ID, persistence timestamps, lifecycle state, revision,
`recorded_via`, or model-authored confirmation/consent field. The event-only
`occurred_at` value is the sole caller-owned structural time.

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

Event duplicate identity includes `occurred_at`: otherwise-equal events at the
same occurrence instant are duplicates, while events at different instants are
distinct. Existing non-event duplicate identity is unchanged.

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
result. Logs never include labels, title, content, tags, language,
`occurred_at`, complete arguments, rejected values, filesystem paths, exception
messages, or tracebacks.

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
provenance, persistence timestamps, optional event occurrence time, and
lifecycle are separate dimensions. IDs determine paths; mutable labels do not.
Record metadata must agree with its location. Unknown fields or mismatched paths
make a version-2 record invalid.

Canonical project events persist `"kind": "event"` and a strict
`"occurred_at"` value. Exact inspection returns that field; recall and listing
retain their existing relevance and identity ordering rather than becoming
chronological views. Mnemosyne does not create timeline resources, infer
causality, automatically supersede state, or make event records fully
append-only. A first-class many-to-many temporal model remains deferred until a
concrete usage need demonstrates it.

Version-2 records are either `active` or `archived`; normal recall excludes
archived records. Revision replaces the same file atomically without retaining
hidden prior content. Forgetting is physical deletion with no tombstone.
Remember creation, complete-state revision, reversible archive/restore, and
archived-only physical forget are exposed through explicit MCP Tools behind
independent default-off gates. Revision atomically replaces the same canonical
file and retains no hidden prior content.

All record files are limited to 64 KiB, content to 4,000 characters, and titles
to 200 characters. Invalid, oversized, too-deep, or unsafe records are skipped
and logged without their content.

Recall retrieval case-folds and tokenizes the query, relative path, title, content, and
record tags. Exact request-tag overlap has the strongest weight, followed by
title, path/record-tag, and content matches. Ties are resolved deterministically.
Symlinks are rejected, no more than 1,000 candidate files are accepted in one
scope, and no more than five records are returned. Files remain the source of
truth: inspect them directly and delete a record by deleting its file.

There is no required manifest or persistent content-bearing index. Exact
inspection and complete listing use structured selectors and never accept a
filesystem path. Scope-wide listing applies the same 1,000-candidate bound;
canonical namespace and collection selectors narrow to their deterministic safe
container before candidate counting. Collectionless and exact-collection
discovery scan only the canonical path level. Listing fails instead of returning
a partial inventory when the selected container exceeds the bound.
Every mutation remains disabled unless its operator gate enables it and the MCP
client can require approval for every exact call. A model-provided confirmation
field is not consent.

## MCP Validation

An MCP request envelope must be an object. Otherwise the server returns
JSON-RPC error `-32600` with the message `Invalid Request` and `id: null`.
When present, its `params` value must also be an object. Otherwise the server
returns JSON-RPC error `-32602` with the message `Invalid params` and preserves
the request ID. For `tools/call`, `params.arguments` must likewise be an object
when present; non-object Tool arguments receive the same `-32602` response
before Tool selection, schema-aware normalization, or handler dispatch.

MCP notifications omit `id` and receive HTTP `202` with no JSON-RPC response
body. `notifications/initialized` and `notifications/cancelled` are accepted;
cancellation is currently a no-op because tool handlers complete synchronously.

For compatibility with MCP clients that stringify structured Tool arguments,
dispatch uses the selected Tool's advertised input schema to remove at most one
extra JSON-encoding layer. Normalization occurs only where the schema disallows
a string and the decoded JSON value has a permitted type. Correctly typed values
are unchanged; fields that permit strings are never decoded; malformed,
wrong-type, or repeatedly encoded values continue to the Tool's normal bounded
validation. The advertised Tool schemas and canonical memory formats remain
unchanged. For `memory_list`, a stringified page size can therefore normalize to
an integer, while `collection_id` strings—including `"null"`—remain strings
because that field legitimately permits them. Collectionless selection requires
native JSON null.

## Intended Role

Mnemosyne is meant to become a local-first MCP server that gives agents controlled access to:

- user-approved durable records and retrieval
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
- a hidden system that mutates model context without visibility

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

The included `opencode.json` registers this server as a remote MCP server,
explicitly allows read-only inventory listing, and requires approval for each
exact prefixed mutation Tool. The agent-level rules are explicit because
per-agent permissions can override top-level rules and OpenCode uses the last
matching Tool-name rule. They deny the broad server prefix first, allow the
lower-breadth read-only Tools, then ask for remember, revise, archive, restore,
and forget:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "mnemosyne_memory_list": "allow",
    "mnemosyne_memory_remember": "ask",
    "mnemosyne_memory_revise": "ask",
    "mnemosyne_memory_archive": "ask",
    "mnemosyne_memory_restore": "ask",
    "mnemosyne_memory_forget": "ask"
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
        "mnemosyne_memory_inspect": "allow",
        "mnemosyne_memory_list": "allow",
        "mnemosyne_memory_remember": "ask",
        "mnemosyne_memory_revise": "ask",
        "mnemosyne_memory_archive": "ask",
        "mnemosyne_memory_restore": "ask",
        "mnemosyne_memory_forget": "ask"
      }
    }
  }
}
```

This client permission does not enable mutation on the server. The operator
must separately set the applicable remember, revise, archive/restore, or forget
server gate and restart the server. After changing `opencode.json` or agent
policy, quit and restart OpenCode so it reloads configuration and Tool discovery.

For every proposed mutation call, review the complete Tool arguments and choose
`once`. Rejecting a mutation prevents the request from reaching Mnemosyne and
therefore produces no write. Do not start OpenCode with `--auto` or enable
interactive auto-approval while memory mutation is enabled: each bypasses
approval on later exact calls. If either mode was used, disable server mutation
and restart both the server and OpenCode before continuing. Any additional
per-agent permission override must preserve this order: broad `mnemosyne_*`
denial first, explicit lower-breadth read-only allows (including `memory_list`)
next, and the exact mutation asks last.

## Roadmap Shape

Likely next steps:

1. Add read-only awareness tools.
2. Add governance rules for consent, hygiene, and no-secret handling.
3. Refine retrieval using observed local recall behavior.
4. Continue automated MCP coverage supplemented by direct protocol checks.

See `VISION.md` for the broader scope and boundaries.

See `docs/ARCHITECTURE.md` for the current code organization.

See `docs/AI_WORKFLOW.md` for contribution and verification gates, and
`docs/GLOSSARY.md` for canonical terms and public-contract language.
