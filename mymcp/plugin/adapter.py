from dataclasses import dataclass

from mymcp.plugin.composition import PluginContribution
from mymcp.plugin.definition import PluginDefinition


@dataclass(frozen=True, slots=True)
class PluginAdapter:
    definition: PluginDefinition
    contribution: PluginContribution

    def __post_init__(self) -> None:
        if (
            not isinstance(self.definition, PluginDefinition)
            or not isinstance(self.contribution, PluginContribution)
        ):
            raise ValueError("invalid plugin adapter")
