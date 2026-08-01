# MyMCP Host Configuration

This is the canonical operator guide for **MyMCP host configuration**. It is
separate from the Mnemosyne plugin's `MNEMOSYNE_*` settings and
`~/.mnemosyne/config.toml`, which continue to own memory roots and mutation
gates.

## Location and loading

At explicit startup, MyMCP selects exactly one path:

1. `$XDG_CONFIG_HOME/mymcp/config.toml` when `XDG_CONFIG_HOME` is a nonempty
   absolute path; otherwise
2. `~/.config/mymcp/config.toml`.

This rule is the same on every platform. Native Windows uses this fallback, not
`%APPDATA%` or `%LOCALAPPDATA%`; absolute drive and UNC XDG paths are accepted,
while drive-relative paths are not. MyMCP does not expand `~` or variables in
`XDG_CONFIG_HOME`, resolve the selected path during selection, probe other
locations, merge files, or fall back to `~/.mymcp/config.toml`.

An absent source supplies immutable schema-1 defaults: bundled Mnemosyne only,
`127.0.0.1:8000`, and no external declarations. A present document must be
valid in full: an empty document, unsupported schema version, unknown field or
table, duplicate key, or wrong type fails startup; disabled declarations do not
suppress validation.

## Host configuration schemas 1 and 2

`schema_version` is required and must be the native TOML integer `1` or `2`.
It versions this document only, independently of the MyMCP package/server,
host plugin API, manifest schema, external plugin-author contract, plugin,
capability, runtime-generation, and record schemas. MyMCP never normalizes,
expands, migrates, rewrites, merges, or falls back between schemas.

Both schemas support an optional `[server]` table. `address` is a literal
loopback IPv4 or IPv6 address, not a hostname, wildcard, LAN, or public address;
`port` is a native integer from 1 through 65535. They default to `127.0.0.1`
and `8000` and apply to packaged `mymcp` and `mymcp-dev` launchers. Direct
Uvicorn invocation owns its binding arguments and is not a supported way to
bypass the machine-local boundary.

Schema 1 preserves exact compatibility: each ordered `[[plugins]]` declaration
contains **exactly** a lowercase kebab-case `id` and native TOML boolean
`enabled`. There is no enablement default. IDs cannot repeat or collide with a
bundled plugin identity, including `mnemosyne`. It is desired state only and
does not locate software or prove installation, compatibility, authority,
safety, or consent. An enabled schema-1 declaration fails before runtime
construction with `enabled_plugin_unsupported`.

Schema 2 declarations contain **exactly** `id`, `enabled`, `manifest_path`, and
`module`, even when disabled:

```toml
schema_version = 2

[server]
address = "127.0.0.1"
port = 8000

[[plugins]]
id = "example-plugin"
enabled = true
manifest_path = "/opt/mymcp-plugins/example-plugin/manifest.json"
module = "example_plugin"
```

`manifest_path` is absolute and cannot contain NUL, `~`, environment-variable
syntax, or `.`/`..` components. `module` is an ASCII dotted Python module path
with valid non-keyword identifier components. MyMCP performs no normalization,
home/environment expansion, fallback, locator inference, or module/package
autodiscovery. Locators are not host-managed installation, dependency or
environment management, plugin configuration, secret storage, trust proof, or
safety control.

## Startup composition and restart

Configuration is read once by each consuming process into an immutable snapshot.
Ordinary imports and runtime requests do not read or watch it. One complete
runtime is composed per server start. Plugin additions, removals, configuration
changes, upgrades, rollback, and operational stop/start require operator action
and a server restart; there is no hot activation, runtime switching, or partial
publication.

Disabled and unconfigured external plugins have no manifest access, module
import, entrypoint invocation, or Tool exposure. For enabled schema-2 plugins,
all manifests preflight in configuration order before any external module import.
Only after complete preflight do modules import and entrypoints run in that same
order. Bundled Mnemosyne is composed first; external contributions follow
configuration order and retain capability order.

Each external module must expose a zero-argument `mymcp_plugin_v1()` entrypoint
returning a `PluginAdapter`. MyMCP validates its definition and contribution
against the preflighted manifest, then assigns each external Tool the deterministic
binding `<plugin-id>__<tool-local-id>`. Any definition, contribution, qualified
identity, reserved-name, binding, or public-name collision fails the complete
composition without overwrite, suffix fallback, alias, or partial runtime.

