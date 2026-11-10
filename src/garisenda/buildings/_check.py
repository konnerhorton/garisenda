"""The damage check for a building's wall: the staged method."""

import itertools
import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd

from garisenda._inputs import (
    InputRecord,
    Sourced,
    judgments,
    preset_caveats,
    record,
    record_method,
)
from garisenda._result import Result, checks_frame, zones_frame
from garisenda.buildings._beam import (
    MAIR_TAYLOR_BURLAND,
    POISSON_RATIO,
    BeamMethod,
    bending_strain,
    diagonal_strain,
    total_bending_strain,
    total_diagonal_strain,
)
from garisenda.buildings._building import Building
from garisenda.buildings._categories import Band, DamageCategories
from garisenda.buildings._cutoff import NoCutoff, TroughWidthCutoff
from garisenda.profile._movement_profile import MERGE_TOLERANCE, profile_rows
from garisenda.sources._critical import find_zeros
from garisenda.sources._movement import MethodRecord
from garisenda.sources._transverse_trough import (
    CRITICAL_DISTANCE_SAMPLING,
    CRITICAL_DISTANCE_TOLERANCE,
)
from garisenda.utilities._continuous_pipe import (
    TIE,
    Along,
    _add_stations,
    _read_interaction,
    _read_limit,
    _read_profile,
    _utilization,
    along_line,
    extreme,
)

FloatArray = npt.NDArray[np.float64]

DEFLECTION_TOLERANCE = 1e-9
"""The length in m to which each zone's Delta is located."""

FLAT = 1e-10
"""Fraction of a zone's largest settlement below which its Delta is zero."""

UNITS = {"chord": "m", "deflection": "m"}

ASSUMPTIONS = (
    "The wall follows the greenfield trough at its foundation level, with no "
    "stiffness of its own: its Delta/L and eps_h are the ground's. Mair, Taylor "
    "& Burland (1996, §5.3) call this usually very conservative; soil-structure "
    "interaction would reduce them.",
    "The wall is a beam of height H and unit width spanning each zone, simply "
    "supported under a central point load, with its neutral axis at the bottom "
    "in hogging (t = H, I = H^3/3) and at mid-height in sagging (t = H/2, "
    "I = H^3/12).",
    "Eq. 10 takes Poisson's ratio as 0.3, as Mair, Taylor & Burland (1996, "
    "p. 717) state it whatever E/G is.",
    "A compressive horizontal strain is used with its sign in Eqs. 9 and 10, as "
    "the sources use it: it lowers eps_bt, and eps_dt is never negative.",
    "The movement across the wall in plan isn't assessed; it is zero for a wall "
    "perpendicular to the tunnel.",
    "Stage 1 (the largest settlement and the largest slope) is taken at the "
    "wall's foundation level, where the published check takes the ground "
    "surface. A trough below the surface is narrower and deeper, so this is "
    "more onerous; a foundation depth of 0 gives the published check. The slope "
    "is along the wall, its tilt: for a wall oblique to the tunnel it is less "
    "than the ground's steepest slope.",
)


@dataclass(frozen=True)
class Zone:
    """One zone of the wall: its ends, chord, Delta and horizontal strain.

    `deflection` is Delta = |d| at `deflection_distance` (NaN for a flat
    zone), and the chord is w(start) + `chord_slope` (s - start).
    """

    number: int
    start: float
    end: float
    mode: str
    deflection: float
    deflection_distance: float
    chord_start: float
    chord_slope: float
    horizontal_strain: float

    @property
    def length(self) -> float:
        return self.end - self.start


