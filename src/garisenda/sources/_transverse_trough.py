"""The steady-state transverse Gaussian trough at depth."""

import itertools
import math
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from garisenda._inputs import InputRecord, judgments, record, record_method
from garisenda.sources._critical import find_critical_distances
from garisenda.sources._movement import Flag, MethodRecord, Movement
from garisenda.sources._segment import check_outside_bore, read_points, read_segment
from garisenda.sources._trough_width import LINEAR_NAME, TroughWidth
from garisenda.sources._tunnel import IdealizedTunnel

DEPTH_TOLERANCE = 1e-3
"""Depth in m within which a point counts as at the surface or at the crown."""
CRITICAL_DISTANCE_SAMPLING = 1 / 8
"""Sampling interval for critical distances, as a fraction of the feature length."""
CRITICAL_DISTANCE_TOLERANCE = 1e-9
"""Length in m to which critical distances are found."""

HOW = (
    "Write it as trough_width=gs.sources.mair_trough_width() (Mair et al. "
    "(1993)'s method for clay) or "
    "trough_width=gs.sources.linear_trough_width(trough_width_parameter=0.5) "
    "(i = k (z0 - z) from your k)."
)

EQUATIONS = (
    "i(z) = c0 z0 + c1 (z0 - z)",
    "A = pi D^2 / 4",
    "Q = V_L A / sqrt(2 pi)",
    "S(o, z) = (Q / i) exp(-r^2 / 2), r = o / i",
    "u_n(o, z) = -c1 r S",
)

SOURCES = (
    "Gaussian at depth: Mair & Taylor (1997), Theme lecture: Bored tunnelling "
    "in the urban environment, p. 2361. Settlement at depth with the volume "
    "V_L A: Bracegirdle et al. (1996), Eq. 1, p. 660. Horizontal movement from "
    "constant volume: Taylor (1995), Tunnelling in soft ground in the UK, "
    "p. 125; Mair & Taylor (1997), p. 2362. Crown limit: Bracegirdle et al. "
    "(1996), p. 660."
)

ASSUMPTIONS = (
    "Steady state: the face has long passed.",
    "Transverse trough only: the longitudinal trough is not considered.",
    "The settlement trough is Gaussian at every depth, with the same volume "
    "V_L A per unit length.",
    "Constant volume (undrained), which sets the horizontal movement.",
    "Points below the tunnel crown get the trough at the crown, flagged.",
    "No validity range is checked for k or volume loss: the sources aren't "
    "verified yet.",
)

BELOW_CROWN = (
    "Below the tunnel crown: the subsurface trough applies only above the crown "
    "(Bracegirdle et al. 1996, p. 660{linear}). Values are the trough at crown "
    "level; movements beside and below the bore need another method or "
    "numerical analysis."
)

# The derivative tables: the polynomials P_ab (settlement) and R_ab (horizontal)
# in r, as coefficients from r^0 up, with a the order in offset and b in depth.
SETTLEMENT_POLYNOMIALS: dict[tuple[int, int], tuple[float, ...]] = {
    (0, 0): (1,),
    (1, 0): (0, -1),
    (0, 1): (1, 0, -1),
    (2, 0): (-1, 0, 1),
    (1, 1): (0, -3, 0, 1),
    (0, 2): (2, 0, -5, 0, 1),
    (3, 0): (0, 3, 0, -1),
    (2, 1): (-3, 0, 6, 0, -1),
    (1, 2): (0, -12, 0, 9, 0, -1),
    (0, 3): (6, 0, -27, 0, 12, 0, -1),
}
HORIZONTAL_POLYNOMIALS: dict[tuple[int, int], tuple[float, ...]] = {
    (0, 0): (0, -1),
    (1, 0): (-1, 0, 1),
    (0, 1): (0, -2, 0, 1),
    (2, 0): (0, 3, 0, -1),
    (1, 1): (-2, 0, 5, 0, -1),
    (0, 2): (0, -6, 0, 7, 0, -1),
    (3, 0): (3, 0, -6, 0, 1),
    (2, 1): (0, 12, 0, -9, 0, 1),
    (1, 2): (-6, 0, 27, 0, -12, 0, 1),
    (0, 3): (0, -24, 0, 48, 0, -15, 0, 1),
}

FloatArray = npt.NDArray[np.float64]


