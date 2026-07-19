# Architecture

Mnemosyne is organized around a small HTTP surface and a separate MCP protocol layer.

The central distinction is:

- FastAPI routes handle transport: where a request arrives.
- MCP modules handle protocol meaning: what the request asks the server to do.

## HTTP Surface

The public HTTP surface is intentionally small:

- `GET /mcp` — MCP stream endpoint.
- `POST /mcp` — MCP JSON-RPC message endpoint.
- `GET /health` — liveness check for the running process.
- `GET /version` — server identity and supported MCP protocol version.

The `/mcp` endpoint is the main protocol gate. Most behavior should be expressed as MCP methods or tools, not as extra HTTP routes.

MCP requests receive JSON-RPC result or error bodies. MCP notifications omit
`id` and receive HTTP `202` with no JSON-RPC body; the transport does not log
their payloads at the default level.

## Filesystem Layout

```text
mnemosyne/
  __init__.py
  app.py              # FastAPI app assembly
  cli.py              # console entrypoints
  settings.py         # identity, memory root, and bounded startup configuration

  memory/
    __init__.py       # stable shared-domain exports
    scopes.py         # canonical scopes and namespace-kind policy
    records.py        # versioned records, drafts, revisions, and references
    normalization.py  # Unicode, identifiers, language, and tags
    paths.py          # deterministic safe filesystem projection
    errors.py         # shared domain and storage errors
    policy.py         # bounded remember/revision content-refusal policy
    store.py          # bounded reads and atomic filesystem persistence
    retrieval.py      # eligibility, ranking, and match evidence
    service.py        # recall, remember, revision, and lifecycle policy

  routes/
    __init__.py
    mcp.py            # HTTP transport for /mcp
    health.py         # GET /health
    version.py        # GET /version

  mcp/
    __init__.py
    messages.py       # MCP message parsing and normalization
    methods.py        # MCP/JSON-RPC method dispatch
    protocol.py       # JSON-RPC result/error helpers
    tool_arguments.py # schema-aware client argument compatibility

    tools/
      __init__.py
      registry.py     # MCP tool registry and dispatch
      _memory_lifecycle.py # private lifecycle schemas, projections, errors, logs
      _memory_revise.py # private revise schema, parsing, projection, errors, logs
      _memory_forget.py # private forget projection, errors, and content-free logs

      list_tools/
        __init__.py   # list_tools tool schema and handler

      memory_recall/
        __init__.py   # public TOOL and handle re-exports
        definition.py # Tool schema derived from canonical shared scopes
        handler.py    # MCP validation, logging, adaptation, and Tool results

      memory_inspect/
        __init__.py   # public TOOL and handle re-exports
        definition.py # strict versioned-reference schema
        handler.py    # exact lookup, public projections, errors, and logs

      memory_remember/
        __init__.py   # public TOOL and handle re-exports
        definition.py # scope/dimension-derived mutation schema
        handler.py    # bounded validation, service adaptation, results, and logs

      memory_revise/
        __init__.py   # public TOOL and handle re-exports
        definition.py # complete canonical revision schema
        handler.py    # enabled service/store construction and private adapter call

      memory_archive/
        __init__.py   # public TOOL and handle re-exports
        definition.py # strict canonical reference/revision schema
        handler.py    # archive service construction and private adapter call

      memory_restore/
        __init__.py   # public TOOL and handle re-exports
        definition.py # strict canonical reference/revision schema
        handler.py    # restore service construction and private adapter call

      memory_forget/
        __init__.py   # public TOOL and handle re-exports
        definition.py # strict canonical reference/revision schema
        handler.py    # forget service construction and private adapter call
```

## Responsibilities

### `mnemosyne/app.py`

Builds the FastAPI application and includes route modules. It should stay thin.

### `mnemosyne/routes/`

Owns HTTP transport concerns:

- paths
- request body intake
- response transport types
- lightweight operational endpoints

Route modules should not accumulate MCP semantics or tool execution logic.

### `mnemosyne/mcp/`

Owns MCP protocol concerns:

- MCP message parsing and normalization
- JSON-RPC request-parameter validation and errors
- JSON-RPC response shape
- MCP method dispatch
- tool registry and dispatch
- individual tool definitions and execution handlers

