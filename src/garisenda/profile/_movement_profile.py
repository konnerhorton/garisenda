"""The ground's movement resolved along a utility (SPEC §3)."""

import math
import re

import numpy as np
import numpy.typing as npt
import pandas as pd

from garisenda._inputs import judgments, record
from garisenda._result import Result, empty_checks
from garisenda.sources._movement import MethodRecord, Source, worst
from garisenda.utilities._utility import Utility

MERGE_TOLERANCE = 1e-6
"""Distance in m within which two stations are merged into one."""

MAXIMUM_STATIONS = 1_000_000
"""The most stations a profile may have."""

GREENFIELD = (
    "Assets follow the ground: greenfield, no soil-structure interaction (SPEC §1.3)."
)

METHOD = MethodRecord(
    "Movement profile along a straight utility",
    (
        "stations: 0, L, every k spacing < L, and the source's critical distances",
        "a = (end - start) / L, l = (a_y, -a_x, 0) / |(a_x, a_y)|, v = l x a",
        "along = u.a, vertical = u.v, lateral = u.l",
        "d(u.e)/ds = e_i (du_i/dx_j) a_j",
        "d2(u.e)/ds2 = e_i (d2u_i/dx_j dx_k) a_j a_k",
    ),
    "Exact derivatives of the source's field along a straight line (SPEC §3); "
    "no external source.",
)

UNITS = {
    "distance": "m",
    "x": "m",
    "y": "m",
    "depth": "m",
    "station": "m",
    "offset": "m",
    "along": "m",
    "vertical": "m",
    "lateral": "m",
    "along_strain": "dimensionless",
    "along_strain_gradient": "1/m",
    "vertical_slope": "dimensionless",
    "vertical_curvature": "1/m",
    "lateral_slope": "dimensionless",
    "lateral_curvature": "1/m",
}

FloatArray = npt.NDArray[np.float64]


