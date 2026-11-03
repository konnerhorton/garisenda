"""The profile figure: movement, strain and curvature along a utility (SPEC §9)."""

from collections.abc import Mapping, Sequence
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from garisenda._result import Result
from garisenda.plot._display import DisplayUnits, resolve
from garisenda.plot._style import style

PANELS = 4
SHADE = {"marginal": "#f6d58e", "outside": "#f2a7a0"}
"""The fill of stations that aren't within, by verdict."""

# Each panel's lines: the column, its legend label and its color.
LINES: tuple[tuple[tuple[str, str, str], ...], ...] = (
    (("vertical", "Settlement", "C0"),),
    (("along", "Along", "C0"), ("lateral", "Lateral", "C1")),
    (("along_strain", "Strain along", "C0"),),
    (
        ("vertical_curvature", "Vertical", "C0"),
        ("lateral_curvature", "Lateral", "C1"),
    ),
)
KINDS = ("displacement", "displacement", "strain", "curvature")
TITLES = ("Settlement", "Horizontal movement", "Strain along", "Curvature")
CONVENTIONS = (
    "down +",
    "along: toward increasing distance +",
    "tension +",
    "hogging +, sagging -",
)
GOVERNING_PANEL = {"vertical": 0, "along_strain": 2, "vertical_curvature": 3}

FloatArray = npt.NDArray[np.float64]


def profile(
    result: Result,
    *,
    axs: Sequence[Axes] | None = None,
    display_units: Mapping[str, object] | None = None,
) -> tuple[Figure, list[Axes]]:
    """Draw a movement profile along its utility: four panels, distance shared.

    The panels, top to bottom, against distance along the utility:

    1. settlement (``vertical``), its axis pointing down, so the trough hangs
       as it does in the ground;
    2. horizontal movement, ``along`` (positive toward increasing distance) and
       ``lateral`` (positive to the right looking along the utility);
    3. strain along the utility (``along_strain``), tension positive;
    4. curvature, ``vertical_curvature`` (hogging positive, sagging negative)
       and ``lateral_curvature``.

    Each governing value (`Result.governing`) is marked with a point and its
    value. Critical stations are ticked along the bottom of every panel.
    Stations that aren't ``"within"`` are shaded on every panel by verdict, and
    each flag's reason is printed under the figure with its distance range, so
    nothing flagged goes unmarked (SPEC §10). For a utility built from station
    and offset, a top axis gives the offset from the tunnel axis.

    The figure draws the result's values and never recalculates them.

    Parameters
    ----------
    result : Result
        A movement profile, from `garisenda.movement_profile`.
    axs : sequence of four matplotlib Axes, optional
        Panels to draw into, top to bottom, as `matplotlib.pyplot.subplots`
        returns them; no figure is created. Otherwise a new figure is made.
    display_units : mapping, optional
        Units per kind of quantity, any of ``length`` (default m),
        ``displacement`` (mm), ``strain`` (microstrain) and ``curvature``
        (1/km), such as ``{"displacement": "m"}``.

    Returns
    -------
    fig : matplotlib.figure.Figure
    axs : list of matplotlib.axes.Axes
        The four panels, top to bottom.

    Raises
    ------
    ValueError
        If `axs` isn't four Axes, the result has no ``distance`` column, or
        `display_units` names an unknown kind.
    pint.DimensionalityError
        If a display unit doesn't fit its kind.
    """
    display = resolve(display_units)
    values = result.values
    if "distance" not in values:
        raise ValueError(
            "The profile figure draws against distance along the asset, but the "
            "result's values have no distance column."
        )
    with style():
        fig, panels = _panels(axs)
        length = display.factor("length")
        distance = values["distance"].to_numpy(dtype=np.float64) * length
        for index, ax in enumerate(panels):
            factor = display.factor(KINDS[index])
            for column, label, color in LINES[index]:
                if column in values:
                    ax.plot(
                        distance,
                        values[column].to_numpy(dtype=np.float64) * factor,
                        color=color,
                        linewidth=1.2,
                        label=label,
                        gid=column,
                    )
            ax.axhline(0.0, color="0.4", linewidth=0.6, zorder=1)
            ax.set_ylabel(display.label(TITLES[index], KINDS[index]))
            ax.set_title(CONVENTIONS[index], loc="right", fontsize=7, color="0.35")
            ax.margins(y=0.18)
            if len(LINES[index]) > 1:
                ax.legend(loc="lower left", ncols=2)
            _shade(ax, values, distance)
            _critical_ticks(ax, values, distance)
        panels[0].invert_yaxis()
        panels[-1].set_xlabel(display.label("Distance along utility", "length"))
        _mark_governing(panels, result, display)
        _offset_axis(panels[0], values, length, display)
        flag_notes(panels[-1], result, distance, display)
        fig.suptitle(f"Movement profile along {result.subject}", fontsize=10)
    return fig, panels


