"""The cross-section figure: tunnel, trough and utility at its station (SPEC §9)."""

from collections.abc import Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Rectangle

from garisenda._result import Result
from garisenda.plot._display import resolve
from garisenda.plot._profile import SHADE, flag_notes
from garisenda.plot._style import style
from garisenda.sources._tunnel import IdealizedTunnel

PANELS = 3
# The trough's panels: the quantity, its label, its sign convention and color.
TROUGH_PANELS = (
    ("vertical", "Settlement at the surface", "down +", "C0"),
    ("horizontal", "Horizontal at the surface", "right +", "C1"),
)
GRID_POINTS = 401
"""The points the trough is drawn with across the section."""
WIDTHS = 3.0
"""How many trough widths i either side of the axis the trough is drawn to."""


def cross_section(
    result: Result,
    *,
    axs: Sequence[Axes] | None = None,
    display_units: Mapping[str, object] | None = None,
) -> tuple[Figure, list[Axes]]:
    """Draw the transverse section at a utility's station: three panels.

    The panels share the x axis, offset from the tunnel axis (positive to the
    right looking up-station, SPEC §8.1):

    1. settlement at the ground surface, its axis pointing down;
    2. horizontal movement at the ground surface, perpendicular to the
       tunnel, positive to the right (toward increasing offset, as in every
       view, SPEC §8.1), on its own panel because settlement's axis points
       down;
    3. the section to scale, depth pointing down from the ground surface at
       0: the tunnel's bore and axis, the utility as a band of its diameter at
       its axis depth between its offsets, and the axis depth and cover
       dimensioned.

    On the first two, the utility's stations are marked on the trough from the
    result's values, and the inflection points at ±i are marked.

    The trough runs past the utility's ends and its curve between stations
    isn't in the result, so the figure evaluates ``result.source`` at the
    surface on 401 points over the wider of the utility's offsets and ±3i, for
    drawing only (SPEC §3). The utility's own values come from the result,
    never recalculated. Stations that aren't ``"within"`` are ringed by
    verdict, and each flag's reason is printed under the figure with its
    distance range (SPEC §10).

    Parameters
    ----------
    result : Result
        A movement profile of a utility built from station and offset, over a
        source with a tunnel, from `garisenda.movement_profile`.
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
    tunnel = getattr(source, "tunnel", None)
    if asset is None or source is None or built is None:
        raise ValueError(
            "The cross-section is drawn at the station of a utility built from "
            "station and offset (gs.utilities.perpendicular_utility); a utility "
            "given by its vertices is drawn in plan by the plan figure (M5)."
        )
    if not isinstance(tunnel, IdealizedTunnel):
        raise ValueError(
            "The cross-section needs a source with a tunnel to draw the section "
            "through; this result's source has none. The plan figure (M5) draws "
            "the rest."
        )

    length = display.factor("length")
    move = display.factor("displacement")
    width = getattr(source, "trough_width", None)
    values = result.values
    offsets = values["offset"].to_numpy(dtype=np.float64)
    reach = max(float(np.max(np.abs(offsets))), WIDTHS * width if width else 0.0)
    if not width:
        reach = max(reach, WIDTHS * tunnel.axis_depth)
    grid = np.linspace(-reach, reach, GRID_POINTS)

    # The surface along the section, for drawing only (SPEC §3).
    station = built.station - tunnel.reference_station
    tangent, normal = np.array(tunnel.tangent), np.array(tunnel.normal)
    plan = (
        np.array([tunnel.reference_x, tunnel.reference_y])
        + station * tangent
        + grid[:, None] * normal
    )
    movement = source.evaluate(x=plan[:, 0], y=plan[:, 1], depth=np.zeros(len(grid)))
    settlement = movement.displacement[:, 2]
    horizontal = movement.displacement[:, :2] @ normal

    # The utility's own values, from the result.
    direction = np.sign(built.end_offset - built.start_offset)
    station_horizontal = direction * values["along"].to_numpy(dtype=np.float64)

    surface = {"vertical": settlement, "horizontal": horizontal}
    at_stations = {
        "vertical": values["vertical"].to_numpy(dtype=np.float64),
        "horizontal": station_horizontal,
    }
    with style():
        fig, panels = _panels(axs)
        trough_panels = dict(zip(("vertical", "horizontal"), panels, strict=False))
        x = grid * length
        verdict = values["verdict"].astype(str).to_numpy()
        for (key, label, convention, color), ax in zip(
            TROUGH_PANELS, panels, strict=False
        ):
            ax.plot(x, surface[key] * move, color=color, label="Trough", gid=key)
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
            ax.set_ylabel(display.label(label, "displacement"))
            ax.set_title(convention, loc="right", fontsize=7, color="0.35")
            ax.legend(loc="best", fontsize=7)
        trough_panels["vertical"].invert_yaxis()

        section = panels[2]
        _section(section, result, tunnel, length, display.symbol("length"), reach)
        section.set_xlabel(display.label("Offset from tunnel axis", "length"))
        section.set_ylabel(display.label("Depth", "length"))
        flag_notes(
            section,
            result,
            values["distance"].to_numpy(dtype=np.float64) * length,
            display,
        )
        fig.suptitle(
            f"Cross-section at station {built.station:.6g} m: {result.subject}",
            fontsize=10,
        )
    return fig, panels


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
    tunnel: IdealizedTunnel,
    length: float,
    unit: str,
    reach: float,
) -> None:
    """Draw the section to scale: ground, bore, axis, utility and dimensions."""
    asset = result.asset
    assert asset is not None and asset.built is not None
    built = asset.built
    radius = tunnel.diameter / 2 * length
    depth = tunnel.axis_depth * length
    ax.axhline(0.0, color="#7a5c3a", linewidth=1.2, gid="ground")
    ax.add_patch(
        Circle(
            (0.0, depth),
            radius,
            facecolor="0.9",
            edgecolor="black",
            linewidth=1.0,
            gid="tunnel",
        )
    )
    ax.plot([0.0], [depth], marker="+", color="black", markersize=8, gid="axis")
    ax.axvline(0.0, color="0.5", linestyle="-.", linewidth=0.6)

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

    # Dimensions: axis depth z0 and cover C, beside the bore.
    where = 1.6 * radius
    for top_y, bottom_y, label, gid in (
        (0.0, depth, f"z0 = {depth:.4g} {unit}", "axis_depth"),
        (0.0, depth - radius, f"C = {depth - radius:.4g} {unit}", "cover"),
    ):
        offset = where if gid == "axis_depth" else -where
        ax.annotate(
            "",
            (offset, bottom_y),
            xytext=(offset, top_y),
            arrowprops={"arrowstyle": "<->", "linewidth": 0.7, "color": "0.3"},
            gid=gid,
        )
        ax.text(
            offset,
            (top_y + bottom_y) / 2,
            f" {label}" if gid == "axis_depth" else f"{label} ",
            ha="left" if gid == "axis_depth" else "right",
            va="center",
            fontsize=7,
            color="0.2",
        )
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlim(-reach * length, reach * length)
    # Depth's range is set through the data limits, not fixed: at equal
    # aspect with x shared, matplotlib extends y to fit the panel.
    ax.update_datalim([(0.0, -2 * radius), (0.0, depth + 2 * radius)])
    ax.autoscale_view()
    ax.invert_yaxis()
