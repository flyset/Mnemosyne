# TRACK 006 [COMPLETED]: shared memory domain architecture

Track
- ID: TRACK_006
- Repository: Mnemosyne
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_006_COMPLETED_shared_memory_domain_architecture.md

Problems (PORE)
- P1: As a maintainer, I cannot add `memory_remember` or other lifecycle tools without importing from or duplicating `memory_recall` internals because canonical scopes, record validation, filesystem behavior, limits, errors, and retrieval types are currently owned by the recall Tool package.
- P2: As the user governing Mnemosyne, I cannot rely on memories remaining consistently organized and manageable across recall, creation, revision, inspection, and deletion because no complete shared record, identity, path, provenance, consent, or lifecycle architecture exists.
- P3: As an MCP model, I cannot use future memory tools consistently because their shared schema dimensions, scope contract, namespace rules, result identities, and error semantics have not been defined from one canonical source.

Objective
- Define the complete shared memory-domain architecture, establish tool-independent canonical components under `mnemosyne/memory/`, and migrate recall to those components without changing its public MCP behavior.

Non-negotiables
- Complete the coherent memory model, filesystem projection, lifecycle semantics, consent boundary, and package architecture before implementation begins; incremental code must conform to that model rather than substitute for it.
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Preserve local-first, single-user, least-privilege, explicit-tool, visible-memory, easy-deletion, and user-governed principles.
- Canonical memory concepts must not be owned by an individual MCP Tool package.
- Recall, remember, inspect, revise, and forget must derive shared scopes, records, paths, validation, storage behavior, and domain errors from one source.
- MCP Tool handlers remain thin adapters over the shared memory domain; HTTP routes remain transport-only.
- Preserve the current `memory_recall` Tool name, input schema, scope descriptions, validation errors, retrieval results, ranking behavior, logs, and filesystem compatibility unless an explicitly documented migration decision requires a public change.
- Durable mutation requires an explicit user-approved MCP client execution boundary; a model-supplied boolean is not evidence of consent.
- Do not add unrestricted filesystem access, arbitrary client-supplied paths, shell execution, external memory services, hidden conversation extraction, or secret storage.
- Do not expose `memory_remember`, `memory_inspect`, `memory_revise`, or `memory_forget` during this Track; their complete contracts must be designed before separate implementation Tracks.
- Never store personal memory fixtures outside temporary automated or direct-protocol validation roots.

Acceptance criteria
- [x] A1) [P1, P3] One canonical shared scope model owns every scope name, description, validation rule, and directory mapping used to derive MCP schemas and runtime behavior.
- [x] A2) [P2, P3] The canonical memory-record model defines identity, schema version, scope, namespace/subject, collection, kind, language, content, tags, provenance, timestamps, lifecycle, and extension boundaries without collapsing independent dimensions, while consent remains an execution policy rather than an unverifiable record claim.
- [x] A3) [P2] Deterministic path derivation is defined for every scope, including stable identifiers, human-readable labels/aliases, directory renames, traversal safety, and the relationship between record metadata and filesystem location.
- [x] A4) [P2] Complete lifecycle semantics are documented for create, inspect, recall, revise/supersede, duplicate, contradiction, conflict, forget, and physical deletion behavior.
- [x] A5) [P2] Durable-write consent is assigned to an enforceable MCP-client approval boundary, with explicit behavior for approved, denied, unavailable, and non-interactive clients.
- [x] A6) [P1, P3] A documented package architecture assigns scopes, records, paths, storage, errors, retrieval, and MCP adaptation to stable owners with no dependency from the shared domain onto a Tool package.
- [x] A7) [P1] Shared domain components are implemented under `mnemosyne/memory/`, and `memory_recall` no longer owns canonical scopes, record parsing, filesystem storage rules, or retrieval-domain types.
- [x] A8) [P1, P3] Recall is migrated through focused TDD chunks and preserves its existing public Tool definition, validation, logging, matching/no-match/error results, filesystem compatibility, and deterministic ranking.
- [x] A9) [P1, P2] Automated tests cover shared scope/schema derivation, record round-tripping, path and storage safety, migration compatibility, package boundaries, and end-to-end recall behavior.
- [x] A10) [P2, P3] `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` document the canonical domain, source-of-truth boundaries, lifecycle design, consent model, package ownership, and future Tool relationships.
- [x] A11) [P1, P2, P3] The architecture is sufficient for a subsequent `memory_remember` Track to implement writes without redefining scopes, records, paths, storage primitives, consent semantics, or shared errors.

