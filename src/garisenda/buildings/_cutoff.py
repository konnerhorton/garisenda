"""Where along a wall the damage check is made: the cut-off."""

import math
from dataclasses import dataclass

from garisenda._inputs import judgments


@dataclass(frozen=True)
class NoCutoff:
    """The whole wall is assessed. Made by `no_cutoff`.

    Attributes
    ----------
    name : str
        Recorded as the ``cutoff`` input's value.
    """

    name: str = "none: the whole wall"


@dataclass(frozen=True)
class TroughWidthCutoff:
    """Only the wall within a multiple of i of a trough's axis is assessed.

    Made by `trough_width_cutoff`.

    Attributes
    ----------
    multiple : float
        m, the half-width in trough widths i.
    name : str
        Recorded as the ``cutoff`` input's value.
    """

    multiple: float

    @property
    def name(self) -> str:
        """``"<m> i from each trough's axis"``."""
        return f"{self.multiple:g} i from each trough's axis"


Cutoff = NoCutoff | TroughWidthCutoff
"""A cut-off method."""


def no_cutoff() -> NoCutoff:
    """Assess the whole wall, however far it runs beyond the trough.

    The wall's ends set the zones' ends where the trough is still
    significant, and where it isn't, the zone runs on, so its Delta/L and
    eps_h are averaged over flat ground.

    Returns
    -------
    NoCutoff
    """
    return NoCutoff()


@judgments(
    multiple="practice varies, and none is chosen here. Pass a number of "
    "trough widths, e.g. multiple=2.5."
)
def trough_width_cutoff(*, multiple: float) -> TroughWidthCutoff:
    """Assess only the wall within m trough widths i of a trough's axis in plan.

    For each transverse trough, the points on the wall's line within m i of
    its axis in plan, with i at the foundation depth; over several troughs,
    from the first such point to the last, so the ground between two tunnels
    is kept. Stations outside have no zone. Where the cut-off falls inside a
    zone it shortens it, which can lower its strains as well as raise them.

    Parameters
    ----------
    multiple : float
        m, a positive number of trough widths. A required judgment with no
        default: practice varies, and no multiple is chosen here.

    Returns
    -------
    TroughWidthCutoff

    Raises
    ------
    TypeError
        If `multiple` is missing.
    ValueError
        If `multiple` isn't positive and finite.
    """
    value = float(multiple)
    if not (math.isfinite(value) and value > 0):
        raise ValueError(f"multiple must be positive and finite, not {value}.")
    return TroughWidthCutoff(value)
