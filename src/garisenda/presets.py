"""Named, cited presets of published limits and parameters.

A preset is a choice someone made: garisenda never applies one unless it is
passed by name. Each value is a `Preset`, a `Sourced` whose source names the
preset call, the row, the paper and its table or page, and whom the paper
quotes; its caveats join the result's assumptions. Every row is a required
keyword argument, so the preset's row is a judgment too.

There is no pipe length preset: no citable source for nominal laying lengths
has been found.
"""

import math
from dataclasses import dataclass
from typing import Any

import pint

from garisenda._inputs import Preset, judgments
from garisenda._units import units
from garisenda.buildings._categories import Band, DamageCategories

__all__ = [
    "JointLimits",
    "PreliminaryLimits",
    "Preset",
    "StrainLimits",
    "cast_iron_joint_limits",
    "damage_categories",
    "grey_iron_tensile_strain_limit",
    "iron_strain_limits",
    "preliminary_assessment_limits",
    "youngs_to_shear_modulus_ratio",
]

BRACEGIRDLE = "Bracegirdle et al. (1996)"

TABLE_2_CAVEAT = (
    "Table 2 is Attewell et al. (1986)'s guidance for cast iron mains, as "
    "quoted by Bracegirdle et al. (1996, p. 661); Attewell et al. hasn't been "
    "read."
)

PULLOUT_CAVEAT = (
    "Bracegirdle et al. (1996, p. 661) give individual joints as the primary "
    "method and, 'again conservatively', the maximum horizontal ground movement "
    "as the pull-out. garisenda's opening is computed at individual joints and "
    "is smaller than that shortcut (for one trough, at most the maximum "
    "horizontal movement, and about a third of it for 4 m pipes 2 m deep "
    "over one tunnel with axis depth 20 m, diameter 6 m, volume loss 1 % and "
    "a linear width with k = 0.5, so i = 9 m). Whether Table 2's pull-out "
    "limits, from Attewell et al. (1986), were calibrated with the shortcut "
    "can't be checked: Attewell et al. "
    "hasn't been read, and Bracegirdle et al.'s horizontal movement (Eq. 3) "
    "can't be read with certainty."
)

NONE_CAVEAT = (
    "Table 2 gives 'none' for a lead-yarn joint in a gas main with a history of "
    "leaks; it is read as a limit of zero, so any rotation or opening fails."
)

TABLE_4_CAVEAT = (
    "Table 4 gives the allowable increase in strain for otherwise sound pipes "
    "(Bracegirdle et al. 1996, p. 662), recommended for application to the "
    "paper's simple methodology, which reduces axial strain by a factor that "
    "garisenda's greenfield check doesn't apply."
)

HERBERT_LEACH_CAVEAT = (
    "Herbert and Leach (1990)'s values, as quoted by Bracegirdle et al. (1996, "
    "p. 662), are tensile strain limits only; Herbert and Leach (1990) hasn't "
    "been read."
)

# Table 2 (p. 661): row, its description, rotation in degrees, pullout in mm.
JOINTS: dict[str, tuple[str, float, float]] = {
    "lead_yarn_gas_main_with_history_of_leaks": (
        "lead-yarn joint in gas main with history of leaks",
        0.0,
        0.0,
    ),
    "lead_yarn_sound_gas_main": ("lead-yarn joint in sound gas main", 1.0, 10.0),
    "lead_yarn_water_main": ("lead-yarn joint in water mains", 1.5, 15.0),
    "rubber_gasket": ("rubber gasket joint in gas or water mains", 2.5, 25.0),
}

# Table 4 (p. 662): row, its description, tensile and compressive in µε.
MATERIALS: dict[str, tuple[str, float, float]] = {
    "grey_iron": ("pit cast and spun cast grey iron", 100.0, 1200.0),
    "ductile_iron": ("ductile iron", 500.0, 700.0),
}

# Herbert and Leach (1990), as quoted on p. 662, in µε.
DIAMETERS: dict[str, str] = {
    "over_300_mm": "pipes in grey iron exceeding 300mm in diameter",
    "300_mm_or_less": "smaller pipes",
}
SITUATIONS = ("general", "particularly_adverse")
GREY_IRON_TENSILE: dict[tuple[str, str], float] = {
    ("over_300_mm", "general"): 200.0,
    ("300_mm_or_less", "general"): 150.0,
    ("over_300_mm", "particularly_adverse"): 150.0,
    ("300_mm_or_less", "particularly_adverse"): 100.0,
}