Why now / impact
- Track 005 made recall functional but necessarily located shared memory concepts inside `memory_recall`. Adding mutation on that foundation would either couple remember to recall or duplicate foundational contracts. Resolving ownership and the complete lifecycle design now prevents incompatible files, scopes, paths, and governance behavior from becoming durable user data.

Scope
- In scope:
  - Complete conceptual separation of scope, namespace/subject, collection, kind, content, tags, provenance, consent, lifecycle, identity, and retrieval policy.
  - Canonical scope definitions and reusable JSON Schema fragments/runtime validation.
  - A versioned memory-record model and compatibility policy for existing Track 005 records.
  - Scope-specific deterministic filesystem projection and stable identity/alias rules.
  - Shared storage boundaries, safe read/write interface design, atomicity, permissions, concurrency, conflict, and physical-deletion semantics.
  - Retrieval/index/source-of-truth boundaries and multilingual normalization policy.
  - Complete contracts and relationships for future remember, inspect, revise, forget, and existing recall capabilities.
  - MCP client approval requirements for durable mutation.
  - A new tool-independent `mnemosyne/memory/` package and behavior-preserving migration of recall.
  - Focused tests, direct recall checks, public documentation, and durable Track evidence.
- Out of scope:
  - Registering or exposing new MCP Tools.
  - Persisting memory through `memory_remember` or any other public mutation endpoint.
  - Creating real user memories, automatically extracting conversations, or silently inferring durable facts.
  - Implementing awareness providers, embeddings, external search, vector databases, encryption, multi-user tenancy, or remote synchronization.
  - Changing the existing memory root default solely for platform convention.

Milestones
- [x] M1) Resolve the complete memory-domain, filesystem, lifecycle, consent, and Tool-relationship design.
- [x] M2) Establish canonical shared memory components and migrate recall without public behavior changes.
- [x] M3) Validate and document that future lifecycle Tools can depend on the shared domain without recall coupling or contract duplication.

Risks / decisions
- Risk: Extracting only the current recall code could preserve its accidental boundaries and merely relocate technical debt.
- Decision: Design the complete lifecycle model first, then extract components according to intended ownership rather than current file shape.
- Risk: A single generic path hierarchy could mix scope with identity, collection, kind, or tags.
- Decision: Treat directory layout as a deterministic projection of separately modeled stable dimensions, with scope remaining the first fixed boundary.
- Risk: Human-readable directory names can change, while durable references must remain stable.
- Decision: Explicitly design stable IDs, display labels, aliases, and rename behavior before choosing scope-specific path rules.
- Risk: A `confirmed: true` field or two model calls could be mistaken for user consent.
- Decision: Durable mutation depends on MCP-client execution approval; server-side schemas may describe intent but cannot manufacture user consent.
- Risk: Designing every future Tool could cause premature implementation complexity.
- Decision: Complete shared contracts and lifecycle relationships in this Track, but expose no new Tool until a separate implementation Track.
- Risk: Moving code may accidentally change recall ranking or its public contract.
- Decision: Treat current Track 005 recall behavior and its 81-test baseline as a compatibility target; migration proceeds through focused characterization and TDD tests.
- Risk: Shared code under `mnemosyne/mcp/` would remain protocol-coupled and be difficult to reuse across lifecycle operations.
- Decision: Place tool-independent memory concepts under `mnemosyne/memory/`; keep MCP Tool definitions and result adaptation under `mnemosyne/mcp/tools/`.

Open questions
- [x] Q1) What exact canonical scope representation lets Tool schemas, runtime validation, directory mapping, and documentation derive from one source without coupling domain code to MCP?
- [x] Q2) What exact fields, constraints, versioning rules, extension policy, and round-trip guarantees define a canonical memory record?
- [x] Q3) Which dimensions are universal, and which namespace/subject/collection dimensions are scope-specific?
- [x] Q4) What controlled vocabularies or extensible identifiers define memory kind, collection, provenance, consent, and lifecycle state?
- [x] Q5) What deterministic directory and filename projection applies to each scope, and how are stable IDs separated from mutable labels and aliases?
- [x] Q6) How do files remain directly visible and deletable while manifests, aliases, indexes, or generated metadata avoid becoming competing sources of truth?
- [x] Q7) What are the exact create, inspect, revise/supersede, duplicate, contradiction, conflict, forget, and physical-deletion semantics?
- [x] Q8) What shared storage interface and error model supports bounded reads plus future atomic writes, permissions, concurrency, and crash recovery?
- [x] Q9) Which storage lifecycle primitives should be implemented in this Track versus only specified for subsequent Tool Tracks?
- [x] Q10) How do lexical normalization, tags, path terms, language, timestamps, lifecycle state, and future indexes interact with retrieval while preserving explainability?
- [x] Q11) What exact request/result/error contracts and dependency boundaries should recall, remember, inspect, revise, and forget use?
- [x] Q12) How is mandatory client approval configured and documented for mutation Tools, and what behavior is required when a client cannot enforce it?
- [x] Q13) How are existing version-1 files and current recall behavior migrated without rewriting user data or changing results unexpectedly?
- [x] Q14) What exact module layout, public interfaces, and import rules prevent circular dependencies and Tool-owned domain concepts?

