"""How the transverse trough's width changes with depth: the width methods."""

import math
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from garisenda._inputs import InputRecord, judgments, record

FloatArray = npt.NDArray[np.float64]

MAIR_NAME = "Mair et al. (1993), clay"
LINEAR_NAME = "linear"

MAIR_SOURCE = (
    "Mair & Taylor (1997), Theme lecture: Bored tunnelling in the urban "
    "environment, Eqs. 7-8, pp. 2361-2362, after Mair et al. (1993); the same "
    "equation as Taylor (1995), Eq. 5, p. 125 and Bracegirdle et al. (1996), "
    "Eq. 2, p. 660. Crown limit: Bracegirdle et al. (1996), p. 660."
)
LINEAR_SOURCE = (
    "The caller's choice: no source gives this width at depth. The crown limit "
    "of Bracegirdle et al. (1996), p. 660 is applied to it by garisenda."
)

MAIR_EQUATIONS = (
    "K(z) = (0.175 + 0.325 (1 - z/z0)) / (1 - z/z0)",
    "i(z) = K(z) (z0 - z) = 0.175 z0 + 0.325 (z0 - z)",
)
LINEAR_EQUATIONS = ("i(z) = k (z0 - z)",)

MAIR_ASSUMPTIONS = (
    "Mair et al. (1993)'s fit is to tunnels in clays (London Clay, soft clay, "
    "centrifuge tests); garisenda can't check the ground.",
)
LINEAR_ASSUMPTIONS = (
    "i = k (z0 - z) with the caller's k, their choice: no source gives this "
    "width at depth. With constant volume, movement is toward the axis; in "
    "sands this may underestimate horizontal movement near the edge of the "
    "trough (Mair & Taylor 1997, p. 2362).",
)


@dataclass(frozen=True)
class TroughWidth:
    """A method for the transverse trough's width at depth.

    Made by `mair_trough_width` or `linear_trough_width`, not directly. Both
    give a width linear in depth, i(z) = c0 z0 + c1 (z0 - z), with z the
    depth and z0 the tunnel's axis depth.

    Attributes
    ----------
    name : str
        The method's name, recorded as the ``trough_width`` input's value.
    surface_coefficient : float
        c0, dimensionless.
    rate : float
        c1, dimensionless: the width decreases by c1 per unit of depth.
    inputs : tuple of InputRecord
        The method's own inputs (``trough_width_parameter`` for the linear
        method; none for Mair's).
    equations : tuple of str
        The method's equations.
    source : str
        Its citation.
    assumptions : tuple of str
        What it assumes and garisenda can't check.
    """

    name: str
    surface_coefficient: float
    rate: float
    inputs: tuple[InputRecord, ...]
    equations: tuple[str, ...]
    source: str
    assumptions: tuple[str, ...]

    def at(self, *, depth: float | FloatArray, axis_depth: float) -> float | FloatArray:
        """Return the trough width i, in m, at a depth.

        Computed as i = c0 z0 + c1 (z0 - z), never as K (z0 - z), so it stays
        finite as z approaches z0. No limit is applied: the trough caps depth
        at the crown before calling it.

        Parameters
        ----------
        depth : float or numpy.ndarray
            z, depth below the ground surface in m, positive downward.
        axis_depth : float
            z0, the tunnel's axis depth in m.

        Returns
        -------
        float or numpy.ndarray
            i, in m.
        """
        width: float | FloatArray = (
            self.surface_coefficient * axis_depth + self.rate * (axis_depth - depth)
        )
        return width


def mair_trough_width() -> TroughWidth:
    """Return Mair et al. (1993)'s trough width at depth for tunnels in clay.

    With z the depth and z0 the axis depth (Mair & Taylor 1997, Eqs. 7-8):

    - K(z) = (0.175 + 0.325 (1 - z/z0)) / (1 - z/z0), which equals Taylor's
      (1995, Eq. 5) form K = 0.325 + 0.175 / (1 - z/z0);
    - i(z) = K(z) (z0 - z) = 0.175 z0 + 0.325 (z0 - z), in m.

    At the surface K = 0.5 and i = 0.5 z0; at the crown, z0 - D/2, the width
    is 0.175 z0 + 0.1625 D. The coefficients 0.175 and 0.325 are the method,
    not inputs: they can't be swept or overridden.

    Returns
    -------
    TroughWidth
        Named ``"Mair et al. (1993), clay"``, with c0 = 0.175 and c1 = 0.325.

    Notes
    -----
    Validity: only above the tunnel crown (Bracegirdle et al. 1996, p. 660:
    "Equation 2 should only be applied when estimating ground movements above
    the level of the crown of the tunnel"); the trough flags deeper points.
    Mair et al. (1993)'s data, in Mair & Taylor (1997) Fig. 20, reach
    z/z0 of about 0.9, all in clays: for a tunnel with z0 < 5 D the crown is
    deeper than that, so near the crown the fit is extrapolated. No source
    states that as a limit, so it isn't flagged.

    Source: Mair & Taylor (1997), Theme lecture: Bored tunnelling in the urban
    environment, Eqs. 7-8, pp. 2361-2362, after Mair et al. (1993); the same
    equation in other forms in Taylor (1995), Eq. 5, p. 125 and Bracegirdle
    et al. (1996), Eq. 2, p. 660. Mair et al. (1993) itself has not been read
    yet.
    """
    return TroughWidth(
        name=MAIR_NAME,
        surface_coefficient=0.175,
        rate=0.325,
        inputs=(),
        equations=MAIR_EQUATIONS,
        source=MAIR_SOURCE,
        assumptions=MAIR_ASSUMPTIONS,
    )


@judgments(
    trough_width_parameter="k sets the trough width i = k (z0 - z) and depends "
    "on the ground. Pass it as a number, e.g. trough_width_parameter=0.5.",
)
def linear_trough_width(*, trough_width_parameter: object) -> TroughWidth:
    """Return a trough width linear in depth from the caller's k.

    With z the depth and z0 the axis depth: i(z) = k (z0 - z), in m. At the
    surface it is k z0, the width of `transverse_surface_trough` with the
    same k; it reaches zero at the axis.

    Parameters
    ----------
    trough_width_parameter : float
        k, dimensionless. A design judgment with no default, recorded as the
        caller's choice: no source gives this width at depth. Must be positive
        and finite.

    Returns
    -------
    TroughWidth
        Named ``"linear"``, with c0 = 0 and c1 = k, and the
        ``trough_width_parameter`` input record.

    Raises
    ------
    TypeError
        If `trough_width_parameter` is missing.
    ValueError
        If it isn't positive and finite.

    Notes
    -----
    Validity: only above the tunnel crown, the limit Bracegirdle et al.
    (1996), p. 660 give for Mair et al. (1993)'s width, applied to this method
    by garisenda; the trough flags deeper points. No range is checked for k.

    Source: the caller's choice; no source gives this width at depth.
    """
    k, k_record = record(
        "trough_width_parameter",
        trough_width_parameter,
        kind="design judgment",
        unit="dimensionless",
        plain_number="read as SI",
    )
    k = float(k)
    if not (math.isfinite(k) and k > 0):
        raise ValueError(f"trough_width_parameter must be positive, not {k}.")
    return TroughWidth(
        name=LINEAR_NAME,
        surface_coefficient=0.0,
        rate=k,
        inputs=(k_record,),
        equations=LINEAR_EQUATIONS,
        source=LINEAR_SOURCE,
        assumptions=LINEAR_ASSUMPTIONS,
    )
