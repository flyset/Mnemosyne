from itertools import product
from importlib.resources import files
import logging

import pytest

from mymcp.host import bootstrap
from mymcp.host.bootstrap import build_production_runtime
from mymcp.host.configuration import (
    HostConfiguration,
    HostConfigurationError,
    parse_host_configuration_toml,
)
from mymcp.mcp.dispatcher import MCPDispatcher
from mymcp.plugins.mnemosyne import plugin as mnemosyne
from mymcp.plugins.mnemosyne.plugin import (
    build_mnemosyne_contribution,
    build_mnemosyne_registrations,
)
from mymcp.plugins.mnemosyne.configuration import MemoryToolSettings
from mymcp.plugin.adapter import PluginAdapter
from mymcp.plugin.composition import ActivatedTool, HostToolOrigin, PluginContribution
from mymcp.plugin.contracts import (
    CapabilityKind,
    CapabilityLocalId,
    ConsentRequirement,
    PluginId,
    PluginVersion,
    QualifiedCapabilityId,
    ToolEffects,
)
from mymcp.plugin.definition import HostApiVersion
from mymcp.plugin.manifest import (
    PluginContractError,
    PluginContractErrorCode,
    parse_manifest_bytes,
    parse_manifest_mapping,
)


DEFAULT_NAMES = ["memory_recall", "memory_list", "memory_inspect"]
MUTATION_NAMES = [
    "memory_archive",
    "memory_restore",
    "memory_remember",
    "memory_revise",
    "memory_forget",
]
DEFAULT_CONFIGURATION = HostConfiguration.default()
BOOTSTRAP_LOGGER = "mymcp.host.bootstrap"


def _identity(name: str) -> QualifiedCapabilityId:
    return QualifiedCapabilityId(
        PluginId("mnemosyne"),
        CapabilityKind.TOOL,
        CapabilityLocalId(name),
    )


def test_bootstrap_rejects_enabled_external_plugin_before_manifest_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = parse_host_configuration_toml(
        'schema_version = 1\n[[plugins]]\nid = "external"\nenabled = true\n'
    )
    monkeypatch.setattr(
        bootstrap,
        "files",
        lambda _package: pytest.fail("invalid composition accessed a manifest"),
    )

    with pytest.raises(HostConfigurationError) as captured:
        build_production_runtime(configuration)

    assert captured.value.code == "enabled_plugin_unsupported"