Decision log
- Decision: Track 005's functional recall is the compatibility baseline, not the final ownership model.
- Decision: Canonical shared memory concepts will live under a tool-independent `mnemosyne/memory/` package.
- Decision: Scope names, descriptions, runtime validation, and directory mapping must have one canonical source shared by recall and all future lifecycle Tools.
- Decision: MCP Tool definitions and handlers adapt shared domain behavior; they do not own record or storage truth.
- Decision: Complete architecture precedes implementation, while implementation may still proceed through bounded TDD chunks after activation.
- Decision: The intended lifecycle includes remember, recall, inspect, revise, and forget as explicit capabilities with shared records and storage.
- Decision: Durable writes require per-call MCP-client approval after the exact proposed memory is visible to the user.
- Decision: A future write Tool will not accept arbitrary filesystem paths; structured domain fields will drive safe deterministic placement.
- Decision: `memory_remember` implementation begins only in a later Track after this shared foundation is complete.
- Decision (Q1): Define an ordered canonical registry of immutable scope definitions under `mnemosyne/memory/scopes.py`. Each definition owns the scope value, plain-language description, fixed directory name, and allowed namespace kinds. Domain code exposes definitions and parsing; MCP adapters derive their JSON Schema `oneOf` branches without the domain importing MCP code.
- Decision (Q1): The canonical values and descriptions remain exactly compatible with Track 005: `self`, `relationship`, `preference`, `practice`, `project`, and `knowledge` in their current order with their current model-facing descriptions.
- Decision (Q2): Existing files remain schema version 1. New canonical writes use schema version 2 and a fixed top-level object with no unknown fields: `schema_version`, `id`, `scope`, `namespace`, `collection`, `kind`, `language`, `title`, `content`, `tags`, `provenance`, `lifecycle`, `created_at`, and `updated_at`.
- Decision (Q2): Version-2 `collection` and `title` are explicitly `null` when absent, and `tags` is always an array. Canonical parsing and serialization round-trip the normalized record deterministically without adding or removing semantic fields.
- Decision (Q2): Memory IDs are server-generated as `mem_` plus 32 lowercase hexadecimal UUID4 characters. Namespace and collection IDs contain 1–64 lowercase ASCII letters, digits, `_`, or `-`, begin and end with an alphanumeric character, and never contain dots, separators, or traversal components.
- Decision (Q2): Namespace and collection labels are optional normalized Unicode text of at most 100 characters; title is optional normalized Unicode text of at most 200 characters; content is non-whitespace normalized Unicode text of at most 4,000 characters; tags are an always-present array of 0–10 normalized Unicode strings of at most 50 characters and are unique by normalized case-folded value.
- Decision (Q2): User-facing Unicode text normalizes to NFC and LF line endings without semantic rewriting. Version-2 timestamps are server-generated RFC 3339 UTC values. Unknown fields are rejected at every object level.
- Decision (Q3): Every version-2 record requires one namespace object with immutable `kind` and `id` plus an optional mutable descriptive label. Collection is an optional object with immutable `id` plus an optional mutable label. Namespace and collection remain distinct from kind and tags.
- Decision (Q3): Allowed namespace kinds are scope-specific: `self` uses `aspect`; `relationship` uses `person`, `group`, or `relationship`; `preference` and `practice` use `domain`; `project` uses `project`; and `knowledge` uses `topic`.
- Decision (Q4): Controlled record kinds are constrained by scope: `self` uses `attribute`; `relationship` uses `perspective` or `summary`; `preference` uses `preference`; `practice` uses `practice`; `project` uses `decision`, `constraint`, `state`, `question`, `reference`, or `summary`; and `knowledge` uses `reference` or `summary`. Kinds are metadata and never path segments.
- Decision (Q4): Provenance contains `origin` and server-controlled `recorded_via`. Origins are `explicit_user_statement`, `user_approved_proposal`, `manual`, or `import`; recording mechanisms are `memory_remember`, `filesystem`, `migration`, or `import`. Provenance stores no prompt, transcript, session content, or false consent attestation.
- Decision (Q4): Version-2 language is always present, defaults to `und`, and accepts normalized BCP-47-style identifiers including `und` and `mul`. Language guides future normalization providers but is never a hard recall filter.
- Decision (Q4): Lifecycle contains `state` (`active` or `archived`) and a positive integer `revision`. `forgotten` is never persisted; forgetting means physical deletion. Consent is an external mutation-execution precondition because current MCP calls carry no verifiable approval attestation.
- Decision (Q5): Derive version-2 paths exclusively from structured fields as `<scope>/<namespace-id>/<collection-id?>/<memory-id>.json`. Scope, namespace ID, optional collection ID, and memory ID form a structured reference; clients never supply paths.
- Decision (Q5): Scope, namespace, and collection metadata inside a version-2 record must agree with its location. A mismatch is invalid and skipped rather than silently moved. IDs are immutable; mutable labels never rename directories. Reclassification or relocation requires a future explicit capability rather than hidden revise behavior.
- Decision (Q5): Version-2 records are self-contained. Namespace and collection labels live in records as descriptive snapshots; no required namespace manifest, alias database, or competing metadata source is introduced.
- Decision (Q6): JSON memory files remain the only durable memory source of truth. No persistent content-bearing index is introduced while bounded scanning remains sufficient. Any future index must be disposable, fully regenerable, and unable to retain forgotten content.
- Decision (Q7): Exact duplicate identity compares scope, namespace kind/ID, collection ID, record kind, normalized title, normalized content, and normalized tag set while ignoring generated ID, timestamps, provenance, revision, and label differences. An active duplicate returns `already_exists`; an archived duplicate returns `existing_archived`; neither creates a file.
- Decision (Q7): Semantic similarity and contradiction detection never mutate automatically. Suspected conflicts are presented for explicit revise, archive, restore, remember, or forget action.
- Decision (Q7): Revise atomically replaces the same file and stable ID after an `expected_revision` check, increments revision, updates `updated_at`, and retains no hidden prior content. Mutable fields are title, content, tags, and descriptive labels; scope, namespace kind/ID, collection ID, kind, ID, and `created_at` remain immutable.
- Decision (Q7): Archive and restore are explicit lifecycle operations with revision checks. Forget physically deletes the file after a revision check, creates no tombstone, retains no deleted content, and leaves empty organizational directories intact.
- Decision (Q8): Define shared structured errors for invalid scope/namespace/collection/kind/record/reference, not found, ambiguous legacy reference, revision conflict, storage unavailable, unsafe path, candidate limit, write conflict, and mutation disabled. MCP handlers map them to Tool-specific results without redefining domain meaning.
- Decision (Q8): The shared store receives an explicit root and owns scope/path resolution, file limits, parsing/serialization, safe discovery, atomic persistence, revision checks, and deletion. It does not read environment variables or import MCP modules.
- Decision (Q8): Under the single-user/single-server model, in-process mutation locking serializes writes. Create uses a same-directory temporary file and no-overwrite atomic publication; revise uses an expected-revision check and same-directory atomic replacement; delete checks revision before unlinking. External changes detected before publication return a conflict. Multi-process writers are unsupported until a later threat model defines cross-process locking.
- Decision (Q8): Mutation-created directories use user-only permissions and files use user-only read/write permissions subject to platform support. Temporary crash files are never recall candidates and may be safely cleaned without reading them as memory.
- Decision (Q9): Track 006 implements shared read/discovery plus create, replace, archive/restore-state, delete, duplicate-key, and lifecycle service primitives against temporary roots, but exposes no mutation MCP Tool. A later remember Track provides client permission configuration and thin MCP adaptation rather than redefining storage behavior.
- Decision (Q10): Preserve Track 005 ranking weights and deterministic tie-breaking exactly. Version-2 recall includes only active records; valid version-1 records remain recallable as legacy-active records. Namespace and collection IDs contribute only through existing path-term behavior; labels, kind, language, provenance, timestamps, and lifecycle do not add hidden score.
- Decision (Q10): The default normalizer preserves current Unicode case-folding, alphanumeric tokenization, and English stop-word behavior. A shared tokenizer/normalizer interface permits future language-specific implementations without changing records or Tool contracts; no translation, stemming, synonym inference, or semantic search is introduced here.
- Decision (Q11): The intended explicit Tool family is recall, inspect, remember, revise, archive, restore, forget, and a future dedicated relocate/reclassify capability. Tools exchange structured references and domain fields, never paths. Inspect is read-only; every other lifecycle operation except recall is independently callable and narrowly scoped.
- Decision (Q11): Remember accepts approved semantic fields but not ID, timestamps, revision, lifecycle state, path, or `recorded_via`. Revise changes only approved mutable fields. Archive, restore, and forget require a structured reference and expected revision. Exact achieved states return normal idempotent outcomes; validation, lookup, ambiguity, revision, storage, and policy failures return stable Tool errors.
- Decision (Q12): Mutation Tools are disabled by default and require explicit operator enablement plus per-call MCP-client approval. Approval causes a request to reach Mnemosyne; denial produces no server call. Clients that cannot enforce per-call approval must leave mutation Tools disabled; a model-provided confirmation field is never accepted as consent.
- Decision (Q12): Future mutation logs contain only operation, outcome, record ID, scope, namespace ID, optional collection ID, and kind. They never contain title, content, tags, deleted data, absolute paths, or complete Tool arguments.
- Decision (Q13): Parse version-1 files through a dedicated compatibility model. Scope and path terms continue deriving from their location, no namespace/kind/provenance/timestamp facts are invented, no background rewrite occurs, and current recall output/ranking remains unchanged.
- Decision (Q13): Future mutation Tools do not revise version-1 files in place. Revising a legacy memory requires an explicit approved migration to version 2. Legacy inspect/forget uses scope and ID with bounded scanning; duplicate IDs return `ambiguous_reference` rather than exposing or guessing a path.
- Decision (Q14): The shared package layout is `mnemosyne/memory/{__init__,scopes,records,normalization,paths,errors,store,retrieval,service}.py`. Its `__init__.py` provides stable domain exports only. `mnemosyne.memory` imports no MCP or route code; MCP memory Tool packages import the shared domain and own only Tool definitions, argument adaptation, logging, and result encoding.
- Decision (Q14): `MemoryService` owns recall, inspect, remember, revise, archive, restore, forget, duplicate, and lifecycle policy. `FilesystemMemoryStore` owns discover, get, create, replace, and delete persistence. Clock and ID generation are injected for deterministic tests.
- Decision (S3): Canonical version-2 text normalization converts CRLF/CR to LF, applies Unicode NFC, and trims outer whitespace. Tag normalization additionally collapses internal whitespace while preserving display case; uniqueness and duplicate identity use case-folded tag values.
- Decision (S4): Shared direct lookup rejects symlinks in every scope-relative path component before checking or reading the final file; discovery continues to reject symlink files and subdirectories without following them.
- Decision (S5): The store re-parses serialized version-2 records before publication and rejects any direct dataclass instance that is not canonical. The service serializes complete lifecycle operations, including duplicate discovery plus create, so concurrent calls through one server service cannot create duplicate memories.
- Decision (S5): Temporary-file creation closes descriptors and removes partial files on write or file-sync failure. Durable publication uses user-only temporary files, same-directory atomic no-overwrite linking for create, fingerprint conflict detection, and atomic replacement for revision/state changes.
- Decision (S6): Shared retrieval removes the fixed scope-directory prefix before path tokenization so the scope name itself cannot add relevance. It preserves every Track 005 score weight, stop word, term/tag evidence rule, tie-breaker, and five-result limit while excluding archived version-2 records.