@dataclass(frozen=True)
class JointLimits:
    """A joint's allowable rotation and pullout, from `cast_iron_joint_limits`.

    Attributes
    ----------
    rotation : Preset
        The allowable joint rotation, an angle in degrees.
    pullout : Preset
        The allowable joint pullout, a length in mm.
    """

    rotation: Preset
    pullout: Preset


@dataclass(frozen=True)
class StrainLimits:
    """A material's allowable tensile and compressive strain.

    From `iron_strain_limits`.

    Attributes
    ----------
    tensile, compressive : Preset
        The allowable increase in strain, as positive magnitudes in µε.
    """

    tensile: Preset
    compressive: Preset


def _row[T](name: str, value: str, rows: dict[str, T] | tuple[str, ...]) -> None:
    """Raise `ValueError` if `value` isn't one of `rows`, listing them."""
    if value not in rows:
        listed = ", ".join(repr(row) for row in rows)
        raise ValueError(f"{name} must be one of {listed}, not {value!r}.")


def _quantity(magnitude: float, unit: str) -> Any:
    quantity: pint.Quantity = units.Quantity(magnitude, unit)
    return quantity


@judgments(
    joint="it depends on the joint and the main's service and condition. Pass "
    "one of " + ", ".join(repr(row) for row in JOINTS) + "."
)
def cast_iron_joint_limits(*, joint: str) -> JointLimits:
    """Return the allowable joint rotation and pullout for cast iron mains (Table 2).

    Bracegirdle et al. (1996), Table 2, p. 661, "Allowable joint rotation and
    pull-out", after Attewell et al. (1986), whose guidance is for cast iron
    mains subjected to ground movements:

    | `joint` | rotation | pullout |
    |---|---|---|
    | `"lead_yarn_gas_main_with_history_of_leaks"` | 0 deg | 0 mm |
    | `"lead_yarn_sound_gas_main"` | 1.0 deg | 10 mm |
    | `"lead_yarn_water_main"` | 1.5 deg | 15 mm |
    | `"rubber_gasket"` | 2.5 deg | 25 mm |

    These are Table 2's rows in order: "lead-yarn joint in gas main with
    history of leaks" (given as "none"), "lead-yarn joint in sound gas main",
    "lead-yarn joint in water mains" and "rubber gasket joint in gas or water
    mains".

    The rows are by joint and service, not by diameter. Pass the values as
    ``joint_rotation_limit`` and ``joint_pullout_limit`` to
    `garisenda.check_jointed_pipe`.

    Caveats, added to the result's assumptions:

    - Table 2 is Attewell et al. (1986)'s guidance, as quoted by Bracegirdle
      et al.; Attewell et al. hasn't been read.
    - The pullout: Bracegirdle et al. (1996,
      p. 661) give individual joints as the primary method and, "again
      conservatively", the maximum horizontal ground movement as the
      pull-out. garisenda's opening is computed at individual joints and is
      smaller than that shortcut (for one trough, at most the maximum
      horizontal movement, and about a third of it for 4 m pipes 2 m
      deep over one tunnel with axis depth 20 m, diameter 6 m, volume loss
      1 % and a linear width with k = 0.5, so i = 9 m). Whether Table 2's
      pull-out limits were calibrated with the shortcut can't be checked.
    - The first row's "none" is read as zero: any rotation or opening fails.

    Parameters
    ----------
    joint : str
        The row of Table 2. A required judgment with no default.

    Returns
    -------
    JointLimits
        ``.rotation`` (degree) and ``.pullout`` (mm), each a `Preset`.

    Raises
    ------
    TypeError
        If `joint` is missing.
    ValueError
        If `joint` isn't a row of the table, listing the rows.

    Examples
    --------
    >>> import garisenda as gs
    >>> limits = gs.presets.cast_iron_joint_limits(joint="lead_yarn_water_main")
    >>> limits.rotation.value, limits.pullout.value
    (Quantity(1.5, "degree"), Quantity(15.0, "millimeter"))
    """
    _row("joint", joint, JOINTS)
    description, rotation, pullout = JOINTS[joint]
    source = (
        f"gs.presets.cast_iron_joint_limits(joint={joint!r}): {BRACEGIRDLE}, "
        f"Table 2, p. 661, after Attewell et al. (1986), {description!r}"
    )
    extra = (NONE_CAVEAT,) if rotation == 0 else ()
    return JointLimits(
        rotation=Preset(
            _quantity(rotation, "degree"), source, (TABLE_2_CAVEAT, *extra)
        ),
        pullout=Preset(
            _quantity(pullout, "mm"),
            source,
            (TABLE_2_CAVEAT, PULLOUT_CAVEAT, *extra),
        ),
    )