def _panels(axs: Sequence[Axes] | None) -> tuple[Figure, list[Axes]]:
    if axs is None:
        fig, created = plt.subplots(
            PANELS, 1, sharex=True, figsize=(7.0, 9.0), layout="constrained"
        )
        return fig, list(created)
    panels = list(axs)
    if len(panels) != PANELS or not all(isinstance(ax, Axes) for ax in panels):
        raise ValueError(
            f"axs must be {PANELS} matplotlib Axes, one per panel (settlement, "
            "horizontal movement, strain along, curvature), as "
            f"plt.subplots({PANELS}, 1, sharex=True) returns them."
        )
    figure = panels[0].get_figure()
    if not isinstance(figure, Figure):
        raise ValueError("axs[0] isn't in a figure.")
    return figure, panels


def _runs(mask: npt.NDArray[np.bool_]) -> list[tuple[int, int]]:
    """Return the first and last positions of each run of True."""
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for index, flagged in enumerate(mask.tolist()):
        if flagged and start is None:
            start = index
        if not flagged and start is not None:
            runs.append((start, index - 1))
            start = None
    if start is not None:
        runs.append((start, len(mask) - 1))
    return runs


def _shade(ax: Axes, values: pd.DataFrame, distance: FloatArray) -> None:
    """Shade the stations that aren't within, by verdict."""
    if "verdict" not in values:
        return
    verdict = values["verdict"].astype(str).to_numpy()
    for name, color in SHADE.items():
        for first, last in _runs(verdict == name):
            width = distance[last] - distance[first]
            if width > 0:
                ax.add_patch(
                    Rectangle(
                        (distance[first], 0.0),
                        width,
                        1.0,
                        transform=ax.get_xaxis_transform(),
                        facecolor=color,
                        alpha=0.5,
                        linewidth=0,
                        zorder=0,
                        gid=name,
                    )
                )
            else:
                ax.axvline(distance[first], color=color, linewidth=2, gid=name)


def _critical_ticks(ax: Axes, values: pd.DataFrame, distance: FloatArray) -> None:
    """Tick the critical stations along the bottom of a panel."""
    if "critical" not in values:
        return
    critical = values["critical"].to_numpy(dtype=bool)
    ax.plot(
        distance[critical],
        np.zeros(int(critical.sum())),
        linestyle="none",
        marker=2,  # a tick pointing up from the bottom edge
        markersize=7,
        markeredgewidth=1.2,
        color="C3",
        transform=ax.get_xaxis_transform(),
        gid="critical",
    )


def _mark_governing(panels: list[Axes], result: Result, display: DisplayUnits) -> None:
    """Mark each governing value with a point and its value."""
    length = display.factor("length")
    for row in result.governing().itertuples():
        panel = GOVERNING_PANEL.get(str(row.column))
        value = float(row.value)
        where = float(row.distance)
        if panel is None or not (np.isfinite(value) and np.isfinite(where)):
            continue
        kind = KINDS[panel]
        shown = value * display.factor(kind)
        ax = panels[panel]
        ax.plot(
            [where * length],
            [shown],
            marker="o",
            markersize=4,
            color="black",
            linestyle="none",
            gid=f"governing:{row.name}",
        )
        ax.annotate(
            f"{shown:.3g} {display.symbol(kind)}",
            (where * length, shown),
            xytext=(4, 4 if shown >= 0 else -4),
            textcoords="offset points",
            va="bottom" if (shown >= 0) != (panel == 0) else "top",
            fontsize=7,
            gid=f"governing:{row.name}",
        )


def _offset_axis(
    ax: Axes, values: pd.DataFrame, length: float, display: DisplayUnits
) -> None:
    """Add a top axis of offset from the tunnel axis, for a built utility."""
    if "offset" not in values or len(values) < 2:
        return
    distance = values["distance"].to_numpy(dtype=np.float64) * length
    offset = values["offset"].to_numpy(dtype=np.float64) * length
    span = distance[-1] - distance[0]
    if span <= 0:
        return
    slope = (offset[-1] - offset[0]) / span
    if abs(slope) < 1e-9:
        return
    start, origin = float(distance[0]), float(offset[0])

    def forward(x: Any) -> Any:
        return origin + slope * (x - start)

    def inverse(o: Any) -> Any:
        return start + (o - origin) / slope

    top = ax.secondary_xaxis("top", functions=(forward, inverse))
    top.set_xlabel(display.label("Offset from tunnel axis", "length"))


def flag_notes(
    ax: Axes, result: Result, distance: FloatArray, display: DisplayUnits
) -> None:
    """Print each flag's reason and distance range under the figure."""
    lines = []
    unit = display.symbol("length")
    for flag in result.warnings:
        where = ""
        if flag.points:
            covered = distance[list(flag.points)]
            where = (
                f" ({len(flag.points)} stations, {covered.min():.4g} to "
                f"{covered.max():.4g} {unit})"
            )
        lines.append(f"{flag.verdict.capitalize()}{where}: {flag.reason}")
    if not lines:
        return
    ax.annotate(
        "\n".join(lines),
        (0.0, 0.0),
        xycoords="axes fraction",
        xytext=(0, -30),
        textcoords="offset points",
        va="top",
        ha="left",
        fontsize=7,
        wrap=True,
        gid="flags",
    )
