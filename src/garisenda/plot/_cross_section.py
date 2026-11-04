"""The cross-section figure: tunnel, trough and utility at its station (SPEC §9)."""

import math
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Rectangle

from garisenda._result import Result
from garisenda.plot._display import resolve
from garisenda.plot._profile import SHADE, flag_notes
from garisenda.plot._style import style
from garisenda.sources._movement import Source
from garisenda.sources._superposition import (
    PARALLEL_TOLERANCE,
    Superposition,
    tunnels,
)
from garisenda.sources._transverse_trough import TransverseTrough
from garisenda.sources._tunnel import IdealizedTunnel

PANELS = 3
# The trough's panels: the quantity, its label, its sign convention and color.
TROUGH_PANELS = (
    ("vertical", "Settlement", "down +", "C0"),
    ("horizontal", "Horizontal", "right +", "C1"),
)
SURFACE_TOLERANCE = 1e-3
"""Depth in m within which the trough is drawn and titled as at the surface."""
DASHES = ("--", ":", (0, (6, 2, 1, 2)), (0, (1, 3)))
"""Each source's own trough, in turn, so the legend tells them apart."""
GRID_POINTS = 401
"""The points the trough is drawn with across the section."""
WIDTHS = 3.0
"""How many trough widths i either side of the axis the trough is drawn to."""
NOTE_BELOW = 30.0
"""How far below the section panel the notes start, in points."""
NOTE_LINE = 20.0
"""How much further down a note of tunnels not drawn pushes the flag notes."""


@dataclass(frozen=True)
class _Bore:
    """A tunnel drawn in the section: its name, and its offset from the reference."""

    name: str
    """Its name path in a superposition; empty for a lone source."""
    tunnel: IdealizedTunnel
    offset: float
    """From the reference tunnel's axis, in m, positive to the right."""
    width: float | None
    """Its trough's width i, in m, if its source has one."""


