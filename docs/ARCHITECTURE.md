# Architecture

MyMCP is the repository and top-level Python host package. It hosts the Mnemosyne
memory domain in-process and is organized around a small HTTP surface, a
runtime-bound MCP protocol layer, and explicit host bootstrap. TRACK_031
implements Phase 1 kind-qualified contracts, `ActivatedTool`/`PluginContribution`
composition, trusted internal effect/consent metadata, host-owned bindings and
`list_tools`, immutable `HostRuntime` assembly, and opaque runtime generations.
TRACK_032 adds immutable definition contracts, strict 64 KiB manifest parsing,
exact parity validation, and fixed packaged declaration loading before runtime
generation. TRACK_033's implemented vertical extraction places the canonical
Mnemosyne adapter, configuration, memory domain, and MCP Tool adapters in its
bundled plugin. TRACK_034 delivered the MyMCP/`mymcp` `0.2.0` public-host release
while Mnemosyne retains its memory-domain identity. TRACK_036 delivered the prior
`0.2.1` Ollama Tool-schema compatibility build; server-side Mnemosyne validation
and all Tool/domain identities remain unchanged. TRACK_039 delivers MyMCP
`0.3.0` host configuration schema 1 and startup integration.

The central distinction is:

- FastAPI routes handle transport: where a request arrives.
- MCP modules handle protocol meaning: what the request asks the server to do.

## Current and Target Architecture

This document describes the **current implementation**. The package layout has
a trusted host/plugin-contract seam and one extracted bundled Mnemosyne plugin.
`mymcp/plugins/mnemosyne/` owns Mnemosyne configuration, memory-domain code,
MCP Tool adapters, the trusted adapter, and its packaged inert declaration.

The approved target is defined in
[`docs/PLUGIN_ARCHITECTURE.md`](PLUGIN_ARCHITECTURE.md). In that target:

- `mymcp/plugin/` owns the generic plugin-author contract;
- `mymcp/host/` owns immutable runtime assembly, explicit built-in bootstrap,
  future startup composition, gateway authority, and bounded security audit;
- concrete bundled implementations live under `mymcp/plugins/`;
- all Mnemosyne production implementation and policy live under
  `mymcp/plugins/mnemosyne/`;
- bundled and configured external plugins share logical manifest, definition,
  capability, configuration, and host-owned binding semantics;
- qualified capability identity includes plugin ID, capability kind, and local
  ID, while the host separately owns the flat endpoint-visible MCP Tool name;
- host API v1 is Tools-only;
- a strict inert manifest validates static built-ins and configured external
  plugin metadata without granting authority or proving isolation;
- configured external plugins will be validated as inert metadata before loading
  implementation code where possible, then run as operator-trusted in-process
  code; MyMCP makes no isolation, restriction, supervision, killability, or
  resource-control guarantee for them;
- the current opaque runtime-generation identity remains a per-start identity,
  while authenticated local client principals, policy-filtered
  discovery/dispatch, host-verifiable exact-call approval, and bounded security
  audit are explicit later gates; and
- released `0.2.0` makes the endpoint,
  application, package metadata, and tracked official client identify MyMCP;
  repository and operational validation are complete; the public, non-draft,
  non-prerelease release is tagged `mymcp-v0.2.0` at `c2852bc`; it preserves
  Mnemosyne's plugin,
  `memory_*`, `MNEMOSYNE_*`, `~/.mnemosyne`, storage, and record identities.

