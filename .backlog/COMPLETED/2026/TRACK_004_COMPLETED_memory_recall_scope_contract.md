# TRACK 004 [COMPLETED]: memory recall scope contract

Track
- ID: TRACK_004
- Repository: Mnemosyne
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_004_COMPLETED_memory_recall_scope_contract.md

Problems (PORE)
- P1: As an MCP model, I cannot explicitly identify the high-level domain of memory needed for a recall request because `memory_recall` accepts only a free-form `query`.
- P2: As the user governing Mnemosyne, I cannot inspect or constrain recall by a stable high-level memory categorization because no scope taxonomy or scope-selection contract exists.
- P3: As an MCP model, I cannot attach concise cross-cutting concepts to a recall request without placing all categorization detail in the free-form query.

Objective
- Define and expose a clear `memory_recall` categorization contract whose individually described scope values and optional free-form tags let models classify recall requests consistently.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Preserve local-first, single-user, least-privilege, and explicit-user-governance principles.
- Design the coherent scope model before implementing it; incremental implementation must conform to that model rather than substitute for it.
- Scope names and descriptions must be understandable without knowledge of Greek philosophy, even when philosophical analysis informs the taxonomy.
- This Track does not implement memory storage, retrieval, ranking, or mutation.

Acceptance criteria
- [x] A1) [P1] The canonical high-level memory scopes and their inclusion and exclusion boundaries are documented.
- [x] A2) [P1] `memory_recall` requires a scope selected through a JSON Schema `oneOf` contract with one uniquely named and individually described `const` option per scope.
- [x] A3) [P1] Automated tests cover the exact Tool schema and valid and invalid scope handling.
- [x] A4) [P2] Public documentation explains the scope taxonomy and how models select a scope.
- [x] A5) [P2] The contract distinguishes high-level memory scope from memory kind, provenance, subject identity, and retrieval policy.
- [x] A6) [P3] `memory_recall` accepts an optional bounded array of free-form tags and returns a stable `invalid_tags` Tool error for invalid tag values.

Why now / impact
- Track 003 established a non-retrieving recall request surface. A coherent scope contract is needed before retrieval design can categorize requests without collapsing unrelated memory dimensions or creating foundational technical debt.

Scope
- In scope:
  - Philosophically and operationally grounded analysis of high-level memory scopes.
  - Stable public names, descriptions, and inclusion and exclusion boundaries for each selected scope.
  - A required `scope` field represented by individually described JSON Schema `oneOf` and `const` options.
  - An optional bounded `tags` array containing unique free-form strings.
  - Tool-owned scope validation, focused automated tests, and public-contract documentation.
- Out of scope:
  - Memory records, storage, indexing, retrieval, matching, ranking, and returned memories.
  - Filtering, ranking, or other retrieval semantics for tags.
  - Memory kinds, provenance schemas, subject identifiers, project identifiers, and scope inheritance unless needed only to establish a clear boundary from scope.
  - Memory creation, update, deletion, lifecycle automation, or conversation extraction.
  - Embeddings, vector databases, external services, and retrieval-provider selection.

Milestones
- [x] M1) Define the conceptual meaning and boundaries of high-level memory scope.
- [x] M2) Select and document the canonical scope taxonomy and model-facing contract.
- [x] M3) Implement, validate, and document scope selection.

Risks / decisions
- Risk: Mixing scope with memory kind, provenance, identity, or retrieval policy creates an unstable taxonomy.
- Decision: Scope answers which high-level realm the requested memory concerns; other dimensions remain separate.
- Risk: Philosophical names may be ambiguous to models and users.
- Decision: Greek concepts may inform analysis, but public scope names and descriptions must use plain language.
- Risk: A plain enum gives models insufficient guidance for choosing among nuanced scopes.
- Decision: Represent each scope as a unique `const` branch under `oneOf` so every value carries its own description.
- Risk: Designing only for the smallest implementation could create foundational technical debt.
- Decision: Resolve the coherent conceptual model before implementing it, then deliver it through bounded TDD chunks.
- Risk: Unbounded or duplicate free-form tags could make requests noisy and validation unpredictable.
- Decision: Keep tags optional and free-form while bounding their count and length and rejecting duplicates.

