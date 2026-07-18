from dataclasses import dataclass
from enum import StrEnum

from mnemosyne.memory.errors import MemoryValidationError


class MemoryScope(StrEnum):
    SELF = "self"
    RELATIONSHIP = "relationship"
    PREFERENCE = "preference"
    PRACTICE = "practice"
    PROJECT = "project"
    KNOWLEDGE = "knowledge"


@dataclass(frozen=True)
class ScopeDefinition:
    scope: MemoryScope
    description: str
    directory: str
    namespace_kinds: tuple[str, ...]


SCOPE_DEFINITIONS = (
    ScopeDefinition(
        scope=MemoryScope.SELF,
        description="Who the user is and their enduring circumstances.",
        directory="self",
        namespace_kinds=("aspect",),
    ),
    ScopeDefinition(
        scope=MemoryScope.RELATIONSHIP,
        description=(
            "People, relationships, and the user's perspective about others."
        ),
        directory="relationship",
        namespace_kinds=("person", "group", "relationship"),
    ),
    ScopeDefinition(
        scope=MemoryScope.PREFERENCE,
        description="Choices the user explicitly wants respected.",
        directory="preference",
        namespace_kinds=("domain",),
    ),
    ScopeDefinition(
        scope=MemoryScope.PRACTICE,
        description="Routines, methods, habits, and actual ways of working.",
        directory="practice",
        namespace_kinds=("domain",),
    ),
    ScopeDefinition(
        scope=MemoryScope.PROJECT,
        description=(
            "Goals, state, decisions, and constraints of a bounded endeavor."
        ),
        directory="project",
        namespace_kinds=("project",),
    ),
    ScopeDefinition(
        scope=MemoryScope.KNOWLEDGE,
        description=(
            "User-approved reference material useful beyond one project, not ordinary "
            "general knowledge."
        ),
        directory="knowledge",
        namespace_kinds=("topic",),
    ),
)

SCOPE_VALUES = tuple(definition.scope.value for definition in SCOPE_DEFINITIONS)
SCOPE_BY_VALUE = {
    definition.scope.value: definition for definition in SCOPE_DEFINITIONS
}


def parse_scope(value: object) -> MemoryScope:
    definition = SCOPE_BY_VALUE.get(value) if isinstance(value, str) else None
    if definition is None:
        raise MemoryValidationError(
            "invalid_scope",
            "scope",
            "unknown memory scope",
        )
    return definition.scope


def get_scope_definition(scope: MemoryScope) -> ScopeDefinition:
    return SCOPE_BY_VALUE[scope.value]
