"""The profile figure: movement, strain and curvature along a utility."""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from garisenda._result import Result, flag_text
from garisenda.plot._display import DisplayUnits, resolve
from garisenda.plot._style import style
from garisenda.sources._superposition import (
    PARALLEL_TOLERANCE,
    Superposition,
    tunnels,
)
from garisenda.sources._tunnel import IdealizedTunnel

SHADE = {"marginal": "#f6d58e", "outside": "#f2a7a0"}
"""The fill of stations that aren't within, by verdict."""

CHECK_ANALYSIS = "continuous_pipe_check"
"""The analysis drawn in six panels."""

JOINTED_ANALYSIS = "jointed_pipe_check"
"""The analysis drawn in eight panels; any other result gets four."""


@dataclass(frozen=True)
class Limit:
    """A limit line: its name (and gid), the check it is read from, its sign."""

    name: str
    check: str
    sign: int
    label: str


@dataclass(frozen=True)
class Panel:
    """One panel: its lines (column, label, color), kind, title and convention.

    `governing` names the `Result.governing` columns marked on it, `limits`
    its limit lines and `checks` the checks whose governing value it marks.
    `dashed` names lines drawn dashed, and `closure` a column whose most
    negative value is marked as a closure, which isn't checked.
    """

    lines: tuple[tuple[str, str, str], ...]
    kind: str
    title: str
    convention: str
    governing: tuple[str, ...] = ()
    limits: tuple[Limit, ...] = ()
    checks: tuple[str, ...] = ()
    dashed: tuple[str, ...] = ()
    closure: str | None = None


SETTLEMENT = Panel(
    (("vertical", "Settlement", "C0"),),
    "displacement",
    "Settlement",
    "down +",
    governing=("vertical",),
)
HORIZONTAL = Panel(
    (("along", "Along", "C0"), ("lateral", "Lateral", "C1")),
    "displacement",
    "Horizontal movement",
    "along: right +; lateral: right looking along +",
)
RADIUS_LIMIT = "radius_of_curvature_limit"
TENSILE_LIMIT = Limit("tensile_strain_limit", "tensile_strain", 1, "tensile limit")
COMPRESSIVE_LIMIT = Limit(
    "compressive_strain_limit", "compressive_strain", -1, "compressive limit"
)

PROFILE_PANELS = (
    SETTLEMENT,
    HORIZONTAL,
    Panel(
        (("along_strain", "Strain along", "C0"),),
        "strain",
        "Strain along",
        "tension +",
        governing=("along_strain",),
    ),
    Panel(
        (
            ("vertical_curvature", "Vertical", "C0"),
            ("lateral_curvature", "Lateral", "C1"),
        ),
        "curvature",
        "Curvature",
        "hogging +, sagging -",
        governing=("vertical_curvature",),
    ),
)
"""The four panels of a movement profile."""

CHECK_PANELS = (
    SETTLEMENT,
    HORIZONTAL,
    Panel(
        (("axial_strain", "Axial", "C0"),),
        "strain",
        "Axial strain",
        "tension +",
        limits=(TENSILE_LIMIT, COMPRESSIVE_LIMIT),
        checks=("axial_tension", "axial_compression"),
    ),
    Panel(
        (
            ("vertical_curvature", "Vertical", "C0"),
            ("lateral_curvature", "Lateral", "C1"),
            ("resultant_curvature", "Resultant", "C2"),
        ),
        "curvature",
        "Curvature",
        "hogging +, sagging -; resultant +",
        limits=(
            Limit(RADIUS_LIMIT, "radius_of_curvature", 1, "radius limit"),
            Limit(RADIUS_LIMIT, "radius_of_curvature", -1, ""),
        ),
        checks=("radius_of_curvature",),
    ),
    Panel(
        (
            ("vertical_bending_strain", "Vertical", "C0"),
            ("lateral_bending_strain", "Lateral", "C1"),
            ("bending_strain", "Resultant", "C2"),
        ),
        "strain",
        "Bending strain",
        "outermost fiber; resultant +",
        limits=(Limit("bending_strain_limit", "bending", 1, "bending limit"),),
        checks=("bending",),
    ),
    Panel(
        (
            ("tensile_strain", "Tensile", "C3"),
            ("compressive_strain", "Compressive", "C0"),
        ),
        "strain",
        "Combined strain",
        "tension +",
        limits=(TENSILE_LIMIT, COMPRESSIVE_LIMIT),
        checks=("tensile_strain", "compressive_strain"),
    ),
)
"""The six panels of a continuous-pipe check."""

