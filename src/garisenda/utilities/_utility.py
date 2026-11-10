"""A utility line and its station-and-offset builder."""

from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt

from garisenda._inputs import InputRecord, record
from garisenda._units import Magnitude
from garisenda.sources._tunnel import IdealizedTunnel

ElevationReference = Literal["invert", "axis", "crown"]
"""Which point of the pipe's section a given depth or elevation is at."""

ELEVATION_REFERENCES: tuple[ElevationReference, ...] = ("invert", "axis", "crown")


@dataclass(frozen=True)
class BuildRecord:
    """How a utility was built from station and offset.

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
    elevation_reference : {"invert", "axis", "crown"}
        The point of the pipe's section the given depth or elevation was at.
    """

    tunnel: IdealizedTunnel
    station: float
    start_offset: float
    end_offset: float
    orientation: Literal["perpendicular"]
    elevation_reference: ElevationReference


@dataclass(frozen=True, init=False)
class Utility:
    """A utility line: a straight polyline in 3D with a diameter.

    Parameters
    ----------
    utility_id : str
        Its name, used in results and error messages.
    vertices : array of lengths, shape (N, 3)
        The vertices of its axis as (x, y, depth), in m if plain numbers, with
        depth positive downward from the ground surface. Two vertices, a
        straight line; polylines with bends aren't supported yet.
    diameter : length
        Its outside diameter, in m if a plain number. Must be positive.

    Attributes
    ----------
    utility_id : str
        Its name.
    vertices : numpy.ndarray, shape (N, 3)
        x, y and depth of its axis, in m.
    diameter : float
        In m.
    built : BuildRecord or None
        How it was built from station and offset, or None if given directly.
    inputs : tuple of InputRecord
        Every input as used, each of kind ``"geometry"``.
    assumptions : tuple of str
        What its geometry assumes: for a built utility, that it is
        perpendicular to the tunnel.

    Raises
    ------
    ValueError
        If there are fewer than two vertices, more than two (polylines with
        bends aren't supported yet), a vertex isn't finite or is above the
        ground surface, the line has zero length, the diameter isn't
        positive, or `utility_id` is empty.
    """

    utility_id: str
    vertices: npt.NDArray[np.float64]
    diameter: float
    built: BuildRecord | None
    inputs: tuple[InputRecord, ...]
    assumptions: tuple[str, ...]

    def __init__(self, *, utility_id: str, vertices: object, diameter: object) -> None:
        if not utility_id:
            raise ValueError(
                f"utility_id must be a non-empty string, not {utility_id!r}."
            )
        where = f"Utility {utility_id!r}"
        points_m, vertices_record = record(
            "vertices", vertices, kind="geometry", unit="m", plain_number="read as SI"
        )
        points = np.array(points_m, dtype=np.float64, ndmin=2)
        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError(
                f"{where}: vertices must be an array of shape (N, 3), rows of "
                f"(x, y, depth), not shape {np.shape(points_m)}."
            )
        if len(points) < 2:
            raise ValueError(
                f"{where}: a line needs at least two vertices, not {len(points)}."
            )
        if len(points) > 2:
            raise ValueError(
                f"{where} has {len(points)} vertices: only straight lines of two "
                "vertices are supported: a bent polyline's strain terms aren't "
                "implemented yet. Split it into straight lines."
            )
        missing = ~np.isfinite(points).all(axis=1)
        if missing.any():
            raise ValueError(
                f"{where}: every vertex needs finite x, y and depth; these "
                f"don't: {np.flatnonzero(missing).tolist()}."
            )
        above = points[:, 2] < 0
        if above.any():
            raise ValueError(
                f"{where}: vertices above the ground surface (negative depth): "
                f"{np.flatnonzero(above).tolist()}."
            )
        lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
        if (lengths == 0).any():
            raise ValueError(
                f"{where}: segments of zero length (repeated vertices) after "
                f"vertices {np.flatnonzero(lengths == 0).tolist()}."
            )
        diameter_m, diameter_record = record(
            "diameter", diameter, kind="geometry", unit="m", plain_number="read as SI"
        )
        diameter_m = float(diameter_m)
        if not (np.isfinite(diameter_m) and diameter_m > 0):
            raise ValueError(f"{where}: diameter must be positive, not {diameter_m} m.")
        points.setflags(write=False)
        values = {
            "utility_id": utility_id,
            "vertices": points,
            "diameter": diameter_m,
            "built": None,
            "inputs": (vertices_record, diameter_record),
            "assumptions": (),
        }
        for name, value in values.items():
            object.__setattr__(self, name, value)


