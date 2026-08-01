# MyMCP Host Configuration

This is the canonical operator guide for **MyMCP host configuration**. It is
separate from the Mnemosyne plugin's `MNEMOSYNE_*` settings and
`~/.mnemosyne/config.toml`; those continue to own memory roots and mutation
gates.

## Location and loading

At explicit startup, MyMCP selects exactly one path:

1. `$XDG_CONFIG_HOME/mymcp/config.toml` when `XDG_CONFIG_HOME` is a nonempty
   absolute path; otherwise
2. `~/.config/mymcp/config.toml`.

This rule is the same on every platform. Native Windows uses the same fallback,
not `%APPDATA%` or `%LOCALAPPDATA%`; absolute drive and UNC XDG paths are
accepted, while drive-relative paths are not. MyMCP does not expand `~` or
variables in `XDG_CONFIG_HOME`, resolve the selected path during selection,
probe other locations, merge files, or fall back to `~/.mymcp/config.toml`.

The selected directory and file may be absent. An absent source supplies the
immutable schema-v1 defaults: bundled Mnemosyne only, `127.0.0.1:8000`, and no
external declarations. A present source must be valid in full; disabled
declarations do not suppress validation.

## Schema version 1

```toml
schema_version = 1

[server]
# Both settings are optional.
address = "127.0.0.1"
port = 8000

[[plugins]]
id = "example-plugin"
enabled = false
```

`schema_version` is required and must be the native TOML integer `1`. It
versions this document only, independently of the MyMCP package/server version,
plugin API, manifest, plugin, capability, and record schemas. An absent file
uses schema-v1 defaults; a present empty file, unsupported version, unknown
field/table, duplicate key, or wrong type fails startup. Future schema changes
require explicit versioning; MyMCP never migrates or rewrites this file.

`[server]` is optional. Its independently optional values default to literal
IPv4 loopback `127.0.0.1` and native TOML integer `8000`. `address` must be a
literal loopback IPv4 or IPv6 address (for example `127.0.0.2` or `::1`), not a
hostname, wildcard, LAN, or public address. `port` must be an integer from 1
through 65535; strings and booleans are invalid. These settings apply to the
packaged `mymcp` and `mymcp-dev` launchers. Direct Uvicorn invocation owns its
own binding arguments and is not a supported way to bypass the machine-local
boundary.

`[[plugins]]` is optional and preserves file order. Every declaration contains
exactly a valid lowercase kebab-case `id` and a native TOML boolean `enabled`;
there is no enablement default. IDs cannot repeat or collide with a bundled
plugin identity, including `mnemosyne`.

Declarations express **desired state only**. They do not locate software,
prove installation, compatibility, authority, safety, or consent, and cannot
declare bindings, configuration values, or secrets. `enabled = false` and no
declaration expose no external Tools and do not import external code. In MyMCP
0.3.0, any otherwise valid `enabled = true` declaration fails before runtime
construction: external implementation loading is not yet supported.

## Startup and restart

Configuration is read once by each process that consumes it and represented by
one immutable snapshot. Normal `mymcp` startup reads once before runtime/app
construction and Uvicorn binding. `mymcp-dev` has a supervisor snapshot for
validation and binding; each reload worker constructs its own snapshot once.
The direct `mymcp.app:create_production_app` factory loads once only when no
snapshot is injected. Ordinary imports and runtime requests do not read or watch
the file. Change configuration by restarting the relevant server process; there
is no hot reload, activation, runtime switching, or partial publication.

## Source safety

MyMCP reads at most 64 KiB, requires UTF-8 and strict TOML, and rejects unsafe
or changing sources. It accepts a symlinked ancestor such as `~/.config`, but
rejects a symlinked or detectable reparse-point `mymcp` directory or
`config.toml`, non-directory application component, non-regular file, and (on
POSIX) group- or world-writable application directory or file. Where available,
it uses no-follow, descriptor-relative access and pre/post identity, type, size,
and permission checks; platforms without equivalent primitives use available
checks without claiming unavailable guarantees. Source replacement or mutation
during reading fails without retry or alternate-path fallback.

On POSIX, use `0700` for the `mymcp` directory and `0600` for `config.toml`.
Do not put plaintext secrets, credentials, tokens, or private keys in host
configuration. This document is process/startup intent, not consent, a trust
proof, a secret store, or plugin safety/isolation control.

## Bounded failures

Configuration failures occur before runtime or HTTP/MCP construction and expose
only a stable code/message, never a path, environment value, document content,
plugin ID, field value, parser/OS detail, or traceback:

| Code | Message |
| --- | --- |
| `invalid_location` | MyMCP configuration location is unavailable |
| `unsafe_path` | MyMCP configuration path is unsafe |
| `not_regular` | MyMCP configuration source is not a regular file |
| `unsafe_permissions` | MyMCP configuration source permissions are unsafe |
| `unreadable` | MyMCP configuration source could not be read |
| `too_large` | MyMCP configuration exceeds 65536 bytes |
| `source_changed` | MyMCP configuration changed while being read |
| `invalid_utf8` | MyMCP configuration is not valid UTF-8 |
| `invalid_toml` | MyMCP configuration is not valid TOML |
| `unsupported_schema_version` | MyMCP configuration schema version is unsupported |
| `invalid_schema` | MyMCP configuration has an invalid schema |
| `duplicate_plugin` | MyMCP configuration contains a duplicate plugin declaration |
| `bundled_plugin_conflict` | MyMCP configuration conflicts with a bundled plugin identity |
| `enabled_plugin_unsupported` | MyMCP external plugin enablement is not supported by this build |

See [Plugin Architecture](PLUGIN_ARCHITECTURE.md) for the later startup-
composition boundary; this configuration foundation does not implement it.