Plan (execution steps)
- [x] S1) Resolve Q1-Q14 and record the complete canonical domain, filesystem, lifecycle, consent, migration, and package contracts.
- [x] S2) Move Track 006 to ACTIVE (folder, filename, title, and current path status).
- [x] S3) Execute one TDD chunk for canonical shared scopes, schema derivation, Unicode/language normalization, version-1 compatibility types, and version-2 records/drafts/revisions/references under `mnemosyne/memory/`.
- [x] S4) Execute one TDD chunk for shared safe path projection, bounded discovery/get behavior, domain errors, and Track 005 filesystem compatibility.
- [x] S5) Execute one TDD chunk for temporary-root-only atomic create/replace/archive/restore/delete primitives, duplicate identity, revision conflicts, and lifecycle service behavior.
- [x] S6) Execute one TDD chunk migrating deterministic retrieval, normalization, result bounding, and match evidence into the shared domain without changing ranking behavior.
- [x] S7) Execute one TDD chunk reducing `memory_recall` to MCP-specific schema/handler adaptation over `MemoryService`, preserving its public contract, and enforcing import-boundary tests.
- [x] S8) Run the full suite and whitespace validation, perform direct MCP compatibility checks against temporary approved fixtures, update public documentation and architecture inventory, and record evidence.
- [x] S9) Confirm all acceptance criteria and move Track 006 to COMPLETED with completion evidence.

