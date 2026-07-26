# Mnemosyne Plugin Scope Rules

- This trusted bundled plugin owns `plugin.py`, `configuration.py`, `memory/`,
  and `mcp/tools/`. Across the MyMCP/`mymcp` `0.2.0` host cutover, permanently
  preserve Mnemosyne plugin identity and public Tool, configuration, storage,
  record, logging, and consent compatibility.
- `plugin.py` may depend only on generic plugin/MCP contracts and this plugin.
  It supplies the definition and gate-selected contribution; it must not build a
  host runtime, bind public names, or contribute `list_tools`.
- `mcp/` may use generic MCP contracts and this plugin's memory types, but must
  not import FastAPI, routes, application assembly, host bootstrap, or another
  plugin. Keep handlers narrow and inject operations rather than constructing
  roots, stores, or services.
- `memory/` and `configuration.py` may depend only on the standard library and
  plugin-local modules. They must not import MCP, host, routes, FastAPI, or other
  plugins.
- Only `mymcp/host/bootstrap.py` may import this concrete plugin from generic
  host code. Do not add discovery, configured imports, installation, external
  execution, lifecycle, or authority claims.