@judgments(
    beam_method="it sets how the wall's shear deflection is taken, and practice "
    "uses two. Pass gs.buildings.burland_wroth_beam() (Eqs. 7 and 8 as Mair, "
    "Taylor & Burland give them) or gs.buildings.timoshenko_beam().",
    youngs_to_shear_modulus_ratio="it depends on how the wall is built. Pass a "
    "number, or a preset such as "
    'gs.presets.youngs_to_shear_modulus_ratio(structure="masonry").',
    category_limits="it sets the strain at which each damage category starts. "
    "Pass a gs.buildings.DamageCategories, such as "
    "gs.presets.damage_categories().",
    cutoff="it sets how much of the wall is assessed. Pass "
    "gs.buildings.no_cutoff() for the whole wall, or "
    "gs.buildings.trough_width_cutoff(multiple=...).",
    settlement_limit="it is the settlement below which the building's risk is "
    "taken as negligible. Pass a length, e.g. "
    "gs.presets.preliminary_assessment_limits().settlement, or None for no "
    "limit.",
    slope_limit="it is the largest slope the building may take. Pass a slope "
    "as a quantity, e.g. gs.presets.preliminary_assessment_limits().slope, or "
    "None for no limit.",
    acceptable_category="it is the worst damage category the project accepts. "
    "Pass a category number from category_limits, e.g. 2, or None to report "
    "the category without a pass or fail.",
    interaction="it says how the building interacts with the ground. Phase 1 "
    'takes only interaction="greenfield": the wall follows the ground.',
)
def check_building(
    profile: Result,
    *,
    beam_method: object,
    youngs_to_shear_modulus_ratio: object,
    category_limits: object,
    cutoff: object,
    settlement_limit: object,
    slope_limit: object,
    acceptable_category: object,
    interaction: object,
) -> Result:
    """Assess a building's wall for damage from the movement profile along it.

    The staged method of Mair, Taylor & Burland (1996), after Burland & Wroth
    (1974) and Boscardin & Cording (1989). The wall follows the greenfield
    trough at its foundation level. With s the distance along the wall, w(s)
    its settlement (positive down) and u_a(s) its movement along itself:

    **Stage 1:** the largest settlement w and the largest slope |dw/ds| along
    the wall, each against its limit.

    **Stage 2:**

    - zones: the wall is split at the zeros of the vertical curvature w'',
      found by root-finding on the source's exact derivatives (sampled at 1/8
      of its feature length, refined to 1e-9 m), so w'' has one sign in each
      zone. Ends closer than 1 um are merged. No minimum length is set: a
      short zone's bending strain goes to zero with its length;
    - chord: on a zone [s1, s2] of length L = s2 - s1,
      c(s) = w(s1) + (w(s2) - w(s1)) (s - s1) / L;
    - deflection: d(s) = w(s) - c(s), negative in hogging (the wall lies
      below its chord) and positive in sagging. Delta = |d| at the zero of
      w'(s) - (w(s2) - w(s1)) / L, which is where |d| is largest, found to
      1e-9 m. A zone whose Delta is below 1e-10 of its largest settlement is
      ``"flat"``: eps_b = eps_d = 0 and it is assessed on eps_h alone;
    - horizontal strain: eps_h = (u_a(s2) - u_a(s1)) / L, the mean ground
      strain along the zone (tension positive);
    - the wall as a beam of height H and unit width, with t the depth of the
      neutral axis below the extreme tensile fiber and I the second moment of
      area: hogging t = H, I = H^3/3; sagging t = H/2, I = H^3/12;
    - bending strain, with alpha_s the beam method's shear-deflection
      coefficient: Delta/L = (L/(12 t) + alpha_s E I/(t L H G)) eps_b. With
      alpha_s = 3/2 this is Eq. 7;
    - diagonal strain: Delta/L = (2 alpha_s/3 + H L^2 G/(18 I E)) eps_d. With
      alpha_s = 3/2 this is Eq. 8;
    - combined: eps_bt = eps_h + eps_b (Eq. 9) and
      eps_dt = 0.35 eps_h + sqrt((0.65 eps_h)^2 + eps_d^2) (Eq. 10, Poisson's
      ratio 0.3);
    - the zone's tensile strain is the larger of eps_bt and eps_dt, and its
      damage category is the band of `category_limits` it falls in. The
      governing zone has the largest tensile strain, the first by distance on
      a tie within 1e-9.

    Sources: Mair, Taylor & Burland (1996), Prediction of ground movements and
    assessment of risk of building damage due to bored tunnelling, Tables 1-2
    (p. 715), Eqs. 7-9 and §§4.1-4.3 (p. 716), Eq. 10, §4.5 and §§5.1-5.3
    (p. 717), after Burland & Wroth (1974), Burland et al. (1977) and
    Boscardin & Cording (1989), which haven't been read. The beam with any
    shear coefficient (Timoshenko's 6/5 among them) and Eq. 10's general form
    are garisenda's own derivation, given in `burland_wroth_beam`,
    `timoshenko_beam` and their strain functions; Jones (2022), Soft Ground
    Tunnel Design, Eqs. 13.12 and 13.23 and Example 13.2, is a check of them.

    Parameters
    ----------
    profile : Result
        A movement profile along a building, from
        ``gs.movement_profile(building, source, spacing=...)``. It keeps the
        source and the wall, which the zones and Delta need.
    beam_method : BeamMethod
        `garisenda.buildings.burland_wroth_beam` (alpha_s = 3/2) or
        `garisenda.buildings.timoshenko_beam` (alpha_s = 6/5). A design
        judgment with no default.
    youngs_to_shear_modulus_ratio : number
        E/G of the wall, dimensionless, positive. A plain number is accepted.
        A design judgment with no default; see
        `garisenda.presets.youngs_to_shear_modulus_ratio`.
    category_limits : DamageCategories
        The damage categories by limiting tensile strain, such as
        `garisenda.presets.damage_categories`. A design judgment with no
        default.
    cutoff : NoCutoff or TroughWidthCutoff
        How much of the wall is assessed: `garisenda.buildings.no_cutoff` (the
        whole wall) or `garisenda.buildings.trough_width_cutoff`. A design
        judgment with no default.
    settlement_limit : length or None
        Stage 1's settlement limit, in m if a plain number; zero or more.
        ``None`` reports the settlement with no utilization.
    slope_limit : slope or None
        Stage 1's slope limit, as a quantity (``2 * gs.units("mm/m")``,
        ``0.2 * gs.units.percent``); a plain number is refused, because 1/500,
        0.2 % and 2 mm/m are all in use. Zero or more. ``None`` reports the
        slope with no utilization.
    acceptable_category : int or None
        The worst damage category accepted, a band number of
        `category_limits` (practice often uses 2). ``None`` reports the
        categories with no pass or fail.
    interaction : {"greenfield"}
        The soil-structure interaction. Phase 1 takes only ``"greenfield"``:
        the wall follows the ground.

    Returns
    -------
    Result
        ``analysis`` is ``"building_check"`` and ``subject`` the building's
        id. ``values`` has every column of the profile, with rows added at
        each zone's ends and Delta (marked ``critical``), and:

        - ``zone`` (nullable integer): the zone a row is in; a zone's end
          belongs to the zone after it, and the wall's last end to the last
          zone. NA outside the assessed range;
        - ``chord`` (m): the zone's chord c(s);
        - ``deflection`` (m): d = w - c, negative in hogging.

        ``zones`` has one row per zone, in order along the wall, with units
        in ``zones.attrs["units"]``: ``zone``, ``mode`` (``"hogging"``,
        ``"sagging"`` or ``"flat"``), ``start``, ``end``, ``length`` (m),
        ``deflection`` (Delta, m), ``deflection_distance`` (m, NaN when
        flat), ``deflection_ratio`` (Delta/L), ``horizontal_strain``,
        ``bending_strain``, ``diagonal_strain``, ``total_bending_strain``,
        ``total_diagonal_strain``, ``tensile_strain`` (all dimensionless),
        ``governed_by`` (``"bending"`` or ``"diagonal"``, ``"bending"`` on a
        tie), and the zone's ``category`` (band number), ``label`` and
        ``severity``.

        ``checks`` has, in this order:

        - ``settlement``: the largest settlement against `settlement_limit`
          (m);
        - ``slope``: the largest |dw/ds| against `slope_limit`;
        - ``zone_1`` to ``zone_n``: each zone's tensile strain against the
          upper limit of `acceptable_category`'s band, with its ``zone`` and
          ``category``. A zone's strain comes from a beam over the whole
          zone, so ``governing_distance`` is NaN; Delta's distance is in
          ``zones``;
        - ``damage_category``: the governing zone's tensile strain, against
          the same limit, with its ``zone`` and ``category``.

        Utilization is value / limit; the last band's limit is infinite, so
        accepting it always passes. With no limit, ``limit`` and
        ``utilization`` are NaN and ``passes`` NA. ``governed_by`` is
        ``"analytical"`` for Stage 1 (the exact extreme) and ``"bending"`` or
        ``"diagonal"`` for a zone. The method, assumptions and inputs are the
        profile's with this check's added, including the presets' caveats;
        validity and warnings are the profile's.

    Raises
    ------
    TypeError
        If a judgment is missing or of the wrong type, the profile isn't a
        movement profile along a building, or `slope_limit` is a plain number.
    ValueError
        If `interaction` isn't ``"greenfield"``, E/G isn't positive, a limit
        is negative, or `acceptable_category` isn't a band of
        `category_limits`.

    Notes
    -----
    Assumed, and recorded on the result: the wall follows the greenfield
    trough at foundation level with no stiffness (usually very conservative),
    it is a beam of height H and unit width, Eq. 10 takes Poisson's ratio as
    0.3, compressive eps_h is used with its sign, movement across the wall
    isn't assessed, and Stage 1 is taken at foundation level along the wall.
    """
    building, source = _read_profile(profile, "check_building", Building)
    beam, beam_record = record_method(
        "beam_method",
        beam_method,
        kind="design judgment",
        expected=BeamMethod,
        how="Pass gs.buildings.burland_wroth_beam() or gs.buildings.timoshenko_beam().",
    )
    ratio_m, ratio_record = record(
        "youngs_to_shear_modulus_ratio",
        youngs_to_shear_modulus_ratio,
        kind="design judgment",
        unit="dimensionless",
        plain_number="read as SI",
    )
    ratio = float(ratio_m)
    if not (math.isfinite(ratio) and ratio > 0):
        raise ValueError(
            f"youngs_to_shear_modulus_ratio (E/G) must be positive, not {ratio}."
        )
    categories, categories_record = _read_categories(category_limits)
    cut, cutoff_record = _read_cutoff(cutoff)
    settlement, settlement_record = _read_limit(
        "settlement_limit", settlement_limit, unit="m", plain_number="read as SI"
    )
    slope, slope_record = _read_limit("slope_limit", slope_limit)
    acceptable, acceptable_record = _read_acceptable(acceptable_category, categories)
    interaction_record = _read_interaction(interaction, "wall")
    _, poisson_record = record(
        "poisson_ratio",
        POISSON_RATIO,
        kind="constant or setting",
        unit="dimensionless",
        plain_number="read as SI",
    )
    if isinstance(cut, TroughWidthCutoff):
        raise NotImplementedError("trough_width_cutoff isn't supported yet.")

    line = along_line(building, source)
    low, high = 0.0, line.length
    zones = _zones(line, low, high)

    distance, is_critical = _add_stations(
        profile.values["distance"].to_numpy(dtype=np.float64),
        profile.values["critical"].to_numpy(dtype=bool),
        np.array(
            [zone.start for zone in zones]
            + [zones[-1].end]
            + [
                zone.deflection_distance
                for zone in zones
                if math.isfinite(zone.deflection_distance)
            ],
            dtype=np.float64,
        ),
    )
    values, flags, validity = profile_rows(building, source, distance, is_critical)
    values = _with_zones(values, zones, low, high)

    zone_rows = [
        _zone_row(zone, building.height, ratio, beam, categories) for zone in zones
    ]
    limit = math.nan if acceptable is None else acceptable.upper_limit
    checks = checks_frame(
        [
            *_stage_1(values, settlement, slope),
            *_zone_checks(zone_rows, limit),
        ]
    )

    assumptions = [
        *ASSUMPTIONS,
        _cutoff_assumption(cut),
        *_unlimited_assumption(
            settlement_limit=settlement,
            slope_limit=slope,
            acceptable_category=limit,
        ),
        *preset_caveats(
            beam_method,
            youngs_to_shear_modulus_ratio,
            category_limits,
            cutoff,
            settlement_limit,
            slope_limit,
            acceptable_category,
            interaction,
        ),
    ]
    return Result(
        analysis="building_check",
        subject=building.building_id,
        values=values,
        checks=checks,
        method=(*profile.method, _method(beam)),
        assumptions=(*profile.assumptions, *assumptions),
        inputs=(
            *profile.inputs,
            beam_record,
            ratio_record,
            categories_record,
            cutoff_record,
            settlement_record,
            slope_record,
            acceptable_record,
            interaction_record,
            poisson_record,
        ),
        validity=validity,
        warnings=flags,
        zones=zones_frame(zone_rows),
        source=source,
        asset=building,
    )