def test_schema_v2_preflight_precedes_bundled_manifest_and_generation(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generation_called = False

    def generation_factory() -> str:
        nonlocal generation_called
        generation_called = True
        return "should-not-run"

    external_manifest = tmp_path / "manifest.json"
    external_manifest.write_bytes(b"{")
    configuration = parse_host_configuration_toml(
        "schema_version = 2\n[[plugins]]\n"
        'id = "external"\nenabled = true\n'
        f'manifest_path = "{external_manifest}"\n'
        'module = "operator_plugins.external"\n'
    )
    monkeypatch.setattr(
        bootstrap,
        "files",
        lambda _package: pytest.fail("bundled manifest accessed before external preflight"),
    )
    monkeypatch.setattr(
        bootstrap,
        "load_external_plugins",
        lambda *_arguments: pytest.fail("external implementation imported before preflight"),
    )

    with pytest.raises(bootstrap.ExternalPluginLoadError) as captured:
        build_production_runtime(
            configuration,
            generation_factory=generation_factory,
        )

    assert captured.value.code == "external_manifest_invalid"
    assert generation_called is False


def test_bootstrap_composes_real_external_fixture_after_bundled_tools(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    manifest = tmp_path / "external-manifest.json"
    manifest.write_text(
        """{
  "manifest_version": 1,
  "id": "external",
  "title": "External",
  "description": "An external plugin.",
  "version": "1.0.0",
  "requires": {"host_api": {"min": 1, "max": 1}},
  "capabilities": [{"kind": "tool", "id": "external_tool", "version": "1.0.0", "read_only": true, "destructive": false, "idempotent": true, "open_world": false, "consent": "none"}],
  "configuration": {"schema_version": 1, "schema": {"type": "object", "properties": {}, "required": [], "additionalProperties": false}},
  "secret_references": [],
  "data_schema_version": 1,
  "authority": {"filesystem": [], "network": false}
}""",
        encoding="utf-8",
    )
    configuration = parse_host_configuration_toml(
        "schema_version = 2\n[[plugins]]\n"
        'id = "external"\nenabled = true\n'
        f'manifest_path = "{manifest}"\n'
        'module = "tests.host.fixtures.operator_plugins.valid"\n'
    )
    monkeypatch.setattr(
        mnemosyne,
        "get_memory_tool_settings",
        lambda: MemoryToolSettings(),
    )

    with caplog.at_level(logging.INFO, logger=BOOTSTRAP_LOGGER):
        runtime = build_production_runtime(
            configuration,
            generation_factory=lambda: "external-generation",
        )

    external = QualifiedCapabilityId(
        PluginId("external"), CapabilityKind.TOOL, CapabilityLocalId("external_tool")
    )
    assert runtime.generation.value == "external-generation"
    assert runtime.plugin_inventory == (
        (PluginId("mnemosyne"), PluginVersion("0.3.0")),
        (PluginId("external"), PluginVersion("1.0.0")),
    )
    assert [tool["name"] for tool in runtime.registry.tools] == [
        "list_tools",
        *DEFAULT_NAMES,
        "external__external_tool",
    ]
    assert runtime.registry.call_tool("external__external_tool", {"value": "ok"}) == {
        "content": [],
        "arguments": {"value": "ok"},
    }
    assert runtime.origins["external__external_tool"] == external
    assert runtime.effects[external] == ToolEffects(True, False, True, False)
    assert runtime.consent[external] is ConsentRequirement.NONE
    assert runtime.bindings[external] == "external__external_tool"
    assert [record.getMessage() for record in caplog.records if record.name == BOOTSTRAP_LOGGER] == [
        "runtime_composition outcome=loaded bundled=1 external=1 capabilities=4"
    ]
    assert "external__external_tool" in runtime.registry.call_tool("list_tools", {})[
        "content"][0]["text"]
    dispatcher = MCPDispatcher(runtime)
    listed = dispatcher.dispatch(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    )
    assert listed is not None
    assert [tool["name"] for tool in listed["result"]["tools"]] == [
        "list_tools",
        *DEFAULT_NAMES,
        "external__external_tool",
    ]
    assert dispatcher.dispatch(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "external__external_tool",
                "arguments": {"value": "protocol"},
            },
        }
    ) == {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {"content": [], "arguments": {"value": "protocol"}},
    }


