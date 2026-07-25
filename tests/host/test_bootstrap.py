from itertools import product

import pytest

from mymcp.host import bootstrap
from mymcp.host.bootstrap import build_production_runtime
from mymcp.mcp.integrations import mnemosyne
from mymcp.mcp.integrations.mnemosyne import (
    build_mnemosyne_contribution,
    build_mnemosyne_registrations,
)
from mymcp.mnemosyne.configuration import MemoryToolSettings
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


DEFAULT_NAMES = ["memory_recall", "memory_list", "memory_inspect"]
MUTATION_NAMES = [
    "memory_archive",
    "memory_restore",
    "memory_remember",
    "memory_revise",
    "memory_forget",
]


def _identity(name: str) -> QualifiedCapabilityId:
    return QualifiedCapabilityId(
        PluginId("mnemosyne"),
        CapabilityKind.TOOL,
        CapabilityLocalId(name),
    )


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
        generation_factory=lambda: "test-generation"
    )
    expected = _selected_names(settings)

    assert settings_calls == 1
    assert runtime.generation.value == "test-generation"
    assert runtime.plugin_inventory == (
        (PluginId("mnemosyne"), PluginVersion("0.1.0")),
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
    assert contribution.version == PluginVersion("0.1.0")
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
        generation_factory=lambda: "test-generation"
    )

    assert runtime.registry.call_tool("list_tools", {}) == {
        "content": [
            {
                "type": "text",
                "text": (
                    "Server: mnemosyne 0.1.4. Available tools: "
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

    with pytest.raises(ValueError, match="^duplicate qualified capability$"):
        build_production_runtime(generation_factory=generation_factory)

    assert generation_called is False