@judgments(
    material="it depends on the pipe's material. Pass one of "
    + ", ".join(repr(row) for row in MATERIALS)
    + "."
)
def iron_strain_limits(*, material: str) -> StrainLimits:
    """Return the allowable increase in strain for iron pipes (Table 4).

    Bracegirdle et al. (1996), Table 4, p. 662, "Recommended allowable
    increase in strain":

    | `material` | Table 4 | tensile | compressive |
    |---|---|---|---|
    | `"grey_iron"` | pit cast and spun cast grey iron | 100 µε | 1200 µε |
    | `"ductile_iron"` | ductile iron | 500 µε | 700 µε |

    Pass the values as ``tensile_strain_limit`` and
    ``compressive_strain_limit``. Table 4 gives no bending limit, and none is
    invented: pass ``bending_strain_limit=None``, or the tensile limit (the
    tensile strain is at least the bending strain, so the bending check then
    adds nothing).

    Caveat, added to the result's assumptions: these are the allowable
    increase in strain for otherwise sound pipes (p. 662), recommended for
    application to the paper's simple methodology, which reduces axial
    strain by a factor that garisenda's greenfield check doesn't apply.

    Parameters
    ----------
    material : str
        The row of Table 4. A required judgment with no default.

    Returns
    -------
    StrainLimits
        ``.tensile`` and ``.compressive`` (µε), each a `Preset`.

    Raises
    ------
    TypeError
        If `material` is missing.
    ValueError
        If `material` isn't a row of the table, listing the rows.
    """
    _row("material", material, MATERIALS)
    description, tensile, compressive = MATERIALS[material]
    source = (
        f"gs.presets.iron_strain_limits(material={material!r}): {BRACEGIRDLE}, "
        f"Table 4, p. 662, {description!r}"
    )
    caveats = (TABLE_4_CAVEAT,)
    return StrainLimits(
        tensile=Preset(_quantity(tensile, "µε"), source, caveats),
        compressive=Preset(_quantity(compressive, "µε"), source, caveats),
    )


@judgments(
    diameter='it depends on the pipe\'s diameter. Pass "over_300_mm" or '
    '"300_mm_or_less"; whether 300 mm is nominal or outside is your call.',
    situation='it depends on how adverse the situation is. Pass "general" or '
    '"particularly_adverse".',
)
def grey_iron_tensile_strain_limit(*, diameter: str, situation: str) -> Preset:
    """Return the allowable tensile strain for grey iron (Herbert and Leach 1990).

    Bracegirdle et al. (1996), p. 662, after Herbert and Leach (1990): "it is
    reasonable to allow up to 200µε for pipes in grey iron exceeding 300mm in
    diameter and 150µε for smaller pipes; values of 150 and 100µε
    respectively being applied in particularly adverse situations."

    | `diameter` | `"general"` | `"particularly_adverse"` |
    |---|---|---|
    | `"over_300_mm"` | 200 µε | 150 µε |
    | `"300_mm_or_less"` | 150 µε | 100 µε |

    The caller picks the row, so garisenda doesn't decide whether "300mm in
    diameter" is nominal or outside. Pass the value as
    ``tensile_strain_limit``.

    Caveat, added to the result's assumptions: these are tensile limits only,
    and Herbert and Leach (1990) hasn't been read.

    Parameters
    ----------
    diameter : {"over_300_mm", "300_mm_or_less"}
        The diameter row. A required judgment with no default.
    situation : {"general", "particularly_adverse"}
        The situation. A required judgment with no default.

    Returns
    -------
    Preset
        The tensile strain limit (µε).

    Raises
    ------
    TypeError
        If `diameter` or `situation` is missing.
    ValueError
        If either isn't one of its rows, listing them.
    """
    _row("diameter", diameter, DIAMETERS)
    _row("situation", situation, SITUATIONS)
    source = (
        f"gs.presets.grey_iron_tensile_strain_limit(diameter={diameter!r}, "
        f"situation={situation!r}): {BRACEGIRDLE}, p. 662, after Herbert and "
        f"Leach (1990), {DIAMETERS[diameter]!r}"
    )
    return Preset(
        _quantity(GREY_IRON_TENSILE[(diameter, situation)], "µε"),
        source,
        (HERBERT_LEACH_CAVEAT,),
    )


