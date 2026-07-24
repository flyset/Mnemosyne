@AGENTS.md

## Approval Granularity (Claude-specific)

- An instruction to work on a Track authorizes only its next unchecked plan
  step. Execute that step, update the Track, report back, and wait for an
  explicit go before starting the next step.
- Run multiple plan steps in one pass only when the user explicitly says so,
  for example "run the whole track without stopping".
- Resolving an Open Question whose answer changes a public contract, Tool
  schema, compatibility version, or storage layout always requires a fresh
  explicit yes, even inside an authorized step.
- Commits, pushes, and releases always require an explicit user request.
- Treat tentative phrasing — "maybe", "it may make sense", "we could",
  "perhaps", thinking out loud — as discussion, not authorization. Respond
  with a proposal and wait for an explicit instruction before changing
  anything.
