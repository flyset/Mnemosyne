from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from mymcp.host.runtime import (
    HostRuntime,
    HostRuntimeCompositionError,
    RuntimeGenerationId,
    build_host_runtime,
)
from mymcp.mcp.tool_registry import ToolRegistration
from mymcp.mcp.tools import list_tools
from mymcp.plugin.composition import ActivatedTool, HostToolOrigin, PluginContribution
from mymcp.plugin.contracts import (
    CapabilityKind,
    CapabilityLocalId,
    ConsentRequirement,
    PluginId,
    PluginVersion,
    PublicToolBinding,
    QualifiedCapabilityId,
    ToolEffects,
)


def _result(arguments: dict[str, Any]) -> dict[str, Any]:
    return {"content": [], "arguments": arguments}


def _identity(plugin_id: str, local_id: str) -> QualifiedCapabilityId:
    return QualifiedCapabilityId(
        PluginId(plugin_id),
        CapabilityKind.TOOL,
        CapabilityLocalId(local_id),
    )


def _contribution(plugin_id: str, *local_ids: str) -> PluginContribution:
    return PluginContribution(
        plugin_id=PluginId(plugin_id),
        version=PluginVersion("1.0.0"),
        tools=tuple(
            ActivatedTool(
                capability=_identity(plugin_id, local_id),
                tool={
                    "name": local_id,
                    "description": f"Synthetic {local_id} Tool.",
                    "inputSchema": {"type": "object", "properties": {}},
                },
                handler=_result,
                effects=ToolEffects(True, False, True, False),
                consent=ConsentRequirement.NONE,
            )
            for local_id in local_ids
        ),
    )


def _binding(plugin_id: str, local_id: str) -> PublicToolBinding:
    return PublicToolBinding(_identity(plugin_id, local_id), local_id)


def _host_registration(
    plugin_tools: tuple[dict[str, Any], ...],
) -> ToolRegistration:
    complete_tools = [dict(list_tools.TOOL), *plugin_tools]
    return ToolRegistration(
        tool=list_tools.TOOL,
        handler=lambda arguments: list_tools.handle(arguments, complete_tools),
    )


@pytest.mark.parametrize(
    "value",
    ["generation-1", "gen_0123456789abcdef", "A.b~c", "a" * 128],
)
def test_runtime_generation_id_accepts_bounded_opaque_safe_tokens(value: str) -> None:
    assert RuntimeGenerationId(value).value == value


@pytest.mark.parametrize(
    "value",
    ["", " bad", "bad/id", "bad value", "a" * 129],
)
def test_runtime_generation_id_rejects_invalid_tokens(value: str) -> None:
    with pytest.raises(ValueError, match="^invalid runtime generation id$"):
        RuntimeGenerationId(value)


def test_runtime_generation_id_is_frozen() -> None:
    generation = RuntimeGenerationId("generation-1")

    with pytest.raises(FrozenInstanceError):
        generation.value = "generation-2"  # type: ignore[misc]


def test_runtime_retains_complete_immutable_composed_state() -> None:
    first = _contribution("first-plugin", "one", "two")
    second = _contribution("second-plugin", "three")

    runtime = build_host_runtime(
        (first, second),
        (
            _binding("first-plugin", "one"),
            _binding("first-plugin", "two"),
            _binding("second-plugin", "three"),
        ),
        _host_registration,
        generation_factory=lambda: "test-generation",
    )

    assert isinstance(runtime, HostRuntime)
    assert runtime.generation == RuntimeGenerationId("test-generation")
    assert runtime.plugin_inventory == (
        (PluginId("first-plugin"), PluginVersion("1.0.0")),
        (PluginId("second-plugin"), PluginVersion("1.0.0")),
    )
    assert [tool["name"] for tool in runtime.registry.tools] == [
        "list_tools",
        "one",
        "two",
        "three",
    ]
    assert runtime.origins["list_tools"] is HostToolOrigin.HOST
    assert runtime.origins["one"] == _identity("first-plugin", "one")
    assert runtime.effects[_identity("first-plugin", "one")].read_only is True
    assert runtime.consent[_identity("first-plugin", "one")] is ConsentRequirement.NONE
    assert runtime.bindings[_identity("second-plugin", "three")] == "three"
    with pytest.raises(FrozenInstanceError):
        runtime.generation = RuntimeGenerationId("other")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        runtime.plugin_inventory = ()  # type: ignore[misc]
    with pytest.raises(TypeError):
        runtime.origins["other"] = HostToolOrigin.HOST  # type: ignore[index]
    with pytest.raises(TypeError):
        runtime.effects[_identity("first-plugin", "one")] = ToolEffects(  # type: ignore[index]
            False, False, False, False
        )
    with pytest.raises(TypeError):
        runtime.consent[_identity("first-plugin", "one")] = (  # type: ignore[index]
            ConsentRequirement.PER_CALL
        )
    with pytest.raises(TypeError):
        runtime.bindings[_identity("first-plugin", "one")] = "other"  # type: ignore[index]


def test_generation_factory_runs_after_complete_composition_validation() -> None:
    generation_called = False

    def generation_factory() -> str:
        nonlocal generation_called
        generation_called = True
        return "should-not-run"

    with pytest.raises(ValueError, match="^duplicate plugin id$"):
        build_host_runtime(
            (
                _contribution("example", "one"),
                _contribution("example", "two"),
            ),
            (
                _binding("example", "one"),
                _binding("example", "two"),
            ),
            _host_registration,
            generation_factory=generation_factory,
        )

    assert generation_called is False