Enabled external plugins are operator-installed, operator-trusted in-process
code. Compatibility validation is not a safety assessment. MyMCP does not
install plugins, manage dependencies/environments, hold plugin configuration or
secrets, upgrade/roll back plugins, or provide lifecycle, worker, isolation,
sandbox, supervision, killability, or resource-control services. The
client-neutral governance gateway remains deferred.

## Source safety and limits

MyMCP reads at most 64 KiB, requires UTF-8 and strict TOML, and rejects unsafe
or changing host-configuration sources. Symlinked ancestors such as `~/.config`
are accepted, but the immediate `mymcp` directory and `config.toml` must not be
symlinks/reparse points; the directory must be a directory and the file regular.
Where available, no-follow descriptor-relative opens and pre/post identity, type,
size, and permission checks are used. Source replacement fails without retry or
alternate-path, conventional-filename, or package-resource lookup. On POSIX, use
`0700` for the immediate `mymcp` directory and `0600` for `config.toml`; group-
or world-writable immediate directory/file sources are rejected. Do not put
plaintext secrets, credentials, tokens, or private keys in host configuration.

Each enabled external manifest is preflighted before any import: it must be a
regular, non-symlink/reparse-point source with a safe immediate parent; POSIX
group/world-writable immediate parent/file sources are rejected, and
replacement/mutation during read fails without retry or fallback. The manifest
must parse as manifest schema 1, match the configured ID, and support host plugin
API 1. At most 32 enabled plugins and 256 aggregate external capabilities are
accepted.

## Logging

`mymcp.host.configuration` emits one terminal event for each configuration-load
attempt: successful loads use `outcome=loaded` or `absent_defaults`; failures use
`outcome=error code=<stable_code>`. `mymcp.host.bootstrap` records bounded
external runtime-composition outcomes. Events do not expose paths, source
content, plugin IDs, environment values, exception details, or tracebacks.

Successful configuration events are
`host_configuration outcome=<loaded|absent_defaults> schema_version=<1|2> address=<loopback> port=<port> declarations=<count> enabled=<count>`;
configuration failures are `host_configuration outcome=error code=<stable_code>`.
Successful composition is
`runtime_composition outcome=loaded bundled=<count> external=<count> capabilities=<count>`.
An external composition failure is
`runtime_composition outcome=error code=<external_stable_code>`.

Normal `mymcp` startup consumes configuration and composes once. The `mymcp-dev`
supervisor consumes and semantically validates configuration for binding without
composing a runtime; each reload worker separately consumes and composes once.
Direct factory use consumes and composes once per process when no snapshot is injected.
These events do not imply lifecycle ownership, watching, rereads, or hot reload.
The `mymcp` and `mymcp-dev` launchers call
`logging.basicConfig(level=logging.INFO)` before loading configuration; direct
Uvicorn retains logging ownership and programmatic callers configure logging.

## Bounded failures

Configuration failures expose only these stable code/message pairs:

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

External startup-composition failures are also bounded and content-free:

| Code | Message |
| --- | --- |
| `external_plugin_limit_exceeded` | MyMCP external plugin limit is exceeded |
| `external_manifest_unsafe_path` | MyMCP external manifest path is unsafe |
| `external_manifest_not_regular` | MyMCP external manifest source is not a regular file |
| `external_manifest_unsafe_permissions` | MyMCP external manifest source permissions are unsafe |
| `external_manifest_unreadable` | MyMCP external manifest source could not be read |
| `external_manifest_too_large` | MyMCP external manifest exceeds 65536 bytes |
| `external_manifest_source_changed` | MyMCP external manifest changed while being read |
| `external_manifest_invalid` | MyMCP external manifest is invalid |
| `external_manifest_identity_mismatch` | MyMCP external manifest identity does not match configuration |
| `external_manifest_host_api_incompatible` | MyMCP external manifest does not support the host API |
| `external_plugin_import_failed` | MyMCP external plugin import failed |
| `external_plugin_entrypoint_invalid` | MyMCP external plugin entrypoint is invalid |
| `external_plugin_contract_invalid` | MyMCP external plugin contract is invalid |
| `external_plugin_composition_invalid` | MyMCP external plugin composition is invalid |

See [Plugin Architecture](PLUGIN_ARCHITECTURE.md) for the full external
plugin-author and composition contract.
