from mymcp.mcp.tool_registry import ToolRegistration
from mymcp.plugins.mnemosyne.mcp.tools import (
    memory_archive,
    memory_forget,
    memory_inspect,
    memory_list,
    memory_recall,
    memory_remember,
    memory_revise,
    memory_restore,
)
from mymcp.plugins.mnemosyne.memory.listing import MemoryListResult, MemoryListSelector
from mymcp.plugins.mnemosyne.memory.records import (
    LegacyMemoryRecordV1,
    LegacyMemoryReference,
    MemoryDraft,
    MemoryRecordV2,
    MemoryReference,
    MemoryRevision,
)
from mymcp.plugins.mnemosyne.memory.retrieval import MemoryMatch
from mymcp.plugins.mnemosyne.memory.scopes import MemoryScope
from mymcp.plugins.mnemosyne.memory.service import ForgetResult, MemoryResult, MemoryService
from mymcp.plugins.mnemosyne.memory.store import FilesystemMemoryStore
from mymcp.plugins.mnemosyne.configuration import (
    get_memory_root,
    get_memory_tool_settings,
)
from mymcp.plugin.composition import ActivatedTool, PluginContribution
from mymcp.plugin.contracts import (
    CapabilityKind,
    CapabilityLocalId,
    ConsentRequirement,
    PluginId,
    PluginVersion,
    QualifiedCapabilityId,
    ToolEffects,
)
from mymcp.plugin.definition import (
    AuthorityDeclaration,
    CapabilityContractVersion,
    CapabilityDeclaration,
    ConfigurationDeclaration,
    ConfigurationSchema,
    ConfigurationSchemaVersion,
    ConfigurationType,
    FilesystemAuthority,
    HostApiRange,
    HostApiVersion,
    ManifestVersion,
    PluginDataSchemaVersion,
    PluginDefinition,
    PluginDescription,
    PluginTitle,
)


_PLUGIN_ID = PluginId("mnemosyne")
_PLUGIN_VERSION = PluginVersion("0.2.0")
_READ_ONLY_EFFECTS = ToolEffects(True, False, True, False)
_MUTATING_EFFECTS = ToolEffects(False, False, True, False)
_DESTRUCTIVE_EFFECTS = ToolEffects(False, True, True, False)


def _capability(
    local_id: str,
    version: str,
    effects: ToolEffects,
    consent: ConsentRequirement,
) -> CapabilityDeclaration:
    return CapabilityDeclaration(
        kind=CapabilityKind.TOOL,
        local_id=CapabilityLocalId(local_id),
        version=CapabilityContractVersion(version),
        effects=effects,
        consent=consent,
    )


_CAPABILITY_DECLARATIONS = (
    _capability(
        "memory_recall", "1.1.0", _READ_ONLY_EFFECTS, ConsentRequirement.NONE
    ),
    _capability(
        "memory_list", "1.0.0", _READ_ONLY_EFFECTS, ConsentRequirement.NONE
    ),
    _capability(
        "memory_inspect", "1.0.0", _READ_ONLY_EFFECTS, ConsentRequirement.NONE
    ),
    _capability(
        "memory_archive",
        "1.0.0",
        _MUTATING_EFFECTS,
        ConsentRequirement.PER_CALL,
    ),
    _capability(
        "memory_restore",
        "1.0.0",
        _MUTATING_EFFECTS,
        ConsentRequirement.PER_CALL,
    ),
    _capability(
        "memory_remember",
        "1.0.0",
        _MUTATING_EFFECTS,
        ConsentRequirement.PER_CALL,
    ),
    _capability(
        "memory_revise",
        "1.0.0",
        _DESTRUCTIVE_EFFECTS,
        ConsentRequirement.PER_CALL,
    ),
    _capability(
        "memory_forget",
        "1.0.0",
        _DESTRUCTIVE_EFFECTS,
        ConsentRequirement.PER_CALL,
    ),
)


def mnemosyne_plugin_definition() -> PluginDefinition:
    return PluginDefinition(
        manifest_version=ManifestVersion(1),
        plugin_id=_PLUGIN_ID,
        title=PluginTitle("Mnemosyne"),
        description=PluginDescription("User-governed local memory for MyMCP."),
        version=_PLUGIN_VERSION,
        requires=HostApiRange(HostApiVersion(1), HostApiVersion(1)),
        capabilities=_CAPABILITY_DECLARATIONS,
        configuration=ConfigurationDeclaration(
            schema_version=ConfigurationSchemaVersion(1),
            schema=ConfigurationSchema(
                type=ConfigurationType.OBJECT,
                properties=(),
                required=(),
                additional_properties=False,
            ),
        ),
        secret_references=(),
        data_schema_version=PluginDataSchemaVersion(1),
        authority=AuthorityDeclaration(
            filesystem=(
                FilesystemAuthority.DATA_READ,
                FilesystemAuthority.DATA_WRITE,
            ),
            network=False,
        ),
    )


def _memory_service(*, mutations_enabled: bool) -> MemoryService:
    return MemoryService(
        FilesystemMemoryStore(get_memory_root()),
        mutations_enabled=mutations_enabled,
    )


def _recall(
    scope: MemoryScope,
    query: str,
    tags: list[str],
    namespace_id: str | None = None,
) -> list[MemoryMatch]:
    service = _memory_service(mutations_enabled=False)
    if namespace_id is None:
        return service.recall(scope, query, tags)
    return service.recall(scope, query, tags, namespace_id=namespace_id)


