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
  settings.py         # server identity, protocol constants, and memory-root config

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
        definition.py # Tool schema and canonical scopes
        handler.py    # validation, logging, orchestration, and Tool results
        retrieval.py  # safe filesystem discovery, parsing, and ranking
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

`memory_recall` validates a narrow query, exactly one required high-level memory
scope, and optional bounded free-form tags. The six scopes are `self`,
`relationship`, `preference`, `practice`, `project`, and `knowledge`; each has an
individual model-facing description in the Tool schema.

The handler maps the validated scope through a fixed allowlist to one directory
under the configured memory root, discovers bounded version-1 JSON records, and
ranks them using deterministic query/path/title/content terms and exact tag
overlap. It returns no more than five records with match evidence and never
returns filesystem paths or internal scores. Missing directories and no positive
match return `no_matches`; source and candidate-limit failures return stable Tool
errors. Recall does not create memory directories, mutate records, persist recall
requests, generate embeddings, or access external services.

The package boundary is deliberately explicit: `definition.py` owns the public
Tool contract, `handler.py` owns MCP argument and result semantics, and
`retrieval.py` owns constrained local-file behavior. `__init__.py` only preserves
the package-level `TOOL` and `handle` imports used by the registry.

## Filesystem Retrieval

The default root is `~/.mnemosyne/memory`; the operator may set
`MNEMOSYNE_MEMORY_ROOT`. Recall never accepts a path from an MCP request. Beneath
the root, the canonical scope names are fixed top-level directories. Records are
UTF-8 JSON objects with required `schema_version: 1`, `id`, and `content`, plus
optional `title` and `tags`.

Discovery rejects symlinks, limits nesting to four directories, limits files to
64 KiB, and fails rather than returning a partial result when a scope exceeds
1,000 candidate JSON files. Invalid individual records are skipped with bounded
warning details. Files remain the source of truth and are directly inspectable
and deletable by the user.

### `mnemosyne/settings.py`

Contains stable server identity constants used across routes and MCP
initialization, plus dynamic resolution of the operator-controlled memory root.

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
