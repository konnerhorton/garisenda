"""Straight segments: reading their ends and their directions (SPEC §3)."""

import math

import numpy as np
import numpy.typing as npt

from garisenda._inputs import record

FloatArray = npt.NDArray[np.float64]


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
