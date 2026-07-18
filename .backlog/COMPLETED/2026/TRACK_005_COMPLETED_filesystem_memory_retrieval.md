# TRACK 005 [COMPLETED]: filesystem memory retrieval

Track
- ID: TRACK_005
- Repository: Mnemosyne
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_005_COMPLETED_filesystem_memory_retrieval.md

Problems (PORE)
- P1: As an MCP model, I cannot retrieve approved memory from a recall request because `memory_recall` always returns `retrieval_unavailable` and has no memory source.
- P2: As the user governing Mnemosyne, I cannot inspect, organize, or directly delete memories because no visible local filesystem layout or record format exists.
- P3: As a maintainer, I cannot evolve recall behavior cleanly because the Tool definition, validation, logging, result construction, and placeholder handler are all implemented in `memory_recall/__init__.py`.

Objective
- Retrieve a bounded set of relevant, user-visible JSON memory records from an allowlisted scope directory while refactoring `memory_recall` into explicit definition, handler, and retrieval modules.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Preserve local-first, single-user, least-privilege, explicit-tool, and user-governed memory principles.
- The MCP client never supplies a filesystem path; required `scope` selects one fixed allowlisted directory below the configured memory root.
- Do not add unrestricted filesystem access, shell execution, external retrieval services, embeddings, or a vector database.
- Reject path traversal and symlink escapes, and bound directory depth, file size, candidate count, and returned record count.
- Files are the source of truth and remain visible and directly deletable by the user.
- This Track implements read-only retrieval only; it does not create, update, or delete memory files.
- Do not store secrets, credentials, sensitive personal data, or unrestricted conversation transcripts.
- Preserve the user's existing uncommitted `memory_recall` logging refinement while refactoring it; do not overwrite unrelated working-tree changes.

Acceptance criteria
- [x] A1) [P1] A valid `memory_recall` request searches only the fixed directory corresponding to its required scope.
- [x] A2) [P1] Retrieval safely discovers and parses bounded version-1 JSON memory records containing required `id` and `content` fields and optional `title` and `tags` fields.
- [x] A3) [P1] Query text, relative path terms, title/content terms, and exact tag overlap produce deterministic candidate ranking.
- [x] A4) [P1] Recall returns at most five bounded memory records, or the stable result `{"status":"no_matches","memories":[]}` when the scope contains no relevant valid record or its directory is absent.
- [x] A5) [P1] Automated tests cover discovery, parsing, malformed records, missing directories, ranking, result bounds, and end-to-end MCP dispatch.
- [x] A6) [P2] The six canonical scopes map to visible top-level directories under a default `~/.mnemosyne/memory` root, with an operator-controlled `MNEMOSYNE_MEMORY_ROOT` override.
- [x] A7) [P2] Retrieval rejects symlinks, path escapes, oversized files, excessive traversal depth, and excessive candidate sets without exposing broad filesystem access.
- [x] A8) [P2] Public documentation describes the directory layout, JSON record contract, read-only behavior, retrieval semantics, and deletion-by-file boundary.
- [x] A9) [P3] `memory_recall/__init__.py` contains no Tool, validation, logging, result, or retrieval logic and only re-exports the package's public `TOOL` and `handle` names.
- [x] A10) [P3] Existing query, scope, tags, error, registration, and logging behavior remains covered while the package is refactored.

Why now / impact
- Tracks 003 and 004 established a visible recall request and categorization contract. Scope-backed local files are the smallest transparent source that can turn those requests into actual user-governed recall without introducing hidden infrastructure.

Scope
- In scope:
  - A fixed memory root with one allowlisted top-level directory per canonical scope.
  - An optional `MNEMOSYNE_MEMORY_ROOT` operator override and a default `~/.mnemosyne/memory` root.
  - Recursive, bounded discovery of JSON memory files beneath the selected scope.
  - A minimal record contract with required `id` and `content`, plus optional `title` and `tags`.
  - Deterministic lexical and tag-based candidate ranking and a maximum of five returned records.
  - Stable successful and no-match MCP Tool results.
  - Refactoring `memory_recall` into re-export-only `__init__.py`, Tool definition, handler, and retrieval modules.
  - Focused automated tests, full-suite validation, direct MCP checks, and public documentation updates.
- Out of scope:
  - Memory creation, update, deletion, migration, compaction, or automated extraction.
  - Generated personal memory fixtures outside temporary automated-test directories.
  - Embeddings, semantic models, vector databases, external search, weather, time, or other awareness providers.
  - Automatic tool chaining or hidden awareness acquisition.
  - Arbitrary client-selected paths, unrestricted file reads, binary records, YAML, Markdown parsing, or multiple storage backends.
  - Project identifiers, relationship subject identifiers, and other structured selectors beyond the existing scope/query/tags request contract.

