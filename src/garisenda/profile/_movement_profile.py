"""The ground's movement resolved along a utility or a building's wall."""

import math
from dataclasses import replace

import numpy as np
import numpy.typing as npt
import pandas as pd

from garisenda._asset import Asset, asset_name
from garisenda._inputs import judgments, record
from garisenda._result import Result, empty_checks
from garisenda.sources._critical import _with_distances
from garisenda.sources._movement import Flag, MethodRecord, Source, Verdict, worst
from garisenda.sources._segment import InsideBoreError, directions

MERGE_TOLERANCE = 1e-6
"""Distance in m within which two stations are merged into one."""

MAXIMUM_STATIONS = 1_000_000
"""The most stations a profile may have."""

GREENFIELD = "Assets follow the ground: greenfield, no soil-structure interaction."

METHOD = MethodRecord(
    "Movement profile along a straight line",
    (
        "stations: 0, L, every k spacing < L, and the source's critical distances",
        "a = (end - start) / L, l = (a_y, -a_x, 0) / |(a_x, a_y)|, v = l x a",
        "along = u.a, vertical = u.v, lateral = u.l",
        "d(u.e)/ds = e_i (du_i/dx_j) a_j",
        "d2(u.e)/ds2 = e_i (d2u_i/dx_j dx_k) a_j a_k",
    ),
    "Exact derivatives of the source's field along a straight line; "
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
def movement_profile(asset: Asset, source: Source, *, spacing: object) -> Result:
    """Return the ground's movement along an asset, with its exact derivatives.

    The asset is a utility, along its axis, or a building's wall, along its
    foundation level. The source is evaluated at stations along the asset
    (never on a grid),
    and its displacement u is resolved into three directions, with components
    in the order (x, y, depth):

    - along: a = (end - start) / L, positive toward increasing distance;
    - lateral: l = (a_y, -a_x, 0) / |(a_x, a_y)|, horizontal and positive to
      the right looking along a, as offset is;
    - vertical: v = l x a, which is (0, 0, 1) for a level asset, so vertical
      is settlement, positive downward.

    Each component u.e has exact derivatives with respect to distance s along
    the asset, from the source's gradient G and Hessian H:
    d(u.e)/ds = e_i G_ij a_j and d2(u.e)/ds2 = e_i H_ijk a_j a_k.

    Parameters
    ----------
    asset : Utility or Building
        A straight utility (two vertices), or a building's wall
        (`garisenda.buildings.Building`), whose profile is at its foundation
        level.
    source : Source
        The source of ground movement, such as a transverse surface trough.
    spacing : length
        The largest distance between stations, in m if a plain number. A
        design judgment with no default. Stations are the asset's ends,
        every multiple of `spacing` below its length L, and the source's
        critical distances (where its quantities peak or change sign), so a
        peak is never missed whatever the spacing. Stations closer than 1 um
        are merged, keeping the critical one. Must be positive.

    Returns
    -------
    Result
        ``analysis`` is ``"movement_profile"`` and ``subject`` the asset's id.
        ``values`` has one row per station, with units in
        ``attrs["units"]``:

        - ``distance`` (m) from the asset's first vertex;
        - ``x``, ``y``, ``depth`` (m) of the station;
        - ``station``, ``offset`` (m) relative to the reference tunnel, only
          for an asset built from station and offset;
        - ``along``, ``vertical``, ``lateral`` (m), the displacement;
        - ``along_strain`` (dimensionless, tension positive) and
          ``along_strain_gradient`` (1/m), the ground's strain along the
          asset and its derivative;
        - ``vertical_slope`` (dimensionless), ``vertical_curvature`` (1/m;
          negative is sagging, as settlement is positive downward);
        - ``lateral_slope`` (dimensionless), ``lateral_curvature`` (1/m);
        - ``critical`` (bool), the station is a critical distance;
        - ``verdict`` (str), the source's verdict at the station.

        ``checks`` is empty: `garisenda.check_continuous_pipe` and
        `garisenda.check_jointed_pipe` add them. The method,
        assumptions and inputs are the source's, the asset's and this
        profile's. The asset's inputs are named for it, such as
        ``utility.diameter`` or ``building.height``; the source's keep their
        names (``diameter`` for one tunnel, ``north.diameter`` in a
        superposition).
        ``validity`` is the worst verdict over the stations and flags, and
        ``warnings`` the source's flags, with points as row positions.

    Raises
    ------
    TypeError
        If `spacing` is missing.
    ValueError
        If `spacing` isn't positive or gives more than 1,000,000 stations, the
        utility is vertical (it has no lateral direction), or the source can't
        evaluate a station (inside the bore, say), naming the asset and the
        stations' distances; inside a bore, also the bore's depths, the
        asset's depth and what to check.

    Notes
    -----
    The profile is the ground's movement (greenfield): the assets follow the
    ground, which is recorded as an assumption. How much of `along_strain` a
    pipe takes is decided by the utility checks, and what a wall takes by
    `garisenda.check_building`.
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

    label, asset_id, prefix = asset_name(asset)
    where = f"{label} {asset_id!r}"
    start, end = (np.asarray(vertex, dtype=np.float64) for vertex in asset.vertices)
    length = float(np.linalg.norm(end - start))
    try:
        directions(start, end)
    except ValueError as error:
        raise ValueError(
            f"{where} is vertical, so it has no lateral direction; a profile "
            "needs a utility that runs some way in plan."
        ) from error

    if length / spacing_m + 1 > MAXIMUM_STATIONS:
        raise ValueError(
            f"spacing {spacing_m:g} m is too fine for {where}, {length:g} m long: "
            f"it gives more than {MAXIMUM_STATIONS:,} stations."
        )
    try:
        critical = np.asarray(
            source.critical_distances(start=start, end=end), dtype=np.float64
        )
    except ValueError as error:
        raise ValueError(f"{where}: {error}{_bore_remedy(asset, error)}") from error
    distance, is_critical = _stations(length, spacing_m, critical)
    values, flags, validity = profile_rows(asset, source, distance, is_critical)
    return Result(
        analysis="movement_profile",
        subject=asset_id,
        values=values,
        checks=empty_checks(),
        method=(*source.method, METHOD),
        assumptions=(*source.assumptions, *asset.assumptions, GREENFIELD),
        inputs=(
            *source.inputs,
            *(replace(entry, name=f"{prefix}.{entry.name}") for entry in asset.inputs),
            spacing_record,
            merge_record,
        ),
        validity=validity,
        warnings=flags,
        source=source,
        asset=asset,
    )


def profile_rows(
    asset: Asset,
    source: Source,
    distance: FloatArray,
    is_critical: npt.NDArray[np.bool_],
) -> tuple[pd.DataFrame, tuple[Flag, ...], Verdict]:
    """Return a profile's rows at the given distances along an asset.

    The columns are `movement_profile`'s, with units in ``attrs["units"]``;
    the flags are the source's, with points as row positions, and the
    validity is the worst verdict over the rows and flags. The asset must
    not be vertical. If the source can't evaluate a point, its `ValueError`
    is raised again naming the asset and the points' distances.
    """
    label, asset_id, _ = asset_name(asset)
    where = f"{label} {asset_id!r}"
    start, end = (np.asarray(vertex, dtype=np.float64) for vertex in asset.vertices)
    a, v, lat = directions(start, end)
    points = start + distance[:, None] * a
    try:
        movement = source.evaluate(x=points[:, 0], y=points[:, 1], depth=points[:, 2])
    except ValueError as error:
        message = _with_distances(str(error), distance)
        raise ValueError(f"{where}: {message}{_bore_remedy(asset, error)}") from error

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
    if asset.built is not None:
        station, offset = asset.built.tunnel.station_offset(
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
    return values, flags, validity


def merge_stations(
    distance: FloatArray, is_critical: npt.NDArray[np.bool_]
) -> tuple[FloatArray, npt.NDArray[np.bool_]]:
    """Sort distances and merge those within 1 um, keeping the critical one."""
    candidates = sorted(
        zip(
            np.asarray(distance, dtype=np.float64).tolist(),
            is_critical.tolist(),
            strict=True,
        )
    )
    kept: list[tuple[float, bool]] = []
    for station, critical in candidates:
        if kept and station - kept[-1][0] < MERGE_TOLERANCE:
            if critical and not kept[-1][1]:
                kept[-1] = (station, True)
            continue
        kept.append((station, critical))
    return (
        np.array([station for station, _ in kept], dtype=np.float64),
        np.array([critical for _, critical in kept], dtype=bool),
    )


def _stations(
    length: float, spacing: float, critical: FloatArray
) -> tuple[FloatArray, npt.NDArray[np.bool_]]:
    """Return the stations' distances and which are critical, merged at 1 um."""
    grid = spacing * np.arange(math.ceil(length / spacing))
    grid = np.append(grid[grid < length], length)
    clipped = np.clip(critical, 0.0, length)
    return merge_stations(
        np.concatenate([clipped, grid]),
        np.concatenate([np.ones(clipped.size, bool), np.zeros(grid.size, bool)]),
    )


def _bore_remedy(asset: Asset, error: ValueError) -> str:
    """For a point inside a bore, the asset's depth and what to check."""
    if not isinstance(error, InsideBoreError):
        return ""
    depths = np.asarray(asset.vertices, dtype=np.float64)[:, 2]
    low, high = float(np.min(depths)), float(np.max(depths))
    if high - low < 1e-9:
        at = f"at depth {low:.6g} m"
    else:
        at = f"at depths {low:.6g} to {high:.6g} m"
    label, _, _ = asset_name(asset)
    if label == "Building":
        return (
            f" The building's foundation is {at}. Check its foundation depth "
            "or elevation."
        )
    built = asset.built
    if built is None:
        check = "Check its vertices' depths."
    else:
        check = (
            "Check its depth, and its elevation_reference "
            f"({built.elevation_reference!r}), which is converted to the axis "
            "with the given diameter."
        )
    return f" The utility's axis is {at}. {check}"