Open questions
- [x] Q1) What canonical high-level scopes cover Mnemosyne's intended memory domains without mixing conceptual dimensions?
- [x] Q2) What precisely belongs in and is excluded from each scope?
- [x] Q3) Is exactly one scope required per recall request, or can a request span scopes?
- [x] Q4) How should missing, unknown, or semantically mismatched scope values fail?
- [x] Q5) How should scope be described in the Tool definition so models select it reliably?
- [x] Q6) What optional tags contract accompanies the required scope without defining retrieval behavior?

Decision log
- Decision: Begin with the distinction between the information need (`query`) and its high-level memory category (`scope`).
- Decision: Taxonomy analysis was informed by ethos/self, praxis/practice, poiesis/project, and episteme/knowledge; the accepted public names remain plain-language terms.
- Decision: `feedback` is not automatically a scope because it may describe how memory was learned rather than the realm it concerns.
- Decision: A user's perspective about another person exposed the need to analyze a possible social or relational realm rather than forcing all personal context into self.
- Decision: Use JSON Schema `oneOf` rather than a bare `enum` so each future scope value has an individual model-facing description.
- Decision (Q1): The canonical high-level scopes are `self` for the user's identity and enduring personal context; `relationship` for the user's relationships with and perspectives about others; `preference` for choices the user explicitly wants respected; `practice` for routines, methods, habits, and ways of working; `project` for the goals, state, decisions, and constraints of bounded endeavors; and `knowledge` for approved facts, concepts, and reference material about the wider world.
- Decision (Q1): Tags are a separate, optional descriptive dimension and do not define high-level memory scope. Embeddings are internal retrieval representations rather than tags or model-supplied scope metadata.
- Decision (Q2 — `self`): Include user-approved, non-sensitive identity, background, values, capabilities, and enduring personal circumstances. Exclude explicit wants, routines, relationships, bounded work, external facts, temporary state, secrets, and sensitive personal data.
- Decision (Q2 — `relationship`): Include user-approved context about people, groups, relationships, and the user's perspective or interactions with them. Keep relational claims attributed to the user's perspective. Exclude claims presented as objective truth about others, sensitive third-party information, general facts about people, the user's own identity, and communication choices.
- Decision (Q2 — `preference`): Include explicit, user-approved choices about how the user wants tools, communication, environments, or outcomes configured. Exclude inferred habits, identity and values, project decisions and constraints, and agent policies that do not express a user choice.
- Decision (Q2 — `practice`): Include user-approved descriptions of routines, methods, habits, workflows, and recurring ways of working. Exclude desired choices, one-time actions, temporary state, project-specific decisions, agent operating policies, and unsupported behavioral inference.
- Decision (Q2 — `project`): Include user-approved context about a bounded endeavor's goals, state, decisions, constraints, conventions, and unresolved questions. Exclude general working methods, cross-project choices, general reference knowledge, secrets, credentials, and unrestricted source content.
- Decision (Q2 — `knowledge`): Include user-approved reference material, concepts, and claims useful beyond a specific project. Exclude ordinary general-knowledge questions, user-specific or relationship context, project-local material, and unattributed or sensitive third-party information.
- Decision (Q3): Every `memory_recall` request requires exactly one high-level scope. A need spanning multiple realms uses separate, narrow recall calls. Optional tags may describe cross-cutting concepts but do not replace or broaden scope.
- Decision (Q4): A missing or unknown scope returns a Tool error with `status: invalid_request`, code `invalid_scope`, and the stable message `scope must be one of: self, relationship, preference, practice, project, knowledge`. Scope errors remain Tool errors rather than JSON-RPC errors, consistent with the existing tool-owned query validation contract.
- Decision (Q4): Schema validation does not reject a valid scope merely because the free-form query may appear semantically mismatched; reliably judging that meaning belongs outside this contract.
- Decision (Q5): The Tool description instructs the model to submit a narrow request for user-approved memory, select exactly one scope according to what the memory concerns rather than how it was learned, and use separate calls for different scopes.
- Decision (Q5): Each `oneOf` branch carries its own model-facing description: `self` — who the user is and their enduring circumstances; `relationship` — people, relationships, and the user's perspective about others; `preference` — choices the user explicitly wants respected; `practice` — routines, methods, habits, and actual ways of working; `project` — goals, state, decisions, and constraints of a bounded endeavor; `knowledge` — user-approved reference material useful beyond one project, not ordinary general knowledge.
- Decision (Q6): `tags` is optional. When present, it is an array of 1–10 unique free-form strings; each tag must contain non-whitespace text and contain at most 50 characters. Invalid values return a Tool error with `status: invalid_request`, code `invalid_tags`, and the stable message `tags must be an array of 1 to 10 unique non-empty strings of at most 50 characters`. This Track assigns tags no filtering, ranking, or other retrieval semantics.