def cross_section(
    result: Result,
    *,
    axs: Sequence[Axes] | None = None,
    display_units: Mapping[str, object] | None = None,
) -> tuple[Figure, list[Axes]]:
    """Draw the transverse section at a utility's station: three panels.

    The panels share the x axis, offset from the tunnel axis (positive to the
    right looking up-station, SPEC §8.1); with several tunnels, from the axis
    of the utility's reference tunnel, the one it was built from:

    1. settlement at the utility's depth, its axis pointing down;
    2. horizontal movement at the utility's depth, perpendicular to the
       tunnel, positive to the right (toward increasing offset, as in every
       view, SPEC §8.1), on its own panel because settlement's axis points
       down;
    3. the section to scale, depth pointing down from the ground surface at
       0: the tunnel's bore and axis, the utility as a band of its diameter at
       its axis depth between its offsets, and the axis depth and cover
       dimensioned.

    On the first two, the utility's stations are marked on the trough from the
    result's values, and the inflection points at ±i are marked, with i at the
    drawn depth (capped at the crown, as the trough's values are).

    **The depth drawn.** A source whose trough changes with depth
    (`garisenda.sources.transverse_trough`) is drawn at the utility's axis
    depth, and the panels say so ("Settlement at depth 10 m"). A source that
    has only a surface trough (`garisenda.sources.transverse_surface_trough`)
    is drawn at the surface, titled so, since that is what it gives at any
    depth; its stations below the surface are ringed as flagged. With several
    sources, the depth is the utility's if any of them changes with depth.
    Points of the drawn line inside a bore aren't evaluated, and the line
    breaks there.

    The trough runs past the utility's ends and its curve between stations
    isn't in the result, so the figure evaluates ``result.source`` at that
    depth on 401 points over the wider of the utility's offsets and ±3i, for
    drawing only (SPEC §3). The utility's own values come from the result,
    never recalculated. Stations that aren't ``"within"`` are ringed by
    verdict, and each flag's reason is printed under the figure with its
    distance range (SPEC §10).

    **Several tunnels** (a source from `garisenda.superpose`, nested ones
    included): the solid line is the combined trough, and each source's own
    trough is drawn thin and dashed, each its own pattern, so what was added
    shows. Each tunnel parallel to the reference tunnel is drawn in the
    section at its offset and depth, labeled with its name and with its axis
    depth and cover dimensioned, and its axis is a dash-dot line on every
    panel. The troughs are drawn over the utility's offsets and each drawn
    tunnel's offset ±3i (or ±3 z0 for a source with no trough width). The ±i
    marks are left out. A tunnel that isn't parallel to the reference tunnel
    isn't drawn, since its section here would mislead; a note under the
    figure names it, its dashed trough is still drawn (it is the field along
    the section), and the plan figure (M5) shows it.

    Parameters
    ----------
    result : Result
        A movement profile of a utility built from station and offset, over a
        source with a tunnel or a superposition of sources with tunnels, from
        `garisenda.movement_profile`.
    axs : sequence of three matplotlib Axes, optional
        Panels to draw into, top to bottom, sharing x; no figure is created.
        Otherwise a new figure is made.
    display_units : mapping, optional
        Units per kind of quantity, any of ``length`` (default m) and
        ``displacement`` (mm); ``strain`` and ``curvature`` are accepted and
        unused.

    Returns
    -------
    fig : matplotlib.figure.Figure
    axs : list of matplotlib.axes.Axes
        The settlement, horizontal movement and section panels.

    Raises
    ------
    ValueError
        If the utility wasn't built from station and offset, or the source has
        no tunnel: the cross-section needs a section through a tunnel, and
        utilities in plan are drawn by the plan figure (M5). Also if `axs`
        isn't three Axes or `display_units` names an unknown kind.
    pint.DimensionalityError
        If a display unit doesn't fit its kind.
    """
    display = resolve(display_units)
    asset, source = result.asset, result.source
    built = getattr(asset, "built", None)
    if asset is None or source is None or built is None:
        raise ValueError(
            "The cross-section is drawn at the station of a utility built from "
            "station and offset (gs.utilities.perpendicular_utility); a utility "
            "given by its vertices is drawn in plan by the plan figure (M5)."
        )
    several = isinstance(source, Superposition)
    if several:
        assert isinstance(source, Superposition)
        reference = built.tunnel
        parts = dict(_parts(source.sources))
        found = list(tunnels(source.sources))
    else:
        tunnel = getattr(source, "tunnel", None)
        parts = {}
        found = [("", tunnel)] if isinstance(tunnel, IdealizedTunnel) else []
    if not found:
        raise ValueError(
            "The cross-section needs a source with a tunnel to draw the section "
            "through; this result's source has none. The plan figure (M5) draws "
            "the rest."
        )

    length = display.factor("length")
    move = display.factor("displacement")
    values = result.values
    offsets = values["offset"].to_numpy(dtype=np.float64)
    every = list(parts.values()) if several else [source]
    deep = any(isinstance(part, TransverseTrough) for part in every)
    depth = float(np.mean(asset.vertices[:, 2])) if deep else 0.0
    if depth <= SURFACE_TOLERANCE:
        depth = 0.0
    if several:
        bores, skipped = _bores(reference, found, parts, depth)
        width = None
        reaches = [(bore.offset, _reach(bore)) for bore in bores]
        low = min([float(np.min(offsets))] + [o - r for o, r in reaches])
        high = max([float(np.max(offsets))] + [o + r for o, r in reaches])
    else:
        reference = found[0][1]
        width = _width(source, depth)
        bores = [_Bore("", reference, 0.0, width)]
        skipped = []
        high = max(float(np.max(np.abs(offsets))), _reach(bores[0]))
        low = -high
    grid = np.linspace(low, high, GRID_POINTS)

    # The trough along the section at the drawn depth, for drawing only
    # (SPEC §3). Points inside a bore can't be evaluated; the drawn line
    # breaks there (NaN in the drawing arrays only, never in a result).
    station = built.station - reference.reference_station
    tangent, normal = np.array(reference.tangent), np.array(reference.normal)
    plan = (
        np.array([reference.reference_x, reference.reference_y])
        + station * tangent
        + grid[:, None] * normal
    )
    clear = np.ones(len(grid), dtype=bool)
    for _, bored in found:
        _, across = bored.station_offset(x=plan[:, 0], y=plan[:, 1])
        clear &= np.hypot(across, depth - bored.axis_depth) >= bored.diameter / 2

    def surface_of(field: Source) -> dict[str, npt.NDArray[np.float64]]:
        drawn = {key: np.full(len(grid), np.nan) for key in ("vertical", "horizontal")}
        if clear.any():
            movement = field.evaluate(
                x=plan[clear, 0],
                y=plan[clear, 1],
                depth=np.full(int(clear.sum()), depth),
            )
            drawn["vertical"][clear] = movement.displacement[:, 2]
            drawn["horizontal"][clear] = movement.displacement[:, :2] @ normal
        return drawn

    surface = surface_of(source)
    own = {name: surface_of(part) for name, part in parts.items()}

    # The utility's own values, from the result.
    direction = np.sign(built.end_offset - built.start_offset)
    station_horizontal = direction * values["along"].to_numpy(dtype=np.float64)

    at_stations = {
        "vertical": values["vertical"].to_numpy(dtype=np.float64),
        "horizontal": station_horizontal,
    }
    with style():
        fig, panels = _panels(axs)
        trough_panels = dict(zip(("vertical", "horizontal"), panels, strict=False))
        x = grid * length
        verdict = values["verdict"].astype(str).to_numpy()
        where = (
            f"at depth {depth * length:.4g} {display.symbol('length')}"
            if depth
            else "at the surface"
        )
        for (key, label, convention, color), ax in zip(
            TROUGH_PANELS, panels, strict=False
        ):
            ax.plot(
                x,
                surface[key] * move,
                color=color,
                label="Combined" if several else "Trough",
                gid=key,
            )
            for index, (name, part) in enumerate(own.items()):
                ax.plot(
                    x,
                    part[key] * move,
                    color=color,
                    linestyle=DASHES[index % len(DASHES)],
                    linewidth=0.8,
                    alpha=0.7,
                    label=name,
                    gid=f"trough:{name}:{key}",
                )
            ax.plot(
                offsets * length,
                at_stations[key] * move,
                linestyle="none",
                marker="o",
                markersize=3.5,
                color=color,
                label=result.subject,
                gid=f"stations:{key}",
            )
            for name, ring in SHADE.items():
                flagged = verdict == name
                if flagged.any():
                    ax.plot(
                        offsets[flagged] * length,
                        at_stations[key][flagged] * move,
                        linestyle="none",
                        marker="o",
                        markersize=8,
                        markerfacecolor="none",
                        markeredgecolor=ring,
                        markeredgewidth=1.5,
                        label=f"{result.subject}, {name}",
                        gid=name,
                    )
            ax.axhline(0.0, color="0.4", linewidth=0.6, zorder=1)
            if several:
                for bore in bores:
                    _axis(ax, bore, length)
            if width:
                for side in (-1, 1):
                    ax.axvline(
                        side * width * length,
                        color="0.5",
                        linestyle=":",
                        linewidth=0.8,
                        gid="inflection",
                    )
                ax.text(
                    width * length,
                    0.02,
                    " i",
                    transform=ax.get_xaxis_transform(),
                    va="bottom",
                    color="0.35",
                    fontsize=8,
                )
            ax.margins(y=0.15)
            ax.set_ylabel(display.label(f"{label} {where}", "displacement"))
            ax.set_title(convention, loc="right", fontsize=7, color="0.35")
            ax.legend(loc="best", fontsize=7)
        trough_panels["vertical"].invert_yaxis()

        section = panels[2]
        _section(section, result, bores, length, display.symbol("length"), (low, high))
        if several:
            for bore in bores:
                _axis(section, bore, length)
        axis_label = (
            "Offset from reference tunnel axis"
            if several
            else "Offset from tunnel axis"
        )
        section.set_xlabel(display.label(axis_label, "length"))
        section.set_ylabel(display.label("Depth", "length"))
        below = NOTE_BELOW
        if skipped:
            below += _note(section, skipped)
        flag_notes(
            section,
            result,
            values["distance"].to_numpy(dtype=np.float64) * length,
            display,
            below=below,
        )
        fig.suptitle(
            f"Cross-section at station {built.station:.6g} m: {result.subject}",
            fontsize=10,
        )
    return fig, panels