def _read_categories(value: object) -> tuple[DamageCategories, InputRecord]:
    """Return the damage categories and their record: the name and the limits."""
    source = None
    if isinstance(value, Sourced):
        source = value.source
        value = value.value
    if not isinstance(value, DamageCategories):
        raise TypeError(
            "category_limits must be a gs.buildings.DamageCategories, such as "
            f"gs.presets.damage_categories(), not {type(value).__name__} "
            f"({value!r})."
        )
    bands = "; ".join(
        f"{band.label} up to {100 * band.upper_limit:g} %"
        if math.isfinite(band.upper_limit)
        else f"{band.label} above"
        for band in value.bands
    )
    return value, InputRecord(
        "category_limits",
        f"{value.name} ({bands})",
        "design judgment",
        "method",
        source,
    )


def _read_cutoff(value: object) -> tuple[NoCutoff | TroughWidthCutoff, InputRecord]:
    """Return the cut-off and its record, by name."""
    how = (
        "Pass gs.buildings.no_cutoff() or gs.buildings.trough_width_cutoff("
        "multiple=...)."
    )
    unwrapped = value.value if isinstance(value, Sourced) else value
    if isinstance(unwrapped, TroughWidthCutoff):
        return record_method(
            "cutoff", value, kind="design judgment", expected=TroughWidthCutoff, how=how
        )
    return record_method(
        "cutoff", value, kind="design judgment", expected=NoCutoff, how=how
    )


