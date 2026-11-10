"""A building check's overlays on the profile: its zones, chords, strains."""

import math
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.patches import Rectangle

from garisenda._result import Result
from garisenda.buildings._categories import Band
from garisenda.plot._display import DisplayUnits, one_in
from garisenda.plot._panel import check_row, mark

FloatArray = npt.NDArray[np.float64]

DISTANCE_TOLERANCE = 1e-9
"""Distance in m within which a row of `values` is at a given distance."""

MODE_COLOR = {"hogging": "#c0392b", "sagging": "#7d5ba6", "flat": "0.55"}
"""Each zone's color by mode, the same on every panel."""

BAND_GRAYS = ("0.95", "0.88")
"""The damage categories' bands, alternating."""

MARGIN = 0.18
"""The tensile strain panel's padding, as a fraction of its span, as `margins`."""

GOVERNING_WIDTH = 2.0
OTHER_WIDTH = 0.8
"""The widths of a zone's governing tensile strain and of the other one."""


def draw_building_check(
    panels: list[Axes], result: Result, distance: FloatArray, display: DisplayUnits
) -> None:
    """Draw a building check's overlays on its five panels.

    `distance` is the values' distance in display units. Every value drawn is
    a column of the result times its display factor; a position that isn't a
    value (a zone's middle, for a label) is drawing only.
    """
    zones = result.zones
    length = display.factor("length")
    for ax in panels:
        _zone_ends(ax, zones, length)
    _cutoff(panels, result, distance, length)
    if zones.empty:
        return
    _settlement(panels[0], result, display)
    _deflection(panels[1], result, display)
    _mark_slope(panels[2], result, display)
    _horizontal_strain(panels[3], zones, display)
    _tensile_strain(panels[4], result, display)


def _middle(zone: Any, length: float) -> float:
    """Return a zone's middle in display units: a position, not a value."""
    return 0.5 * (float(zone.start) + float(zone.end)) * length


def _zone_rows(result: Result, zone: Any) -> npt.NDArray[np.bool_]:
    """Return the rows of `values` from a zone's start to its end, both included.

    The rows at the ends belong to the neighboring zones as well: the chords
    meet the settlement there, so each zone's chord and fill reach its ends.
    """
    distance = result.values["distance"].to_numpy(dtype=np.float64)
    inside: npt.NDArray[np.bool_] = (
        distance >= float(zone.start) - DISTANCE_TOLERANCE
    ) & (distance <= float(zone.end) + DISTANCE_TOLERANCE)
    return inside


def _zone_ends(ax: Axes, zones: pd.DataFrame, length: float) -> None:
    """Draw a thin line at each inner zone end."""
    for end in zones["end"].to_numpy(dtype=np.float64)[:-1]:
        ax.axvline(end * length, color="0.45", linewidth=0.6, zorder=1, gid="zone_end")


def _cutoff(
    panels: list[Axes], result: Result, distance: FloatArray, length: float
) -> None:
    """Hatch the wall beyond the cut-off, with a dotted line where it ends.

    The assessed range is the zones' extent; with no zone, the whole wall is
    beyond the cut-off. Nothing is drawn where the range reaches the wall's
    end.
    """
    first, last = float(distance[0]), float(distance[-1])
    zones = result.zones
    if zones.empty:
        spans = [(first, last)]
        lines: list[float] = []
    else:
        low = float(zones["start"].iloc[0]) * length
        high = float(zones["end"].iloc[-1]) * length
        tolerance = DISTANCE_TOLERANCE * length
        spans = []
        lines = []
        if low > first + tolerance:
            spans.append((first, low))
            lines.append(low)
        if high < last - tolerance:
            spans.append((high, last))
            lines.append(high)
    for ax in panels:
        for start, end in spans:
            ax.add_patch(
                Rectangle(
                    (start, 0.0),
                    end - start,
                    1.0,
                    transform=ax.get_xaxis_transform(),
                    facecolor="none",
                    edgecolor="0.7",
                    hatch="///",
                    linewidth=0,
                    zorder=0,
                    gid="beyond_cutoff",
                )
            )
        for where in lines:
            ax.axvline(where, color="0.3", linewidth=0.8, linestyle=":", gid="cutoff")
    if spans:
        start, end = max(spans, key=lambda span: span[1] - span[0])
        panels[0].annotate(
            "beyond the cut-off:\nnot assessed",
            (0.5 * (start + end), 0.5),
            xycoords=("data", "axes fraction"),
            ha="center",
            va="center",
            rotation=90,
            fontsize=6,
            color="0.35",
            gid="beyond_cutoff",
        )