Current production uses the explicit trusted Mnemosyne `0.3.0` bundled-plugin
adapter over canonical registrations. `memory_recall` declares capability
contract `1.2.0`; the other seven `memory_*` capabilities declare `1.1.0`.
MyMCP's host/package/server marker is independently `0.3.0`. Host configuration
is loaded into one immutable startup snapshot before bootstrap. Bootstrap then
reads only the fixed `mymcp.plugins.mnemosyne` `manifest.json`, strictly parses its at-most-64-KiB
bytes, and validates exact manifest/adapter/selected-contribution parity before
generation construction. This fixed validation is neither dynamic discovery nor
authority grant. Schema-v1 configuration can declare external desired state, but
enabled external plugins fail before runtime construction in this build. Startup
composition, gateway governance, and public metadata projection remain deferred.
The canonical repository is `https://github.com/flyset/MyMCP`, and the former
URL redirects there. Local origin/history/tag/placeholder verification is
complete. The tracked and ignored OpenCode migration uses connection/agent/prefix
`mymcp` with deny-first, four read-only allows, and five exact mutation asks;
Claude configuration is excluded. The normal endpoint and final client reconnect
were verified. Isolated approved-once and rejected/no-Tools-call checks passed
without changing the memory root. The public release is available at
<https://github.com/flyset/MyMCP/releases/tag/mymcp-v0.2.0>. Loopback reachability and client-side
permission prompts remain operational boundaries, not authenticated principal
identity or host-verifiable exact-call approval.

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
mymcp/
  __init__.py
  app.py              # FastAPI app assembly
  cli.py              # console entrypoints
  settings.py         # retained server/process identity constants

  routes/
    __init__.py
    mcp.py            # HTTP transport for /mcp
    health.py         # GET /health
    version.py        # GET /version

  host/
    configuration.py    # XDG source, strict schema-v1 snapshot, semantic checks
    bootstrap.py        # explicit production runtime construction
    runtime.py          # immutable HostRuntime and opaque generation

  plugin/
    contracts.py        # kind-qualified contracts and effect/consent metadata
    definition.py       # immutable inert definition contracts
    manifest.py         # strict parser and parity validation
    composition.py      # ActivatedTool/PluginContribution composition

  plugins/
    mnemosyne/          # trusted bundled Mnemosyne implementation
      manifest.json     # fixed packaged inert declaration
      plugin.py         # definition, selected contribution, service composition
      configuration.py  # memory root and bounded startup configuration
      memory/           # records, storage, retrieval, listing, and lifecycle
      mcp/
        tools/          # eight memory_* adapters and private helpers

  mcp/
    __init__.py
    messages.py       # MCP message parsing and normalization
    dispatcher.py      # runtime-bound MCP/JSON-RPC dispatch
    protocol.py       # JSON-RPC result/error helpers
    tool_registry.py  # generic immutable Tool registration and dispatch
    tool_arguments.py # schema-aware client argument compatibility

    tools/
      __init__.py
      list_tools/
        __init__.py   # host-owned complete-surface Tool