def _parts(sources: Mapping[str, Source]) -> Iterator[tuple[str, Source]]:
    """Yield each source that isn't a superposition, by its name path."""
    for name, part in sources.items():
        if isinstance(part, Superposition):
            for inner, nested in _parts(part.sources):
                yield f"{name}.{inner}", nested
        else:
            yield name, part


def _bores(
    reference: IdealizedTunnel,
    found: list[tuple[str, IdealizedTunnel]],
    parts: Mapping[str, Source],
    depth: float,
) -> tuple[list[_Bore], list[str]]:
    """Split the tunnels into those parallel to the reference and the rest."""
    bores: list[_Bore] = []
    skipped: list[str] = []
    for name, tunnel in found:
        if abs(math.sin(tunnel.azimuth - reference.azimuth)) > PARALLEL_TOLERANCE:
            skipped.append(name)
            continue
        _, offset = reference.station_offset(x=tunnel.reference_x, y=tunnel.reference_y)
        part = parts.get(name)
        width = None if part is None else _width(part, depth)
        bores.append(_Bore(name, tunnel, float(offset), width))
    return bores, skipped


def _width(source: Source, depth: float) -> float | None:
    """Return a source's trough width i in m at a depth, if it has one.

    i at the depth capped at the crown for a trough at depth, so the marks
    match the values drawn below it; M1's surface width otherwise.
    """
    if isinstance(source, TransverseTrough):
        return float(source.width_at(depth))
    width = getattr(source, "trough_width", None)
    return float(width) if isinstance(width, int | float) else None