JOINTED_PANELS = (
    *CHECK_PANELS,
    Panel(
        (
            ("joint_vertical_rotation", "Vertical", "C0"),
            ("joint_lateral_rotation", "Lateral", "C1"),
            ("joint_rotation", "Resultant", "C2"),
        ),
        "angle",
        "Joint rotation",
        "hogging +, sagging -; resultant +",
        limits=(Limit("joint_rotation_limit", "joint_rotation", 1, "rotation limit"),),
        checks=("joint_rotation",),
    ),
    Panel(
        (
            ("joint_opening", "At the axis", "C0"),
            ("joint_outer_opening", "Outer", "C1"),
        ),
        "displacement",
        "Joint opening",
        "opens +, closes -",
        limits=(Limit("joint_pullout_limit", "joint_pullout", 1, "pullout limit"),),
        checks=("joint_pullout",),
        dashed=("joint_outer_opening",),
        closure="joint_opening",
    ),
)
"""The eight panels of a jointed-pipe check."""

PANELS = {CHECK_ANALYSIS: CHECK_PANELS, JOINTED_ANALYSIS: JOINTED_PANELS}
"""The panels of each check's analysis."""

DISCRETE_COLUMN = {
    "axial_strain": "discrete_axial_strain",
    "vertical_curvature": "discrete_vertical_curvature",
    "lateral_curvature": "discrete_lateral_curvature",
    "resultant_curvature": "discrete_resultant_curvature",
    "bending_strain": "discrete_bending_strain",
    "tensile_strain": "discrete_tensile_strain",
    "compressive_strain": "discrete_compressive_strain",
}
"""The discrete column drawn dashed beside each analytical one, in a check."""

DASHED = (0, (4, 2))
"""The dash pattern of discrete lines."""

FloatArray = npt.NDArray[np.float64]