```

## Responsibilities

### `mymcp/app.py`

Builds the FastAPI application and includes route modules. It should stay thin.

### `mymcp/routes/`

Owns HTTP transport concerns:

- paths
- request body intake
- response transport types
- lightweight operational endpoints

Route modules should not accumulate MCP semantics or tool execution logic.

### `mymcp/mcp/`

Owns MCP protocol concerns:

- MCP message parsing and normalization
- JSON-RPC request-parameter validation and errors
- JSON-RPC response shape
- MCP method dispatch
- tool registry and dispatch
- schema-aware argument normalization
- host-owned `list_tools`

It owns no Mnemosyne Tool definition, handler, configuration, or memory policy.

Before a known Tool handler runs, the immutable registry normalizes its arguments
against the same selected `inputSchema` used for discovery. This compatibility
boundary removes at most one JSON-stringification layer only when a schema
position disallows strings and the decoded JSON type is allowed. It handles the
current object properties and `oneOf` / `anyOf` composition without becoming a
second schema validator: malformed, wrong-type, ambiguous string-permitted, or
repeatedly encoded values remain unchanged for the Tool's existing validation.
Native arguments and legitimate text fields remain unchanged.

### `mymcp/plugin/composition.py`

Owns Phase 1 composition of immutable `ActivatedTool` values into
`PluginContribution` values and a complete bound Tool surface. It validates
qualified capability identity, trusted effect/consent metadata, host-owned
public bindings, and collisions before constructing the registry. It performs no
manifest, package, entry-point, or network discovery.

### `mymcp/plugin/definition.py` and `mymcp/plugin/manifest.py`

These generic modules own immutable inert declaration values and manifest-v1
validation. The parser accepts an already-decoded mapping or at most 64 KiB of
strict UTF-8 JSON bytes, rejects duplicate keys and unknown or invalid fields,
and performs no path, package, import, metadata, or network discovery. Parity
requires exact manifest and adapter definitions, host-API compatibility, and an
ordered selected contribution subset with matching effect/consent metadata.
Declarations carry no handler, Tool schema, configuration or secret value,
public Tool name, lifecycle instruction, granted authority, or consent proof.

### `mymcp/mcp/tool_registry.py`

Owns generic registration and dispatch mechanics without importing Mnemosyne
Tools, the memory domain, or Mnemosyne settings. A frozen `ToolRegistration`
pairs one Tool definition with one handler. `ToolRegistry` accepts only explicit
complete registrations, preserves their order, rejects duplicate names,
snapshots discovery definitions defensively, and dispatches known calls through
schema-aware one-layer argument normalization. It has no dynamic loading,
integration metadata, gate selection, or plugin lifecycle.

### `mymcp/host/bootstrap.py` and `mymcp/host/runtime.py`

`mymcp/host/configuration.py` exclusively owns XDG path selection, safe bounded
source reading, strict schema-v1 TOML parsing, immutable host/server/external
declaration values, and bounded configuration errors. It imports neither FastAPI,
routes, MCP dispatch, nor concrete plugins. The snapshot expresses process and
future composition desired state; it is not Mnemosyne configuration, consent,
trust proof, or external-plugin safety control.

It also owns the `mymcp.host.configuration` startup terminal event: one `INFO`
event per successful consuming process with `outcome` (`loaded` or
`absent_defaults`), schema version, validated loopback address/port, declaration
count, and enabled count; or one `ERROR` event with only `outcome=error` and a
stable configuration code before the unchanged `HostConfigurationError`
propagates. It logs no path, environment value, source content, plugin ID,
unapproved value, exception detail, or traceback. The normal launcher consumes
configuration once; each distinct development supervisor or reload-worker
process emits one event when it consumes configuration; direct Uvicorn factory
startup consumes it once per process when no snapshot is injected. This is not a worker-lifecycle claim and
does not add runtime rereads, watching, or hot reload. See
[Configuration startup logging](CONFIGURATION.md#startup-logging) for the exact
event format and operator behavior.

`build_production_runtime()` is the explicit production composition root. It
first validates the supplied snapshot against bundled identities, then reads
exactly the source-controlled packaged Mnemosyne `manifest.json`, parses
it, obtains the trusted adapter definition and gate-selected contribution, and
validates parity before applying canonical host-owned bindings, binding
`list_tools`, or constructing an immutable `HostRuntime` generation. Any such
failure returns no runtime. `create_app(runtime)` and `MCPDispatcher(runtime)`
use that runtime for discovery and dispatch. `create_production_app()` is the
local factory used by the supported Uvicorn target: it accepts an injected
snapshot or loads once when none is supplied. Ordinary imports do not load
configuration, build a runtime, or create a global application. `mymcp` loads
once and supplies the validated address/port to Uvicorn; `mymcp-dev` loads once
in its supervisor for validation/binding and each reload worker loads once. No
process watches configuration. The `mymcp` and `mymcp-dev` launchers configure
standard Python logging at `INFO` before loading; route imports do not configure
logging. Direct Uvicorn factory invocation retains Uvicorn logging ownership,
while programmatic users configure standard Python logging themselves.

### `mymcp/plugins/mnemosyne/plugin.py`

Owns the trusted in-process Mnemosyne integration: memory Tool imports, one
immutable startup resolution of Mnemosyne-owned mutation settings, fixed public
ordering, independent mutation-gate selection, definition/handler binding, and
memory service/store composition. Its zero-argument production entrypoint
contributes a trusted Mnemosyne `0.3.0` `PluginContribution` over canonical
registrations; it does not contribute `list_tools`, public bindings, or the final
`HostRuntime`. One ordered declaration table also derives its immutable complete
`PluginDefinition`: every capability row declares its own contract version, all
eight possible memory Tools remain declared, and startup gates select the runtime
subset. A lower-level helper accepts explicit gate booleans for deterministic
focused tests.

Focused tests own a version-keyed canonical-JSON digest ledger for declared Tool
definitions. Each entry couples a capability identity and declared version to a
SHA-256 digest and readable top-level properties/required-field fingerprints;
historical entries, including `memory_recall` `1.0.0` and `1.1.0`, remain
reviewable beside the current `1.2.0` contract. This guard detects
declared-definition drift, not
handler result/error semantics or every compatibility consequence. Behavioral
tests and the required version-impact review remain the authority for deciding
whether a version changes.

The integration lazily resolves the configured root and constructs a fresh
`FilesystemMemoryStore` and `MemoryService` for each validated operation call.
Recall, list, and inspect operations receive mutation-disabled services;
remember, revise, archive, restore, and forget receive mutation-enabled services
only after their handlers pass Tool-specific validation and enabled mutation
gates.

Each memory handler receives only its narrow typed operation. Handlers retain
request parsing, Tool-level gate checks, result projection, bounded error
mapping, and content-free logging; they do not resolve roots or import or
construct concrete stores and services. This is a trusted bundled plugin, not a
dynamic discovery system, production second integration, or public Tool
namespace.

Public Tool schemas with argument variants must keep the complete caller-visible
field set in top-level `properties` with top-level required fields. Composition
keywords may refine valid combinations but must not be the only place fields are
declared. Tool and property descriptions must also explain legal combinations,
because compatible clients may retain only the flat property bag and required
list while discarding `oneOf`, `anyOf`, or conditional constraints. Compatibility
tests for such Tools must exercise that reduced view as well as the complete
schema.

This is where the protocol surface should grow.

### `mymcp/plugins/mnemosyne/memory/`

Owns tool-independent memory meaning and local persistence:

- canonical scope definitions and scope-specific namespace kinds;
- version-1 compatibility and canonical version-2 records;
- namespace, collection, kind, language, provenance, occurrence-time, and
  lifecycle dimensions;
- canonical per-(scope, kind) definitions and model-facing writing guidance;
- structured references and deterministic safe path projection;
- bounded scope/container discovery and exact lookup;
- complete listing selectors, deterministic mixed-schema ordering, whole-snapshot
  legacy ambiguity, bounded pages, and authenticated continuation cursors;
- private atomic create/replace/delete primitives and revision conflicts;
- complete normalized revision values, mutable-field rules, and immutable
  identity/metadata enforcement;
- project-event occurrence validation, duplicate identity, and immutable
  replacement enforcement;
- active/archived eligibility, deterministic ranking, and match evidence;
- bounded remember/revision first-match content refusal, canonical source field,
  broad reason classification, and no retained rejected value before storage
  access;
- active/archived revision and exact no-op semantics;
- uncertain post-publication replacement durability;
- mutation-disabled-by-default lifecycle policy.

The shared domain imports no MCP, FastAPI, or route modules. MCP Tool handlers
adapt domain inputs/results; they do not own record, storage, or retrieval truth.
Import-boundary tests enforce this dependency direction.

`memory_recall` validates a narrow query, exactly one required high-level memory
scope, an optional canonical namespace ID, and optional bounded free-form tags.
The seven scopes are `self`, `relationship`, `preference`, `practice`, `project`,
`knowledge`, and `agent`; each has an individual model-facing description and is
exposed through one explicit string enum in the Tool schema for broad client
compatibility. The namespace selector accepts no collection selector.

The handler validates the request and adapts it to its supplied typed recall
operation. With no namespace selector, the integration-backed operation discovers
compatible version-1 and canonical version-2 records scope-wide. With a valid
namespace selector, the store narrows candidate discovery to that exact canonical
version-2 namespace before applying the unchanged deterministic query/path/title/
content ranking and exact tag overlap; legacy records are excluded. A valid
unknown or missing selected namespace returns `no_matches`; an invalid selector
returns `invalid_request` / `invalid_namespace`. A selected symlink root is
skipped safely, while a selected non-directory is unavailable. Recall returns no
more than five records with match evidence and an inspect-compatible versioned
reference. Legacy references contain scope and ID; canonical references also
contain namespace ID and nullable collection ID. Recall never returns paths,
internal scores, provenance, or lifecycle metadata. Archived version-2 records
are excluded. Source and candidate-limit failures return stable Tool errors. Its
request log records selector presence but never its value.

The recall package is deliberately limited to `__init__.py`, `definition.py`,
and `handler.py`. Its definition derives the scope enum from the shared registry;
its handler owns MCP-specific argument/result semantics. Storage and ranking do
not live under the Tool package.

`memory_list` is a separate read-only Tool with the same three-file package
shape. Its schema publishes scope, namespace, collection, page-size, and cursor
fields in top-level object properties so limited clients do not project an empty
argument object. Scope uses the same explicit seven-value string enum as recall.
Four mutually exclusive presence/exclusion branches retain strict scope-wide and
canonical namespace selection for initial and continuation requests. Collection
selection is omission-sensitive: absent means every collection state, null means
collectionless only, and a string means one exact collection. Initial requests
accept an optional page size from 1 through 100; continuations repeat the exact
selector with an opaque cursor and omit page size. The Tool accepts no query,
path, content, cross-scope selector, or arbitrary filter.

The handler validates independently, creates a `MemoryListSelector`, and invokes
its supplied typed list operation only after validation. The integration-backed
operation delegates to `MemoryService.list_memories()`, whose store narrows to
the deterministic scope, namespace, collectionless level, or exact collection
before applying the candidate bound. The shared listing domain orders legacy
records by ID with an unexposed path tie-breaker, orders canonical records by
namespace/collection/ID, marks duplicate legacy references ambiguous across the
complete snapshot, and slices only after ordering and annotation.

Listing cursors contain only a version, process marker, keyed selector/snapshot
digests, next offset, and fixed page size under an HMAC. Relative paths and raw
file fingerprints contribute only to the keyed snapshot digest and are never
returned. A process-shared in-memory codec permits continuation across service
instances in the single-process server; restart, selected snapshot changes, or
foreign process markers make the cursor stale. Current-process authentication,
shape, selector, and pagination failures make it invalid. There is no persistent
cursor key, snapshot store, manifest, or index.

Results are `status: ok` even when empty and contain compact list items plus page
number, returned count, total count, total pages, truncation state, and nullable
next cursor. Legacy items expose only reference, nullable title, and
inspectability. Canonical items additionally expose kind and lifecycle state.
Content, tags, labels, language, provenance, timestamps, lifecycle revision,
paths, fingerprints, scores, and match evidence remain absent. Bounded request,
cursor, candidate, source, and internal failures never return partial pages.
Logger `mcp.memory_list` emits one terminal event containing only allowlisted
outcome, selector-presence, count, page, and stable error metadata.

`memory_inspect` is likewise limited to `__init__.py`, `definition.py`, and
`handler.py`. Its strict schema accepts one reference discriminated by schema
version. Version 2 requires scope, namespace ID, nullable collection ID, and
canonical ID; version 1 requires scope and legacy ID. It accepts no filesystem
path, storage root, broad selector, query, lifecycle state, or mutation field.

The inspect handler validates before invoking its supplied typed inspect
operation. The integration-backed operation delegates exact lookup to the
existing read-only `MemoryService.inspect()` and `FilesystemMemoryStore.get()`
contracts. Canonical results contain a record-derived reference and all
user-visible version-2 fields. Legacy results contain a versioned reference and
only ID, nullable title, content, and tags. Archived canonical records remain
inspectable without a lifecycle selector. Missing, ambiguous, candidate-limit,
unsafe/unavailable-source, validation, and unexpected failures map to bounded
Tool errors. Inspection does not initialize the root or change files. Logger
`mcp.memory_inspect` emits one content-free terminal event containing only
allowlisted outcome/reference metadata; shared skip warnings omit candidate
paths.

For a canonical project event, the complete inspection projection includes its
strict structural `occurred_at`. Inspection remains exact and does not add a
chronological selector or ordering mode.

`memory_remember` is also limited to `__init__.py`, `definition.py`, and
`handler.py`. Its schema derives seven scope branches, namespace kinds, memory
kinds, and per-(scope, kind) writing guidance from the shared domain. It accepts
the nine unconditional scope, namespace, optional collection, kind, language,
title, content, tags, and public-origin fields, plus structural `occurred_at`
exactly for project events. It accepts no path or server-owned identity,
provenance mechanism, persistence timestamp, or lifecycle field.

The schema publishes ten caller-visible top-level properties—nine unconditionally
required fields plus optional `occurred_at`—and rejects additional properties.
This preserves a complete flat field bag for clients that discard composition.
The seven full `oneOf` branches retain strict scope-specific namespace-kind and
memory-kind constraints; only the project branch admits occurrence time and its
condition requires it for event while rejecting it for every project non-event.
Each complete branch renders its ordered canonical kind guidance, and the flat
top-level kind description groups all guidance by scope. Public origin is
caller-supplied provenance context, not consent; the MCP client supplies the
separate enforceable per-call approval boundary and the server assigns
`recorded_via`.

All eight public `memory_*` schemas include `agent`; generated clients that model
scope as a closed union must refresh their schemas. The agent branch has namespace
kind `agent` and kinds `persona`, `policy`, `checklist`, and `failure_mode`; it is
non-event and therefore never accepts `occurred_at`. Agent records are ordinary
scope records under the existing consent, no-secrets, recall, list, inspect,
revise, archive, restore, forget, storage, structured-reference, and gate
contracts. They grant no special cross-agent authority, routing, or isolation,
and scope-wide listing retains its ordinary semantics.

The remember handler validates a `MemoryDraft`, enforces its Tool-level mutation
gate, and then invokes its supplied typed remember operation. The
integration-backed operation constructs the enabled service only at that point.
The service applies the shared content policy before duplicate discovery,
generates all operational fields, copies an event's parsed occurrence time, and
uses the existing atomic store. Event duplicate identity includes occurrence
time; non-events use a null internal key position without changing their prior
equality. Store replacement treats occurrence time as immutable, while revision
and lifecycle replacements preserve it. The handler returns only status,
structured reference, and lifecycle for `remembered`, `already_exists`, or
`existing_archived`; failures are bounded Tool errors. Logger
`mcp.memory_remember` emits one content-free terminal event and never records
submitted memory text, labels, tags, paths, exception messages, or tracebacks.
For content refusal, the handler maps canonical namespace/collection source
fields to bounded top-level caller-visible names and returns that field, one
broad reason, and stable safe-retry guidance. It does not add refusal field or
reason to the minimized log event.

Event is a kind under `project`, not a separate scope or a separate temporal
resource family. There is no timeline/membership model, chronological query,
causal inference, automatic state supersession, or append-only-event guarantee.
The larger many-to-many temporal model remains deferred until demonstrated by a
concrete workflow.

`memory_revise` has the same three-file public package shape plus a private,
capability-free `_memory_revise.py` adapter. Its flat canonical-only request
requires the exact reference, positive expected revision, and complete
replacement values for namespace label, title, content, and tags. Collection
label is required as a nullable replacement only when the immutable reference
contains a collection ID; a collectionless reference may omit the structurally
nonexistent label and the adapter supplies null. Nullable scalar types and field
descriptions remain visible without composition-only projection. The request
accepts no path, legacy identity, patch language, relocation, reclassification,
lifecycle target, provenance replacement, timestamp, or model confirmation.

The private adapter parses the exact reference before enforcing conditional
replacement completeness, owns strict normalization, minimal projection, result
consistency, field-aligned bounded errors, and content-free logging. Literal
string `"null"` remains text. The public handler supplies its narrow revise
operation to that adapter; service/store construction remains in the
integration-backed operation. The shared domain applies content policy before
storage access, checks the exact revision, detects normalized no-ops, preserves
immutable identity/metadata and lifecycle state, and atomically replaces the
same file only on change. Changed results are `revised`; no-ops are
`already_current`. Archived records remain archived and recall-excluded.
Revision retains no patch, backup, tombstone, or hidden prior content.

`_memory_content_refusal.py` is a private capability-free MCP helper containing
only the stable remediation message shared by remember and revision. The revise
adapter maps canonical `namespace.label` and `collection.label` refusal fields
to `namespace_label` and `collection_label`; direct title/content/tag fields are
unchanged. Both Tools expose only the deterministic first field and one of the
five broad public reasons. They never expose or retain the match, offset, regex,
provider-specific detector, fingerprint, or tag index, and their refusal logs do
not add field or reason metadata.

`memory_archive` and `memory_restore` are separate least-privilege Tools, each
with the same three-file public package shape. Their shared private
`_memory_lifecycle.py` adapter owns the canonical-only schema, strict request
parsing, minimal result projection, bounded error mapping, result consistency
checks, and content-free logging; it exposes no Tool or storage capability.

Each public handler validates through that adapter, enforces its Tool-level
mutation gate, and invokes only its supplied typed archive or restore operation.
The integration-backed operation constructs an enabled service after those
checks. Requests contain exactly one canonical version-2 reference and positive
exact-integer expected revision. They accept no path, legacy identity, record
content, target state, timestamp, or model confirmation. The shared service
checks revision before lifecycle idempotency and atomically replaces the same
file only for a state change. Current target state returns `already_archived` or
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

The public handler validates, enforces its Tool-level mutation gate, and invokes
only its supplied typed forget operation. The integration-backed operation
constructs an enabled service after those checks. Revision is checked before
archived-state eligibility. Definitive identity, revision, state, safe-path, and
bounded-fingerprint checks occur at the store deletion point under a mutation
lock shared by in-process stores for the same absolute root. Successful deletion
unlinks one source file, syncs its parent, leaves directories intact, and returns
only `forgotten` plus the same canonical reference. There is no tombstone or
idempotent repeat result; later exact access returns not found.

A failure after unlink but before confirmed parent-directory sync raises a
distinct uncertain-outcome domain error. The MCP result instructs the caller to
inspect the same reference before any newly approved retry. Logger
`mcp.memory_forget` emits one terminal event containing only bounded outcome,
code/field, schema version, and scope. Multi-process/external last-instruction
races and secure erasure of journals, snapshots, backups, or external copies are
outside this local filesystem contract.

Tool availability is startup-fixed. The in-process Mnemosyne configuration
boundary owns resolution of supplied values for
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

The Mnemosyne configuration layer performs no initialization. It bounds the
file to 16 KiB of UTF-8 TOML, rejects unknown structure, symlinked or
non-regular sources, metadata replacement during open, unreadable sources, and
group/world-writable POSIX application directories or files.
Descriptor-relative/no-follow access is used where supported, and failures
expose only stable non-content-bearing codes/messages. The immutable startup
registry always contains `list_tools`,
`memory_recall`, `memory_list`, and `memory_inspect`, in that order; appends
archive and restore together when their pair gate is enabled; appends remember
when its independent gate is enabled; appends revise when its independent gate
is enabled; and appends forget last when its independent gate is enabled. Every
definition and dispatch handler is connected
as a pair, so no placeholder Tool is advertised. The same
startup selection drives MCP `tools/list`, the `list_tools` Tool, and dispatch
until restart. No HTTP route or CLI entrypoint owns this policy, and server
enablement remains separate from per-call client consent.

`list_tools` prefixes its selected names with the static `SERVER_VERSION`, which
is `mymcp 0.3.0` and is kept equal to the package version. The marker is also
returned by initialize and `/version`; the
public-host cutover was released as `mymcp 0.2.0`. This marker identifies stale
processes after public-contract updates; it is not a dynamic Git identifier or a
replacement for reconnecting Tool discovery.

The registry also derives an immutable Tool-name-to-input-schema mapping from
that same startup selection. Known Tool calls pass through the shared
schema-aware one-layer argument normalizer before their paired handler; unknown
Tool behavior is unchanged. This keeps client serialization compatibility in
the MCP layer rather than in memory-domain models or individual Tool handlers.

## Filesystem Retrieval

The default root is `~/.mnemosyne/memory`; the operator may set
`MNEMOSYNE_MEMORY_ROOT`. Recall, listing, and inspection never accept a path from
an MCP request. Beneath the root, the canonical scope names are fixed top-level
directories. Legacy version-1 files remain readable without rewriting. New
canonical records use schema version 2 and derive their location from scope,
namespace ID, optional collection ID, and server-generated memory ID.

The filesystem store initializes directories lazily only on canonical create.
After validating that the deterministic record parent is beneath the configured
root, it collects a missing root-ancestor chain back to the nearest existing
directory and creates each missing component in parent-to-child order. Newly
created directories use mode `0700` on POSIX, existing directories are not
chmodded, and atomic record files retain mode `0600`. Symlink/non-directory
conflicts and creation failures remain bounded domain errors. Settings
resolution, startup, recall, listing, inspection, disabled or invalid
remember/revise calls, and content-policy refusal do not create the root or its
parents.

Discovery rejects symlinks, limits nesting to four directories, limits files to
64 KiB, and fails rather than returning a partial result when the selected
discovery root exceeds 1,000 candidate JSON files. Invalid individual records
are skipped with warnings limited to scope and a bounded reason; candidate paths
are not logged. Files remain the source of truth and are directly inspectable and
deletable by the user.

Selected-root contracts differ by read operation. For recall, a selected canonical
namespace narrows discovery before ranking: a missing or symlinked selected root
yields no matches, while a selected non-directory is unavailable. For listing, a
selected root symlink is unsafe, a non-directory is unavailable, and a genuinely
missing container is a successful empty inventory. Scope-wide listing retains the
full-scope bound. Namespace-wide listing counts only that namespace;
collectionless and exact-collection selectors scan only direct JSON files at
their canonical level. Candidate counting occurs before record parsing, and
canonical selectors exclude legacy records after bounded discovery as defense in
depth.

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

### `mymcp/settings.py`

Contains only stable server/process identity constants used across application
assembly, routes, MCP initialization, and `list_tools`: `SERVER_NAME`,
`SERVER_VERSION`, `PROTOCOL_VERSION`, and `APP_TITLE`. It owns no memory root,
mutation gate, environment name, local-file parser, or memory settings model.

### `mymcp/plugins/mnemosyne/configuration.py`

Owns the in-process Mnemosyne operator-configuration contract: dynamic
resolution of the memory root and strict environment-first/fixed-file startup
parsing for independent remember, archive/restore, revise, and forget
enablement. Each supplied environment value overrides only its matching
setting; unresolved values use at most one strict file read. It owns the fixed
local settings path, schema, bounded source checks, and stable configuration
failures without creating or editing operator configuration. It imports no MCP
Tool package, FastAPI, or route module. This plugin-owned boundary is not a
dynamic configuration system or public plugin contract.

### `mymcp/cli.py`

Contains console entrypoints for normal and development server startup, plus
the test-suite runner when the `test` extra is installed.

## Design Rule

Keep FastAPI routes thin. Put MCP meaning under `mymcp/mcp/`.

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
- `mymcp/mcp/AGENTS.md` governs MCP protocol and tool work.
- `mymcp/routes/AGENTS.md` governs HTTP transport work.