Current inventory
- Commit `f17847f` completed Track 005 and is synchronized on `main`/`origin/main`; Track 006 changes are uncommitted.
- `mnemosyne/memory/scopes.py` now owns the ordered canonical scope enum, values, descriptions, fixed directory names, namespace-kind matrix, and runtime parsing.
- `mnemosyne/memory/normalization.py` now owns version-2 Unicode text, identifier, language, memory-ID, tag, and duplicate-tag-key normalization.
- `mnemosyne/memory/records.py` now owns version-1 compatibility records, the complete version-2 record envelope, controlled kinds/provenance/lifecycle values, scope-dimension validation, deterministic parsing/serialization, structured current and legacy references, approved drafts, complete mutable revisions, and duplicate identity.
- `mnemosyne/memory/errors.py` owns structured validation, unsafe-path, source-unavailable, candidate-limit, not-found, ambiguous-reference, revision-conflict, write-conflict, and mutation-disabled errors.
- `mnemosyne/memory/paths.py` owns canonical scope-directory lookup, structured-reference and record projection, relative-path safety, and version-2 record/location agreement checks.
- `mnemosyne/memory/store.py` owns bounded sorted scope discovery, safe version-1/version-2 parsing, path agreement, symlink/depth/size/candidate constraints, safe warnings, exact and legacy lookup, canonical pre-publication validation, private directory/file creation, same-directory temporary writes, atomic no-overwrite create, fingerprint/revision-checked replacement, physical current/legacy deletion, and crash-temp cleanup.
- `mnemosyne/memory/retrieval.py` now owns the Track 005-compatible tokenizer, stop words, deterministic weighted scoring, active/legacy eligibility, evidence, scope-relative path ranking, tie-breaking, and five-result bound for both record versions.
- `mnemosyne/memory/service.py` owns read-only scope-isolated recall and inspect plus mutation-disabled-by-default policy, injected clock/ID generation, serialized duplicate-aware remember, complete mutable-state revise, revisioned/idempotent archive/restore, and physical current/legacy forget outcomes.
- `mnemosyne/memory/__init__.py` provides stable record, scope, store, retrieval, and lifecycle-service exports without logic.
- `mnemosyne/mcp/tools/memory_recall/definition.py` derives its unchanged scope `oneOf` schema from the shared canonical registry.
- `mnemosyne/mcp/tools/memory_recall/handler.py` is an MCP-specific adapter that preserves query/scope/tags validation and logs, constructs a read-only shared store/service for the configured root, maps shared source/candidate errors to stable Tool errors, and serializes shared matches without paths, scores, or lifecycle metadata.
- `mnemosyne/mcp/tools/memory_recall/` now contains only `__init__.py`, `definition.py`, and `handler.py`; the Tool-owned `retrieval.py` and its duplicate tests are removed.
- `mnemosyne/settings.py` continues to own memory-root resolution; the recall handler supplies that root to the shared store without coupling the domain to environment configuration.
- `README.md` documents the shared-domain foundation, version-1 compatibility, complete canonical version-2 example/path, lifecycle/source-of-truth rules, absence of exposed mutation Tools, and future per-call client approval requirement.
- `docs/ARCHITECTURE.md` documents the `mnemosyne/memory/` package layout/responsibilities, one-way dependency boundary, shared recall orchestration, v1/v2 storage, lifecycle primitives, and future thin mutation adapters.
- `docs/GLOSSARY.md` defines legacy/current records, namespace, collection, kind, language-bearing record dimensions, provenance, lifecycle, structured references, shared domain, mutation, and client-enforced consent.
- `tests/memory/test_scopes.py`, `test_normalization.py`, and `test_records.py` cover the canonical scope contract, unchanged MCP schema derivation, strict normalization and constraints, version-1 compatibility, version-2 round trips and nested unknown-field rejection, dimension matrices, timestamps/lifecycle, structured references, drafts/revisions, and duplicate identity.
- `tests/memory/test_paths.py` covers deterministic collection/no-collection projection, canonical scope directories, record/location agreement, mismatches, traversal, and absolute-path rejection.
- `tests/memory/test_store.py` covers sorted scope-isolated v1/v2 discovery, missing sources, archived inspectability, safe invalid/path-mismatch warnings, depth/size/symlink/candidate bounds, exact current lookup, unique/ambiguous/missing legacy lookup, unreadable sources, and direct-lookup ancestor-symlink rejection.
- `tests/memory/test_store_mutations.py` covers private atomic creation, canonical revalidation, no overwrite, symlink-parent rejection, failed-sync temporary cleanup, expected-revision replacement, external fingerprint conflict, physical current/legacy deletion, revision conflicts, no hidden prior content, no tombstones, and retained empty organization directories.
- `tests/memory/test_service.py` covers disabled-by-default mutation, injected operational fields, active/archived duplicate outcomes, concurrent duplicate serialization, read-only inspection while disabled, mutable-only revision, stale revisions, revisioned/idempotent archive/restore, and physical current/legacy forget.
- `tests/memory/test_retrieval.py` covers every Track 005 score/evidence/order rule, Unicode and punctuation handling, stop words, record-tag terms, positive-score and result bounds, archived exclusion, scope-prefix exclusion, v1/v2 content equivalence, and read-only scope isolation through `MemoryService`.
- `tests/memory/test_import_boundaries.py` enforces that the shared domain imports no MCP, route, or FastAPI modules and that recall contains only adapter modules importing the shared service/store.
- `tests/mcp/test_memory_recall.py` now covers unchanged version-1 behavior plus active version-2 serialization, archived exclusion, shared-error mapping, package re-exports, exact logs, and all stable validation contracts; duplicate recall-owned retrieval tests are removed.
- `memory_recall` remains the only exposed memory Tool. Shared remember/inspect/revise/archive/restore/forget domain behavior now exists only behind a mutation-disabled service and temporary-root tests; no mutation MCP Tool, permission configuration, real memory write, manifest, alias database, or persistent index exists.
- Existing version-1 memory files contain required `schema_version`, `id`, and `content`, plus optional `title` and `tags`; scope and path-derived context are not represented inside the record.
- The consolidated current automated suite passes 186 tests; isolated direct MCP validation confirms unchanged Tool discovery, version-1 recall, active version-2 recall, archived exclusion, bounded public results, and absence of mutation Tools.

