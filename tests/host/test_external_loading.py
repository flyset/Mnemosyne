import sys
from types import ModuleType

import pytest

from mymcp.host.configuration import parse_host_configuration_toml
from mymcp.host.external_plugins import ExternalPluginLoadError, load_external_plugins
from mymcp.plugin.adapter import PluginAdapter
from mymcp.plugin.composition import PluginContribution
from mymcp.plugin.manifest import parse_manifest_mapping


def _definition(plugin_id: str):
    return parse_manifest_mapping(
        {
            "manifest_version": 1,
            "id": plugin_id,
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


def _configuration(*plugins: tuple[str, bool, str]):
    lines = ["schema_version = 2"]
    for plugin_id, enabled, module in plugins:
        lines.extend(
            (
                "[[plugins]]",
                f'id = "{plugin_id}"',
                f"enabled = {str(enabled).lower()}",
                'manifest_path = "/opt/external/manifest.json"',
                f'module = "{module}"',
            )
        )
    return parse_host_configuration_toml("\n".join(lines))


def _adapter(definition):
    return PluginAdapter(
        definition,
        PluginContribution(definition.plugin_id, definition.version, ()),
    )


def test_loader_imports_real_fixture_and_returns_its_adapter() -> None:
    module_name = "tests.host.fixtures.operator_plugins.valid"
    sys.modules.pop(module_name, None)
    definition = _definition("external")

    adapters = load_external_plugins(
        _configuration(("external", True, module_name)),
        (definition,),
    )

    assert len(adapters) == 1
    assert isinstance(adapters[0], PluginAdapter)
    assert adapters[0].definition == definition


def test_loader_preserves_enabled_declaration_order_and_calls_each_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _definition("first")
    second = _definition("second")
    calls: list[str] = []

    def importer(name: str) -> ModuleType:
        calls.append(f"import:{name}")
        module = ModuleType(name)

        def entrypoint() -> PluginAdapter:
            calls.append(f"entrypoint:{name}")
            return _adapter(first if name.endswith("first") else second)

        module.mymcp_plugin_v1 = entrypoint  # type: ignore[attr-defined]
        return module

    import mymcp.host.external_plugins as external_plugins

    monkeypatch.setattr(external_plugins.importlib, "import_module", importer)
    adapters = load_external_plugins(
        _configuration(
            ("first", True, "operator_plugins.first"),
            ("disabled", False, "operator_plugins.disabled"),
            ("second", True, "operator_plugins.second"),
        ),
        (first, second),
    )

    assert [adapter.definition.plugin_id.value for adapter in adapters] == ["first", "second"]
    assert calls == [
        "import:operator_plugins.first",
        "entrypoint:operator_plugins.first",
        "import:operator_plugins.second",
        "entrypoint:operator_plugins.second",
    ]


def test_loader_does_not_import_when_unconfigured_or_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import mymcp.host.external_plugins as external_plugins

    monkeypatch.setattr(
        external_plugins.importlib,
        "import_module",
        lambda _name: pytest.fail("loader imported a disabled or absent declaration"),
    )

    assert load_external_plugins(_configuration(), ()) == ()
    assert load_external_plugins(
        _configuration(("external", False, "operator_plugins.external")), ()
    ) == ()


@pytest.mark.parametrize(
    ("module", "expected"),
    [
        (ModuleType("missing"), "external_plugin_entrypoint_invalid"),
        (ModuleType("noncallable"), "external_plugin_entrypoint_invalid"),
        (ModuleType("raising"), "external_plugin_entrypoint_invalid"),
        (ModuleType("wrong"), "external_plugin_contract_invalid"),
    ],
)
def test_loader_maps_invalid_entrypoints_to_bounded_errors(
    module: ModuleType, expected: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    definition = _definition("external")
    if module.__name__ == "noncallable":
        module.mymcp_plugin_v1 = object()  # type: ignore[attr-defined]
    elif module.__name__ == "raising":
        module.mymcp_plugin_v1 = lambda: (_ for _ in ()).throw(RuntimeError())  # type: ignore[attr-defined]
    elif module.__name__ == "wrong":
        module.mymcp_plugin_v1 = lambda: object()  # type: ignore[attr-defined]
    import mymcp.host.external_plugins as external_plugins

    monkeypatch.setattr(external_plugins.importlib, "import_module", lambda _name: module)

    with pytest.raises(ExternalPluginLoadError) as captured:
        load_external_plugins(
            _configuration(("external", True, "operator_plugins.external")),
            (definition,),
        )

    assert captured.value.code == expected
    assert captured.value.__cause__ is None


def test_loader_maps_import_failures_and_stops_without_partial_return(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _definition("first")
    second = _definition("second")
    calls: list[str] = []

    def importer(name: str) -> ModuleType:
        calls.append(name)
        if name.endswith("second"):
            raise ImportError("hidden")
        module = ModuleType(name)
        module.mymcp_plugin_v1 = lambda: _adapter(first)  # type: ignore[attr-defined]
        return module

    import mymcp.host.external_plugins as external_plugins

    monkeypatch.setattr(external_plugins.importlib, "import_module", importer)

    with pytest.raises(ExternalPluginLoadError) as captured:
        load_external_plugins(
            _configuration(
                ("first", True, "operator_plugins.first"),
                ("second", True, "operator_plugins.second"),
                ("later", True, "operator_plugins.later"),
            ),
            (first, second, _definition("later")),
        )

    assert captured.value.code == "external_plugin_import_failed"
    assert captured.value.__cause__ is None
    assert calls == ["operator_plugins.first", "operator_plugins.second"]


def test_loader_rejects_mismatched_preflight_input_before_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import mymcp.host.external_plugins as external_plugins

    monkeypatch.setattr(
        external_plugins.importlib,
        "import_module",
        lambda _name: pytest.fail("loader imported mismatched preflight input"),
    )
    configuration = _configuration(("external", True, "operator_plugins.external"))

    with pytest.raises(ValueError, match="^invalid external plugin loading input$"):
        load_external_plugins(configuration, ())
    with pytest.raises(ValueError, match="^invalid external plugin loading input$"):
        load_external_plugins(configuration, (_definition("different"),))