def perpendicular_utility(
    tunnel: IdealizedTunnel,
    *,
    utility_id: str,
    station: object,
    start_offset: object,
    end_offset: object,
    diameter: object,
    elevation_reference: ElevationReference,
    depth: object = None,
    elevation: object = None,
    ground_elevation: object = None,
) -> Utility:
    """Build a straight utility perpendicular to a tunnel at a station.

    The spreadsheet's input: a utility crossing the tunnel square at a station,
    from one offset to another. Its two vertices are, at each offset o,

        p = p0 + (station - s0) t + o n,

    with p0 the tunnel's reference point, s0 its station, t the unit tangent
    and n the unit normal to the right looking up-station, both at
    the axis depth of the utility.

    Parameters
    ----------
    tunnel : IdealizedTunnel
        The reference tunnel.
    utility_id : str
        The utility's name.
    station : length
        The station it crosses at, in m if a plain number.
    start_offset, end_offset : length
        The offsets of its first and last vertex, in m if plain numbers,
        positive to the right looking up-station. Distance along the utility
        runs from the start offset to the end offset.
    diameter : length
        Its outside diameter, in m if a plain number.
    elevation_reference : {"invert", "axis", "crown"}
        The point of the pipe's section the depth or elevation is at. Required,
        with no default: survey data comes in all three, and a wrong guess
        shifts the pipe by its diameter.
    depth : length, optional
        The depth of that point below the ground surface.
    elevation, ground_elevation : length, optional
        Instead of `depth`: the elevation of that point with the ground
        elevation, both in the site's one length unit.

    Returns
    -------
    Utility
        The utility, with its `BuildRecord`, its inputs and the assumption that
        it is perpendicular to the tunnel. The axis depth is the given depth
        less D/2 for an invert, plus D/2 for a crown; for an invert or crown
        the wall thickness is ignored, which is recorded as an assumption.

    Raises
    ------
    TypeError
        If the level isn't given by exactly one of `depth` or `elevation` with
        `ground_elevation`.
    ValueError
        If `elevation_reference` isn't one of the three, the offsets are equal,
        the axis is above the ground surface, or an input isn't finite.
    """
    if elevation_reference not in ELEVATION_REFERENCES:
        raise ValueError(
            "elevation_reference must be one of "
            f"{', '.join(map(repr, ELEVATION_REFERENCES))}, "
            f"not {elevation_reference!r}."
        )
    inputs: list[InputRecord] = []

    def read(name: str, value: object) -> float:
        magnitude, entry = record(
            name, value, kind="geometry", unit="m", plain_number="read as SI"
        )
        number = _scalar(name, magnitude)
        inputs.append(entry)
        return number

    station_m = read("station", station)
    start_m = read("start_offset", start_offset)
    end_m = read("end_offset", end_offset)
    if start_m == end_m:
        raise ValueError(
            f"Utility {utility_id!r}: start_offset and end_offset are both "
            f"{start_m} m, so the utility has no length."
        )
    diameter_m = read("diameter", diameter)

    given = [
        name
        for name, value in [
            ("depth", depth),
            ("elevation", elevation),
            ("ground_elevation", ground_elevation),
        ]
        if value is not None
    ]
    if given == ["depth"]:
        level_depth = read("depth", depth)
    elif given == ["elevation", "ground_elevation"]:
        level_depth = read("ground_elevation", ground_elevation) - read(
            "elevation", elevation
        )
    else:
        raise TypeError(
            "Give the utility's level either as depth, or as elevation with "
            "ground_elevation; got "
            f"{', '.join(given) if given else 'none of them'}."
        )
    shift = {"invert": -diameter_m / 2, "axis": 0.0, "crown": diameter_m / 2}
    axis_depth = level_depth + shift[elevation_reference]
    if axis_depth < 0:
        raise ValueError(
            f"Utility {utility_id!r}: its axis would be {-axis_depth} m above the "
            f"ground surface (the {elevation_reference} at depth {level_depth} m)."
        )

    along = station_m - tunnel.reference_station
    t, n = np.array(tunnel.tangent), np.array(tunnel.normal)
    origin = np.array([tunnel.reference_x, tunnel.reference_y]) + along * t
    vertices = [(*(origin + offset * n), axis_depth) for offset in (start_m, end_m)]

    utility = Utility(utility_id=utility_id, vertices=vertices, diameter=diameter_m)
    assumptions = [
        f"Built perpendicular to the tunnel at station {station_m:g} m, whatever "
        "its real orientation."
    ]
    if elevation_reference != "axis":
        assumptions.append(
            f"The {elevation_reference} is converted to the axis with half the given "
            f"diameter ({diameter_m / 2:g} m), ignoring the wall thickness: an "
            f"{elevation_reference} measured inside the pipe puts the axis off by "
            "the wall thickness."
        )
    built = BuildRecord(
        tunnel=tunnel,
        station=station_m,
        start_offset=start_m,
        end_offset=end_m,
        orientation="perpendicular",
        elevation_reference=elevation_reference,
    )
    for name, value in {
        "built": built,
        "inputs": tuple(inputs),
        "assumptions": tuple(assumptions),
    }.items():
        object.__setattr__(utility, name, value)
    return utility


def _scalar(name: str, magnitude: Magnitude) -> float:
    array = np.asarray(magnitude, dtype=np.float64)
    if array.ndim != 0:
        raise ValueError(
            f"{name} must be a single value, not an array of shape {array.shape}."
        )
    if not np.isfinite(array):
        raise ValueError(f"{name} must be finite, not {float(array)}.")
    return float(array)
