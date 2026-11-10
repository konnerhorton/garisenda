"""What utilities and buildings share: the build record and station placement."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import numpy as np

from garisenda._units import Magnitude
from garisenda.sources._tunnel import IdealizedTunnel

if TYPE_CHECKING:
    from garisenda.buildings._building import Building
    from garisenda.utilities._utility import Utility

ElevationReference = Literal["invert", "axis", "crown"]
"""Which point of the pipe's section a given depth or elevation is at."""

ELEVATION_REFERENCES: tuple[ElevationReference, ...] = ("invert", "axis", "crown")

type Asset = Utility | Building
"""An asset a movement profile runs along: a utility or a building's wall."""


@dataclass(frozen=True)
class BuildRecord:
    """How an asset was built from station and offset.

    Attributes
    ----------
    tunnel : IdealizedTunnel
        The reference tunnel its station and offsets are measured from.
    station : float
        The station it crosses at, in m.
    start_offset, end_offset : float
        The offsets of its first and last vertex, in m, positive to the right
        looking up-station.
    orientation : {"perpendicular"}
        Its plan direction relative to the tunnel.
    elevation_reference : {"invert", "axis", "crown"} or None
        For a utility, the point of the pipe's section the given depth or
        elevation was at; None for a building, whose wall has no section.
    """

    tunnel: IdealizedTunnel
    station: float
    start_offset: float
    end_offset: float
    orientation: Literal["perpendicular"]
    elevation_reference: ElevationReference | None


def asset_name(asset: "Asset") -> tuple[str, str, str]:
    """Return an asset's label, id and input prefix.

    ``("Utility", id, "utility")`` or ``("Building", id, "building")``.
    """
    from garisenda.buildings._building import Building

    if isinstance(asset, Building):
        return "Building", asset.building_id, "building"
    return "Utility", asset.utility_id, "utility"


def perpendicular_vertices(
    tunnel: IdealizedTunnel,
    station: float,
    offsets: tuple[float, float],
    depth: float,
) -> list[tuple[float, float, float]]:
    """Return the (x, y, depth) of points square to a tunnel at a station.

    Each point is p0 + (station - s0) t + o n, with p0 the tunnel's
    reference point, s0 its station, t the unit tangent and n the unit normal
    to the right looking up-station.
    """
    along = station - tunnel.reference_station
    t, n = np.array(tunnel.tangent), np.array(tunnel.normal)
    origin = np.array([tunnel.reference_x, tunnel.reference_y]) + along * t
    return [
        (float(x), float(y), depth)
        for x, y in (origin + offset * n for offset in offsets)
    ]


def scalar(name: str, magnitude: Magnitude) -> float:
    """Return a single finite value, or raise `ValueError` naming it."""
    array = np.asarray(magnitude, dtype=np.float64)
    if array.ndim != 0:
        raise ValueError(
            f"{name} must be a single value, not an array of shape {array.shape}."
        )
    if not np.isfinite(array):
        raise ValueError(f"{name} must be finite, not {float(array)}.")
    return float(array)
