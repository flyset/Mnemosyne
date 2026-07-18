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
  settings.py         # identity, protocol, memory-root, and remember-gate config

  memory/
    __init__.py       # stable shared-domain exports
    scopes.py         # canonical scopes and namespace-kind policy
    records.py        # versioned records, drafts, revisions, and references
    normalization.py  # Unicode, identifiers, language, and tags
    paths.py          # deterministic safe filesystem projection
    errors.py         # shared domain and storage errors
    policy.py         # bounded remember-content refusal policy
    store.py          # bounded reads and atomic filesystem persistence
    retrieval.py      # eligibility, ranking, and match evidence
    service.py        # recall and lifecycle policy

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

    tools/
      __init__.py
      registry.py     # MCP tool registry and dispatch

      list_tools/
        __init__.py   # list_tools tool schema and handler

      memory_recall/
        __init__.py   # public TOOL and handle re-exports
        definition.py # Tool schema derived from canonical shared scopes
        handler.py    # MCP validation, logging, adaptation, and Tool results

      memory_remember/
        __init__.py   # public TOOL and handle re-exports
        definition.py # scope/dimension-derived mutation schema
        handler.py    # bounded validation, service adaptation, results, and logs
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

This is where the protocol surface should grow.

### `mnemosyne/memory/`

Owns tool-independent memory meaning and local persistence:

- canonical scope definitions and scope-specific namespace kinds;
- version-1 compatibility and canonical version-2 records;
- namespace, collection, kind, language, provenance, and lifecycle dimensions;
- structured references and deterministic safe path projection;
- bounded filesystem discovery and exact lookup;
- private atomic create/replace/delete primitives and revision conflicts;
- active/archived eligibility, deterministic ranking, and match evidence;
- bounded remember-content refusal before discovery or writes;
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
returns no more than five records with match evidence and never returns paths,
internal scores, provenance, or lifecycle metadata. Archived version-2 records
are excluded. Missing directories and no positive match return `no_matches`;
source and candidate-limit failures return stable Tool errors.

The recall package is deliberately limited to `__init__.py`, `definition.py`,
and `handler.py`. Its definition derives scope branches from the shared registry;
its handler owns MCP-specific argument/result semantics. Storage and ranking do
not live under the Tool package.

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

Tool availability is startup-fixed. `MNEMOSYNE_MEMORY_REMEMBER_ENABLED` accepts
only exact lowercase `true` or `false`; absence is false and every other value
fails startup closed. The immutable startup registry contains only `list_tools`
and `memory_recall` by default and appends the remember definition and handler
together when enabled. The same selection drives MCP `tools/list`, the
`list_tools` Tool, and dispatch. No HTTP route owns this policy.

## Filesystem Retrieval

The default root is `~/.mnemosyne/memory`; the operator may set
`MNEMOSYNE_MEMORY_ROOT`. Recall never accepts a path from an MCP request. Beneath
the root, the canonical scope names are fixed top-level directories. Legacy
version-1 files remain readable without rewriting. New canonical records use
schema version 2 and derive their location from scope, namespace ID, optional
collection ID, and server-generated memory ID.

Discovery rejects symlinks, limits nesting to four directories, limits files to
64 KiB, and fails rather than returning a partial result when a scope exceeds
1,000 candidate JSON files. Invalid individual records are skipped with bounded
warning details. Files remain the source of truth and are directly inspectable
and deletable by the user.

Version-2 metadata must agree with its path. JSON files are the only durable
memory source of truth; there is no required manifest, alias database, persistent
content index, tombstone, or hidden revision history. Atomic mutation primitives
exist only in the shared domain and are disabled by default. Remember is the
only mutation exposed through MCP, and its Tool registration remains off unless
the exact startup gate enables it.

Future revise/archive/restore/forget Tools must be thin adapters over the
existing service/store contracts. Remember and every future mutation Tool
require explicit operator enablement and a client capable of per-call approval;
clients without that boundary must leave mutation Tools disabled.

### `mnemosyne/settings.py`

Contains stable server identity constants used across routes and MCP
initialization, dynamic resolution of the operator-controlled memory root, and
strict startup parsing for the remember-only enablement gate.

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