MAIR_TAYLOR_BURLAND = "Mair, Taylor & Burland (1996)"

BURLAND_WROTH_CAVEAT = (
    "Burland & Wroth (1974), whom Mair, Taylor & Burland (1996, p. 717) cite "
    "for E/G, hasn't been read."
)

FRAMED_CAVEAT = (
    "Mair, Taylor & Burland (1996, p. 717) give E/G = 12.5 for reinforced "
    "concrete framed buildings on shallow foundations, used in Eqs. 7 and 8; "
    "Eq. 10 still takes Poisson's ratio as 0.3, which E/G = 12.5 doesn't imply "
    "for an isotropic material."
)

TABLE_2_DAMAGE_CAVEAT = (
    "Table 2 of Mair, Taylor & Burland (1996, p. 715) is after Boscardin & "
    "Cording (1989), which hasn't been read. Boscardin & Cording describe "
    "0.15-0.3 % as 'Moderate to Severe'; Mair, Taylor & Burland note that none "
    "of their cases showed severe damage in that range. Table 1's note on "
    "slopes (1/100 clearly visible, 1/150 undesirable) isn't checked."
)

PRELIMINARY_CAVEAT = (
    "Mair, Taylor & Burland (1996, p. 717) set 10 mm and 1/500 against "
    "contours of ground surface settlement; Jones (2022, Soft Ground Tunnel "
    "Design, p. 469) attributes the stage to Rankin (1988), which hasn't been "
    "read. garisenda checks them at the wall's foundation level, where a trough "
    "below the surface is narrower and deeper, so they are more onerous there "
    "than at the surface; a foundation depth of 0 gives the published check. "
    "The slope check 'is rarely critical' (p. 717)."
)

# p. 716 (masonry, "often taken as 2.6") and §4.5, p. 717 (framed).
STRUCTURES: dict[str, tuple[float, str]] = {
    "masonry": (2.6, "p. 716, 'often taken as 2.6' for masonry"),
    "framed": (
        12.5,
        "§4.5, p. 717, reinforced concrete framed buildings on shallow "
        "foundations, after Burland & Wroth (1974)",
    ),
}

# Table 2 (p. 715): number, label, normal degree of severity, upper limit in %.
DAMAGE_BANDS: tuple[tuple[int, str, str, float], ...] = (
    (0, "0", "negligible", 0.05),
    (1, "1", "very slight", 0.075),
    (2, "2", "slight", 0.15),
    (3, "3", "moderate", 0.3),
    (4, "4 to 5", "severe to very severe", math.inf),
)


@dataclass(frozen=True)
class PreliminaryLimits:
    """The preliminary assessment's limits, from `preliminary_assessment_limits`.

    Attributes
    ----------
    settlement : Preset
        The settlement below which a building's risk is negligible, a length
        in mm.
    slope : Preset
        The slope no such building may exceed, in mm/m.
    """

    settlement: Preset
    slope: Preset


@judgments(
    structure="it depends on how the building is built. Pass one of "
    + ", ".join(repr(row) for row in STRUCTURES)
    + "."
)
def youngs_to_shear_modulus_ratio(*, structure: str) -> Preset:
    """Return E/G for a building's wall as Mair, Taylor & Burland give it.

    Mair, Taylor & Burland (1996), Prediction of ground movements and
    assessment of risk of building damage due to bored tunnelling:

    | `structure` | E/G | where |
    |---|---|---|
    | `"masonry"` | 2.6 | p. 716 |
    | `"framed"` | 12.5 | §4.5, p. 717, after Burland & Wroth (1974) |

    On p. 716: "Although masonry is not an isotropic material, the ratio E/G
    is often taken as 2.6, which is consistent with an isotropic Poisson's
    ratio of 0.3." On p. 717, for reinforced concrete framed buildings on
    shallow foundations: "It is more appropriate to adopt an E/G ratio of
    12.5, rather than 2.6 used for masonry buildings (Burland and Wroth,
    1974)".

    Pass the value as ``youngs_to_shear_modulus_ratio`` to
    `garisenda.check_building`.

    Caveats, added to the result's assumptions:

    - Burland & Wroth (1974) hasn't been read.
    - For `"framed"`, Eq. 10 still takes Poisson's ratio as 0.3.

    Parameters
    ----------
    structure : {"masonry", "framed"}
        The row. A required judgment with no default.

    Returns
    -------
    Preset
        E/G, dimensionless.

    Raises
    ------
    TypeError
        If `structure` is missing.
    ValueError
        If `structure` isn't a row, listing the rows.
    """
    _row("structure", structure, STRUCTURES)
    ratio, where = STRUCTURES[structure]
    source = (
        f"gs.presets.youngs_to_shear_modulus_ratio(structure={structure!r}): "
        f"{MAIR_TAYLOR_BURLAND}, {where}"
    )
    caveats: tuple[str, ...] = (BURLAND_WROTH_CAVEAT,)
    if structure == "framed":
        caveats += (FRAMED_CAVEAT,)
    return Preset(_quantity(ratio, "dimensionless"), source, caveats)


