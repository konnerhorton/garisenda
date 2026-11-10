"""Sources of ground movement: each produces a movement field."""

from garisenda.sources._movement import Flag, MethodRecord, Movement, Source, Verdict
from garisenda.sources._superposition import Superposition
from garisenda.sources._transverse import (
    TransverseSurfaceTrough,
    transverse_surface_trough,
)
from garisenda.sources._transverse_trough import (
    TransverseTrough,
    transverse_trough,
)
from garisenda.sources._trough_width import (
    TroughWidth,
    linear_trough_width,
    mair_trough_width,
)
from garisenda.sources._tunnel import IdealizedTunnel

__all__ = [
    "Flag",
    "IdealizedTunnel",
    "MethodRecord",
    "Movement",
    "Source",
    "Superposition",
    "TransverseSurfaceTrough",
    "TransverseTrough",
    "TroughWidth",
    "Verdict",
    "linear_trough_width",
    "mair_trough_width",
    "transverse_surface_trough",
    "transverse_trough",
]
