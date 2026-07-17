# Mnemosyne

Mnemosyne is an experimental local MCP server.

Its intended direction is a personal memory and awareness layer for AI agents: a small local service that lets compatible models remember approved context, inspect safe environment signals, and operate under explicit user-governed boundaries.

## Current Status

This repository currently contains a minimal FastAPI-based MCP skeleton.

Implemented tools:

- `hello` — returns a greeting
- `list_tools` — lists the tools exposed by the server

This is not yet a full memory or awareness system. The current code is a starting point for shaping that server.

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

1. Define memory schemas and storage layout.
2. Add read-only awareness tools.
3. Add explicit memory recall and remember tools.
4. Add governance rules for consent, hygiene, and no-secret handling.
5. Add tests or protocol checks for MCP behavior.

See `VISION.md` for the broader scope and boundaries.

See `docs/ARCHITECTURE.md` for the current code organization.
