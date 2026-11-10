"""Straight segments: reading their ends and their directions."""

import math
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt

from garisenda._inputs import record

if TYPE_CHECKING:
    from garisenda.sources._tunnel import IdealizedTunnel

FloatArray = npt.NDArray[np.float64]


def read_points(
    x: object, y: object, depth: object, *, surface_tolerance: float
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Return points' x, y and depth as flat arrays in m, checked.

    Raises
    ------
    ValueError
        If the arrays differ in length, a coordinate isn't finite (naming the
        points), or a point is above the ground surface (depth less than
        ``-surface_tolerance``).
    """
    coordinates = [
        np.atleast_1d(
            np.asarray(
                record(
                    name, value, kind="geometry", unit="m", plain_number="read as SI"
                )[0],
                dtype=np.float64,
            )
        )
        for name, value in (("x", x), ("y", y), ("depth", depth))
    ]
    if len({array.shape for array in coordinates}) != 1:
        raise ValueError(
            "x, y and depth must have the same length; got shapes "
            f"{', '.join(str(array.shape) for array in coordinates)}."
        )
    x_m, y_m, depth_m = (array.ravel() for array in coordinates)
    missing = ~(np.isfinite(x_m) & np.isfinite(y_m) & np.isfinite(depth_m))
    if missing.any():
        raise ValueError(
            "Every point needs finite x, y and depth; these points don't: "
            f"{np.flatnonzero(missing).tolist()}."
        )
    above = depth_m < -surface_tolerance
    if above.any():
        raise ValueError(
            "Points above the ground surface (negative depth) can't be "
            f"evaluated: {np.flatnonzero(above).tolist()}."
        )
    return x_m, y_m, depth_m


class InsideBoreError(ValueError):
    """A point inside a tunnel's bore, where a trough can't be evaluated.

    Private: callers that re-raise keep the type (``type(error)(...)``), so a
    profile can tell this error from others and say how to fix the utility.
    """


def check_outside_bore(
    tunnel: "IdealizedTunnel", offset: FloatArray, depth: FloatArray
) -> None:
    """Raise if a point, at its offset from the axis and depth, is inside the bore.

    Raises
    ------
    InsideBoreError
        Naming the points inside the bore, as a trailing list of indices, and
        the bore's extent.
    """
    inside = np.hypot(offset, depth - tunnel.axis_depth) < tunnel.diameter / 2
    if inside.any():
        radius = tunnel.diameter / 2
        raise InsideBoreError(
            f"Points inside the bore can't be evaluated: "
            f"{np.flatnonzero(inside).tolist()}. The bore has its axis at depth "
            f"{tunnel.axis_depth:.6g} m and diameter {tunnel.diameter:.6g} m, so "
            f"it spans depths {tunnel.axis_depth - radius:.6g} to "
            f"{tunnel.axis_depth + radius:.6g} m."
        )


def read_segment(start: object, end: object) -> tuple[FloatArray, FloatArray, float]:
    """Return a segment's ends as (x, y, depth) arrays in m, and its length in m.

    Raises
    ------
    ValueError
        If an end isn't three finite values, or the segment has zero length.
    """
    ends = []
    for name, value in (("start", start), ("end", end)):
        magnitude, _ = record(
            name, value, kind="geometry", unit="m", plain_number="read as SI"
        )
        point = np.asarray(magnitude, dtype=np.float64)
        if point.shape != (3,) or not np.isfinite(point).all():
            raise ValueError(
                f"{name} must be three finite values (x, y, depth), not {point}."
            )
        ends.append(point)
    length = float(np.linalg.norm(ends[1] - ends[0]))
    if length == 0:
        raise ValueError("The segment has zero length: start and end are equal.")
    return ends[0], ends[1], length


def directions(
    start: FloatArray, end: FloatArray
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Return a segment's along, vertical and lateral unit vectors (a, v, l).

    a = (end - start) / L; l = (a_y, -a_x, 0) / |(a_x, a_y)|, horizontal and to
    the right looking along a; v = l x a, which is (0, 0, 1) for a level segment.

    Raises
    ------
    ValueError
        If the segment is vertical, so it has no lateral direction.
    """
    along = (end - start) / float(np.linalg.norm(end - start))
    horizontal = math.hypot(along[0], along[1])
    if horizontal < 1e-12:
        raise ValueError("The segment is vertical, so it has no lateral direction.")
    lateral = np.array([along[1], -along[0], 0.0]) / horizontal
    vertical: FloatArray = np.cross(lateral, along)
    return along, vertical, lateral


def offset_extent(
    tunnel: "IdealizedTunnel",
    start: FloatArray,
    end: FloatArray,
    length: float,
    half_width: float,
) -> tuple[float, float] | None:
    """Return the distances along a segment within a half-width of a tunnel's axis.

    The offset o is linear in distance s along a straight segment, so the
    points with |o(s)| <= half_width form one interval, clipped to [0, L].
    A segment parallel to the tunnel is all within or all beyond.

    Returns
    -------
    tuple of two floats, or None
        The interval's ends in m from `start`, or None if no length of the
        segment is within.
    """
    _, offsets = tunnel.station_offset(
        x=np.array([start[0], end[0]]), y=np.array([start[1], end[1]])
    )
    o_start, o_end = (float(value) for value in np.atleast_1d(offsets))
    change = o_end - o_start
    if abs(change) <= 1e-12 * length:
        return (0.0, length) if abs(o_start) <= half_width else None
    ends = sorted(
        length * (target - o_start) / change for target in (-half_width, half_width)
    )
    low, high = max(ends[0], 0.0), min(ends[1], length)
    if high <= low:
        return None
    return low, high


def read_multiple(multiple: float) -> float:
    """Return a trough-width multiple as a positive finite float, or raise."""
    value = float(multiple)
    if not (math.isfinite(value) and value > 0):
        raise ValueError(f"multiple must be positive and finite, not {value}.")
    return value