def _reach(bore: _Bore) -> float:
    """How far either side of a bore's axis the troughs are drawn."""
    return WIDTHS * (bore.width if bore.width else bore.tunnel.axis_depth)


def _axis(ax: Axes, bore: _Bore, length: float) -> None:
    """Draw a bore's axis as a dash-dot line across the panel."""
    ax.axvline(
        bore.offset * length,
        color="0.5",
        linestyle="-.",
        linewidth=0.6,
        gid=f"axis:{bore.name}" if bore.name else None,
    )


def _note(ax: Axes, skipped: list[str]) -> float:
    """Name the tunnels not drawn under the figure; return the points it takes."""
    names = ", ".join(skipped)
    if len(skipped) == 1:
        text = (
            f"{names} isn't parallel to the reference tunnel, so the section "
            "doesn't draw it; the troughs include it, and the plan figure (M5) "
            "shows it."
        )
    else:
        text = (
            f"{names} aren't parallel to the reference tunnel, so the section "
            "doesn't draw them; the troughs include them, and the plan figure "
            "(M5) shows them."
        )
    ax.annotate(
        text,
        (0.0, 0.0),
        xycoords="axes fraction",
        xytext=(0, -NOTE_BELOW),
        textcoords="offset points",
        va="top",
        ha="left",
        fontsize=7,
        wrap=True,
        gid="note",
    )
    return NOTE_LINE


def _panels(axs: Sequence[Axes] | None) -> tuple[Figure, list[Axes]]:
    if axs is None:
        fig, created = plt.subplots(
            PANELS,
            1,
            sharex=True,
            figsize=(7.0, 9.0),
            layout="constrained",
            height_ratios=(1.0, 0.8, 1.3),
        )
        return fig, list(created)
    panels = list(axs)
    if len(panels) != PANELS or not all(isinstance(ax, Axes) for ax in panels):
        raise ValueError(
            f"axs must be {PANELS} matplotlib Axes (settlement, horizontal "
            "movement and the section), "
            f"as plt.subplots({PANELS}, 1, sharex=True) returns them."
        )
    figure = panels[0].get_figure()
    if not isinstance(figure, Figure):
        raise ValueError("axs[0] isn't in a figure.")
    return figure, panels


