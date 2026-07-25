import re
from dataclasses import dataclass
from enum import StrEnum


_MAX_ID_LENGTH = 64
_PLUGIN_ID_PATTERN = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
_CAPABILITY_LOCAL_ID_PATTERN = re.compile(
    r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*\Z"
)
_SEMVER_PATTERN = re.compile(
    r"""
    (0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)
    (?:-
        (?:
            (?:0|[1-9][0-9]*)
            |(?:[0-9]*[A-Za-z-][0-9A-Za-z-]*)
        )
        (?:\.
            (?:
                (?:0|[1-9][0-9]*)
                |(?:[0-9]*[A-Za-z-][0-9A-Za-z-]*)
            )
        )*
    )?
    (?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?
    \Z
    """,
    re.VERBOSE,
)


def _is_strict_semver(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) <= _MAX_ID_LENGTH
        and _SEMVER_PATTERN.fullmatch(value) is not None
    )


@dataclass(frozen=True, slots=True)
class PluginId:
    value: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.value, str)
            or len(self.value) > _MAX_ID_LENGTH
            or _PLUGIN_ID_PATTERN.fullmatch(self.value) is None
        ):
            raise ValueError("invalid plugin id")


@dataclass(frozen=True, slots=True)
class PluginVersion:
    value: str

    def __post_init__(self) -> None:
        if not _is_strict_semver(self.value):
            raise ValueError("invalid plugin version")


class CapabilityKind(StrEnum):
    TOOL = "tool"


@dataclass(frozen=True, slots=True)
class CapabilityLocalId:
    value: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.value, str)
            or len(self.value) > _MAX_ID_LENGTH
            or _CAPABILITY_LOCAL_ID_PATTERN.fullmatch(self.value) is None
        ):
            raise ValueError("invalid capability local id")


@dataclass(frozen=True, slots=True)
class QualifiedCapabilityId:
    plugin_id: PluginId
    kind: CapabilityKind
    local_id: CapabilityLocalId

    def __post_init__(self) -> None:
        if (
            not isinstance(self.plugin_id, PluginId)
            or not isinstance(self.kind, CapabilityKind)
            or not isinstance(self.local_id, CapabilityLocalId)
        ):
            raise ValueError("invalid qualified capability id")


@dataclass(frozen=True, slots=True)
class ToolEffects:
    read_only: bool
    destructive: bool
    idempotent: bool
    open_world: bool

    def __post_init__(self) -> None:
        if any(
            type(value) is not bool
            for value in (
                self.read_only,
                self.destructive,
                self.idempotent,
                self.open_world,
            )
        ):
            raise ValueError("invalid tool effects")


class ConsentRequirement(StrEnum):
    NONE = "none"
    PER_CALL = "per_call"


@dataclass(frozen=True, slots=True)
class PublicToolBinding:
    capability: QualifiedCapabilityId
    public_name: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.capability, QualifiedCapabilityId)
            or not isinstance(self.public_name, str)
            or not self.public_name
        ):
            raise ValueError("invalid public tool binding")