def test_bootstrap_logs_one_loaded_event_after_bundled_runtime_construction(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(
        mnemosyne,
        "get_memory_tool_settings",
        lambda: MemoryToolSettings(),
    )

    with caplog.at_level(logging.INFO, logger=BOOTSTRAP_LOGGER):
        runtime = build_production_runtime(
            DEFAULT_CONFIGURATION,
            generation_factory=lambda: "logged-generation",
        )

    records = [record for record in caplog.records if record.name == BOOTSTRAP_LOGGER]
    assert runtime.generation.value == "logged-generation"
    assert [(record.levelno, record.getMessage(), record.exc_info) for record in records] == [
        (
            logging.INFO,
            "runtime_composition outcome=loaded bundled=1 external=0 capabilities=3",
            None,
        )
    ]


def test_bootstrap_logs_one_bounded_error_before_reraising_same_exception(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    expected = bootstrap.ExternalPluginLoadError("external_manifest_invalid")
    monkeypatch.setattr(
        bootstrap,
        "preflight_external_manifests",
        lambda _configuration: (_ for _ in ()).throw(expected),
    )
    monkeypatch.setattr(
        bootstrap,
        "files",
        lambda _package: pytest.fail("bounded preflight failure reached bundled manifest"),
    )

    with caplog.at_level(logging.INFO, logger=BOOTSTRAP_LOGGER):
        with pytest.raises(bootstrap.ExternalPluginLoadError) as captured:
            build_production_runtime(DEFAULT_CONFIGURATION)

    records = [record for record in caplog.records if record.name == BOOTSTRAP_LOGGER]
    assert captured.value is expected
    assert [(record.levelno, record.getMessage(), record.exc_info) for record in records] == [
        (
            logging.ERROR,
            "runtime_composition outcome=error code=external_manifest_invalid",
            None,
        )
    ]


def test_bootstrap_does_not_log_loaded_when_generation_construction_fails(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(
        mnemosyne,
        "get_memory_tool_settings",
        lambda: MemoryToolSettings(),
    )

    with caplog.at_level(logging.INFO, logger=BOOTSTRAP_LOGGER):
        with pytest.raises(RuntimeError, match="^generation failed$"):
            build_production_runtime(
                DEFAULT_CONFIGURATION,
                generation_factory=lambda: (_ for _ in ()).throw(
                    RuntimeError("generation failed")
                ),
            )

    assert [record for record in caplog.records if record.name == BOOTSTRAP_LOGGER] == []


def test_external_parity_failure_is_bounded_and_prevents_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = parse_host_configuration_toml(
        "schema_version = 2\n[[plugins]]\n"
        'id = "external"\nenabled = true\n'
        'manifest_path = "/opt/external/manifest.json"\n'
        'module = "operator_plugins.external"\n'
    )
    definition = mnemosyne.mnemosyne_plugin_definition()
    generation_called = False

    def reject_external_parity(**arguments) -> None:
        if arguments["manifest_definition"] is definition:
            raise PluginContractError(
                PluginContractErrorCode.DEFINITION_MISMATCH,
                "hidden external parity detail",
            )

    monkeypatch.setattr(bootstrap, "preflight_external_manifests", lambda _: (definition,))
    monkeypatch.setattr(
        bootstrap,
        "load_external_plugins",
        lambda *_: (
            type(
                "Adapter",
                (),
                {"definition": definition, "contribution": mnemosyne.mnemosyne_contribution()},
            )(),
        ),
    )
    monkeypatch.setattr(bootstrap, "validate_plugin_contract", reject_external_parity)

    def generation_factory() -> str:
        nonlocal generation_called
        generation_called = True
        return "should-not-run"

    with pytest.raises(bootstrap.ExternalPluginLoadError) as captured:
        build_production_runtime(
            configuration,
            generation_factory=generation_factory,
        )

    assert captured.value.code == "external_plugin_composition_invalid"
    assert captured.value.__cause__ is None
    assert generation_called is False


def test_bootstrap_preserves_external_configuration_and_capability_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = parse_host_configuration_toml(
        "schema_version = 2\n[[plugins]]\n"
        'id = "first"\nenabled = true\n'
        'manifest_path = "/opt/first/manifest.json"\nmodule = "operator_plugins.first"\n'
        "[[plugins]]\n"
        'id = "second"\nenabled = true\n'
        'manifest_path = "/opt/second/manifest.json"\nmodule = "operator_plugins.second"\n'
    )

    def adapter(plugin_id: str, *local_ids: str) -> PluginAdapter:
        definition = parse_manifest_mapping(
            {
                "manifest_version": 1,
                "id": plugin_id,
                "title": plugin_id,
                "description": "A controlled external plugin.",
                "version": "1.0.0",
                "requires": {"host_api": {"min": 1, "max": 1}},
                "capabilities": [
                    {
                        "kind": "tool",
                        "id": local_id,
                        "version": "1.0.0",
                        "read_only": True,
                        "destructive": False,
                        "idempotent": True,
                        "open_world": False,
                        "consent": "none",
                    }
                    for local_id in local_ids
                ],
                "configuration": {
                    "schema_version": 1,
                    "schema": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": False,
                    },
                },
                "secret_references": [],
                "data_schema_version": 1,
                "authority": {"filesystem": [], "network": False},
            }
        )
        tools = tuple(
            ActivatedTool(
                capability=QualifiedCapabilityId(
                    definition.plugin_id,
                    CapabilityKind.TOOL,
                    CapabilityLocalId(local_id),
                ),
                tool={
                    "name": local_id,
                    "description": "A controlled external Tool.",
                    "inputSchema": {"type": "object", "properties": {}},
                },
                handler=lambda arguments: {"content": [], "arguments": arguments},
                effects=ToolEffects(True, False, True, False),
                consent=ConsentRequirement.NONE,
            )
            for local_id in local_ids
        )
        return PluginAdapter(
            definition,
            PluginContribution(definition.plugin_id, definition.version, tools),
        )

    first = adapter("first", "one", "two")
    second = adapter("second", "three")
    monkeypatch.setattr(
        bootstrap,
        "preflight_external_manifests",
        lambda _: (first.definition, second.definition),
    )
    monkeypatch.setattr(
        bootstrap,
        "load_external_plugins",
        lambda *_: (first, second),
    )
    monkeypatch.setattr(
        mnemosyne,
        "get_memory_tool_settings",
        lambda: MemoryToolSettings(),
    )

    runtime = build_production_runtime(
        configuration,
        generation_factory=lambda: "ordered-generation",
    )

    assert runtime.plugin_inventory == (
        (PluginId("mnemosyne"), PluginVersion("0.3.0")),
        (PluginId("first"), PluginVersion("1.0.0")),
        (PluginId("second"), PluginVersion("1.0.0")),
    )
    assert [tool["name"] for tool in runtime.registry.tools] == [
        "list_tools",
        *DEFAULT_NAMES,
        "first__one",
        "first__two",
        "second__three",
    ]


def test_external_composition_failure_is_bounded_and_prevents_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = parse_host_configuration_toml(
        "schema_version = 2\n[[plugins]]\n"
        'id = "external"\nenabled = true\n'
        'manifest_path = "/opt/external/manifest.json"\n'
        'module = "operator_plugins.external"\n'
    )
    definition = parse_manifest_mapping(
        {
            "manifest_version": 1,
            "id": "external",
            "title": "External",
            "description": "An external plugin.",
            "version": "1.0.0",
            "requires": {"host_api": {"min": 1, "max": 1}},
            "capabilities": [
                {
                    "kind": "tool",
                    "id": "external_tool",
                    "version": "1.0.0",
                    "read_only": True,
                    "destructive": False,
                    "idempotent": True,
                    "open_world": False,
                    "consent": "none",
                }
            ],
            "configuration": {"schema_version": 1, "schema": {"type": "object", "properties": {}, "required": [], "additionalProperties": False}},
            "secret_references": [],
            "data_schema_version": 1,
            "authority": {"filesystem": [], "network": False},
        }
    )
    adapter = PluginAdapter(
        definition,
        PluginContribution(definition.plugin_id, definition.version, ()),
    )
    generation_called = False
    monkeypatch.setattr(bootstrap, "preflight_external_manifests", lambda _: (definition,))
    monkeypatch.setattr(bootstrap, "load_external_plugins", lambda *_: (adapter,))
    monkeypatch.setattr(
        bootstrap,
        "build_host_runtime",
        lambda *_arguments, **_keywords: (_ for _ in ()).throw(
            bootstrap.HostRuntimeCompositionError("reserved public tool name")
        ),
    )

    def generation_factory() -> str:
        nonlocal generation_called
        generation_called = True
        return "should-not-run"

    with pytest.raises(bootstrap.ExternalPluginLoadError) as captured:
        build_production_runtime(configuration, generation_factory=generation_factory)

    assert captured.value.code == "external_plugin_composition_invalid"
    assert captured.value.__cause__ is None
    assert generation_called is False


def _selected_names(settings: MemoryToolSettings) -> list[str]:
    names = list(DEFAULT_NAMES)
    if settings.archive_restore_enabled:
        names.extend(("memory_archive", "memory_restore"))
    if settings.remember_enabled:
        names.append("memory_remember")
    if settings.revise_enabled:
        names.append("memory_revise")
    if settings.forget_enabled:
        names.append("memory_forget")
    return names


@pytest.mark.parametrize(
    "settings",
    [
        MemoryToolSettings(
            remember_enabled=remember,
            archive_restore_enabled=archive_restore,
            revise_enabled=revise,
            forget_enabled=forget,
        )
        for remember, archive_restore, revise, forget in product(
            (False, True), repeat=4
        )
    ],
)
def test_bootstrap_resolves_settings_once_and_preserves_every_gate_combination(
    settings: MemoryToolSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings_calls = 0

    def resolve_settings() -> MemoryToolSettings:
        nonlocal settings_calls
        settings_calls += 1
        return settings

    monkeypatch.setattr(mnemosyne, "get_memory_tool_settings", resolve_settings)
    monkeypatch.setattr(
        mnemosyne,
        "get_memory_root",
        lambda: pytest.fail("bootstrap resolved the memory root"),
    )

    runtime = build_production_runtime(
        DEFAULT_CONFIGURATION,
        generation_factory=lambda: "test-generation"
    )
    expected = _selected_names(settings)

    assert settings_calls == 1
    assert runtime.generation.value == "test-generation"
    assert runtime.plugin_inventory == (
        (PluginId("mnemosyne"), PluginVersion("0.3.0")),
    )
    assert [tool["name"] for tool in runtime.registry.tools] == [
        "list_tools",
        *expected,
    ]
    assert runtime.origins["list_tools"] is HostToolOrigin.HOST
    assert runtime.bindings == {_identity(name): name for name in expected}


def test_trusted_adapter_assigns_exact_effect_and_consent_metadata() -> None:
    contribution = build_mnemosyne_contribution(
        memory_remember_enabled=True,
        memory_archive_restore_enabled=True,
        memory_revise_enabled=True,
        memory_forget_enabled=True,
    )
    by_name = {tool.capability.local_id.value: tool for tool in contribution.tools}

    assert contribution.plugin_id == PluginId("mnemosyne")
    assert contribution.version == PluginVersion("0.3.0")
    assert list(by_name) == [*DEFAULT_NAMES, *MUTATION_NAMES]
    for name in DEFAULT_NAMES:
        assert by_name[name].effects == ToolEffects(True, False, True, False)
        assert by_name[name].consent is ConsentRequirement.NONE
    for name in ("memory_remember", "memory_archive", "memory_restore"):
        assert by_name[name].effects == ToolEffects(False, False, True, False)
        assert by_name[name].consent is ConsentRequirement.PER_CALL
    for name in ("memory_revise", "memory_forget"):
        assert by_name[name].effects == ToolEffects(False, True, True, False)
        assert by_name[name].consent is ConsentRequirement.PER_CALL


def test_bootstrap_preserves_exact_public_definitions_without_policy_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = MemoryToolSettings(
        remember_enabled=True,
        archive_restore_enabled=True,
        revise_enabled=True,
        forget_enabled=True,
    )
    monkeypatch.setattr(mnemosyne, "get_memory_tool_settings", lambda: settings)

    runtime = build_production_runtime(
        DEFAULT_CONFIGURATION,
        generation_factory=lambda: "test-generation"
    )
    registrations = build_mnemosyne_registrations(
        memory_remember_enabled=True,
        memory_archive_restore_enabled=True,
        memory_revise_enabled=True,
        memory_forget_enabled=True,
    )

    assert runtime.registry.tools[1:] == tuple(item.tool for item in registrations)
    assert all(
        "effects" not in tool and "consent" not in tool
        for tool in runtime.registry.tools
    )


def test_bootstrap_list_tools_reports_complete_selected_surface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mnemosyne,
        "get_memory_tool_settings",
        lambda: MemoryToolSettings(remember_enabled=True, revise_enabled=True),
    )

    runtime = build_production_runtime(
        DEFAULT_CONFIGURATION,
        generation_factory=lambda: "test-generation"
    )

    assert runtime.registry.call_tool("list_tools", {}) == {
        "content": [
            {
                "type": "text",
                "text": (
                    "Server: mymcp 0.10.1. Available tools: "
                    "list_tools, memory_recall, memory_list, memory_inspect, "
                    "memory_remember, memory_revise"
                ),
            }
        ]
    }


def test_bootstrap_and_invalid_calls_do_not_construct_memory_domain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mnemosyne,
        "get_memory_tool_settings",
        lambda: MemoryToolSettings(
            remember_enabled=True,
            archive_restore_enabled=True,
            revise_enabled=True,
            forget_enabled=True,
        ),
    )
    monkeypatch.setattr(
        mnemosyne,
        "get_memory_root",
        lambda: pytest.fail("memory root was resolved"),
    )

    runtime = build_production_runtime(
        DEFAULT_CONFIGURATION,
        generation_factory=lambda: "test-generation"
    )

    for name in [*DEFAULT_NAMES, *MUTATION_NAMES]:
        assert runtime.registry.call_tool(name, {}) is not None


def test_failed_adapter_composition_does_not_create_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contribution = build_mnemosyne_contribution(False)
    duplicate = PluginContribution(
        contribution.plugin_id,
        contribution.version,
        (contribution.tools[0], contribution.tools[0]),
    )
    generation_called = False

    def generation_factory() -> str:
        nonlocal generation_called
        generation_called = True
        return "should-not-run"

    monkeypatch.setattr(bootstrap, "mnemosyne_contribution", lambda: duplicate)

    with pytest.raises(
        PluginContractError,
        match="^plugin contribution selects a capability more than once$",
    ) as captured:
        build_production_runtime(
            DEFAULT_CONFIGURATION,
            generation_factory=generation_factory,
        )

    assert captured.value.code is PluginContractErrorCode.DUPLICATE_SELECTED_CAPABILITY
    assert generation_called is False


def test_bootstrap_reads_only_the_fixed_mnemosyne_manifest_resource(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_bytes = (
        files("mymcp.plugins.mnemosyne").joinpath("manifest.json").read_bytes()
    )
    calls: list[tuple[str, str]] = []

    class ManifestResource:
        def read_bytes(self) -> bytes:
            return manifest_bytes

    class PluginPackage:
        def joinpath(self, resource_name: str) -> ManifestResource:
            calls.append(("resource", resource_name))
            return ManifestResource()

    def fixed_package(package_name: str) -> PluginPackage:
        calls.append(("package", package_name))
        return PluginPackage()

    monkeypatch.setattr(bootstrap, "files", fixed_package, raising=False)

    runtime = build_production_runtime(
        DEFAULT_CONFIGURATION,
        generation_factory=lambda: "fixed-resource",
    )

    assert calls == [
        ("package", "mymcp.plugins.mnemosyne"),
        ("resource", "manifest.json"),
    ]
    assert runtime.generation.value == "fixed-resource"


def test_bootstrap_validates_exact_contract_before_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def validate(**arguments) -> None:
        calls.append("validate")
        assert arguments["manifest_definition"] == parse_manifest_bytes(
            files("mymcp.plugins.mnemosyne").joinpath("manifest.json").read_bytes()
        )
        assert arguments["adapter_definition"] == mnemosyne.mnemosyne_plugin_definition()
        assert arguments["contribution"].plugin_id == PluginId("mnemosyne")
        assert arguments["supported_host_api"] == HostApiVersion(1)

    def generation_factory() -> str:
        calls.append("generation")
        return "validated-generation"

    monkeypatch.setattr(
        bootstrap,
        "validate_plugin_contract",
        validate,
        raising=False,
    )

    runtime = build_production_runtime(
        DEFAULT_CONFIGURATION,
        generation_factory=generation_factory,
    )

    assert calls == ["validate", "generation"]
    assert runtime.generation.value == "validated-generation"


def test_manifest_parse_failure_precedes_settings_and_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generation_called = False

    def reject_manifest(_: bytes):
        raise PluginContractError(
            PluginContractErrorCode.INVALID_JSON,
            "plugin manifest resource is not valid JSON",
        )

    def generation_factory() -> str:
        nonlocal generation_called
        generation_called = True
        return "should-not-run"

    monkeypatch.setattr(bootstrap, "parse_manifest_bytes", reject_manifest, raising=False)
    monkeypatch.setattr(
        mnemosyne,
        "get_memory_tool_settings",
        lambda: pytest.fail("settings resolved after manifest parse failure"),
    )

    with pytest.raises(
        PluginContractError,
        match="^plugin manifest resource is not valid JSON$",
    ):
        build_production_runtime(
            DEFAULT_CONFIGURATION,
            generation_factory=generation_factory,
        )

    assert generation_called is False


def test_manifest_resource_failure_precedes_settings_and_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generation_called = False

    class MissingManifest:
        def read_bytes(self) -> bytes:
            raise OSError("manifest unavailable")

    class PluginPackage:
        def joinpath(self, resource_name: str) -> MissingManifest:
            assert resource_name == "manifest.json"
            return MissingManifest()

    def generation_factory() -> str:
        nonlocal generation_called
        generation_called = True
        return "should-not-run"

    monkeypatch.setattr(
        bootstrap,
        "files",
        lambda package_name: (
            PluginPackage()
            if package_name == "mymcp.plugins.mnemosyne"
            else pytest.fail("bootstrap selected another package")
        ),
    )
    monkeypatch.setattr(
        mnemosyne,
        "get_memory_tool_settings",
        lambda: pytest.fail("settings resolved after manifest resource failure"),
    )

    with pytest.raises(OSError, match="^manifest unavailable$"):
        build_production_runtime(
            DEFAULT_CONFIGURATION,
            generation_factory=generation_factory,
        )

    assert generation_called is False


def test_adapter_definition_failure_precedes_settings_and_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generation_called = False

    def fail_definition():
        raise RuntimeError("definition failed")

    def generation_factory() -> str:
        nonlocal generation_called
        generation_called = True
        return "should-not-run"

    monkeypatch.setattr(
        bootstrap,
        "mnemosyne_plugin_definition",
        fail_definition,
        raising=False,
    )
    monkeypatch.setattr(
        mnemosyne,
        "get_memory_tool_settings",
        lambda: pytest.fail("settings resolved after definition failure"),
    )

    with pytest.raises(RuntimeError, match="^definition failed$"):
        build_production_runtime(
            DEFAULT_CONFIGURATION,
            generation_factory=generation_factory,
        )

    assert generation_called is False


def test_parity_failure_prevents_generation_and_partial_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generation_called = False

    def reject_parity(**_arguments) -> None:
        raise PluginContractError(
            PluginContractErrorCode.DEFINITION_MISMATCH,
            "plugin definition does not match manifest",
        )

    def generation_factory() -> str:
        nonlocal generation_called
        generation_called = True
        return "should-not-run"

    monkeypatch.setattr(
        bootstrap,
        "validate_plugin_contract",
        reject_parity,
        raising=False,
    )

    with pytest.raises(
        PluginContractError,
        match="^plugin definition does not match manifest$",
    ):
        build_production_runtime(
            DEFAULT_CONFIGURATION,
            generation_factory=generation_factory,
        )

    assert generation_called is False