@judgments(
    volume_loss="it depends on the tunneling method, the ground and the "
    "workmanship. Pass it as a pint quantity, e.g. "
    "volume_loss=0.5 * gs.units.percent.",
    trough_width="the trough's width at depth depends on the ground, and "
    f"practice uses more than one method. {HOW}",
)
def transverse_trough(
    tunnel: IdealizedTunnel, *, volume_loss: object, trough_width: object
) -> "TransverseTrough":
    """Return the steady-state transverse Gaussian trough at any depth.

    With o a point's offset from the tunnel axis in plan, z its depth, z0 the
    axis depth, D the diameter and (c0, c1) the width method's coefficients:

    - trough width: i(z) = c0 z0 + c1 (z0 - z), in m, with
      (c0, c1) = (0.175, 0.325) for `mair_trough_width` and (0, k) for
      `linear_trough_width`;
    - tunnel area: A = pi D^2 / 4, and Q = V_L A / sqrt(2 pi), in m^2;
    - settlement: S(o, z) = (Q / i) exp(-r^2 / 2), r = o / i, in m, so the
      trough's volume per unit length is sqrt(2 pi) i S_max = V_L A at every
      depth;
    - horizontal movement toward the axis, along the right-hand normal n:
      u_n = -c1 r S, in m. It is the only one that keeps the volume constant,
      du_n/do + dS/dz = 0, and is zero over the axis. Its vectors meet the
      centerline (c0 / c1) z0 below the axis: for Mair's method 0.175 z0 / 0.325
      below it (Taylor 1995), which gives 65 % of the horizontal movement
      toward the axis at the surface (Mair & Taylor 1997); for the linear
      method the axis itself, u_n = -(o / (z0 - z)) S.

    At the surface the linear method is `transverse_surface_trough` with the
    same k. Mair's has its settlement with k = 0.5 and 0.65 of its horizontal
    movement, as the paper states.

    Parameters
    ----------
    tunnel : IdealizedTunnel
        The tunnel.
    volume_loss : pint quantity
        V_L, the trough volume per unit length as a fraction of the tunnel's
        area. A design judgment with no default; a plain number is refused,
        because 0.5 could be 0.5 % or 50 %. Must be more than 0 and less than
        100 %.
    trough_width : TroughWidth
        How the width changes with depth: ``gs.sources.mair_trough_width()``
        or ``gs.sources.linear_trough_width(trough_width_parameter=k)``. A
        design judgment with no default, recorded by the method's
        name.

    Returns
    -------
    TransverseTrough
        The source; call its `evaluate` for the movement at points.

    Raises
    ------
    TypeError
        If a judgment is missing, `volume_loss` is a plain number, or
        `trough_width` isn't one of the width methods.
    ValueError
        If `volume_loss` is outside its physical range.

    Notes
    -----
    Validity: points no deeper than the crown, z0 - D/2, plus 1 mm are
    ``"within"``. Deeper points outside the bore (beside it or below the axis)
    are ``"outside"`` and get the trough at the crown, with depth derivatives
    zero: "Equation 2 should only be applied when estimating ground movements
    above the level of the crown of the tunnel" (Bracegirdle et al. 1996,
    p. 660). For the linear method garisenda applies the same limit. Points
    inside the bore or above the surface raise. Mair et al. (1993)'s data
    reach z/z0 of about 0.9, so near the crown of a tunnel with z0 < 5 D the
    fit is extrapolated; no source states that as a limit, so it isn't
    flagged.

    Sources: the Gaussian at depth, Mair & Taylor (1997), Theme lecture:
    Bored tunnelling in the urban environment, p. 2361; the width for clay,
    Mair & Taylor (1997), Eqs. 7-8, pp. 2361-2362, after Mair et al. (1993),
    with Taylor (1995), Eq. 5, p. 125 and Bracegirdle et al. (1996), Eq. 2,
    p. 660 as the same equation in other forms; settlement at depth with the
    volume V_L A, Bracegirdle et al. (1996), Eq. 1, p. 660; the point O and
    constant volume, Taylor (1995), Tunnelling in soft ground in the UK,
    p. 125, and Mair & Taylor (1997), p. 2362; the crown limit, Bracegirdle
    et al. (1996), p. 660.
    """
    ratio, volume_record = record(
        "volume_loss",
        volume_loss,
        kind="design judgment",
        unit="dimensionless",
        plain_number="refuse",
    )
    ratio = float(ratio)
    if not 0 < ratio < 1:
        raise ValueError(
            f"volume_loss must be more than 0 and less than 100 %, not {ratio:.6g} "
            "(as a fraction)."
        )
    width, width_record = record_method(
        "trough_width",
        trough_width,
        kind="design judgment",
        expected=TroughWidth,
        how=HOW,
    )
    constants = [
        record(
            name,
            value,
            kind="constant or setting",
            unit=unit,
            plain_number="read as SI",
        )[1]
        for name, value, unit in (
            ("depth_tolerance", DEPTH_TOLERANCE, "m"),
            ("critical_distance_sampling", CRITICAL_DISTANCE_SAMPLING, "dimensionless"),
            ("critical_distance_tolerance", CRITICAL_DISTANCE_TOLERANCE, "m"),
        )
    ]
    area = math.pi * tunnel.diameter**2 / 4
    return TransverseTrough(
        tunnel=tunnel,
        volume_loss=ratio,
        trough_width=width,
        volume_factor=ratio * area / math.sqrt(2 * math.pi),
        depth_tolerance=DEPTH_TOLERANCE,
        inputs=(
            *tunnel.inputs,
            volume_record,
            width_record,
            *width.inputs,
            *constants,
        ),
        method=(
            MethodRecord(
                "Transverse Gaussian trough at depth",
                (*EQUATIONS, *width.equations),
                f"{SOURCES} Width ({width.name}): {width.source}",
            ),
        ),
        assumptions=(*ASSUMPTIONS, *width.assumptions, *tunnel.assumptions),
    )