def test_runtime_wraps_only_composition_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import mymcp.host.runtime as runtime_module

    generation_called = False
    monkeypatch.setattr(
        runtime_module,
        "compose_tool_surface",
        lambda *_: (_ for _ in ()).throw(ValueError("hidden composition detail")),
    )

    with pytest.raises(HostRuntimeCompositionError) as captured:
        build_host_runtime(
            (_contribution("example", "one"),),
            (_binding("example", "one"),),
            _host_registration,
            generation_factory=lambda: generation_called,
        )

    assert str(captured.value) == "hidden composition detail"
    assert captured.value.__cause__ is None
    assert generation_called is False


def test_runtime_leaves_generation_factory_errors_unchanged() -> None:
    with pytest.raises(RuntimeError, match="^generation failed$"):
        build_host_runtime(
            (_contribution("example", "one"),),
            (_binding("example", "one"),),
            _host_registration,
            generation_factory=lambda: (_ for _ in ()).throw(RuntimeError("generation failed")),
        )


def test_generation_factory_runs_after_host_tool_validation() -> None:
    generation_called = False

    def invalid_host_registration(
        plugin_tools: tuple[dict[str, Any], ...],
    ) -> ToolRegistration:
        return ToolRegistration(
            tool={
                "name": "not_list_tools",
                "description": "Invalid host Tool.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            handler=_result,
        )

    def generation_factory() -> str:
        nonlocal generation_called
        generation_called = True
        return "should-not-run"

    with pytest.raises(ValueError, match="^invalid host tool registration$"):
        build_host_runtime(
            (_contribution("example", "one"),),
            (_binding("example", "one"),),
            invalid_host_registration,
            generation_factory=generation_factory,
        )

    assert generation_called is False


def test_generation_factory_does_not_run_after_binding_validation_failure() -> None:
    generation_called = False

    def generation_factory() -> str:
        nonlocal generation_called
        generation_called = True
        return "should-not-run"

    with pytest.raises(ValueError, match="^reserved public tool name$"):
        build_host_runtime(
            (_contribution("example", "one"),),
            (PublicToolBinding(_identity("example", "one"), "list_tools"),),
            _host_registration,
            generation_factory=generation_factory,
        )

    assert generation_called is False


def test_generation_factory_runs_after_registry_schema_validation() -> None:
    generation_called = False

    def malformed_host_registration(
        plugin_tools: tuple[dict[str, Any], ...],
    ) -> ToolRegistration:
        return ToolRegistration(
            tool={"name": "list_tools", "description": "Malformed host Tool."},
            handler=_result,
        )

    def generation_factory() -> str:
        nonlocal generation_called
        generation_called = True
        return "should-not-run"

    with pytest.raises(ValueError, match="^invalid tool registration$"):
        build_host_runtime(
            (_contribution("example", "one"),),
            (_binding("example", "one"),),
            malformed_host_registration,
            generation_factory=generation_factory,
        )

    assert generation_called is False


def test_invalid_generation_factory_output_returns_no_runtime() -> None:
    with pytest.raises(ValueError, match="^invalid runtime generation id$"):
        build_host_runtime(
            (_contribution("example", "one"),),
            (_binding("example", "one"),),
            _host_registration,
            generation_factory=lambda: "invalid/generation",
        )


def test_default_generation_factory_produces_independent_opaque_identities() -> None:
    first = build_host_runtime((), (), _host_registration)
    second = build_host_runtime((), (), _host_registration)

    assert first.generation != second.generation
    assert RuntimeGenerationId(first.generation.value) == first.generation
    assert RuntimeGenerationId(second.generation.value) == second.generation


def test_independent_runtimes_keep_separate_registries_and_generations() -> None:
    first = build_host_runtime(
        (_contribution("first-plugin", "first"),),
        (_binding("first-plugin", "first"),),
        _host_registration,
        generation_factory=lambda: "first-generation",
    )
    second = build_host_runtime(
        (_contribution("second-plugin", "second"),),
        (_binding("second-plugin", "second"),),
        _host_registration,
        generation_factory=lambda: "second-generation",
    )

    assert [tool["name"] for tool in first.registry.tools] == ["list_tools", "first"]
    assert [tool["name"] for tool in second.registry.tools] == [
        "list_tools",
        "second",
    ]
    assert first.generation == RuntimeGenerationId("first-generation")
    assert second.generation == RuntimeGenerationId("second-generation")


def test_same_inputs_produce_non_aliasing_runtime_containers() -> None:
    contribution = _contribution("example", "one")
    bindings = (_binding("example", "one"),)

    first = build_host_runtime(
        (contribution,),
        bindings,
        _host_registration,
        generation_factory=lambda: "first-generation",
    )
    second = build_host_runtime(
        (contribution,),
        bindings,
        _host_registration,
        generation_factory=lambda: "second-generation",
    )
    first_discovery = first.registry.tools
    first_discovery[1]["name"] = "changed"

    assert first.registry is not second.registry
    assert first.origins is not second.origins
    assert first.effects is not second.effects
    assert first.consent is not second.consent
    assert first.bindings is not second.bindings
    assert second.registry.tools[1]["name"] == "one"
