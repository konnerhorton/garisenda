"""The wall as a deep beam: its bending and diagonal strains (Eqs. 7-10)."""

import math
from dataclasses import dataclass
from typing import Literal

Mode = Literal["hogging", "sagging"]
"""Which way a zone of the wall bends: hogging (convex up) or sagging."""

MODES: tuple[Mode, ...] = ("hogging", "sagging")

POISSON_RATIO = 0.3
"""nu in Eq. 10, fixed by the method whatever E/G is (Mair, Taylor & Burland
1996, p. 717)."""

MAIR_TAYLOR_BURLAND = (
    "Mair, Taylor & Burland (1996), Prediction of ground movements and "
    "assessment of risk of building damage due to bored tunnelling"
)

BURLAND_WROTH_NAME = "Burland & Wroth (1974), shear coefficient 3/2"
TIMOSHENKO_NAME = "Timoshenko, shear coefficient 6/5"


@dataclass(frozen=True)
class BeamMethod:
    """How the wall's shear deflection is taken: the beam's shear coefficient.

    Made by `burland_wroth_beam` or `timoshenko_beam`, not directly. The wall
    is a simply supported beam of height H and unit width under a central
    point load P; its deflection at mid-span is the bending deflection
    P L^3 / (48 E I) plus the shear deflection alpha_s P L / (4 G H), with
    alpha_s the shear-deflection coefficient.

    Attributes
    ----------
    name : str
        The method's name, recorded as the ``beam_method`` input's value.
    shear_deflection_coefficient : float
        alpha_s, dimensionless.
    """

    name: str
    shear_deflection_coefficient: float


def burland_wroth_beam() -> BeamMethod:
    """Return the beam of Eqs. 7 and 8 as Mair, Taylor & Burland give them.

    The shear-deflection coefficient alpha_s = 3/2, which is what Eqs. 7 and 8
    imply: with it, `bending_strain` and `diagonal_strain` are

        Delta/L = (L / (12 t) + 3 I E / (2 t L H G)) eps_b       (Eq. 7)
        Delta/L = (1 + H L^2 G / (18 I E)) eps_d                  (Eq. 8)

    Source: Mair, Taylor & Burland (1996), Prediction of ground movements and
    assessment of risk of building damage due to bored tunnelling, Eqs. 7-8,
    p. 716, after Burland & Wroth (1974), which hasn't been read. That alpha_s
    = 3/2 is the coefficient the equations imply is garisenda's derivation.

    Returns
    -------
    BeamMethod
        Named ``"Burland & Wroth (1974), shear coefficient 3/2"``.
    """
    return BeamMethod(BURLAND_WROTH_NAME, 1.5)


def timoshenko_beam() -> BeamMethod:
    """Return the beam with Timoshenko's shear coefficient for a rectangle.

    The shear-deflection coefficient alpha_s = 6/5. With it, `bending_strain`
    and `diagonal_strain` are

        Delta/L = (L / (12 t) + 6 I E / (5 t L H G)) eps_b
        Delta/L = (4/5 + H L^2 G / (18 I E)) eps_d

    which give larger strains than Eqs. 7 and 8 at the same Delta/L. The
    derivation is garisenda's own; Jones (2022), Soft Ground Tunnel Design,
    Eqs. 13.12 and 13.23, pp. 476 and 479, write the same two equations, and
    are a check, not the source.

    Returns
    -------
    BeamMethod
        Named ``"Timoshenko, shear coefficient 6/5"``.
    """
    return BeamMethod(TIMOSHENKO_NAME, 1.2)


def section(mode: Mode, height: float) -> tuple[float, float]:
    """Return the wall's t and I, in m and m^3 per unit width.

    t is the depth of the neutral axis below the extreme tensile fiber and I
    the second moment of area of a wall of height H and unit width:

    - hogging: the neutral axis at the bottom, t = H and I = H^3 / 3;
    - sagging: the neutral axis at mid-height, t = H / 2 and I = H^3 / 12.

    Source: Mair, Taylor & Burland (1996), Prediction of ground movements and
    assessment of risk of building damage due to bored tunnelling, p. 716.

    Raises
    ------
    ValueError
        If `mode` isn't ``"hogging"`` or ``"sagging"``.
    """
    if mode == "hogging":
        return height, height**3 / 3
    if mode == "sagging":
        return height / 2, height**3 / 12
    raise ValueError(f"mode must be 'hogging' or 'sagging', not {mode!r}.")