def _settlement(ax: Axes, result: Result, display: DisplayUnits) -> None:
    """Draw each zone's chord dashed, the deflection filled, and its label."""
    values = result.values
    factor = display.factor("displacement")
    length = display.factor("length")
    for zone in result.zones.itertuples():
        rows = _zone_rows(result, zone)
        color = MODE_COLOR[str(zone.mode)]
        x = values["distance"].to_numpy(dtype=np.float64)[rows] * length
        chord = values["chord"].to_numpy(dtype=np.float64)[rows] * factor
        settlement = values["vertical"].to_numpy(dtype=np.float64)[rows] * factor
        ax.plot(
            x,
            chord,
            color=color,
            linewidth=0.8,
            linestyle=(0, (4, 2)),
            gid=f"chord:zone_{zone.zone}",
        )
        ax.fill_between(
            x,
            settlement,
            chord,
            color=color,
            alpha=0.3,
            linewidth=0,
            zorder=1,
            gid=f"zone_{zone.zone}",
        )
        ax.annotate(
            f"{zone.zone} {zone.mode}",
            (_middle(zone, length), 1.0),
            xycoords=("data", "axes fraction"),
            xytext=(0, -3),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=6.5,
            color=color,
            gid=f"zone_label:{zone.zone}",
        )


def _deflection(ax: Axes, result: Result, display: DisplayUnits) -> None:
    """Mark each zone's Delta, with Delta/L as 1/n; say a flat zone is flat."""
    factor = display.factor("displacement")
    length = display.factor("length")
    unit = display.symbol("displacement")
    for zone in result.zones.itertuples():
        if zone.mode == "flat":
            ax.annotate(
                "flat: no deflection",
                (_middle(zone, length), 0.0),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=6.5,
                color="0.35",
                gid=f"flat:zone_{zone.zone}",
            )
            continue
        delta = float(zone.deflection) * factor
        shown = -delta if zone.mode == "hogging" else delta
        mark(
            ax,
            float(zone.deflection_distance) * length,
            shown,
            f"Δ = {delta:.3g} {unit}, Δ/L = {one_in(float(zone.deflection_ratio))}",
            f"delta:zone_{zone.zone}",
            inverted=True,
        )


def _horizontal_strain(ax: Axes, zones: pd.DataFrame, display: DisplayUnits) -> None:
    """Draw each zone's average horizontal strain as a level line across it."""
    factor = display.factor("strain")
    length = display.factor("length")
    for zone in zones.itertuples():
        level = float(zone.horizontal_strain) * factor
        ax.plot(
            [float(zone.start) * length, float(zone.end) * length],
            [level, level],
            color=MODE_COLOR[str(zone.mode)],
            linewidth=1.6,
            gid=f"horizontal_strain:zone_{zone.zone}",
        )


def row_at(result: Result, where: float) -> int | None:
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
    position = None if math.isnan(where) else row_at(result, where)
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


def _acceptable(result: Result) -> tuple[Band | None, float]:
    """Return the acceptable category's band and its limit (NaN for none)."""
    row = check_row(result, "damage_category")
    limit = math.nan if row is None else float(row["limit"])
    categories = result.categories
    if categories is None or math.isnan(limit):
        return None, limit
    band = next((band for band in categories.bands if band.upper_limit == limit), None)
    return band, limit