@judgments(
    spacing="it sets the stations between the source's critical points (which "
    "are always included), and so how finely the profile is resolved and drawn. "
    "Pass a length, e.g. spacing=1 * gs.units.m."
)
def movement_profile(utility: Utility, source: Source, *, spacing: object) -> Result:
    """Return the ground's movement along a utility, with its exact derivatives.

    The source is evaluated at stations along the utility (never on a grid),
    and its displacement u is resolved into three directions, with components
    in the order (x, y, depth):

    - along: a = (end - start) / L, positive toward increasing distance;
    - lateral: l = (a_y, -a_x, 0) / |(a_x, a_y)|, horizontal and positive to
      the right looking along a, as offset is (SPEC §8.1);
    - vertical: v = l x a, which is (0, 0, 1) for a level utility, so vertical
      is settlement, positive downward.

    Each component u.e has exact derivatives with respect to distance s along
    the utility, from the source's gradient G and Hessian H:
    d(u.e)/ds = e_i G_ij a_j and d2(u.e)/ds2 = e_i H_ijk a_j a_k.

    Parameters
    ----------
    utility : Utility
        A straight utility (two vertices).
    source : Source
        The source of ground movement, such as a transverse surface trough.
    spacing : length
        The largest distance between stations, in m if a plain number. A
        design judgment with no default. Stations are the utility's ends,
        every multiple of `spacing` below its length L, and the source's
        critical distances (where its quantities peak or change sign), so a
        peak is never missed whatever the spacing. Stations closer than 1 um
        are merged, keeping the critical one. Must be positive.

    Returns
    -------
    Result
        ``analysis`` is ``"movement_profile"`` and ``subject`` the utility's id.
        ``values`` has one row per station, with units in
        ``attrs["units"]``:

        - ``distance`` (m) from the utility's first vertex;
        - ``x``, ``y``, ``depth`` (m) of the station;
        - ``station``, ``offset`` (m) relative to the reference tunnel, only
          for a utility built from station and offset;
        - ``along``, ``vertical``, ``lateral`` (m), the displacement;
        - ``along_strain`` (dimensionless, tension positive) and
          ``along_strain_gradient`` (1/m), the ground's strain along the
          utility and its derivative;
        - ``vertical_slope`` (dimensionless), ``vertical_curvature`` (1/m;
          negative is sagging, as settlement is positive downward);
        - ``lateral_slope`` (dimensionless), ``lateral_curvature`` (1/m);
        - ``critical`` (bool), the station is a critical distance;
        - ``verdict`` (str), the source's verdict at the station.

        ``checks`` is empty (the utility checks are M3). The method,
        assumptions and inputs are the source's, the utility's and this
        profile's; ``validity`` is the worst verdict over the stations and
        flags, and ``warnings`` the source's flags, with points as row
        positions.

    Raises
    ------
    TypeError
        If `spacing` is missing.
    ValueError
        If `spacing` isn't positive or gives more than 1,000,000 stations, the
        utility is vertical (it has no lateral direction), or the source can't
        evaluate a station (inside the bore, say), naming the utility and the
        stations' distances.

    Notes
    -----
    The profile is the ground's movement (greenfield): the assets follow the
    ground, which is recorded as an assumption. How much of `along_strain` a
    pipe takes is decided by the utility checks (M3).
    """
    spacing_m, spacing_record = record(
        "spacing", spacing, kind="design judgment", unit="m", plain_number="read as SI"
    )
    spacing_m = float(spacing_m)
    if not (math.isfinite(spacing_m) and spacing_m > 0):
        raise ValueError(f"spacing must be positive, not {spacing_m} m.")
    _, merge_record = record(
        "station_merge_tolerance",
        MERGE_TOLERANCE,
        kind="constant or setting",
        unit="m",
        plain_number="read as SI",
    )

    where = f"Utility {utility.utility_id!r}"
    start, end = (np.asarray(vertex, dtype=np.float64) for vertex in utility.vertices)
    length = float(np.linalg.norm(end - start))
    along_direction = (end - start) / length
    horizontal = math.hypot(along_direction[0], along_direction[1])
    if horizontal < 1e-12:
        raise ValueError(
            f"{where} is vertical, so it has no lateral direction; a profile "
            "needs a utility that runs some way in plan."
        )
    lateral_direction = (
        np.array([along_direction[1], -along_direction[0], 0.0]) / horizontal
    )
    vertical_direction = np.cross(lateral_direction, along_direction)

    if length / spacing_m + 1 > MAXIMUM_STATIONS:
        raise ValueError(
            f"spacing {spacing_m:g} m is too fine for {where}, {length:g} m long: "
            f"it gives more than {MAXIMUM_STATIONS:,} stations."
        )
    critical = np.asarray(
        source.critical_distances(start=start, end=end), dtype=np.float64
    )
    distance, is_critical = _stations(length, spacing_m, critical)

    points = start + distance[:, None] * along_direction
    try:
        movement = source.evaluate(x=points[:, 0], y=points[:, 1], depth=points[:, 2])
    except ValueError as error:
        raise ValueError(f"{where}: {_with_distances(str(error), distance)}") from error

    a, v, lat = along_direction, vertical_direction, lateral_direction
    gradient, hessian = movement.gradient, movement.hessian

    def first(e: FloatArray) -> FloatArray:
        result: FloatArray = np.einsum("i,nij,j->n", e, gradient, a)
        return result

    def second(e: FloatArray) -> FloatArray:
        result: FloatArray = np.einsum("i,nijk,j,k->n", e, hessian, a, a)
        return result

    columns: dict[str, object] = {
        "distance": distance,
        "x": points[:, 0],
        "y": points[:, 1],
        "depth": points[:, 2],
    }
    if utility.built is not None:
        station, offset = utility.built.tunnel.station_offset(
            x=points[:, 0], y=points[:, 1]
        )
        columns["station"] = np.atleast_1d(station)
        columns["offset"] = np.atleast_1d(offset)
    columns |= {
        "along": movement.displacement @ a,
        "vertical": movement.displacement @ v,
        "lateral": movement.displacement @ lat,
        "along_strain": first(a),
        "along_strain_gradient": second(a),
        "vertical_slope": first(v),
        "vertical_curvature": second(v),
        "lateral_slope": first(lat),
        "lateral_curvature": second(lat),
        "critical": is_critical,
        "verdict": movement.verdict.astype(str),
    }
    values = pd.DataFrame(columns)
    values.attrs["units"] = {name: UNITS[name] for name in columns if name in UNITS}

    flags = movement.flags
    validity = worst([*movement.verdict.tolist(), *(flag.verdict for flag in flags)])
    return Result(
        analysis="movement_profile",
        subject=utility.utility_id,
        values=values,
        checks=empty_checks(),
        method=(*source.method, METHOD),
        assumptions=(*source.assumptions, *utility.assumptions, GREENFIELD),
        inputs=(*source.inputs, *utility.inputs, spacing_record, merge_record),
        validity=validity,
        warnings=flags,
        source=source,
        asset=utility,
    )


def _stations(
    length: float, spacing: float, critical: FloatArray
) -> tuple[FloatArray, npt.NDArray[np.bool_]]:
    """Return the stations' distances and which are critical, merged at 1 um."""
    grid = spacing * np.arange(math.ceil(length / spacing))
    grid = np.append(grid[grid < length], length)
    candidates = sorted(
        [(float(s), True) for s in np.clip(critical, 0.0, length)]
        + [(float(s), False) for s in grid]
    )
    kept: list[tuple[float, bool]] = []
    for distance, is_critical in candidates:
        if kept and distance - kept[-1][0] < MERGE_TOLERANCE:
            if is_critical and not kept[-1][1]:
                kept[-1] = (distance, True)
            continue
        kept.append((distance, is_critical))
    return (
        np.array([distance for distance, _ in kept]),
        np.array([flag for _, flag in kept], dtype=bool),
    )


def _with_distances(message: str, distance: FloatArray) -> str:
    """Name the stations' distances where a source's message lists indices."""
    lists = re.findall(r"\[(\d+(?:, \d+)*)\]", message)
    if not lists:
        return message
    indices = [int(index) for index in lists[-1].split(", ")]
    named = ", ".join(f"{distance[index]:.6g}" for index in indices)
    return f"{message} These are the stations at distances {named} m along it."
