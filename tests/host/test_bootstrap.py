from itertools import product
from importlib.resources import files

import pytest

from mymcp.host import bootstrap
from mymcp.host.bootstrap import build_production_runtime
from mymcp.host.configuration import (
    HostConfiguration,
    HostConfigurationError,
    parse_host_configuration_toml,
)
from mymcp.plugins.mnemosyne import plugin as mnemosyne
from mymcp.plugins.mnemosyne.plugin import (
    build_mnemosyne_contribution,
    build_mnemosyne_registrations,
)
from mymcp.plugins.mnemosyne.configuration import MemoryToolSettings
from mymcp.plugin.composition import HostToolOrigin, PluginContribution
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
                    "Server: mymcp 0.3.0. Available tools: "
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