Milestones
- [x] M1) Finalize the filesystem, record, safety, ranking, and result contracts.
- [x] M2) Implement safe scope-backed discovery and deterministic retrieval through bounded TDD chunks.
- [x] M3) Integrate retrieval into the MCP Tool, complete the package refactor, and validate the public behavior.

Risks / decisions
- Risk: Building paths directly from model arguments could expose arbitrary local files.
- Decision: Map validated scope values through a fixed internal allowlist; never accept a path from an MCP request.
- Risk: Semantic filenames and nested directories could be mistaken for a complete index.
- Decision: Treat paths as one relevance signal alongside record title, content, and tags; files remain the source of truth.
- Risk: Free-form tags may drift or fail to match equivalent concepts.
- Decision: Use exact normalized tag overlap only as a ranking signal, not as a required filter; query and record text remain primary retrieval inputs.
- Risk: Recursive scanning could become expensive or follow unsafe links.
- Decision: Reject symlinks and impose explicit traversal depth, file-size, candidate-count, and result-count limits.
- Risk: A malformed record could make all recall unavailable.
- Decision: Skip invalid individual records deterministically and continue with other safe candidates; cover this behavior with tests.
- Risk: A default directory inside the repository could accidentally place personal memory under version control.
- Decision: Default to `~/.mnemosyne/memory`; permit an explicit operator-controlled environment override for tests and deployment.
- Risk: Splitting a small module prematurely could obscure behavior.
- Decision: Use only three focused implementation modules: `definition.py`, `handler.py`, and `retrieval.py`; keep `__init__.py` as a compatibility re-export surface.
- Risk: The working tree already contains a user-authored logging refinement and trailing whitespace.
- Decision: Preserve the intended message/scope/tags log behavior during refactoring and avoid overwriting unrelated changes; whitespace hygiene will be handled explicitly during the approved implementation chunk.

Open questions
- [x] Q1) What exact JSON field constraints and per-file byte limit should apply?
- [x] Q2) What exact traversal-depth and candidate-count limits should apply?
- [x] Q3) What deterministic lexical and tag scoring formula should rank candidates and define relevance?
- [x] Q4) What exact successful MCP result shape should expose matching records and match evidence?
- [x] Q5) Should malformed or unsafe files emit warning logs, and if so, which non-sensitive details may be logged?

Decision log
- Decision: Use the six canonical memory scopes as top-level directory names: `self`, `relationship`, `preference`, `practice`, `project`, and `knowledge`.
- Decision: A recall request searches only its selected scope directory.
- Decision: Use individual JSON files as the initial durable, user-visible source of truth.
- Decision: Keep tags as record metadata rather than directories because tags are many-to-many and cross-cutting.
- Decision: Permit nested directories for user-organized topics, projects, or subjects, but do not infer a new public identifier contract in this Track.
- Decision: A missing scope directory behaves as an empty source and returns `no_matches`; recall does not create directories.
- Decision: Return no more than five memory records from one recall call.
- Decision: The model receives bounded memory record data rather than arbitrary filesystem paths or file contents outside the record contract.
- Decision (Q1): A memory record is one UTF-8 `.json` file of at most 65,536 bytes whose top-level value is an object. It requires `schema_version` with the exact integer value `1`, `id`, and `content`; it optionally accepts `title` and `tags`; unknown fields make the record invalid.
- Decision (Q1): `id` is a string of 1–100 characters drawn only from ASCII letters, digits, `.`, `_`, and `-`. `content` contains non-whitespace text of at most 4,000 characters. Optional `title` contains non-whitespace text of at most 200 characters. Optional `tags` follows the recall-tag bounds: 1–10 unique strings, each containing non-whitespace text and at most 50 characters. An omitted title is represented as `null` in a returned memory, and omitted tags are represented as `[]`.
- Decision (Q2): A record may be located directly in its scope directory or beneath at most four nested directories. Discovery considers only regular `.json` files, traverses candidates by sorted scope-relative path, rejects symlink files and directories, and never follows links.
- Decision (Q2): A scope may contain at most 1,000 candidate JSON files. Unsafe, too-deep, oversized, or malformed individual files are skipped. Discovery of a 1,001st candidate fails the recall with the stable `candidate_limit_exceeded` Tool error rather than returning partial results. At most five matching records are returned.
- Decision (Q3): Normalize text with Unicode case-folding and tokenize it into alphanumeric terms; punctuation, underscores, and hyphens separate terms. Ignore one-character terms and the fixed question-word set `a`, `an`, `and`, `are`, `do`, `does`, `for`, `how`, `i`, `in`, `is`, `it`, `of`, `on`, `or`, `the`, `to`, `user`, `what`, `when`, `where`, `which`, `who`, and `why`.
- Decision (Q3): Score each unique exact normalized overlap independently: request tag to record tag adds 4; query term to title adds 3; query term to a scope-relative path term or record tag adds 2; and query term to content adds 1. A record must have a positive score. Sort by descending score, then ascending scope-relative path, then ascending record ID.
- Decision (Q3): Exact normalized request-tag overlap is a ranking signal and never a required filter. This gives the existing free-form tags retrieval semantics without treating them as directories or project/subject identifiers.
- Decision (Q4): A matching call returns a normal Tool result with text JSON shaped as `{"status":"ok","memories":[...]}`. Every returned memory contains `id`, the requested `scope`, `title` as a string or `null`, `content`, `tags` as an array, and `match` containing sorted unique `terms` and `tags` arrays. Results never contain absolute or relative filesystem paths or raw ranking scores.
- Decision (Q4): A missing scope directory or no positive-scoring valid record returns the normal Tool result `{"status":"no_matches","memories":[]}`.
- Decision (Q4): An unreadable memory source returns `isError: true` with `status: retrieval_error`, code `memory_source_unavailable`, and message `memory source could not be read`. Exceeding 1,000 candidates returns `isError: true` with `status: retrieval_error`, code `candidate_limit_exceeded`, and message `memory scope contains more than 1000 candidate files`.
- Decision (Q5): Preserve the user-authored INFO request log containing message, scope, and tags. Every skipped unsafe, too-deep, oversized, malformed, or schema-invalid file emits a warning containing only the selected scope, its scope-relative path, and a stable reason code; never log an absolute path or file content.

