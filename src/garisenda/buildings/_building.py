"""A building's wall and its station-and-offset builder."""

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from garisenda._asset import BuildRecord, perpendicular_vertices, scalar
from garisenda._inputs import InputRecord, record
from garisenda.sources._tunnel import IdealizedTunnel


@dataclass(frozen=True, init=False)
class Building:
    """A building's wall: a level straight line in plan at its foundation level.

    The wall is assessed as a beam of height `height` and unit width, following
    the ground's movement at its foundation level.

    Parameters
    ----------
    building_id : str
        Its name, used in results and error messages.
    vertices : array of lengths, shape (2, 2)
        The wall's two ends in plan as (x, y), in m if plain numbers. Walls
        with bends or steps (polylines) aren't supported yet.
    foundation_depth : length
        The depth of its foundation below the ground surface, in m if a plain
        number. Zero or more; the wall is level at this depth.
    height : length
        The wall's height H from foundation level to the eaves, in m if a
        plain number. Must be positive.

    Attributes
    ----------
    building_id : str
        Its name.
    vertices : numpy.ndarray, shape (2, 3)
        x, y and depth of the wall's ends at foundation level, in m, as a
        utility carries its axis.
    foundation_depth : float
        In m.
    height : float
        In m.
    built : BuildRecord or None
        How it was built from station and offset, or None if given directly.
    inputs : tuple of InputRecord
        Every input as used, each of kind ``"geometry"``.
    assumptions : tuple of str
        What its geometry assumes: for a built building, that its wall is
        perpendicular to the tunnel.

    Raises
    ------
    ValueError
        If there aren't exactly two plan vertices, a vertex isn't finite, the
        wall has zero length, the foundation depth is negative or not finite,
        the height isn't positive, or `building_id` is empty.
    """

    building_id: str
    vertices: npt.NDArray[np.float64]
    foundation_depth: float
    height: float
    built: BuildRecord | None
    inputs: tuple[InputRecord, ...]
    assumptions: tuple[str, ...]

    def __init__(
        self,
        *,
        building_id: str,
        vertices: object,
        foundation_depth: object,
        height: object,
    ) -> None:
        if not building_id:
            raise ValueError(
                f"building_id must be a non-empty string, not {building_id!r}."
            )
        where = f"Building {building_id!r}"
        points_m, vertices_record = record(
            "vertices", vertices, kind="geometry", unit="m", plain_number="read as SI"
        )
        plan = np.array(points_m, dtype=np.float64, ndmin=2)
        if plan.ndim != 2 or plan.shape[1] != 2:
            raise ValueError(
                f"{where}: vertices must be an array of shape (2, 2), rows of "
                f"(x, y) in plan, not shape {np.shape(points_m)}."
            )
        if len(plan) != 2:
            raise ValueError(
                f"{where} has {len(plan)} vertices: a wall is a straight line of "
                "two vertices; walls with bends or steps aren't supported yet. "
                "Assess each straight wall as its own building."
            )
        missing = ~np.isfinite(plan).all(axis=1)
        if missing.any():
            raise ValueError(
                f"{where}: every vertex needs finite x and y; these don't: "
                f"{np.flatnonzero(missing).tolist()}."
            )
        if np.linalg.norm(plan[1] - plan[0]) == 0:
            raise ValueError(f"{where}: its two vertices are the same point.")
        depth_m, depth_record = record(
            "foundation_depth",
            foundation_depth,
            kind="geometry",
            unit="m",
            plain_number="read as SI",
        )
        depth_m = float(depth_m)
        if not (np.isfinite(depth_m) and depth_m >= 0):
            raise ValueError(
                f"{where}: foundation_depth must be zero or more (below the ground "
                f"surface), not {depth_m} m."
            )
        height_m, height_record = record(
            "height", height, kind="geometry", unit="m", plain_number="read as SI"
        )
        height_m = float(height_m)
        if not (np.isfinite(height_m) and height_m > 0):
            raise ValueError(f"{where}: height must be positive, not {height_m} m.")
        points = np.column_stack([plan, np.full(2, depth_m)])
        points.setflags(write=False)
        values = {
            "building_id": building_id,
            "vertices": points,
            "foundation_depth": depth_m,
            "height": height_m,
            "built": None,
            "inputs": (vertices_record, depth_record, height_record),
            "assumptions": (),
        }
        for name, value in values.items():
            object.__setattr__(self, name, value)


