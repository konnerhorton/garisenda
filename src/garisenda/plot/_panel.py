"""What the profile's panels are made of, and the helpers every panel shares."""

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from matplotlib.axes import Axes

from garisenda._result import Result
from garisenda.plot._display import DisplayUnits, one_in


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
    negative value is marked as a closure, which isn't checked. `down`
    points the axis down, as settlement hangs in the ground.
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
    down: bool = False


DASHED = (0, (4, 2))
"""The dash pattern of discrete lines."""


def check_row(result: Result, check: str) -> Any:
    """Return a check's row of `Result.checks`, or None."""
    rows = result.checks[result.checks["check"] == check]
    return None if rows.empty else rows.iloc[0]


def draw_limits(ax: Axes, spec: Panel, result: Result, display: DisplayUnits) -> None:
    """Draw a panel's limit lines, or note the limits not given."""
    missing: list[str] = []
    for limit in spec.limits:
        row = check_row(result, limit.check)
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
        if spec.kind == "slope":
            text += f" ({one_in(given)})"
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


def mark(ax: Axes, x: float, y: float, text: str, gid: str, *, inverted: bool) -> None:
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


def mark_checks(ax: Axes, spec: Panel, result: Result, display: DisplayUnits) -> None:
    """Mark each of the panel's checks at its governing value and utilization."""
    length = display.factor("length")
    for check in spec.checks:
        row = check_row(result, check)
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
        mark(ax, where * length, shown, text, f"check:{check}", inverted=spec.down)
