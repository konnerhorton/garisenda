"""The house style, applied only inside a context (SPEC §9)."""

from collections.abc import Iterator
from contextlib import contextmanager

import matplotlib as mpl

STYLE: dict[str, object] = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "legend.frameon": False,
    "axes.linewidth": 0.6,
    "axes.grid": True,
    "axes.grid.which": "major",
    "axes.axisbelow": True,
    "grid.linewidth": 0.5,
    "grid.color": "#d9d9d9",
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "savefig.dpi": 300,
}
"""The house style, as hangtu's: matplotlib rcParams."""


@contextmanager
def style() -> Iterator[None]:
    """Apply the house style inside a ``with`` block, never globally.

    Every rcParam is restored afterwards, even if the block raises.
    """
    # matplotlib types rc's keys as literals; STYLE's keys are plain str.
    with mpl.rc_context(rc=STYLE):  # type: ignore[arg-type]
        yield