def perpendicular_building(
    tunnel: IdealizedTunnel,
    *,
    building_id: str,
    station: object,
    start_offset: object,
    end_offset: object,
    height: object,
    foundation_depth: object = None,
    foundation_elevation: object = None,
    ground_elevation: object = None,
) -> Building:
    """Build a building's wall perpendicular to a tunnel at a station.

    The spreadsheet's input: a wall crossing the tunnel square at a station,
    from one offset to another. Its two ends are, at each offset o,

        p = p0 + (station - s0) t + o n,

    with p0 the tunnel's reference point, s0 its station, t the unit tangent
    and n the unit normal to the right looking up-station, at the foundation
    depth.

    Parameters
    ----------
    tunnel : IdealizedTunnel
        The reference tunnel.
    building_id : str
        The building's name.
    station : length
        The station it crosses at, in m if a plain number.
    start_offset, end_offset : length
        The offsets of the wall's first and last end, in m if plain numbers,
        positive to the right looking up-station. Distance along the wall runs
        from the start offset to the end offset.
    height : length
        The wall's height H from foundation level to the eaves, in m if a
        plain number.
    foundation_depth : length, optional
        The depth of its foundation below the ground surface.
    foundation_elevation, ground_elevation : length, optional
        Instead of `foundation_depth`: the elevation of the foundation with the
        ground elevation, both in the site's one length unit.

    Returns
    -------
    Building
        The building, with its `BuildRecord` (with no elevation reference), its
        inputs and the assumption that its wall is perpendicular to the tunnel.

    Raises
    ------
    TypeError
        If the level isn't given by exactly one of `foundation_depth` or
        `foundation_elevation` with `ground_elevation`.
    ValueError
        If the offsets are equal, the foundation is above the ground surface,
        the height isn't positive, or an input isn't finite.
    """
    inputs: list[InputRecord] = []

    def read(name: str, value: object) -> float:
        magnitude, entry = record(
            name, value, kind="geometry", unit="m", plain_number="read as SI"
        )
        number = scalar(name, magnitude)
        inputs.append(entry)
        return number

    station_m = read("station", station)
    start_m = read("start_offset", start_offset)
    end_m = read("end_offset", end_offset)
    if start_m == end_m:
        raise ValueError(
            f"Building {building_id!r}: start_offset and end_offset are both "
            f"{start_m} m, so the wall has no length."
        )
    height_m = read("height", height)

    given = [
        name
        for name, value in [
            ("foundation_depth", foundation_depth),
            ("foundation_elevation", foundation_elevation),
            ("ground_elevation", ground_elevation),
        ]
        if value is not None
    ]
    if given == ["foundation_depth"]:
        depth_m = read("foundation_depth", foundation_depth)
    elif given == ["foundation_elevation", "ground_elevation"]:
        depth_m = read("ground_elevation", ground_elevation) - read(
            "foundation_elevation", foundation_elevation
        )
    else:
        raise TypeError(
            "Give the building's level either as foundation_depth, or as "
            "foundation_elevation with ground_elevation; got "
            f"{', '.join(given) if given else 'none of them'}."
        )
    if depth_m < 0:
        raise ValueError(
            f"Building {building_id!r}: its foundation would be {-depth_m} m above "
            "the ground surface."
        )

    vertices = perpendicular_vertices(tunnel, station_m, (start_m, end_m), depth_m)
    building = Building(
        building_id=building_id,
        vertices=[vertex[:2] for vertex in vertices],
        foundation_depth=depth_m,
        height=height_m,
    )
    built = BuildRecord(
        tunnel=tunnel,
        station=station_m,
        start_offset=start_m,
        end_offset=end_m,
        orientation="perpendicular",
        elevation_reference=None,
    )
    assumptions = (
        f"Built perpendicular to the tunnel at station {station_m:g} m, whatever "
        "its real orientation.",
    )
    for name, value in {
        "built": built,
        "inputs": tuple(inputs),
        "assumptions": assumptions,
    }.items():
        object.__setattr__(building, name, value)
    return building