def _read_acceptable(
    value: object, categories: DamageCategories
) -> tuple[Band | None, InputRecord]:
    """Return the acceptable category's band (None for none) and its record."""
    source = None
    if isinstance(value, Sourced):
        source = value.source
        value = value.value
    if value is None:
        return None, InputRecord(
            "acceptable_category", "none", "design judgment", "none", source
        )
    if isinstance(value, bool) or not isinstance(value, int | np.integer):
        raise TypeError(
            "acceptable_category must be a category number from category_limits, "
            f"such as 2, or None, not {type(value).__name__} ({value!r})."
        )
    band = categories.band(int(value))
    return band, InputRecord(
        "acceptable_category", band.label, "design judgment", "category number", source
    )


def _zones(line: Along, low: float, high: float) -> list[Zone]:
    """Split [low, high] at the zeros of w'' and find each zone's Delta and eps_h."""
    span = high - low
    step = CRITICAL_DISTANCE_SAMPLING * line.feature
    samples = low + np.linspace(0.0, span, max(math.ceil(span / step), 1) + 1)
    sampled, displacement = line.derivatives(samples)
    largest = float(np.max(np.linalg.norm(displacement, axis=1)))
    # The scale find_critical_distances sets for a second derivative.
    scale = max(float(np.max(np.abs(sampled[:, 1, 1]))), largest / line.feature**2)

    def curvature(distance: FloatArray) -> FloatArray:
        result: FloatArray = line.derivatives(low + distance)[0][:, 1, 1:2]
        return result

    zeros = low + find_zeros(
        curvature,
        length=span,
        step=step,
        tolerance=CRITICAL_DISTANCE_TOLERANCE,
        scales=np.array([scale]),
    )
    ends = [low]
    for zero in zeros.tolist():
        if zero - ends[-1] >= MERGE_TOLERANCE and high - zero >= MERGE_TOLERANCE:
            ends.append(zero)
    ends.append(high)
    return [
        _zone(line, number, start, end)
        for number, (start, end) in enumerate(itertools.pairwise(ends), 1)
    ]