def _section(
    ax: Axes,
    result: Result,
    bores: Sequence[_Bore],
    length: float,
    unit: str,
    reach: tuple[float, float],
) -> None:
    """Draw the section to scale: ground, bores, axes, utility and dimensions.

    A lone source's bore keeps M1's gids (``tunnel``, ``axis``,
    ``axis_depth``, ``cover``); a named bore's carry its name
    (``tunnel:<name>``, ...), and its axis line is drawn by the caller on
    every panel.
    """
    asset = result.asset
    assert asset is not None and asset.built is not None
    built = asset.built
    ax.axhline(0.0, color="#7a5c3a", linewidth=1.2, gid="ground")
    deepest = 0.0
    for bore in bores:
        deepest = max(deepest, _bore(ax, bore, length, unit))

    utility_depth = float(np.mean(asset.vertices[:, 2])) * length
    diameter = asset.diameter * length
    low, high = sorted((built.start_offset, built.end_offset))
    ax.add_patch(
        Rectangle(
            (low * length, utility_depth - diameter / 2),
            (high - low) * length,
            diameter,
            facecolor="C2",
            edgecolor="C2",
            linewidth=0.8,
            gid="utility",
        )
    )
    ax.annotate(
        f"{result.subject}, diameter {diameter:.3g} {unit}",
        (high * length, utility_depth),
        xytext=(4, 0),
        textcoords="offset points",
        va="center",
        fontsize=7,
    )
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlim(reach[0] * length, reach[1] * length)
    # Depth's range is set through the data limits, not fixed: at equal
    # aspect with x shared, matplotlib extends y to fit the panel.
    largest = max(bore.tunnel.diameter for bore in bores) * length
    ax.update_datalim([(0.0, -largest), (0.0, deepest + largest)])
    ax.autoscale_view()
    ax.invert_yaxis()


def _bore(ax: Axes, bore: _Bore, length: float, unit: str) -> float:
    """Draw one bore with its axis depth and cover; return its axis depth."""
    suffix = f":{bore.name}" if bore.name else ""
    center = bore.offset * length
    radius = bore.tunnel.diameter / 2 * length
    depth = bore.tunnel.axis_depth * length
    ax.add_patch(
        Circle(
            (center, depth),
            radius,
            facecolor="0.9",
            edgecolor="black",
            linewidth=1.0,
            gid=f"tunnel{suffix}",
        )
    )
    ax.plot(
        [center],
        [depth],
        marker="+",
        color="black",
        markersize=8,
        gid=None if bore.name else "axis",
    )
    if bore.name:
        ax.annotate(
            bore.name,
            (center, depth + radius),
            xytext=(0, -3),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=7,
            gid=f"label{suffix}",
        )
    else:
        ax.axvline(center, color="0.5", linestyle="-.", linewidth=0.6)

    # Dimensions: axis depth z0 and cover C, beside the bore.
    where = 1.6 * radius
    for top_y, bottom_y, label, kind in (
        (0.0, depth, f"z0 = {depth:.4g} {unit}", "axis_depth"),
        (0.0, depth - radius, f"C = {depth - radius:.4g} {unit}", "cover"),
    ):
        right = kind == "axis_depth"
        x = center + (where if right else -where)
        ax.annotate(
            "",
            (x, bottom_y),
            xytext=(x, top_y),
            arrowprops={"arrowstyle": "<->", "linewidth": 0.7, "color": "0.3"},
            gid=f"{kind}{suffix}",
        )
        if bore.name:
            # Bores side by side would put one bore's label beside the
            # next one's arrow; written along its own arrow, it can't.
            ax.annotate(
                label,
                (x, (top_y + bottom_y) / 2),
                xytext=(-2, 0),
                textcoords="offset points",
                rotation=90,
                ha="right",
                va="center",
                fontsize=7,
                color="0.2",
            )
            continue
        ax.text(
            x,
            (top_y + bottom_y) / 2,
            f" {label}" if right else f"{label} ",
            ha="left" if right else "right",
            va="center",
            fontsize=7,
            color="0.2",
        )
    return depth
