import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from mymcp.plugin.composition import (
    ActivatedTool,
    HostToolOrigin,
    PluginContribution,
    compose_tool_surface as _compose_tool_surface,
)
from mymcp.mcp.tool_registry import ToolRegistration
from mymcp.mcp.tools import list_tools
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
from mymcp.settings import SERVER_NAME, SERVER_VERSION


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPOSITION_MODULE = PROJECT_ROOT / "mymcp" / "plugin" / "composition.py"


def _result(arguments: dict[str, Any]) -> dict[str, Any]:
    return {"content": [], "arguments": arguments}


def _host_registration(
    plugin_tools: tuple[dict[str, Any], ...],
) -> ToolRegistration:
    complete_tools = [dict(list_tools.TOOL), *plugin_tools]
    return ToolRegistration(
        tool=list_tools.TOOL,
        handler=lambda arguments: list_tools.handle(arguments, complete_tools),
    )


def compose_tool_surface(
    contributions: tuple[PluginContribution, ...],
    bindings: tuple[PublicToolBinding, ...],
):
    return _compose_tool_surface(contributions, bindings, _host_registration)


def _identity(plugin_id: str, local_id: str) -> QualifiedCapabilityId:
    return QualifiedCapabilityId(
        PluginId(plugin_id),
        CapabilityKind.TOOL,
        CapabilityLocalId(local_id),
    )


def _activated_tool(
    plugin_id: str,
    local_id: str,
    *,
    read_only: bool = True,
    consent: ConsentRequirement = ConsentRequirement.NONE,
) -> ActivatedTool:
    return ActivatedTool(
        capability=_identity(plugin_id, local_id),
        tool={
            "name": local_id,
            "description": f"Synthetic {local_id} Tool.",
            "inputSchema": {
                "type": "object",
                "properties": {"count": {"type": "integer"}},
            },
        },
        handler=_result,
        effects=ToolEffects(
            read_only=read_only,
            destructive=not read_only,
            idempotent=read_only,
            open_world=False,
        ),
        consent=consent,
    )


def _contribution(
    plugin_id: str,
    *local_ids: str,
) -> PluginContribution:
    return PluginContribution(
        plugin_id=PluginId(plugin_id),
        version=PluginVersion("1.0.0"),
        tools=tuple(_activated_tool(plugin_id, local_id) for local_id in local_ids),
    )


def _binding(plugin_id: str, local_id: str, public_name: str) -> PublicToolBinding:
    return PublicToolBinding(_identity(plugin_id, local_id), public_name)