def _zone(line: Along, number: int, start: float, end: float) -> Zone:
    """Return a zone's chord, Delta and eps_h, by root-finding on w' - chord slope."""
    a, v, _ = line.directions
    length = end - start
    _, ends = line.derivatives(np.array([start, end]))
    settlement, along = ends @ v, ends @ a
    slope = float(settlement[1] - settlement[0]) / length
    horizontal = float(along[1] - along[0]) / length

    def departure(distance: FloatArray) -> FloatArray:
        result: FloatArray = line.derivatives(start + distance)[0][:, 0, 1:2] - slope
        return result

    step = CRITICAL_DISTANCE_SAMPLING * line.feature
    samples = start + np.linspace(0.0, length, max(math.ceil(length / step), 1) + 1)
    sampled, displacement = line.derivatives(samples)
    largest = float(np.max(np.abs(displacement @ v)))
    scale = max(float(np.max(np.abs(sampled[:, 0, 1] - slope))), largest / line.feature)
    found = start + find_zeros(
        departure,
        length=length,
        step=step,
        tolerance=DEFLECTION_TOLERANCE,
        scales=np.array([scale]),
    )
    chord = (float(settlement[0]), slope)
    if found.size:
        _, at = line.derivatives(found)
        deflection = at @ v - (chord[0] + slope * (found - start))
        index = int(np.argmax(np.abs(deflection)))
        signed, where = float(deflection[index]), float(found[index])
    else:
        signed, where = 0.0, math.nan
    if abs(signed) <= FLAT * largest:
        return Zone(number, start, end, "flat", 0.0, math.nan, *chord, horizontal)
    mode = "hogging" if signed < 0 else "sagging"
    return Zone(number, start, end, mode, abs(signed), where, *chord, horizontal)