Artifacts
- Design discussion: current development session after completing and live-testing Track 005.
- Baseline implementation: commit `f17847f` (`Add filesystem memory retrieval`).
- S1 architecture discussion: canonical scope/record dimensions, scope-specific namespaces and kinds, version-2 records, deterministic paths, source-of-truth files, lifecycle semantics, consent boundary, future Tool family, language/retrieval policy, shared package APIs, and version-1 migration.
- S3 TDD red evidence: `PYENV_VERSION=3.13.5 python -m pytest tests/memory/test_scopes.py tests/memory/test_normalization.py tests/memory/test_records.py` failed during collection in all three modules because `mnemosyne.memory` did not exist.
- S3 TDD green evidence: after the smallest shared scope, normalization, record, validation-error, and recall scope-consumer implementation, the same focused command passed all 72 tests.
- S3 focused compatibility evidence: `PYENV_VERSION=3.13.5 python -m pytest tests/memory tests/mcp/test_memory_recall.py tests/mcp/test_memory_retrieval.py tests/mcp/test_registry.py tests/routes/test_mcp.py` passed all 142 tests.
- S3 refactor: made enum parsing type-preserving without changing record behavior.
- S3 full validation evidence: `PYENV_VERSION=3.13.5 python -m pytest tests` passed all 153 tests; tracked and new-file whitespace validation passed.
- S4 TDD red evidence: `PYENV_VERSION=3.13.5 python -m pytest tests/memory/test_paths.py tests/memory/test_store.py` failed during collection because the shared path/store errors and modules did not exist.
- S4 TDD green evidence: after the smallest deterministic path, domain-error, and bounded read-store implementation, the same focused command passed all 20 tests.
- S4 hardening red evidence: direct `get()` followed a symlinked namespace directory, so the focused ancestor-symlink test failed as expected.
- S4 hardening green evidence: after component-by-component symlink rejection, the complete S4 focused suite passed all 21 tests.
- S4 full validation evidence: `PYENV_VERSION=3.13.5 python -m pytest tests` passed all 174 tests; tracked and new-file whitespace validation passed.
- S5 TDD red evidence: `PYENV_VERSION=3.13.5 python -m pytest tests/memory/test_store_mutations.py tests/memory/test_service.py` failed during collection because mutation errors and service APIs did not exist.
- S5 TDD green evidence: after the smallest atomic store and mutation-disabled lifecycle service implementation, the focused command passed all 19 initial tests.
- S5 canonical/concurrency hardening red evidence: direct invalid dataclasses were published before read-back rejection, and concurrent remember calls overlapped duplicate discovery.
- S5 canonical/concurrency hardening green evidence: canonical re-parsing before publication and service-level mutation serialization passed the expanded 21-test focused suite.
- S5 crash-cleanup hardening red evidence: a forced temporary-file `fsync` failure left a partial `.tmp` file.
- S5 crash-cleanup hardening green evidence: exception-safe descriptor/temp cleanup passed the final 22-test focused suite.
- S5 full validation evidence: `PYENV_VERSION=3.13.5 python -m pytest tests` passed all 196 tests; tracked and new-file whitespace validation passed.
- S6 TDD red evidence: `PYENV_VERSION=3.13.5 python -m pytest tests/memory/test_retrieval.py` failed during collection because `mnemosyne.memory.retrieval` did not exist.
- S6 TDD green evidence: after the smallest shared eligibility, tokenizer, ranking, evidence, bounding, and service recall implementation, the focused command passed all 11 tests.
- S6 focused compatibility evidence: `PYENV_VERSION=3.13.5 python -m pytest tests/memory/test_retrieval.py tests/mcp/test_memory_retrieval.py tests/mcp/test_memory_recall.py tests/routes/test_mcp.py` passed all 79 tests, including direct old/new ranking characterization.
- S6 full validation evidence: `PYENV_VERSION=3.13.5 python -m pytest tests` passed all 207 tests; tracked and new-file whitespace validation passed.
- S7 TDD red evidence: `PYENV_VERSION=3.13.5 python -m pytest tests/mcp/test_memory_recall.py tests/memory/test_import_boundaries.py` produced the expected five failures covering active version-2 recall, shared error mapping, adapter-only package shape, and shared service/store imports.
- S7 TDD green evidence: after migrating the handler to a read-only `MemoryService(FilesystemMemoryStore(...))`, mapping shared errors, serializing shared matches, and removing Tool-owned retrieval code/tests, `PYENV_VERSION=3.13.5 python -m pytest tests/mcp/test_memory_recall.py tests/memory/test_import_boundaries.py tests/memory/test_retrieval.py tests/mcp/test_registry.py tests/routes/test_mcp.py` passed all 60 tests.
- S7 ownership review: repository search found no obsolete `memory_recall.retrieval`, `discover_records`, or `rank_records` imports; recall contains only its public re-export, Tool definition, and handler adapter.
- S7 full validation evidence: `PYENV_VERSION=3.13.5 python -m pytest tests` passed the consolidated 186-test suite; whitespace validation passed.
- S8 final automated validation evidence: after public documentation updates, `PYENV_VERSION=3.13.5 python -m pytest tests` passed all 186 tests and `git diff --check` passed.
- S8 configured-client evidence: the configured MCP connection was unavailable, so no result was claimed from it.
- S8 direct MCP evidence: an isolated local server used one legacy v1 preference fixture, one active v2 project fixture, and one archived v2 knowledge fixture. `tools/list` exposed only `list_tools` and the unchanged `memory_recall`; v1 and active-v2 calls returned `status: ok` with expected content and match evidence but no paths, scores, provenance, or lifecycle metadata; the archived-only query returned `status: no_matches`.
- S8 cleanup evidence: the temporary server stopped and its isolated root, three fixtures, and server log were removed; no `mnemosyne-s8.*` path remained.
- S8 documentation review: repository search found no stale current-document claim that recall owns retrieval or reads only version-1 records; historical completed-Track evidence remains intentionally unchanged.