def _list_memories(
    selector: MemoryListSelector,
    page_size: int | None,
    cursor: str | None,
) -> MemoryListResult:
    return _memory_service(mutations_enabled=False).list_memories(
        selector,
        page_size=page_size,
        cursor=cursor,
    )


def _inspect(
    reference: MemoryReference | LegacyMemoryReference,
) -> MemoryRecordV2 | LegacyMemoryRecordV1:
    return _memory_service(mutations_enabled=False).inspect(reference)


def _remember(draft: MemoryDraft) -> MemoryResult:
    return _memory_service(mutations_enabled=True).remember(draft)


def _archive(reference: MemoryReference, revision: int) -> MemoryResult:
    return _memory_service(mutations_enabled=True).archive(
        reference,
        expected_revision=revision,
    )


def _restore(reference: MemoryReference, revision: int) -> MemoryResult:
    return _memory_service(mutations_enabled=True).restore(
        reference,
        expected_revision=revision,
    )


def _revise(
    reference: MemoryReference,
    revision: MemoryRevision,
) -> MemoryResult:
    return _memory_service(mutations_enabled=True).revise(reference, revision)


def _forget(reference: MemoryReference, revision: int) -> ForgetResult:
    return _memory_service(mutations_enabled=True).forget(
        reference,
        expected_revision=revision,
    )


def build_mnemosyne_registrations(
    memory_remember_enabled: bool,
    *,
    memory_archive_restore_enabled: bool = False,
    memory_forget_enabled: bool = False,
    memory_revise_enabled: bool = False,
) -> tuple[ToolRegistration, ...]:
    registrations = [
        ToolRegistration(
            tool=memory_recall.TOOL,
            handler=lambda arguments: memory_recall.handle(
                arguments,
                recall_operation=_recall,
            ),
        ),
        ToolRegistration(
            tool=memory_list.TOOL,
            handler=lambda arguments: memory_list.handle(
                arguments,
                list_operation=_list_memories,
            ),
        ),
        ToolRegistration(
            tool=memory_inspect.TOOL,
            handler=lambda arguments: memory_inspect.handle(
                arguments,
                inspect_operation=_inspect,
            ),
        ),
    ]

    if memory_archive_restore_enabled:
        registrations.extend(
            (
                ToolRegistration(
                    tool=memory_archive.TOOL,
                    handler=lambda arguments: memory_archive.handle(
                        arguments,
                        archive_operation=_archive,
                        mutations_enabled=True,
                    ),
                ),
                ToolRegistration(
                    tool=memory_restore.TOOL,
                    handler=lambda arguments: memory_restore.handle(
                        arguments,
                        restore_operation=_restore,
                        mutations_enabled=True,
                    ),
                ),
            )
        )

    if memory_remember_enabled:
        registrations.append(
            ToolRegistration(
                tool=memory_remember.TOOL,
                handler=lambda arguments: memory_remember.handle(
                    arguments,
                    remember_operation=_remember,
                    mutations_enabled=True,
                ),
            )
        )

    if memory_revise_enabled:
        registrations.append(
            ToolRegistration(
                tool=memory_revise.TOOL,
                handler=lambda arguments: memory_revise.handle(
                    arguments,
                    revise_operation=_revise,
                    mutations_enabled=True,
                ),
            )
        )

    if memory_forget_enabled:
        registrations.append(
            ToolRegistration(
                tool=memory_forget.TOOL,
                handler=lambda arguments: memory_forget.handle(
                    arguments,
                    forget_operation=_forget,
                    mutations_enabled=True,
                ),
            )
        )

    return tuple(registrations)


def build_mnemosyne_contribution(
    memory_remember_enabled: bool,
    *,
    memory_archive_restore_enabled: bool = False,
    memory_forget_enabled: bool = False,
    memory_revise_enabled: bool = False,
) -> PluginContribution:
    registrations = build_mnemosyne_registrations(
        memory_remember_enabled=memory_remember_enabled,
        memory_archive_restore_enabled=memory_archive_restore_enabled,
        memory_forget_enabled=memory_forget_enabled,
        memory_revise_enabled=memory_revise_enabled,
    )
    declarations = {
        capability.local_id.value: capability
        for capability in _CAPABILITY_DECLARATIONS
    }
    activated_tools: list[ActivatedTool] = []
    for registration in registrations:
        name = registration.tool["name"]
        declaration = declarations[name]
        activated_tools.append(
            ActivatedTool(
                capability=QualifiedCapabilityId(
                    plugin_id=_PLUGIN_ID,
                    kind=declaration.kind,
                    local_id=declaration.local_id,
                ),
                tool=registration.tool,
                handler=registration.handler,
                effects=declaration.effects,
                consent=declaration.consent,
            )
        )
    return PluginContribution(
        plugin_id=_PLUGIN_ID,
        version=_PLUGIN_VERSION,
        tools=activated_tools,
    )


def mnemosyne_contribution() -> PluginContribution:
    settings = get_memory_tool_settings()
    return build_mnemosyne_contribution(
        memory_remember_enabled=settings.remember_enabled,
        memory_archive_restore_enabled=settings.archive_restore_enabled,
        memory_forget_enabled=settings.forget_enabled,
        memory_revise_enabled=settings.revise_enabled,
    )