def _with_zones(
    values: pd.DataFrame, zones: list[Zone], low: float, high: float
) -> pd.DataFrame:
    """Add the ``zone``, ``chord`` and ``deflection`` columns."""
    distance = values["distance"].to_numpy(dtype=np.float64)
    inside = (distance >= low - MERGE_TOLERANCE) & (distance <= high + MERGE_TOLERANCE)
    inner = np.array([zone.start for zone in zones[1:]], dtype=np.float64)
    index = np.searchsorted(inner - MERGE_TOLERANCE, distance, side="right")
    chord = np.full(distance.shape, np.nan)
    for position, zone in enumerate(zones):
        rows = inside & (index == position)
        chord[rows] = zone.chord_start + zone.chord_slope * (
            distance[rows] - zone.start
        )
    number = pd.array(
        [int(i) + 1 if row else pd.NA for i, row in zip(index, inside, strict=True)],
        dtype="Int64",
    )
    units = dict(values.attrs["units"])
    result = values.assign(
        zone=number,
        chord=chord,
        deflection=values["vertical"].to_numpy(dtype=np.float64) - chord,
    )
    result.attrs["units"] = units | UNITS
    return result


def _zone_row(
    zone: Zone,
    height: float,
    ratio: float,
    beam: BeamMethod,
    categories: DamageCategories,
) -> dict[str, Any]:
    """Return a zone's row of the zones table: its strains and category."""
    deflection_ratio = zone.deflection / zone.length
    if zone.mode == "flat":
        bending = diagonal = 0.0
    else:
        common: dict[str, Any] = {
            "length": zone.length,
            "height": height,
            "mode": zone.mode,
            "youngs_to_shear_modulus_ratio": ratio,
            "beam": beam,
        }
        bending = bending_strain(deflection_ratio, **common)
        diagonal = diagonal_strain(deflection_ratio, **common)
    total_bending = total_bending_strain(bending, zone.horizontal_strain)
    total_diagonal = total_diagonal_strain(diagonal, zone.horizontal_strain)
    tensile = max(total_bending, total_diagonal)
    band = categories.category(tensile)
    return {
        "zone": zone.number,
        "mode": zone.mode,
        "start": zone.start,
        "end": zone.end,
        "length": zone.length,
        "deflection": zone.deflection,
        "deflection_distance": zone.deflection_distance,
        "deflection_ratio": deflection_ratio,
        "horizontal_strain": zone.horizontal_strain,
        "bending_strain": bending,
        "diagonal_strain": diagonal,
        "total_bending_strain": total_bending,
        "total_diagonal_strain": total_diagonal,
        "tensile_strain": tensile,
        "governed_by": "bending" if total_bending >= total_diagonal else "diagonal",
        "category": band.number,
        "label": band.label,
        "severity": band.severity,
    }