Completion notes
- Track moved to ACTIVE after the complete shared domain, filesystem, lifecycle, consent, migration, and package contracts were resolved; implementation has not started.
- S3 established the canonical shared scope and versioned-record foundation, migrated recall scope schema/runtime/directory consumers to it without public changes, and created no runtime memory data.
- S4 established deterministic safe paths and the shared bounded read store for compatible version-1 and canonical version-2 files, including hardened exact lookup, without changing recall or creating runtime memory data.
- S5 established mutation-disabled shared lifecycle primitives with private atomic writes, duplicate/conflict/revision policy, archive/restore, and physical deletion entirely under temporary automated-test roots; no mutation Tool or real memory data was created.
- S6 established shared deterministic recall across active version-2 and legacy version-1 records with exact Track 005 ranking compatibility; MCP still uses its old adapter until S7.
- S7 migrated the public recall adapter fully onto the shared store/service, added active-v2 and archived-state behavior, removed Tool-owned domain/storage/ranking code, and enforced one-way package dependencies without changing the Tool contract.
- S8 synchronized public documentation, passed final automated validation, and directly verified v1/v2/archived behavior plus the no-mutation-Tool boundary without retaining temporary data.
- S9 confirmed all eleven acceptance criteria and three milestones, synchronized the Track's folder, filename, title, and current path, and completed Track 006 with 186 passing tests and direct MCP compatibility evidence.