def _tensile_strain(ax: Axes, result: Result, display: DisplayUnits) -> None:
    """Draw each zone's tensile strains on the categories' bands, and the limit.

    A zone's strain is a beam's over the whole zone, so it is a level line
    across it. The scale covers the zones' strains, the acceptable limit and
    the upper limit of the band holding the largest strain, so that band shows
    whole and the bands beyond are clipped.
    """
    zones = result.zones
    factor = display.factor("strain")
    length = display.factor("length")
    unit = display.symbol("strain")
    for zone in zones.itertuples():
        color = MODE_COLOR[str(zone.mode)]
        start, end = float(zone.start) * length, float(zone.end) * length
        for column, name in (
            ("total_bending_strain", "bending"),
            ("total_diagonal_strain", "diagonal"),
        ):
            level = float(getattr(zone, column)) * factor
            governs = zone.governed_by == name
            ax.plot(
                [start, end],
                [level, level],
                color=color,
                linewidth=GOVERNING_WIDTH if governs else OTHER_WIDTH,
                gid=f"{column}:zone_{zone.zone}",
            )
            ax.annotate(
                f"{name}, category {zone.label}" if governs else name,
                (start, level),
                xytext=(2, 1.5),
                textcoords="offset points",
                ha="left",
                va="bottom",
                fontsize=6,
                color=color,
                gid=f"{column}:zone_{zone.zone}",
            )
    band, limit = _acceptable(result)
    shown_limit = limit * factor
    if band is not None and math.isfinite(limit):
        ax.axhline(
            shown_limit, color="0.45", linewidth=0.7, gid="damage_category_limit"
        )
        ax.annotate(
            f"acceptable: category {band.label}, {shown_limit:.4g} {unit}",
            (1.0, shown_limit),
            xycoords=("axes fraction", "data"),
            xytext=(-2, 2),
            textcoords="offset points",
            ha="right",
            va="bottom",
            fontsize=6,
            color="0.35",
            gid="damage_category_limit",
        )
    _scale(ax, result, factor)
    _bands(ax, result, factor)
    _mark_category(ax, result, display)


def _scale(ax: Axes, result: Result, factor: float) -> None:
    """Set the tensile strain panel's range; the bands don't move it."""
    zones = result.zones
    levels = [
        *zones["total_bending_strain"].to_numpy(dtype=np.float64),
        *zones["total_diagonal_strain"].to_numpy(dtype=np.float64),
        0.0,
    ]
    _, limit = _acceptable(result)
    if math.isfinite(limit):
        levels.append(limit)
    categories = result.categories
    if categories is not None:
        largest = float(zones["tensile_strain"].max())
        upper = categories.category(largest).upper_limit
        if math.isfinite(upper):
            levels.append(upper)
    low, high = min(levels) * factor, max(levels) * factor
    span = high - low
    ax.set_ylim(low - MARGIN * span, high + MARGIN * span)


def _bands(ax: Axes, result: Result, factor: float) -> None:
    """Shade each damage category's band within the panel's range, labeled."""
    categories = result.categories
    if categories is None:
        return
    bottom, top = ax.get_ylim()
    lower = -math.inf
    for index, band in enumerate(categories.bands):
        low, high = lower * factor, band.upper_limit * factor
        lower = band.upper_limit
        if high <= bottom or low >= top:
            continue
        low, high = max(low, bottom), min(high, top)
        ax.add_patch(
            Rectangle(
                (0.0, low),
                1.0,
                high - low,
                transform=ax.get_yaxis_transform(),
                facecolor=BAND_GRAYS[index % 2],
                linewidth=0,
                zorder=0,
                gid=f"band:{band.number}",
            )
        )
        ax.annotate(
            f"{band.label} {band.severity}",
            (1.0, 0.5 * (low + high)),
            xycoords=("axes fraction", "data"),
            xytext=(-2, 0),
            textcoords="offset points",
            ha="right",
            va="center",
            fontsize=6,
            color="0.45",
            gid=f"band:{band.number}",
        )


def _mark_category(ax: Axes, result: Result, display: DisplayUnits) -> None:
    """Mark the governing zone at the middle of its governing level line."""
    row = check_row(result, "damage_category")
    if row is None or pd.isna(row["zone"]):
        return
    zone = next(
        zone for zone in result.zones.itertuples() if zone.zone == int(row["zone"])
    )
    utilization = float(row["utilization"])
    used = "no limit" if math.isnan(utilization) else f"u = {utilization:.2f}"
    mark(
        ax,
        _middle(zone, display.factor("length")),
        float(row["value"]) * display.factor("strain"),
        f"category {zone.label} ({zone.severity}), {used}",
        "check:damage_category",
        inverted=False,
    )