def test_generic_composition_imports_no_concrete_tool_or_domain_package() -> None:
    tree = ast.parse(COMPOSITION_MODULE.read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert all(
        not imported.startswith(
            (
                "mymcp.mcp.tools",
                "mymcp.plugins",
                "mymcp.mnemosyne",
                "mymcp.memory",
            )
        )
        for imported in imports
    )


def test_activated_tool_snapshots_definition_and_is_frozen() -> None:
    source = {
        "name": "read_status",
        "description": "Read status.",
        "inputSchema": {
            "type": "object",
            "properties": {"count": {"type": "integer"}},
        },
    }
    activated = ActivatedTool(
        capability=_identity("example", "read_status"),
        tool=source,
        handler=_result,
        effects=ToolEffects(True, False, True, False),
        consent=ConsentRequirement.NONE,
    )
    source["name"] = "changed"
    source["inputSchema"]["properties"].clear()  # type: ignore[index]
    exposed = activated.tool
    exposed["name"] = "also_changed"

    assert activated.tool["name"] == "read_status"
    assert activated.tool["inputSchema"]["properties"] == {
        "count": {"type": "integer"}
    }
    with pytest.raises(FrozenInstanceError):
        activated.consent = ConsentRequirement.PER_CALL  # type: ignore[misc]


def test_plugin_contribution_snapshots_ordered_tools_and_is_frozen() -> None:
    first = _activated_tool("example", "first")
    second = _activated_tool("example", "second")
    tools = [first, second]

    contribution = PluginContribution(
        plugin_id=PluginId("example"),
        version=PluginVersion("1.0.0"),
        tools=tools,
    )
    tools.reverse()

    assert contribution.tools == (first, second)
    with pytest.raises(FrozenInstanceError):
        contribution.version = PluginVersion("2.0.0")  # type: ignore[misc]


def test_composition_projects_bound_names_and_retains_internal_metadata() -> None:
    read = _activated_tool("example", "read_status")
    mutate = _activated_tool(
        "example",
        "change_status",
        read_only=False,
        consent=ConsentRequirement.PER_CALL,
    )
    contribution = PluginContribution(
        PluginId("example"), PluginVersion("1.2.3"), (read, mutate)
    )
    bindings = (
        _binding("example", "read_status", "status"),
        _binding("example", "change_status", "status-change"),
    )

    surface = compose_tool_surface((contribution,), bindings)

    assert [tool["name"] for tool in surface.registry.tools] == [
        "list_tools",
        "status",
        "status-change",
    ]
    assert surface.registry.tools[1] == {
        **read.tool,
        "name": "status",
    }
    assert surface.registry.call_tool("status-change", {"count": 2}) == {
        "content": [],
        "arguments": {"count": 2},
    }
    assert surface.plugin_inventory == (
        (PluginId("example"), PluginVersion("1.2.3")),
    )
    assert surface.origins == {
        "list_tools": HostToolOrigin.HOST,
        "status": read.capability,
        "status-change": mutate.capability,
    }
    assert surface.effects == {
        read.capability: read.effects,
        mutate.capability: mutate.effects,
    }
    assert surface.consent == {
        read.capability: ConsentRequirement.NONE,
        mutate.capability: ConsentRequirement.PER_CALL,
    }
    assert surface.bindings == {
        read.capability: "status",
        mutate.capability: "status-change",
    }


def test_host_list_tools_reports_complete_final_bound_surface() -> None:
    surface = compose_tool_surface(
        (_contribution("example", "first", "second"),),
        (
            _binding("example", "first", "public_first"),
            _binding("example", "second", "public_second"),
        ),
    )

    assert surface.registry.call_tool("list_tools", {}) == {
        "content": [
            {
                "type": "text",
                "text": (
                    f"Server: {SERVER_NAME} {SERVER_VERSION}. Available tools: "
                    "list_tools, public_first, public_second"
                ),
            }
        ]
    }


def test_composition_preserves_cross_plugin_and_tool_order() -> None:
    surface = compose_tool_surface(
        (
            _contribution("first-plugin", "one", "two"),
            _contribution("second-plugin", "three", "four"),
        ),
        (
            _binding("first-plugin", "one", "one"),
            _binding("first-plugin", "two", "two"),
            _binding("second-plugin", "three", "three"),
            _binding("second-plugin", "four", "four"),
        ),
    )

    assert surface.plugin_inventory == (
        (PluginId("first-plugin"), PluginVersion("1.0.0")),
        (PluginId("second-plugin"), PluginVersion("1.0.0")),
    )
    assert [tool["name"] for tool in surface.registry.tools] == [
        "list_tools",
        "one",
        "two",
        "three",
        "four",
    ]


@pytest.mark.parametrize("public_name", ["list_tools", "mymcp_admin"])
def test_composition_rejects_host_reserved_public_names(public_name: str) -> None:
    with pytest.raises(ValueError, match="^reserved public tool name$"):
        compose_tool_surface(
            (_contribution("example", "first"),),
            (_binding("example", "first", public_name),),
        )


def test_composition_rejects_duplicate_plugin_ids_without_partial_result() -> None:
    with pytest.raises(ValueError, match="^duplicate plugin id$"):
        compose_tool_surface(
            (
                _contribution("example", "first"),
                _contribution("example", "second"),
            ),
            (
                _binding("example", "first", "first"),
                _binding("example", "second", "second"),
            ),
        )


def test_validation_failure_does_not_invoke_host_registration_factory() -> None:
    factory_called = False

    def host_registration_factory(
        plugin_tools: tuple[dict[str, Any], ...],
    ) -> ToolRegistration:
        nonlocal factory_called
        factory_called = True
        return _host_registration(plugin_tools)

    with pytest.raises(ValueError, match="^duplicate plugin id$"):
        _compose_tool_surface(
            (
                _contribution("example", "first"),
                _contribution("example", "second"),
            ),
            (
                _binding("example", "first", "first"),
                _binding("example", "second", "second"),
            ),
            host_registration_factory,
        )

    assert factory_called is False


def test_composition_rejects_duplicate_qualified_capabilities() -> None:
    capability = _activated_tool("example", "first")
    contribution = PluginContribution(
        PluginId("example"), PluginVersion("1.0.0"), (capability, capability)
    )

    with pytest.raises(ValueError, match="^duplicate qualified capability$"):
        compose_tool_surface(
            (contribution,),
            (_binding("example", "first", "first"),),
        )


def test_composition_rejects_contribution_capability_from_another_plugin() -> None:
    contribution = PluginContribution(
        PluginId("example"),
        PluginVersion("1.0.0"),
        (_activated_tool("other", "first"),),
    )

    with pytest.raises(ValueError, match="^capability plugin mismatch$"):
        compose_tool_surface(
            (contribution,),
            (_binding("other", "first", "first"),),
        )


def test_composition_rejects_duplicate_public_names() -> None:
    with pytest.raises(ValueError, match="^duplicate public tool name$"):
        compose_tool_surface(
            (_contribution("example", "first", "second"),),
            (
                _binding("example", "first", "shared"),
                _binding("example", "second", "shared"),
            ),
        )


def test_composition_rejects_duplicate_bindings_for_one_capability() -> None:
    with pytest.raises(ValueError, match="^duplicate capability binding$"):
        compose_tool_surface(
            (_contribution("example", "first"),),
            (
                _binding("example", "first", "first"),
                _binding("example", "first", "other"),
            ),
        )


def test_composition_rejects_missing_selected_capability_binding() -> None:
    with pytest.raises(ValueError, match="^missing capability binding$"):
        compose_tool_surface((_contribution("example", "first"),), ())


def test_composition_rejects_binding_for_unselected_capability() -> None:
    with pytest.raises(ValueError, match="^unknown capability binding$"):
        compose_tool_surface(
            (_contribution("example", "first"),),
            (
                _binding("example", "first", "first"),
                _binding("example", "other", "other"),
            ),
        )


def test_composed_mappings_and_discovery_are_defensive() -> None:
    contribution = _contribution("example", "first")
    surface = compose_tool_surface(
        (contribution,), (_binding("example", "first", "first"),)
    )
    discovered = surface.registry.tools
    discovered[1]["name"] = "changed"

    assert surface.registry.tools[1]["name"] == "first"
    with pytest.raises(TypeError):
        surface.origins["other"] = HostToolOrigin.HOST  # type: ignore[index]
    with pytest.raises(TypeError):
        surface.effects[contribution.tools[0].capability] = ToolEffects(  # type: ignore[index]
            False, False, False, False
        )