def profile(
    result: Result,
    *,
    axs: Sequence[Axes] | None = None,
    display_units: Mapping[str, object] | None = None,
) -> tuple[Figure, list[Axes]]:
    """Draw a profile along its utility: four, six or eight panels.

    A movement profile is drawn in four panels, top to bottom, against
    distance along the utility:

    1. settlement (``vertical``), its axis pointing down, so the trough hangs
       as it does in the ground;
    2. horizontal movement, ``along`` (positive toward increasing distance) and
       ``lateral`` (positive to the right looking along the utility);
    3. strain along the utility (``along_strain``), tension positive;
    4. curvature, ``vertical_curvature`` (hogging positive, sagging negative)
       and ``lateral_curvature``.

    Each governing value (`Result.governing`) is marked with a point and its
    value.

    A continuous-pipe check (from `garisenda.check_continuous_pipe`) is drawn
    in six panels:

    1. settlement, as above, with its largest value marked;
    2. horizontal movement, as above;
    3. axial strain, with the tensile limit (+) and the compressive limit (-);
    4. curvature: vertical, lateral and the resultant, with the radius limit
       drawn as +-1/R;
    5. bending strain at the outermost fiber: vertical, lateral and the
       resultant, with the bending limit;
    6. combined strain, tensile and compressive, with their limits.

    Analytical values are solid lines; discrete ones are dashed in the same
    color, with gaps at stations that have none. Limits are thin gray lines
    labeled with their value, and a check given no limit draws no line and
    says so on its panel. Each check's governing value (`Result.checks`) is
    marked with its value and utilization; the radius is marked at its
    curvature, 1/R, on the curvature panel, since an infinite radius can't be
    drawn.

    A jointed-pipe check (from `garisenda.check_jointed_pipe`) is drawn in
    eight panels: the six above, with the discrete values at the pipe length,
    then

    7. joint rotation: vertical, lateral and the resultant, in degrees, with
       the rotation limit;
    8. joint opening at the axis, and the outer opening (dashed), with the
       pullout limit; the largest closure is marked, and isn't checked.

    Joint values exist only at a pipe length's spacing, so they have no
    analytical twin; they are solid lines with gaps near the ends.

    On every figure, critical stations are ticked along the bottom of every panel.
    Stations that aren't ``"within"`` are shaded on every panel by verdict, and
    each flag's reason is printed under the figure with its distance range, so
    nothing flagged goes unmarked. For a utility built from station
    and offset, a top axis gives the offset from the tunnel axis.

    The figure draws the result's values and never recalculates them.

    Parameters
    ----------
    result : Result
        A movement profile, from `garisenda.movement_profile`, or a check,
        from `garisenda.check_continuous_pipe` or
        `garisenda.check_jointed_pipe`.
    axs : sequence of matplotlib Axes, optional
        Four, or six for a continuous-pipe check, or eight for a jointed one.
        The panels to draw into, top to bottom, as `matplotlib.pyplot.subplots`
        returns them; no figure is created. Otherwise a new figure is made.
    display_units : mapping, optional
        Units per kind of quantity, any of ``length`` (default m),
        ``displacement`` (mm), ``strain`` (microstrain), ``curvature``
        (1/km) and ``angle`` (degree), such as ``{"displacement": "m"}``.

    Returns
    -------
    fig : matplotlib.figure.Figure
    axs : list of matplotlib.axes.Axes
        The panels, top to bottom.

    Raises
    ------
    ValueError
        If `axs` isn't four Axes (six or eight for a check), the result has no
        ``distance`` column, or `display_units` names an unknown kind.
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
    specs = PANELS.get(result.analysis, PROFILE_PANELS)
    with style():
        fig, panels = _panels(axs, specs)
        length = display.factor("length")
        distance = values["distance"].to_numpy(dtype=np.float64) * length
        for spec, ax in zip(specs, panels, strict=True):
            _draw_lines(ax, spec, values, distance, display)
            ax.axhline(0.0, color="0.4", linewidth=0.6, zorder=1)
            ax.set_ylabel(display.label(spec.title, spec.kind))
            ax.set_title(spec.convention, loc="right", fontsize=7, color="0.35")
            ax.margins(y=0.18)
            _draw_limits(ax, spec, result, display)
            _shade(ax, values, distance)
            _critical_ticks(ax, values, distance)
            _mark_governing(ax, spec, result, display)
            _mark_checks(ax, spec, result, display)
            _mark_closure(ax, spec, values, distance, display)
        panels[0].invert_yaxis()
        panels[-1].set_xlabel(display.label("Distance along utility", "length"))
        _offset_axis(panels[0], values, length, display, offset_label(result))
        flag_notes(panels[-1], result, distance, display)
        fig.suptitle(_title(result, display), fontsize=10)
    return fig, panels


def _title(result: Result, display: DisplayUnits) -> str:
    if result.analysis not in PANELS:
        return f"Movement profile along {result.subject}"
    jointed = result.analysis == JOINTED_ANALYSIS
    name = "pipe_length" if jointed else "interval"
    interval = next(
        (entry.value for entry in result.inputs if entry.name == name), None
    )
    span = ""
    if interval is not None and not isinstance(interval, str):
        shown = interval.m_as("m") * display.factor("length")
        span = f" at {shown:.3g} {display.symbol('length')}"
        if jointed:
            span += " pipe length"
    kind = "Jointed" if jointed else "Continuous"
    return (
        f"{kind} pipe check along {result.subject}\n"
        f"analytical solid, discrete dashed{span}"
    )


def _draw_lines(
    ax: Axes,
    spec: Panel,
    values: pd.DataFrame,
    distance: FloatArray,
    display: DisplayUnits,
) -> None:
    """Draw a panel's analytical lines, and their discrete ones dashed."""
    factor = display.factor(spec.kind)
    dashed = False
    for column, label, color in spec.lines:
        if column not in values:
            continue
        ax.plot(
            distance,
            values[column].to_numpy(dtype=np.float64) * factor,
            color=color,
            linewidth=1.2,
            label=label,
            gid=column,
            linestyle=DASHED if column in spec.dashed else "-",
        )
        discrete = DISCRETE_COLUMN.get(column)
        if discrete is None or discrete not in values:
            continue
        ax.plot(
            distance,
            values[discrete].to_numpy(dtype=np.float64) * factor,
            color=color,
            linewidth=1.0,
            linestyle=DASHED,
            label="_nolegend_",
            gid=discrete,
        )
        dashed = True
    handles, labels = ax.get_legend_handles_labels()
    if dashed:
        handles.append(Line2D([], [], color="0.3", linewidth=1.0, linestyle=DASHED))
        labels.append("Discrete")
    if len(handles) > 1:
        # Above the panel, left, clear of the lines and the limits' labels.
        ax.legend(
            handles,
            labels,
            loc="lower left",
            bbox_to_anchor=(0.0, 1.0),
            ncols=len(handles),
            fontsize=7,
            borderaxespad=0.1,
        )