Plan (execution steps)
- [x] S1) Resolve Q1-Q5 and record exact record, safety, ranking, logging, and MCP result contracts.
- [x] S2) Move Track 005 to ACTIVE (folder, filename, title, and current path status).
- [x] S3) Execute one TDD chunk for safe scope-directory resolution, bounded JSON discovery, record parsing, and malformed/unsafe-file handling; refactor the Tool definition out of `__init__.py` as part of the smallest coherent package boundary.
- [x] S4) Execute one TDD chunk for deterministic query/path/title/content/tag ranking and five-result bounding.
- [x] S5) Execute one TDD chunk integrating retrieval with handler validation, logging, stable success/no-match Tool results, registry dispatch, and the re-export-only `__init__.py` boundary.
- [x] S6) Run the full suite and `git diff --check`, perform direct MCP checks against temporary approved memory fixtures, update public documentation and architecture inventory, and record evidence.
- [x] S7) Confirm all acceptance criteria and move Track 005 to COMPLETED with completion evidence.

Current inventory
- `memory_recall` requires `query` and one canonical `scope`, accepts optional bounded free-form `tags`, validates those arguments, searches only the selected scope directory, and returns stable `ok`, `no_matches`, invalid-request, or retrieval-error Tool results.
- `mnemosyne/mcp/tools/memory_recall/__init__.py` is a five-line compatibility surface that re-exports only `TOOL` and `handle` and declares those names in `__all__`.
- `mnemosyne/mcp/tools/memory_recall/definition.py` now owns the unchanged public Tool definition and canonical scope tuple.
- `mnemosyne/mcp/tools/memory_recall/handler.py` now owns request validation, the preserved message/scope/tags INFO log, configured-root lookup, discovery/ranking orchestration, stable Tool errors, and path/score-free result serialization.
- `mnemosyne/mcp/tools/memory_recall/retrieval.py` now owns fixed scope-directory resolution, sorted bounded discovery, symlink and depth rejection, file-size and candidate limits, warning logs, strict version-1 JSON parsing, immutable `MemoryRecord` and `MemoryMatch` representations, Unicode-aware term normalization, deterministic weighted ranking, match evidence, tie-breaking, and the five-result bound.
- `mnemosyne/mcp/tools/registry.py` continues to import and dispatch the package-level re-exported `TOOL` and `handle` names without registry changes.
- `tests/mcp/test_memory_retrieval.py` covers scope isolation, sorted nested discovery, missing and unknown scopes, strict record validation, invalid JSON and encoding, file-size and depth limits, symlink rejection, the 1,000-candidate limit, normalization and stop words, every declared score weight, positive-score filtering, deterministic tie-breaking, match evidence, and the five-result bound.
- `tests/mcp/test_memory_recall.py`, `tests/mcp/test_registry.py`, and `tests/routes/test_mcp.py` cover package re-exports, memory-root configuration, exact request logging, matching/no-match and stable-error results, scope isolation, registry dispatch, and end-to-end HTTP retrieval through temporary test fixtures.
- `mnemosyne/settings.py` provides dynamic `MNEMOSYNE_MEMORY_ROOT` resolution with the default `~/.mnemosyne/memory` path.
- `README.md` documents setup, the visible scope-directory layout, the version-1 JSON record contract and limits, deterministic retrieval behavior, stable results/errors, and deletion by removing a source file.
- `docs/ARCHITECTURE.md` documents the definition/handler/retrieval package boundary, configured root, safe discovery constraints, and read-only orchestration.
- `docs/GLOSSARY.md` defines memory records, roots, scope directories, retrieval-aware recall tags, match evidence, no-match results, and retrieval errors.
- No runtime memory root or memory files are created by recall. Memory mutation does not exist.
- The current full suite passes 81 tests, and whitespace validation passes for tracked and new files.