def damage_categories() -> Preset:
    """Return the damage categories by limiting tensile strain (Table 2).

    Mair, Taylor & Burland (1996), Prediction of ground movements and
    assessment of risk of building damage due to bored tunnelling, Table 2,
    p. 715, "Relationship between category of damage and limiting tensile
    strain", after Boscardin & Cording (1989):

    | number | label | normal degree of severity | limiting tensile strain |
    |---|---|---|---|
    | 0 | `"0"` | negligible | 0-0.05 % |
    | 1 | `"1"` | very slight | 0.05-0.075 % |
    | 2 | `"2"` | slight | 0.075-0.15 % |
    | 3 | `"3"` | moderate | 0.15-0.3 % |
    | 4 | `"4 to 5"` | severe to very severe | > 0.3 % |

    The table's ranges share their ends; a strain exactly on a boundary falls
    in the lower category. Categories 4 and 5 are one band, as Table 2 gives
    them. Pass the value as ``category_limits`` to
    `garisenda.check_building`.

    Caveat, added to the result's assumptions: Boscardin & Cording (1989)
    hasn't been read; they describe 0.15-0.3 % as "Moderate to Severe", and
    Mair, Taylor & Burland note none of their cases showed severe damage in
    that range. Table 1's note on slopes isn't checked.

    Returns
    -------
    Preset
        A `garisenda.buildings.DamageCategories` named
        ``"Mair, Taylor & Burland (1996), Table 2"``.
    """
    categories = DamageCategories(
        name=f"{MAIR_TAYLOR_BURLAND}, Table 2",
        bands=[
            Band(number, label, severity, limit / 100)
            for number, label, severity, limit in DAMAGE_BANDS
        ],
    )
    source = (
        f"gs.presets.damage_categories(): {MAIR_TAYLOR_BURLAND}, Table 2, p. 715, "
        "after Boscardin & Cording (1989)"
    )
    return Preset(categories, source, (TABLE_2_DAMAGE_CAVEAT,))


def preliminary_assessment_limits() -> PreliminaryLimits:
    """Return the preliminary assessment's settlement and slope limits.

    Mair, Taylor & Burland (1996), Prediction of ground movements and
    assessment of risk of building damage due to bored tunnelling, §5.2,
    p. 717: "a building has a negligible risk of damage when subjected to
    settlements of less than 10mm", with "an additional check ... that no
    eliminated building experiences a slope exceeding 1/500".

    The slope is given as 2 mm/m, which is 1/500, because a slope must be
    a quantity. Pass them as ``settlement_limit`` and ``slope_limit`` to
    `garisenda.check_building`.

    Caveat, added to the result's assumptions: they are set against the
    ground surface, and Jones (2022, p. 469) attributes them to Rankin (1988),
    which hasn't been read; garisenda checks them at the wall's foundation
    level, which is more onerous for a foundation below the surface.

    Returns
    -------
    PreliminaryLimits
        ``.settlement`` (10 mm) and ``.slope`` (2 mm/m), each a `Preset`.
    """
    source = (
        f"gs.presets.preliminary_assessment_limits(): {MAIR_TAYLOR_BURLAND}, "
        "§5.2, p. 717"
    )
    caveats = (PRELIMINARY_CAVEAT,)
    return PreliminaryLimits(
        settlement=Preset(_quantity(10, "mm"), source, caveats),
        slope=Preset(_quantity(2, "mm/m"), source, caveats),
    )