def bending_strain(
    deflection_ratio: float,
    *,
    length: float,
    height: float,
    mode: Mode,
    youngs_to_shear_modulus_ratio: float,
    beam: BeamMethod,
) -> float:
    """Return the bending strain eps_b at a deflection ratio.

    The wall is a simply supported beam of span L and height H under a
    central point load P, so M = P L / 4 and eps_b = P L t / (4 E I). Its
    mid-span deflection is P L^3 / (48 E I) + alpha_s P L / (4 G H), so

        Delta/L = (L / (12 t) + alpha_s E I / (t L H G)) eps_b

    With alpha_s = 3/2 this is Mair, Taylor & Burland (1996)'s Eq. 7 (p. 716):
    Delta/L = (L / (12 t) + 3 I E / (2 t L H G)) eps_b. The derivation for any
    alpha_s is garisenda's own.

    Parameters
    ----------
    deflection_ratio : float
        Delta/L, dimensionless, as a magnitude.
    length : float
        L, the zone's length, in m. Positive.
    height : float
        H, the wall's height, in m. Positive.
    mode : {"hogging", "sagging"}
        Sets t and I (`section`).
    youngs_to_shear_modulus_ratio : float
        E/G, dimensionless. Positive.
    beam : BeamMethod
        alpha_s.

    Returns
    -------
    float
        eps_b, dimensionless.
    """
    t, inertia = section(mode, height)
    ratio = youngs_to_shear_modulus_ratio
    shear = beam.shear_deflection_coefficient * ratio * inertia / (t * length * height)
    return deflection_ratio / (length / (12 * t) + shear)


def diagonal_strain(
    deflection_ratio: float,
    *,
    length: float,
    height: float,
    mode: Mode,
    youngs_to_shear_modulus_ratio: float,
    beam: BeamMethod,
) -> float:
    """Return the diagonal strain eps_d at a deflection ratio.

    The beam of `bending_strain` carries a shear force P / 2, so its peak
    shear strain, at the neutral axis, is gamma = (3/2)(P / 2) / (G H), where
    3/2 is a rectangle's ratio of peak to mean shear stress. The largest
    principal strain of pure shear is eps_d = gamma / 2 = 3 P / (8 G H), so

        Delta/L = (2 alpha_s / 3 + H L^2 G / (18 I E)) eps_d

    With alpha_s = 3/2 this is Mair, Taylor & Burland (1996)'s Eq. 8 (p. 716):
    Delta/L = (1 + H L^2 G / (18 I E)) eps_d. The derivation for any alpha_s
    is garisenda's own; the 3/2 of the peak shear stress stays whatever
    alpha_s is.

    Parameters
    ----------
    deflection_ratio, length, height, mode, youngs_to_shear_modulus_ratio, beam
        As for `bending_strain`.

    Returns
    -------
    float
        eps_d, dimensionless.
    """
    _, inertia = section(mode, height)
    ratio = youngs_to_shear_modulus_ratio
    bending = height * length**2 / (18 * inertia * ratio)
    return deflection_ratio / (2 * beam.shear_deflection_coefficient / 3 + bending)


def total_bending_strain(bending: float, horizontal: float) -> float:
    """Return eps_bt = eps_h + eps_b (Eq. 9).

    The horizontal strain is uniform over the section, so it adds to the
    bending strain at the extreme fiber. Compressive eps_h (negative) is used
    with its sign.

    Source: Mair, Taylor & Burland (1996), Prediction of ground movements and
    assessment of risk of building damage due to bored tunnelling, Eq. 9,
    p. 716.
    """
    return horizontal + bending


def total_diagonal_strain(
    diagonal: float, horizontal: float, poisson_ratio: float = POISSON_RATIO
) -> float:
    """Return the largest principal strain eps_dt from eps_d and eps_h (Eq. 10).

    The wall is free to strain vertically, so a horizontal strain eps_h comes
    with -nu eps_h vertically, and the shear adds a half shear strain eps_d.
    By Mohr's circle,

        eps_dt = eps_h (1 - nu) / 2 + sqrt((eps_h (1 + nu) / 2)^2 + eps_d^2)

    With nu = 0.3 this is Mair, Taylor & Burland (1996)'s Eq. 10 (p. 717):
    eps_dt = 0.35 eps_h + sqrt((0.65 eps_h)^2 + eps_d^2), stated there for
    nu = 0.3 whatever E/G is. The general form is garisenda's own derivation.
    eps_dt is never negative.

    Parameters
    ----------
    diagonal : float
        eps_d, dimensionless.
    horizontal : float
        eps_h, dimensionless, tension positive; compression is used with its
        sign.
    poisson_ratio : float, optional
        nu. The method fixes it at 0.3; it is a parameter only so the general
        form can be checked.
    """
    nu = poisson_ratio
    return horizontal * (1 - nu) / 2 + math.hypot(horizontal * (1 + nu) / 2, diagonal)