Artifacts
- Design discussion: current development session following Track 004 and the manual `memory_recall` logging refinement.
- Pre-implementation verification: `PYENV_VERSION=3.13.5 python -m pytest tests` passed all 47 tests; direct handler invocation emitted message, scope, and tags; `git diff --check` identified two pre-existing trailing-whitespace lines in the user-authored change.
- S3 TDD red evidence: `PYENV_VERSION=3.13.5 python -m pytest tests/mcp/test_memory_retrieval.py` failed during collection with `ModuleNotFoundError` because the declared retrieval module did not exist.
- S3 TDD green evidence: after the smallest discovery and parser implementation, the same focused command passed all 19 tests.
- S3 focused regression evidence: `PYENV_VERSION=3.13.5 python -m pytest tests/mcp/test_memory_recall.py tests/mcp/test_memory_retrieval.py` passed all 41 tests.
- S3 full validation evidence: `PYENV_VERSION=3.13.5 python -m pytest tests` passed all 66 tests; `git diff --check` passed.
- S4 TDD red evidence: `PYENV_VERSION=3.13.5 python -m pytest tests/mcp/test_memory_retrieval.py` failed during collection because the declared `MemoryMatch` and ranking API did not exist.
- S4 TDD green evidence: after the smallest tokenizer, scoring, evidence, ordering, and result-limit implementation, the same focused command passed all 25 tests.
- S4 refactor: simplified record-tag term collection without changing ranking behavior.
- S4 focused regression evidence: `PYENV_VERSION=3.13.5 python -m pytest tests/mcp/test_memory_recall.py tests/mcp/test_memory_retrieval.py` passed all 47 tests.
- S4 full validation evidence: `PYENV_VERSION=3.13.5 python -m pytest tests` passed all 72 tests; whitespace validation passed for tracked and new files.
- S5 TDD red evidence: `PYENV_VERSION=3.13.5 python -m pytest tests/mcp/test_memory_recall.py tests/mcp/test_registry.py tests/routes/test_mcp.py` failed during collection because the declared `memory_recall.handler` module did not exist.
- S5 TDD green evidence: after the smallest configured-root, handler integration, result serialization, error handling, and package re-export implementation, the same focused command passed all 45 tests.
- S5 full validation evidence: `PYENV_VERSION=3.13.5 python -m pytest tests` passed all 81 tests; whitespace validation passed for tracked and new files.
- S6 final automated validation evidence: `PYENV_VERSION=3.13.5 python -m pytest tests` passed all 81 tests after public documentation updates; `git diff --check` and new-file whitespace checks passed.
- S6 configured-client evidence: the configured MCP connection was unavailable, so no result was claimed from it.
- S6 direct MCP evidence: a temporary local server used an isolated `MNEMOSYNE_MEMORY_ROOT` containing one non-personal preference fixture. `tools/list` exposed the unchanged Tool definition; a preference call returned the fixture with `status: ok`, matched terms/tags, no path, and no score; the same query against `self` returned `status: no_matches`.
- S6 cleanup evidence: the temporary server stopped and the isolated memory root, fixture, and server log were removed; a filesystem check found no remaining `mnemosyne-s6.*` path.

Completion notes
- Track moved to ACTIVE after the filesystem, record, safety, ranking, logging, and result contracts were resolved; implementation has not started.
- S3 completed safe scope-backed JSON discovery and parsing, moved the unchanged Tool definition into `definition.py`, preserved the current placeholder MCP behavior, and created no runtime memory data.
- S4 completed deterministic lexical and tag ranking with explicit match evidence and a five-result bound; MCP behavior remains the placeholder until S5 integration.
- S5 connected configured filesystem retrieval to the MCP handler, replaced the placeholder with stable matching/no-match/error results, preserved and tested the request log, and completed the re-export-only package boundary.
- S6 synchronized public documentation with the implemented filesystem contract and completed automated and direct MCP validation without retaining test memory.
- S7 confirmed all ten acceptance criteria, synchronized the Track's folder, filename, title, and current path, and completed Track 005 with 81 passing tests and direct MCP evidence.