Before a known Tool handler runs, the immutable registry normalizes its arguments
against the same selected `inputSchema` used for discovery. This compatibility
boundary removes at most one JSON-stringification layer only when a schema
position disallows strings and the decoded JSON type is allowed. It handles the
current object properties and `oneOf` / `anyOf` composition without becoming a
second schema validator: malformed, wrong-type, ambiguous string-permitted, or
repeatedly encoded values remain unchanged for the Tool's existing validation.
Native arguments and legitimate text fields remain unchanged.

This is where the protocol surface should grow.

### `mnemosyne/memory/`

Owns tool-independent memory meaning and local persistence:

- canonical scope definitions and scope-specific namespace kinds;
- version-1 compatibility and canonical version-2 records;
- namespace, collection, kind, language, provenance, and lifecycle dimensions;
- structured references and deterministic safe path projection;
- bounded filesystem discovery and exact lookup;
- private atomic create/replace/delete primitives and revision conflicts;
- complete normalized revision values, mutable-field rules, and immutable
  identity/metadata enforcement;
- active/archived eligibility, deterministic ranking, and match evidence;
- bounded remember/revision content refusal before storage access;
- active/archived revision and exact no-op semantics;
- uncertain post-publication replacement durability;
- mutation-disabled-by-default lifecycle policy.

The shared domain imports no MCP, FastAPI, or route modules. MCP Tool handlers
adapt domain inputs/results; they do not own record, storage, or retrieval truth.
Import-boundary tests enforce this dependency direction.

`memory_recall` validates a narrow query, exactly one required high-level memory
scope, and optional bounded free-form tags. The six scopes are `self`,
`relationship`, `preference`, `practice`, `project`, and `knowledge`; each has an
individual model-facing description in the Tool schema.

The handler constructs a read-only `MemoryService` over a
`FilesystemMemoryStore` rooted at the configured location. The shared service
discovers compatible version-1 and canonical version-2 records and ranks them
using deterministic query/path/title/content terms and exact tag overlap. It
returns no more than five records with match evidence and an inspect-compatible
versioned reference. Legacy references contain scope and ID; canonical
references also contain namespace ID and nullable collection ID. Recall never
returns paths, internal scores, provenance, or lifecycle metadata. Archived
version-2 records are excluded. Missing directories and no positive match return
`no_matches`; source and candidate-limit failures return stable Tool errors.

The recall package is deliberately limited to `__init__.py`, `definition.py`,
and `handler.py`. Its definition derives scope branches from the shared registry;
its handler owns MCP-specific argument/result semantics. Storage and ranking do
not live under the Tool package.

`memory_inspect` is likewise limited to `__init__.py`, `definition.py`, and
`handler.py`. Its strict schema accepts one reference discriminated by schema
version. Version 2 requires scope, namespace ID, nullable collection ID, and
canonical ID; version 1 requires scope and legacy ID. It accepts no filesystem
path, storage root, broad selector, query, lifecycle state, or mutation field.

The inspect handler validates before resolving the memory root and delegates
exact lookup to the existing read-only `MemoryService.inspect()` and
`FilesystemMemoryStore.get()` contracts. Canonical results contain a
record-derived reference and all user-visible version-2 fields. Legacy results
contain a versioned reference and only ID, nullable title, content, and tags.
Archived canonical records remain inspectable without a lifecycle selector.
Missing, ambiguous, candidate-limit, unsafe/unavailable-source, validation, and
unexpected failures map to bounded Tool errors. Inspection does not initialize
the root or change files. Logger `mcp.memory_inspect` emits one content-free
terminal event containing only allowlisted outcome/reference metadata; shared
skip warnings omit candidate paths.

`memory_remember` is also limited to `__init__.py`, `definition.py`, and
`handler.py`. Its schema derives six scope branches, namespace kinds, and memory
kinds from the shared domain and accepts only scope, namespace, optional
collection, kind, language, title, content, tags, and one of the two public
origins. It accepts no path or server-owned identity, provenance-mechanism,
timestamp, or lifecycle field.

The remember handler validates a `MemoryDraft`, then—only when selected by the
enabled startup registry—constructs an enabled `MemoryService` over the
configured `FilesystemMemoryStore`. The service applies the shared content
policy before duplicate discovery, generates all operational fields, and uses
the existing atomic store. The handler returns only status, structured
reference, and lifecycle for `remembered`, `already_exists`, or
`existing_archived`; failures are bounded Tool errors. Logger
`mcp.memory_remember` emits one content-free terminal event and never records
submitted memory text, labels, tags, paths, exception messages, or tracebacks.

