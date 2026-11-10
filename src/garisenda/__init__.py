"""Ground movements from tunneling and their effect on utilities and buildings."""

from importlib.metadata import version

from garisenda import buildings, plot, presets, sources, utilities
from garisenda._inputs import Sourced
from garisenda._result import Result
from garisenda._sweep import sweep
from garisenda._units import units
from garisenda.buildings._check import check_building
from garisenda.profile import movement_profile
from garisenda.sources._superposition import superpose
from garisenda.utilities._continuous_pipe import check_continuous_pipe
from garisenda.utilities._jointed_pipe import check_jointed_pipe

__version__ = version("garisenda")

__all__ = [
    "Result",
    "Sourced",
    "__version__",
    "buildings",
    "check_building",
    "check_continuous_pipe",
    "check_jointed_pipe",
    "movement_profile",
    "plot",
    "presets",
    "sources",
    "superpose",
    "sweep",
    "units",
    "utilities",
]
