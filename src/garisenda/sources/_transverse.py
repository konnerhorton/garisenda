"""The steady-state transverse Gaussian trough at the ground surface."""

import math
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from garisenda._inputs import InputRecord, judgments, record
from garisenda.sources._movement import Flag, MethodRecord, Movement
from garisenda.sources._segment import (
    check_outside_bore,
    directions,
    read_points,
    read_segment,
)
from garisenda.sources._tunnel import IdealizedTunnel

SURFACE_TOLERANCE = 1e-3
"""Depth in m within which a point counts as at the ground surface."""

SOURCES = (
    "🔬 Peck (1969), the Gaussian form; O'Reilly & New (1982), the trough width, "
    "the volume relation and horizontal movement toward the axis. Not verified "
    "against the sources (TODO #2)."
)

EQUATIONS = (
    "i = k z0",
    "A = pi D^2 / 4",
    "S_max = V_L A / (sqrt(2 pi) i)",
    "S(o) = S_max exp(-o^2 / (2 i^2))",
    "u_n(o) = -(o / z0) S(o)",
)

ASSUMPTIONS = (
    "Steady state: the face has long passed.",
    "Transverse trough only: the longitudinal trough is not considered (SPEC §1.3).",
    "The settlement trough is Gaussian.",
    "Ground moves toward the tunnel axis, which sets horizontal movement.",
    "The surface trough is applied at each point's plan position, whatever its "
    "depth; points below the surface are flagged.",
    "No validity range is checked for k, volume loss or cover yet: the sources "
    "are unverified (TODO #2).",
)

BELOW_SURFACE = (
    "Surface trough applied below the ground surface: the trough at depth is "
    "narrower, so settlement and curvature there are underestimated. For the "
    "trough at depth, use gs.sources.transverse_trough."
)

FloatArray = npt.NDArray[np.float64]


