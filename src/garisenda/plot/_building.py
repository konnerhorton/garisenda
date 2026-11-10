"""A building check's overlays on the profile: its zones, chords, strains."""

import math

import numpy as np
import numpy.typing as npt
from matplotlib.axes import Axes

from garisenda._result import Result
from garisenda.plot._display import DisplayUnits
from garisenda.plot._panel import check_row, mark

FloatArray = npt.NDArray[np.float64]

DISTANCE_TOLERANCE = 1e-9
"""Distance in m within which a row of `values` is at a given distance."""


def draw_building_check(
    panels: list[Axes], result: Result, distance: FloatArray, display: DisplayUnits
) -> None:
    """Draw a building check's overlays on its five panels.

    `distance` is the values' distance in display units. Every value drawn is
    a column of the result times its display factor; a position that isn't a
    value (a zone's middle, for a label) is drawing only.
    """
    _mark_slope(panels[2], result, display)


def _row_at(result: Result, where: float) -> int | None:
    """Return the position of the row of `values` at a distance (m), or None."""
    found = np.flatnonzero(
        np.isclose(
            result.values["distance"].to_numpy(dtype=np.float64),
            where,
            rtol=0,
            atol=DISTANCE_TOLERANCE,
        )
    )
    return int(found[0]) if found.size else None


def _mark_slope(ax: Axes, result: Result, display: DisplayUnits) -> None:
    """Mark the slope check at the signed slope of its governing row.

    The check is on the slope's size; the mark keeps its sign, so it sits on
    the line.
    """
    row = check_row(result, "slope")
    if row is None:
        return
    where = float(row["governing_distance"])
    position = None if math.isnan(where) else _row_at(result, where)
    if position is None:
        return
    slope = float(result.values["vertical_slope"].iloc[position])
    shown = slope * display.factor("slope")
    utilization = float(row["utilization"])
    used = "no limit" if math.isnan(utilization) else f"u = {utilization:.2f}"
    mark(
        ax,
        where * display.factor("length"),
        shown,
        f"{shown:.3g} {display.symbol('slope')}, {used}",
        "check:slope",
        inverted=False,
    )