Plan (execution steps)
- [x] S1) Resolve Q1-Q6 and record the complete scope and tags categorization contract decisions.
- [x] S2) Move Track 004 to ACTIVE (folder, filename, and title status).
- [x] S3) Read the ACTIVE Track and write focused failing tests for the selected Tool schema and scope validation contract.
- [x] S4) Implement the smallest scope schema and validation changes that pass S3.
- [x] S5) Refactor as needed, run the full relevant validation suite, perform a direct MCP protocol check, and update public documentation, inventory, and evidence.
- [x] S6) Move Track 004 to COMPLETED (folder, filename, and title status) and record completion notes.

Current inventory
- `memory_recall` accepts one required free-form `query` string of at most 1000 characters, exactly one required scope through individually described `oneOf` branches, and an optional array of 1–10 unique free-form tags of at most 50 characters each; it declares `additionalProperties: false`.
- The handler validates `query`, `scope`, and optional `tags`, returns stable tool-owned errors for invalid arguments, and continues to return `retrieval_unavailable` for valid calls.
- No memory schema, storage source, tag retrieval semantics, or retrieval behavior exists.
- Track 003 is completed in the current uncommitted working tree and explicitly allows the initial query-only Tool definition to be revised after evidence and analysis.
- `mnemosyne/mcp/tools/memory_recall/__init__.py` owns the Tool definition and request validation.
- `tests/mcp/test_memory_recall.py`, `tests/mcp/test_registry.py`, and `tests/routes/test_mcp.py` cover the current Tool contract and dispatch behavior.
- `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` document the public scope and tags categorization contract while preserving the no-retrieval boundary.

Artifacts
- Design discussion: current development session following completion of Track 003.
- TDD red evidence: `PYENV_VERSION=3.13.5 python -m pytest tests/mcp/test_memory_recall.py tests/mcp/test_registry.py tests/routes/test_mcp.py` collected 36 tests and produced the expected 14 failures with 22 passes before implementation; failures covered the Tool schema, missing and unknown scopes, and invalid tags.
- TDD green evidence: after the smallest implementation, the same focused command passed all 36 tests.
- Refactor review: the bounded schema and validation implementation remained small and explicit; no behavior-preserving refactor was needed.
- Final automated validation evidence: `PYENV_VERSION=3.13.5 python -m pytest tests` passed all 47 tests; `git diff --check` passed.
- Direct MCP evidence: the configured MCP client connection was unavailable, so a temporary local server was checked directly over `/mcp`; `tools/list` exposed all six individually described scopes and optional tags, a valid scoped and tagged call returned `retrieval_unavailable`, and an unknown scope returned the stable `invalid_scope` Tool error.

Completion notes
- Completed the `memory_recall` categorization contract with exactly one required high-level scope and optional bounded free-form tags.
- The accepted scopes are `self`, `relationship`, `preference`, `practice`, `project`, and `knowledge`; every scope has an individual model-facing description under JSON Schema `oneOf`.
- Missing or unknown scopes return the stable `invalid_scope` Tool error, and invalid tags return the stable `invalid_tags` Tool error.
- The change preserves the no-retrieval boundary: valid calls still return `retrieval_unavailable`, and tags currently define no filtering, ranking, or other retrieval semantics.
- Final automated validation passed all 47 tests, and direct local MCP checks verified Tool discovery, valid scoped and tagged calls, and invalid-scope behavior.