def _check_row(result: Result, check: str) -> Any:
    """Return a check's row of `Result.checks`, or None."""
    rows = result.checks[result.checks["check"] == check]
    return None if rows.empty else rows.iloc[0]


def _draw_limits(ax: Axes, spec: Panel, result: Result, display: DisplayUnits) -> None:
    """Draw a panel's limit lines, or note the limits not given."""
    missing: list[str] = []
    for limit in spec.limits:
        row = _check_row(result, limit.check)
        if row is None:
            continue
        given = float(row["limit"])
        if math.isnan(given):
            if limit.label and limit.label not in missing:
                missing.append(limit.label)
            continue
        radius = limit.check == "radius_of_curvature"
        level = limit.sign * (1.0 / given if radius else given)
        shown = level * display.factor(spec.kind)
        ax.axhline(shown, color="0.45", linewidth=0.7, linestyle="-", gid=limit.name)
        if not limit.label:
            continue
        value = given * display.factor("length") if radius else shown
        unit = display.symbol("length" if radius else spec.kind)
        text = f"R = {value:.4g} {unit}" if radius else f"{value:.4g} {unit}"
        ax.annotate(
            f"{limit.label}: {text}",
            (1.0, shown),
            xycoords=("axes fraction", "data"),
            xytext=(-2, 2 if limit.sign > 0 else -2),
            textcoords="offset points",
            ha="right",
            va="bottom" if limit.sign > 0 else "top",
            fontsize=6,
            color="0.35",
            gid=limit.name,
        )
    if missing:
        ax.annotate(
            "no " + ", no ".join(missing),
            (1.0, 1.0),
            xycoords="axes fraction",
            xytext=(-2, -2),
            textcoords="offset points",
            ha="right",
            va="top",
            fontsize=6,
            color="0.35",
            gid="no_limit",
        )