@judgments(
    volume_loss="it depends on the tunneling method, the ground and the "
    "workmanship. Pass it as a pint quantity, e.g. "
    "volume_loss=0.5 * gs.units.percent.",
    trough_width_parameter="k sets the trough width i = k z0 and depends on the "
    "ground. Pass it as a number, e.g. trough_width_parameter=0.5.",
)
def transverse_surface_trough(
    tunnel: IdealizedTunnel, *, volume_loss: object, trough_width_parameter: object
) -> "TransverseSurfaceTrough":
    """Return the steady-state transverse Gaussian trough at the ground surface.

    This is the movement at the ground surface (z = 0) only. For a buried
    utility, use `gs.sources.transverse_trough`, which gives the trough at its
    depth, and at z = 0 gives this same trough with
    `gs.sources.linear_trough_width` and the same k.

    With o the offset of a point from the tunnel axis in plan, z0 the axis depth
    and D the diameter:

    - trough width: i = k z0
    - tunnel area: A = pi D^2 / 4
    - maximum settlement: S_max = V_L A / (sqrt(2 pi) i), from the trough
      volume sqrt(2 pi) i S_max = V_L A
    - settlement: S(o) = S_max exp(-o^2 / (2 i^2))
    - horizontal movement toward the axis: h(o) = (o / z0) S(o), so the
      displacement along the right-hand normal n is u_n = -(o / z0) S

    Parameters
    ----------
    tunnel : IdealizedTunnel
        The tunnel.
    volume_loss : pint quantity
        V_L, the trough volume per unit length as a fraction of the tunnel's
        area. A design judgment with no default; a plain number is refused,
        because 0.5 could be 0.5 % or 50 %. Must be more than 0 and less than
        100 %.
    trough_width_parameter : float
        k, dimensionless. A design judgment with no default. Must be positive.

    Returns
    -------
    TransverseSurfaceTrough
        The source; call its `evaluate` for the movement at points.

    Raises
    ------
    TypeError
        If a judgment is missing, or `volume_loss` is a plain number.
    ValueError
        If a value is outside its physical range.

    Notes
    -----
    Validity: points at the ground surface (depth within 1 mm) are ``"within"``;
    points below it are ``"outside"``, because the trough at depth is narrower.
    No range is checked for k, volume loss or cover yet, because the sources are
    unverified (TODO #2); the assumptions say so.

    Source: 🔬 Peck (1969) for the Gaussian form; O'Reilly & New (1982) for the
    trough width, the volume relation and horizontal movement. Not verified
    against the sources (TODO #2).
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
    _, tolerance_record = record(
        "surface_tolerance",
        SURFACE_TOLERANCE,
        kind="constant or setting",
        unit="m",
        plain_number="read as SI",
    )
    width = k * tunnel.axis_depth
    area = math.pi * tunnel.diameter**2 / 4
    return TransverseSurfaceTrough(
        tunnel=tunnel,
        volume_loss=ratio,
        trough_width_parameter=k,
        trough_width=width,
        maximum_settlement=ratio * area / (math.sqrt(2 * math.pi) * width),
        surface_tolerance=SURFACE_TOLERANCE,
        inputs=(*tunnel.inputs, volume_record, k_record, tolerance_record),
        method=(
            MethodRecord("Transverse Gaussian surface trough", EQUATIONS, SOURCES),
        ),
        assumptions=(*ASSUMPTIONS, *tunnel.assumptions),
    )


@dataclass(frozen=True)
class TransverseSurfaceTrough:
    """The transverse surface trough over an idealized tunnel, as a source.

    Made by `transverse_surface_trough`, which documents the equations.

    Attributes
    ----------
    tunnel : IdealizedTunnel
        The tunnel.
    volume_loss : float
        V_L, as a fraction.
    trough_width_parameter : float
        k.
    trough_width : float
        i, in m.
    maximum_settlement : float
        S_max, in m.
    surface_tolerance : float
        Depth in m within which a point counts as at the surface.
    inputs : tuple of InputRecord
        Every input as used, the tunnel's included.
    method : tuple of MethodRecord
        The method, its equations and its source.
    assumptions : tuple of str
        What the method assumes and garisenda can't check.
    """

    tunnel: IdealizedTunnel
    volume_loss: float
    trough_width_parameter: float
    trough_width: float
    maximum_settlement: float
    surface_tolerance: float
    inputs: tuple[InputRecord, ...]
    method: tuple[MethodRecord, ...]
    assumptions: tuple[str, ...]

    def evaluate(self, *, x: object, y: object, depth: object) -> Movement:
        """Return the movement and its exact derivatives at points.

        With g = (n_x, n_y, 0) the gradient of the offset o, the derivatives
        are exact: du/dx_j = (du/do) g_j, d2u/dx_j dx_k = (d2u/do2) g_j g_k and
        d3u/dx_j dx_k dx_l = (d3u/do3) g_j g_k g_l, where, with r = o / i,

        - dS/do = -(o / i^2) S
        - d2S/do2 = (r^2 - 1) S / i^2
        - d3S/do3 = (o / i^4) S (3 - r^2)
        - du_n/do = -(S / z0)(1 - r^2)
        - d2u_n/do2 = -(S / z0)(o / i^2)(r^2 - 3)
        - d3u_n/do3 = (S / (z0 i^2))(r^4 - 6 r^2 + 3)

        Every derivative with respect to depth is exactly zero, and with respect
        to station zero to rounding.

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
            than 1 mm gets the surface values at its plan position and is
            flagged ``"outside"``.

        Raises
        ------
        ValueError
            If the arrays differ in length, a coordinate isn't finite (naming
            the points), a point is above the ground surface, or a point is
            inside the bore.
        """
        x_m, y_m, depth_m = read_points(
            x, y, depth, surface_tolerance=self.surface_tolerance
        )
        _, offset = self.tunnel.station_offset(x=x_m, y=y_m)
        o = np.asarray(offset, dtype=np.float64)
        check_outside_bore(self.tunnel, o, depth_m)
        return self._movement(o, depth_m)

    def critical_distances(
        self, *, start: object, end: object
    ) -> npt.NDArray[np.float64]:
        """Return where the trough's quantities peak or change sign on a segment.

        These are where the segment's offset crosses 0 (the axis: peak
        settlement, sagging curvature and compressive strain), +-i (the
        inflection points: peak slope and horizontal movement, zero curvature
        and strain) and +-sqrt(3) i (peak hogging curvature and tensile strain).
        On a segment that isn't perpendicular to the tunnel (|n.l| > 1e-10,
        with l its lateral direction), the lateral displacement u_n (n.l)
        isn't zero, and its curvature peaks where d3u_n/do3 = 0: at
        r^4 - 6 r^2 + 3 = 0 with r = o / i, so o = +-sqrt(3 - sqrt(6)) i and
        +-sqrt(3 + sqrt(6)) i (about 0.742 i and 2.334 i). Offset is linear in
        distance along a straight segment, so each crossing is exact:
        s = L (c - o_start) / (o_end - o_start) for each offset c.

        Parameters
        ----------
        start, end : array of three lengths
            The segment's ends as (x, y, depth), in m if plain numbers.

        Returns
        -------
        numpy.ndarray
            The distances from `start` in m, sorted, within [0, L]. A segment at
            constant offset (parallel to the tunnel) has none.

        Raises
        ------
        ValueError
            If an end isn't three finite values, or the segment has zero length.
        """
        start_m, end_m, length = read_segment(start, end)
        _, offsets = self.tunnel.station_offset(
            x=np.array([start_m[0], end_m[0]]), y=np.array([start_m[1], end_m[1]])
        )
        o_start, o_end = (float(value) for value in np.atleast_1d(offsets))
        change = o_end - o_start
        if abs(change) <= 1e-12 * length:
            return np.empty(0)
        i = self.trough_width
        roots = [0.0, 1.0, math.sqrt(3)]
        _, _, lateral = directions(start_m, end_m)
        n_x, n_y = self.tunnel.normal
        if abs(n_x * lateral[0] + n_y * lateral[1]) > 1e-10:
            roots += [math.sqrt(3 - math.sqrt(6)), math.sqrt(3 + math.sqrt(6))]
        targets = np.array(sorted({sign * root for root in roots for sign in (-1, 1)}))
        targets *= i
        distances = length * (targets - o_start) / change
        inside = (distances >= 0) & (distances <= length)
        return np.sort(distances[inside])

    def feature_length(self, *, start: object, end: object) -> float:
        """Return the trough width i, in m, whatever the segment.

        The trough changes over a length of order i everywhere: its peaks and
        zeros are at 0, +-i and +-sqrt(3) i in offset.
        """
        return self.trough_width

    def _movement(self, o: FloatArray, depth: FloatArray) -> Movement:
        i, z0 = self.trough_width, self.tunnel.axis_depth
        ratio = o**2 / i**2
        settlement = self.maximum_settlement * np.exp(-ratio / 2)
        normal = -(o / z0) * settlement
        first = (-(o / i**2) * settlement, -(settlement / z0) * (1 - ratio))
        second = (
            (ratio - 1) * settlement / i**2,
            -(settlement / z0) * (o / i**2) * (ratio - 3),
        )
        third = (
            (o / i**4) * settlement * (3 - ratio),
            settlement / (z0 * i**2) * (ratio**2 - 6 * ratio + 3),
        )

        n_x, n_y = self.tunnel.normal
        horizontal = np.array([n_x, n_y, 0.0])
        vertical = np.array([0.0, 0.0, 1.0])
        g = horizontal  # the gradient of the offset o

        def components(
            normal_part: FloatArray, settlement_part: FloatArray
        ) -> FloatArray:
            combined: FloatArray = (
                normal_part[:, None] * horizontal + settlement_part[:, None] * vertical
            )
            return combined

        displacement = components(normal, settlement)
        gradient = components(first[1], first[0])[:, :, None] * g
        hessian = components(second[1], second[0])[:, :, None, None] * np.outer(g, g)
        # g_j g_k g_l, multiplied in sorted index order so it is exactly symmetric.
        index = np.sort(np.indices((3, 3, 3)).reshape(3, -1), axis=0)
        g3 = (g[index[0]] * g[index[1]] * g[index[2]]).reshape(3, 3, 3)
        third_derivative = components(third[1], third[0])[:, :, None, None, None] * g3

        deep = depth > self.surface_tolerance
        verdict = np.where(deep, "outside", "within")
        flags: tuple[Flag, ...] = ()
        if deep.any():
            flags = (
                Flag(
                    "outside",
                    BELOW_SURFACE,
                    f"depth at most {self.surface_tolerance * 1000:g} mm "
                    "(the ground surface)",
                    tuple(np.flatnonzero(deep).tolist()),
                ),
            )
        return Movement(
            displacement, gradient, hessian, third_derivative, verdict, flags
        )