def _stage_1(
    values: pd.DataFrame, settlement_limit: float, slope_limit: float
) -> list[dict[str, Any]]:
    """Return Stage 1's checks: the largest settlement and the largest |slope|."""
    distance = values["distance"].to_numpy(dtype=np.float64)
    rows = []
    for name, column, limit, unit in (
        ("settlement", "vertical", settlement_limit, "m"),
        ("slope", "vertical_slope", slope_limit, "dimensionless"),
    ):
        found = values[column].to_numpy(dtype=np.float64)
        if name == "slope":
            found = np.abs(found)
        value, where = extreme(found, distance, 1)
        utilization, passes = _utilization(value, limit, smallest=False)
        rows.append(
            {
                "check": name,
                "value": value,
                "unit": unit,
                "limit": limit,
                "utilization": utilization,
                "governing_distance": where,
                "passes": passes,
                "governed_by": "analytical",
            }
        )
    return rows


def _zone_checks(zone_rows: list[dict[str, Any]], limit: float) -> list[dict[str, Any]]:
    """Return a check per zone and the governing zone's ``damage_category``."""
    rows = []
    for zone in zone_rows:
        rows.append(_strain_check(f"zone_{zone['zone']}", zone, limit))
    if zone_rows:
        largest = max(zone["tensile_strain"] for zone in zone_rows)
        governing = next(
            zone
            for zone in zone_rows
            if zone["tensile_strain"] >= largest - TIE * abs(largest)
        )
        rows.append(_strain_check("damage_category", governing, limit))
    return rows


def _strain_check(name: str, zone: dict[str, Any], limit: float) -> dict[str, Any]:
    value = float(zone["tensile_strain"])
    utilization, passes = _utilization(value, limit, smallest=False)
    return {
        "check": name,
        "value": value,
        "unit": "dimensionless",
        "limit": limit,
        "utilization": utilization,
        "governing_distance": math.nan,
        "passes": passes,
        "governed_by": zone["governed_by"],
        "zone": zone["zone"],
        "category": zone["category"],
    }


def _cutoff_assumption(cut: NoCutoff | TroughWidthCutoff) -> str:
    if isinstance(cut, NoCutoff):
        return (
            "The whole wall is assessed, with no cut-off: the outer zones run to "
            "the wall's ends."
        )
    return (
        f"Only the wall within {cut.multiple:g} i of a trough's axis is assessed; "
        "cutting a zone short can lower its strains as well as raise them."
    )


def _unlimited_assumption(**limits: float) -> list[str]:
    """Return the assumption naming the checks with no limit, if any."""
    unlimited = [name for name, limit in limits.items() if math.isnan(limit)]
    if not unlimited:
        return []
    return [
        f"No limit was given for {', '.join(unlimited)}: those checks are "
        "reported without a utilization."
    ]


def _method(beam: BeamMethod) -> MethodRecord:
    """Return the method record, with Eqs. 7 and 8 in the beam's form."""
    alpha = Fraction(beam.shear_deflection_coefficient).limit_denominator(100)
    diagonal = Fraction(2, 3) * alpha
    return MethodRecord(
        "Building damage, staged method",
        (
            "Stage 1: the largest settlement w and the largest |dw/ds| along the "
            "wall at foundation level",
            "zones: split at the zeros of w'' = d2w/ds2; on [s1, s2], L = s2 - s1",
            "chord: c(s) = w(s1) + (w(s2) - w(s1)) (s - s1) / L",
            "deflection: d(s) = w(s) - c(s), hogging where d < 0; Delta = |d| "
            "where w'(s) = (w(s2) - w(s1)) / L",
            "horizontal strain: eps_h = (u_a(s2) - u_a(s1)) / L",
            "section: hogging t = H, I = H^3/3; sagging t = H/2, I = H^3/12",
            f"bending: Delta/L = (L/(12 t) + {alpha} E I/(t L H G)) eps_b "
            f"({beam.name})",
            f"diagonal: Delta/L = ({diagonal} + H L^2 G/(18 I E)) eps_d",
            "eps_bt = eps_h + eps_b (Eq. 9)",
            "eps_dt = 0.35 eps_h + sqrt((0.65 eps_h)^2 + eps_d^2) (Eq. 10)",
            "tensile strain: max(eps_bt, eps_dt); category from the limiting "
            "tensile strains",
        ),
        f"{MAIR_TAYLOR_BURLAND}, pp. 715-717, Tables 1-2 and Eqs. 7-10, after "
        "Burland & Wroth (1974), Burland et al. (1977) and Boscardin & Cording "
        "(1989). The beam with any shear coefficient, Eq. 10's general form, "
        "the zones and Delta are garisenda's own derivation.",
    )