def _panels(
    axs: Sequence[Axes] | None, specs: tuple[Panel, ...]
) -> tuple[Figure, list[Axes]]:
    count = len(specs)
    if axs is None:
        fig, created = plt.subplots(
            count,
            1,
            sharex=True,
            figsize=(7.0, {4: 9.0, 6: 12.5}.get(count, 16.0)),
            layout="constrained",
        )
        return fig, list(created)
    panels = list(axs)
    if len(panels) != count or not all(isinstance(ax, Axes) for ax in panels):
        names = ", ".join(spec.title.lower() for spec in specs)
        raise ValueError(
            f"axs must be {count} matplotlib Axes, one per panel ({names}), as "
            f"plt.subplots({count}, 1, sharex=True) returns them."
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


def _mark(ax: Axes, x: float, y: float, text: str, gid: str, *, inverted: bool) -> None:
    """Mark a point with its value."""
    ax.plot(
        [x], [y], marker="o", markersize=4, color="black", linestyle="none", gid=gid
    )
    ax.annotate(
        text,
        (x, y),
        xytext=(4, 4 if y >= 0 else -4),
        textcoords="offset points",
        va="bottom" if (y >= 0) != inverted else "top",
        fontsize=7,
        gid=gid,
    )


def _mark_governing(
    ax: Axes, spec: Panel, result: Result, display: DisplayUnits
) -> None:
    """Mark each governing value of the panel's columns with its value."""
    length = display.factor("length")
    for row in result.governing().itertuples():
        value = float(row.value)
        where = float(row.distance)
        if str(row.column) not in spec.governing or not (
            np.isfinite(value) and np.isfinite(where)
        ):
            continue
        shown = value * display.factor(spec.kind)
        _mark(
            ax,
            where * length,
            shown,
            f"{shown:.3g} {display.symbol(spec.kind)}",
            f"governing:{row.name}",
            inverted=spec is SETTLEMENT,
        )


def _mark_checks(ax: Axes, spec: Panel, result: Result, display: DisplayUnits) -> None:
    """Mark each of the panel's checks at its governing value and utilization."""
    length = display.factor("length")
    for check in spec.checks:
        row = _check_row(result, check)
        if row is None:
            continue
        value = float(row["value"])
        where = float(row["governing_distance"])
        if not (np.isfinite(value) and np.isfinite(where)):
            continue
        utilization = float(row["utilization"])
        used = "no limit" if math.isnan(utilization) else f"u = {utilization:.2f}"
        if check == "radius_of_curvature":
            # A radius is drawn at its curvature, 1/R, positive as the resultant.
            shown = display.factor(spec.kind) / value
            text = f"R = {value * length:.4g} {display.symbol('length')}, {used}"
        else:
            shown = value * display.factor(spec.kind)
            text = f"{shown:.3g} {display.symbol(spec.kind)}, {used}"
        _mark(ax, where * length, shown, text, f"check:{check}", inverted=False)


def _mark_closure(
    ax: Axes,
    spec: Panel,
    values: pd.DataFrame,
    distance: FloatArray,
    display: DisplayUnits,
) -> None:
    """Mark the most negative value of the panel's closure column, if any."""
    if spec.closure is None or spec.closure not in values:
        return
    column = values[spec.closure].to_numpy(dtype=np.float64)
    if not np.any(column < 0.0):
        return
    # The first of any tie, so the smaller distance, as the checks report.
    index = int(np.nanargmin(column))
    shown = column[index] * display.factor(spec.kind)
    _mark(
        ax,
        float(distance[index]),
        shown,
        f"closure {shown:.3g} {display.symbol(spec.kind)}, not checked",
        "closure",
        inverted=False,
    )


def _offset_axis(
    ax: Axes, values: pd.DataFrame, length: float, display: DisplayUnits, label: str
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
    top.set_xlabel(display.label(label, "length"))


SAME_AXIS_TOLERANCE = 1e-3
"""Distance in m within which two parallel tunnels' axes count as the same."""


def offset_label(result: Result) -> str:
    """Name the axis a built utility's offsets are measured from.

    One tunnel: its axis. Several, by superposition: the axis of the tunnel the
    utility was built from, named when exactly one part's tunnel lies on it,
    so the profile and the cross-section agree.
    """
    source = result.source
    if not isinstance(source, Superposition):
        return "Offset from tunnel axis"
    built = getattr(result.asset, "built", None)
    reference = getattr(built, "tunnel", None)
    if isinstance(reference, IdealizedTunnel):
        names = [
            name
            for name, tunnel in tunnels(source.sources)
            if _same_axis(reference, tunnel)
        ]
        if len(names) == 1:
            return f"Offset from axis of tunnel '{names[0]}'"
    return "Offset from reference tunnel axis"


def _same_axis(reference: IdealizedTunnel, tunnel: IdealizedTunnel) -> bool:
    """Whether a tunnel is parallel to the reference and on its axis."""
    if abs(math.sin(tunnel.azimuth - reference.azimuth)) > PARALLEL_TOLERANCE:
        return False
    _, offset = reference.station_offset(x=tunnel.reference_x, y=tunnel.reference_y)
    return (
        abs(float(offset)) <= SAME_AXIS_TOLERANCE
        and abs(tunnel.axis_depth - reference.axis_depth) <= SAME_AXIS_TOLERANCE
    )


def flag_notes(
    ax: Axes,
    result: Result,
    distance: FloatArray,
    display: DisplayUnits,
    *,
    below: float = 30.0,
) -> None:
    """Print each flag's reason and distance range, `below` points under `ax`."""
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
        lines.append(f"{flag.verdict.capitalize()}{where}: {flag_text(flag)}")
    if not lines:
        return
    ax.annotate(
        "\n".join(lines),
        (0.0, 0.0),
        xycoords="axes fraction",
        xytext=(0, -below),
        textcoords="offset points",
        va="top",
        ha="left",
        fontsize=7,
        wrap=True,
        gid="flags",
    )