`memory_revise` has the same three-file public package shape plus a private,
capability-free `_memory_revise.py` adapter. Its flat canonical-only request
requires the exact reference, positive expected revision, and complete
replacement values for namespace label, collection label, title, content, and
tags. It accepts no path, legacy identity, patch language, relocation,
reclassification, lifecycle target, provenance replacement, timestamp, or model
confirmation.

The private adapter owns strict parsing, normalization, minimal projection,
result consistency, bounded error mapping, and content-free logging. Only the
public handler constructs `MemoryService` and `FilesystemMemoryStore`. The
shared domain applies content policy before storage access, checks the exact
revision, detects normalized no-ops, preserves immutable identity/metadata and
lifecycle state, and atomically replaces the same file only on change. Changed
results are `revised`; no-ops are `already_current`. Archived records remain
archived and recall-excluded. Revision retains no patch, backup, tombstone, or
hidden prior content.

`memory_archive` and `memory_restore` are separate least-privilege Tools, each
with the same three-file public package shape. Their shared private
`_memory_lifecycle.py` adapter owns the canonical-only schema, strict request
parsing, minimal result projection, bounded error mapping, result consistency
checks, and content-free logging; it exposes no Tool or storage capability.

Each public handler validates through that adapter before resolving the root,
then constructs an enabled `MemoryService` over the configured
`FilesystemMemoryStore` only when selected by the startup registry. Requests
contain exactly one canonical version-2 reference and positive exact-integer
expected revision. They accept no path, legacy identity, record content, target
state, timestamp, or model confirmation. The shared service checks revision
before lifecycle idempotency and atomically replaces the same file only for a
state change. Current target state returns `already_archived` or
`already_active` without write; stale revisions conflict.

Lifecycle results contain only status, canonical versioned reference, and
state/revision. Loggers `mcp.memory_archive` and `mcp.memory_restore` emit one
terminal event with only bounded outcome/reference/lifecycle metadata. Archive
removes a canonical record from recall while exact inspection still returns it;
restore makes it recall-eligible again.

Archive, restore, and revise share the atomic store replacement primitive. If
`os.replace` publishes the new record but parent-directory sync fails, the store
raises `ReplacementOutcomeUncertain`. MCP maps this to `status: uncertain` and
`replacement_outcome_uncertain`; callers must inspect the exact reference before
any newly approved retry. This is distinct from deletion uncertainty.

`memory_forget` is a separate least-privilege, canonical-only, archived-only
Tool with the same three-file public package shape. It reuses only strict request
mechanics from `_memory_lifecycle.py`; deletion-specific projection, bounded
errors, result consistency, and content-free logging live in private
`_memory_forget.py`, which owns no storage capability.

The public handler validates before root resolution and constructs an enabled
shared service/store only when startup registration selects it. Revision is
checked before archived-state eligibility. Definitive identity, revision, state,
safe-path, and bounded-fingerprint checks occur at the store deletion point
under a mutation lock shared by in-process stores for the same absolute root.
Successful deletion unlinks one source file, syncs its parent, leaves directories
intact, and returns only `forgotten` plus the same canonical reference. There is
no tombstone or idempotent repeat result; later exact access returns not found.

A failure after unlink but before confirmed parent-directory sync raises a
distinct uncertain-outcome domain error. The MCP result instructs the caller to
inspect the same reference before any newly approved retry. Logger
`mcp.memory_forget` emits one terminal event containing only bounded outcome,
code/field, schema version, and scope. Multi-process/external last-instruction
races and secure erasure of journals, snapshots, backups, or external copies are
outside this local filesystem contract.

Tool availability is startup-fixed. Supplied values for
`MNEMOSYNE_MEMORY_REMEMBER_ENABLED`,
`MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED`,
`MNEMOSYNE_MEMORY_REVISE_ENABLED`, and `MNEMOSYNE_MEMORY_FORGET_ENABLED`
independently override their matching file keys, accept only exact lowercase
`true` or `false`, and fail
startup closed before file access for every other value. Unresolved values come
from at most one read of `Path.home() / ".mnemosyne" / "config.toml"`; the strict
optional `[memory]` table may contain only the optional TOML booleans
`remember_enabled`, `archive_restore_enabled`, `forget_enabled`, and
`revise_enabled`. The file is bypassed only when all four environment values are
supplied. All default false.