@dataclass(frozen=True)
class TransverseTrough:
    """The transverse trough at depth over an idealized tunnel, as a source.

    Made by `transverse_trough`, which documents the equations.

    Attributes
    ----------
    tunnel : IdealizedTunnel
        The tunnel.
    volume_loss : float
        V_L, as a fraction.
    trough_width : TroughWidth
        The width method.
    volume_factor : float
        Q = V_L A / sqrt(2 pi), in m^2.
    depth_tolerance : float
        Depth in m within which a point counts as at the surface or the crown.
    inputs : tuple of InputRecord
        Every input as used, the tunnel's included.
    method : tuple of MethodRecord
        The method, its equations and its sources.
    assumptions : tuple of str
        What the method assumes and garisenda can't check.
    """

    tunnel: IdealizedTunnel
    volume_loss: float
    trough_width: TroughWidth
    volume_factor: float
    depth_tolerance: float
    inputs: tuple[InputRecord, ...]
    method: tuple[MethodRecord, ...]
    assumptions: tuple[str, ...]

    @property
    def crown_depth(self) -> float:
        """z_c = z0 - D/2, the crown's depth in m."""
        return self.tunnel.axis_depth - self.tunnel.diameter / 2

    def width_at(self, depth: float | FloatArray) -> float | FloatArray:
        """Return i in m at a depth, with depth capped at the crown."""
        capped = np.minimum(depth, self.crown_depth)
        width = self.trough_width.at(depth=capped, axis_depth=self.tunnel.axis_depth)
        return float(width) if np.ndim(width) == 0 else width

    def evaluate(self, *, x: object, y: object, depth: object) -> Movement:
        """Return the movement and its exact derivatives at points.

        With g = (n_x, n_y, 0) the gradient of the offset o and e_z that of
        the depth z, every derivative of the displacement is assembled from

        - d^(a+b) S / do^a dz^b = (Q c1^b / i^(1+a+b)) P_ab(r) exp(-r^2/2)
        - d^(a+b) u_n / do^a dz^b = (Q c1^(b+1) / i^(1+a+b)) R_ab(r) exp(-r^2/2)

        with r = o / i and polynomials P_ab and R_ab in r, derived here by
        differentiating S(o, z) and u_n(o, z) (not from a published source),
        up to a + b = 3: a component whose indices include b
        depth indices is the (a, b) derivative times g over its other
        indices, so the Hessian and third derivative are symmetric by
        construction. Every derivative with respect to station is zero.

        Parameters
        ----------
        x, y : length or array of lengths
            Plan coordinates, in m if plain numbers.
        depth : length or array of lengths
            Depth below the ground surface, positive downward, in m if plain
            numbers.

        Returns
        -------
        Movement
            Displacement (u_x, u_y, settlement) in m, its gradient, Hessian and
            third derivative, a verdict per point and the flags. A point deeper
            than the crown plus 1 mm, outside the bore, gets the trough at the
            crown, with every derivative with respect to depth exactly zero,
            and is flagged ``"outside"``.

        Raises
        ------
        ValueError
            If the arrays differ in length, a coordinate isn't finite (naming
            the points), a point is above the ground surface, or a point is
            inside the bore.
        """
        x_m, y_m, depth_m = read_points(
            x, y, depth, surface_tolerance=self.depth_tolerance
        )
        _, offset = self.tunnel.station_offset(x=x_m, y=y_m)
        o = np.asarray(offset, dtype=np.float64)
        check_outside_bore(self.tunnel, o, depth_m)
        return self._movement(o, depth_m)

    def critical_distances(
        self, *, start: object, end: object
    ) -> npt.NDArray[np.float64]:
        """Return where the trough's quantities peak or change sign on a segment.

        Found by root-finding on the exact derivatives along the segment
        (`find_critical_distances`), sampled at 1/8 of the feature length and
        refined to 1e-9 m. On a level segment the result is the analytic set
        at that depth's i: offsets 0, +-i and +-sqrt(3) i, and on a segment
        that isn't perpendicular to the tunnel also +-0.74196378 i and
        +-2.3344142 i (the zeros of r^4 - 6 r^2 + 3). On a segment that
        changes depth, i varies along it and there is no closed form, hence
        the root-finding for both.

        What this can miss, as for a superposition: two zeros of one function
        closer together than the sampling interval, which a lone trough never
        has. Where a segment crosses the crown, the depth derivatives drop to
        zero (the values below are the crown's), so a function can jump there;
        if it jumps across zero, the crossing is returned as a critical
        distance, though it isn't a zero.

        Parameters
        ----------
        start, end : array of three lengths
            The segment's ends as (x, y, depth), in m if plain numbers.

        Returns
        -------
        numpy.ndarray
            The distances from `start` in m, sorted, within [0, L].

        Raises
        ------
        ValueError
            If the segment is bad or vertical, or a sample can't be evaluated
            (inside the bore or above the surface), naming its distance along
            the segment.
        """
        return find_critical_distances(
            self,
            start=start,
            end=end,
            sampling=CRITICAL_DISTANCE_SAMPLING,
            tolerance=CRITICAL_DISTANCE_TOLERANCE,
        )

    def feature_length(self, *, start: object, end: object) -> float:
        """Return the least trough width i on a segment, in m.

        i decreases with depth, so it is i at the segment's deeper end, with
        depth capped at the crown.

        Raises
        ------
        ValueError
            If an end isn't three finite values, or the segment has zero length.
        """
        start_m, end_m, _ = read_segment(start, end)
        return float(self.width_at(max(float(start_m[2]), float(end_m[2]))))

    def _movement(self, o: FloatArray, depth: FloatArray) -> Movement:
        crown = self.crown_depth
        deep = depth > crown + self.depth_tolerance
        z = np.where(deep, crown, depth)
        width = self.trough_width
        i = np.asarray(
            width.at(depth=z, axis_depth=self.tunnel.axis_depth), dtype=np.float64
        )
        c1 = width.rate
        r = o / i
        gauss = self.volume_factor * np.exp(-(r**2) / 2)

        # (d S, d u_n) / do^a dz^b at each point, for every a + b <= 3.
        derivatives: dict[tuple[int, int], tuple[FloatArray, FloatArray]] = {}
        for (a, b), coefficients in SETTLEMENT_POLYNOMIALS.items():
            scale = gauss * c1**b / i ** (1 + a + b)
            settlement = scale * np.polynomial.polynomial.polyval(r, coefficients)
            normal = (
                scale
                * c1
                * np.polynomial.polynomial.polyval(r, HORIZONTAL_POLYNOMIALS[(a, b)])
            )
            if b > 0:
                settlement = np.where(deep, 0.0, settlement)
                normal = np.where(deep, 0.0, normal)
            derivatives[(a, b)] = (settlement, normal)

        n_x, n_y = self.tunnel.normal
        horizontal = np.array([n_x, n_y, 0.0])
        vertical = np.array([0.0, 0.0, 1.0])

        def tensor(order: int) -> FloatArray:
            """Return the derivatives of one order, shape (N, 3, 3, ...)."""
            components = list(itertools.product(range(3), repeat=order))
            count = len(o)
            flat = np.zeros((count, 3, len(components)))
            for column, component in enumerate(components):
                # g over the indices that aren't depth, in sorted order, so a
                # component and its permutations multiply identically.
                taken = sorted(component)
                b = taken.count(2)
                weight = 1.0
                for index in taken:
                    if index != 2:
                        weight *= horizontal[index]
                settlement, normal = derivatives[(order - b, b)]
                flat[:, :, column] = (
                    normal[:, None] * horizontal + settlement[:, None] * vertical
                ) * weight
            shaped: FloatArray = flat.reshape((count, 3, *((3,) * order)))
            return shaped

        deep_points = tuple(np.flatnonzero(deep).tolist())
        verdict = np.where(deep, "outside", "within")
        flags: tuple[Flag, ...] = ()
        if deep_points:
            linear = (
                "; applied to the linear method by garisenda"
                if width.name == LINEAR_NAME
                else ""
            )
            flags = (
                Flag(
                    "outside",
                    BELOW_CROWN.format(linear=linear),
                    f"depth at most z0 - D/2 = {crown:.6g} m (the crown)",
                    deep_points,
                ),
            )
        return Movement(tensor(0), tensor(1), tensor(2), tensor(3), verdict, flags)