The settings layer performs no initialization. It bounds the file to 16 KiB of
UTF-8 TOML, rejects unknown structure, symlinked or non-regular sources,
metadata replacement during open, unreadable sources, and group/world-writable
POSIX application directories or files. Descriptor-relative/no-follow access
is used where supported, and failures expose only stable non-content-bearing
codes/messages. The immutable startup registry always contains `list_tools`,
`memory_recall`, and `memory_inspect`, in that order; appends archive and restore
together when their pair gate is enabled; and appends remember when its
independent gate is enabled; appends revise when its independent gate is
enabled; and appends forget last when its independent gate is enabled. Every
definition and dispatch handler is connected
as a pair, so no placeholder Tool is advertised. The same
startup selection drives MCP `tools/list`, the `list_tools` Tool, and dispatch
until restart. No HTTP route or CLI entrypoint owns this policy, and server
enablement remains separate from per-call client consent.

The registry also derives an immutable Tool-name-to-input-schema mapping from
that same startup selection. Known Tool calls pass through the shared
schema-aware one-layer argument normalizer before their paired handler; unknown
Tool behavior is unchanged. This keeps client serialization compatibility in
the MCP layer rather than in memory-domain models or individual Tool handlers.

## Filesystem Retrieval

The default root is `~/.mnemosyne/memory`; the operator may set
`MNEMOSYNE_MEMORY_ROOT`. Recall and inspection never accept a path from an MCP
request. Beneath the root, the canonical scope names are fixed top-level directories. Legacy
version-1 files remain readable without rewriting. New canonical records use
schema version 2 and derive their location from scope, namespace ID, optional
collection ID, and server-generated memory ID.

The filesystem store initializes directories lazily only on canonical create.
After validating that the deterministic record parent is beneath the configured
root, it collects a missing root-ancestor chain back to the nearest existing
directory and creates each missing component in parent-to-child order. Newly
created directories use mode `0700` on POSIX, existing directories are not
chmodded, and atomic record files retain mode `0600`. Symlink/non-directory
conflicts and creation failures remain bounded domain errors. Settings
resolution, startup, recall, disabled or invalid remember/revise calls, and
content-policy refusal do not create the root or its parents.

Discovery rejects symlinks, limits nesting to four directories, limits files to
64 KiB, and fails rather than returning a partial result when a scope exceeds
1,000 candidate JSON files. Invalid individual records are skipped with warnings
limited to scope and a bounded reason; candidate paths are not logged. Files
remain the source of truth and are directly inspectable and deletable by the
user.

Version-2 metadata must agree with its path. JSON files are the only durable
memory source of truth; there is no required manifest, alias database, persistent
content index, tombstone, or hidden revision history. Atomic mutation primitives
exist only in the shared domain and are disabled by default. Remember,
complete-state revise, reversible archive/restore, and archived-only physical
forget are exposed through independent startup gates.

Future mutation Tools must be thin adapters over the existing service/store
contracts. Every mutation Tool requires explicit operator enablement and a
client capable of per-call approval; clients without that boundary must leave
mutation Tools disabled.

### `mnemosyne/settings.py`

Contains stable server identity constants used across routes and MCP
initialization, dynamic resolution of the operator-controlled memory root, and
strict environment-first/fixed-file startup parsing for independent remember,
archive/restore, revise, and forget enablement. Each supplied environment value
overrides only its matching setting; unresolved values use at most one strict
file read. It owns the fixed local settings path, schema, bounded source
checks, and stable configuration failures without creating or editing operator
configuration.

### `mnemosyne/cli.py`

Contains console entrypoints for normal and development server startup, plus
the test-suite runner when the `test` extra is installed.

## Design Rule

Keep FastAPI routes thin. Put MCP meaning under `mnemosyne/mcp/`.

In short:

```text
HTTP request
  -> FastAPI route
    -> MCP method handler
      -> MCP tool handler
```

The door is HTTP. The language spoken behind it is MCP.

## Contribution Boundaries

- Project-wide workflow and verification gates live in `docs/AI_WORKFLOW.md`.
- Canonical product and public-contract terms live in `docs/GLOSSARY.md`.
- `mnemosyne/mcp/AGENTS.md` governs MCP protocol and tool work.
- `mnemosyne/routes/AGENTS.md` governs HTTP transport work.
