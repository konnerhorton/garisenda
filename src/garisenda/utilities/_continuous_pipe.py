"""Strain checks for a continuous pipe (M3 (a) spec)."""

import math
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd

from garisenda._inputs import InputRecord, Sourced, judgments, record
from garisenda._result import CHECK_COLUMNS, CHECK_TYPES, Result
from garisenda.profile._movement_profile import (
    MERGE_TOLERANCE,
    _with_distances,
    merge_stations,
    profile_rows,
)
from garisenda.sources._critical import _derivatives, find_zeros
from garisenda.sources._movement import Flag, MethodRecord, Source, worst
from garisenda.sources._segment import directions
from garisenda.sources._transverse_trough import (
    CRITICAL_DISTANCE_SAMPLING,
    CRITICAL_DISTANCE_TOLERANCE,
)
from garisenda.utilities._utility import Utility

FloatArray = npt.NDArray[np.float64]

TIE = 1e-9
"""Relative difference within which two extremes are equal (as `Result.governing`)."""

INTERACTIONS = ("greenfield",)
"""The soil-structure interactions Phase 1 takes (SPEC §1.3)."""

METHOD = MethodRecord(
    "Strain checks for a continuous pipe",
    (
        "axial strain: eps_a = du_a/ds (the along strain; the pipe follows the ground)",
        "bending strain in each plane: eps_b,v = r kappa_v, eps_b,l = r kappa_l, "
        "r = D / 2, kappa = d2w/ds2",
        "resultant curvature: |kappa| = sqrt(kappa_v^2 + kappa_l^2); bending "
        "strain eps_b = r |kappa|",
        "tensile strain: eps_t = max(eps_a, 0) + r |kappa|",
        "compressive strain: eps_c = min(eps_a, 0) - r |kappa|",
        "radius of curvature: R = 1 / |kappa|, infinite where |kappa| = 0",
        "peaks: zeros of d|kappa|^2/ds, d eps_t/ds and d eps_c/ds along the pipe",
        "discrete axial strain: eps_a,d(s) = (u_a(s + h/2) - u_a(s - h/2)) / h",
        "discrete curvature in each plane: kappa_d(s) = (w(s + h) - 2 w(s) + "
        "w(s - h)) / h^2",
        "discrete resultant, bending, combined strains and radius: as above, "
        "from eps_a,d and kappa_d",
        "governing: the worse of the analytical and discrete extremes, per check",
    ),
    "Mechanics, derived in the M3 (a) spec; the approach after Bracegirdle et "
    "al. (1996), pp. 660, 663.",
)

ASSUMPTIONS = (
    "The pipe follows the ground, with no reduction for its stiffness or for "
    "slip: its axial strain is the ground's strain along it and its curvature "
    "the ground's. Soil-structure interaction would reduce them (SPEC §1.3, "
    "§13 Q1).",
    "The pipe's section is circular and strain is taken at its outermost "
    "fiber, from the given outside diameter.",
    "Displacements and slopes are small: strain is du_a/ds, without the half "
    "slope squared, and curvature is d2w/ds2, without the factor "
    "(1 + w'^2)^(-3/2).",
    "Combined strain never counts axial strain as helping: compression doesn't "
    "reduce the tensile strain, nor tension the compressive strain.",
)

LIMITS = (
    "tensile_strain_limit",
    "compressive_strain_limit",
    "bending_strain_limit",
    "radius_of_curvature_limit",
)

# Each check: its name, the column it reads, the extreme (+1 the largest
# positive, -1 the most negative, 0 the smallest), its limit and its unit.
CHECKS: tuple[tuple[str, str, int, str, str], ...] = (
    ("axial_tension", "axial_strain", 1, "tensile_strain_limit", "dimensionless"),
    (
        "axial_compression",
        "axial_strain",
        -1,
        "compressive_strain_limit",
        "dimensionless",
    ),
    ("bending", "bending_strain", 1, "bending_strain_limit", "dimensionless"),
    (
        "tensile_strain",
        "tensile_strain",
        1,
        "tensile_strain_limit",
        "dimensionless",
    ),
    (
        "compressive_strain",
        "compressive_strain",
        -1,
        "compressive_strain_limit",
        "dimensionless",
    ),
    (
        "radius_of_curvature",
        "radius_of_curvature",
        0,
        "radius_of_curvature_limit",
        "m",
    ),
)

UNITS = {
    "axial_strain": "dimensionless",
    "vertical_bending_strain": "dimensionless",
    "lateral_bending_strain": "dimensionless",
    "resultant_curvature": "1/m",
    "bending_strain": "dimensionless",
    "tensile_strain": "dimensionless",
    "compressive_strain": "dimensionless",
    "radius_of_curvature": "m",
}

DISCRETE_UNITS = {
    "discrete_axial_strain": "dimensionless",
    "discrete_vertical_curvature": "1/m",
    "discrete_lateral_curvature": "1/m",
    "discrete_resultant_curvature": "1/m",
    "discrete_bending_strain": "dimensionless",
    "discrete_tensile_strain": "dimensionless",
    "discrete_compressive_strain": "dimensionless",
    "discrete_radius_of_curvature": "m",
}


@judgments(
    interval="it is the span over which practice computes strain from sampled "
    "movements: a short one exaggerates small differences, a long one smooths "
    "the peaks. Pass a length, e.g. interval=1 * gs.units.m.",
    interaction="it says how the pipe interacts with the ground. Phase 1 takes "
    'only interaction="greenfield": the pipe follows the ground (SPEC §1.3).',
    tensile_strain_limit="it depends on the pipe's material and its condition. "
    'Pass a strain, e.g. gs.units.Quantity(1000, "µε"), or None for no limit.',
    compressive_strain_limit="it depends on the pipe's material and its "
    'condition. Pass a strain, e.g. gs.units.Quantity(1000, "µε"), or None for '
    "no limit.",
    bending_strain_limit="it depends on the pipe's material; where none is given "
    "separately, pass the smaller of the tensile and compressive limits, or None "
    "for no limit.",
    radius_of_curvature_limit="it depends on the pipe's material and joints. "
    "Pass a length, e.g. 500 * gs.units.m, or None for no limit.",
)
def check_continuous_pipe(
    profile: Result,
    *,
    interval: object,
    interaction: object,
    tensile_strain_limit: object,
    compressive_strain_limit: object,
    bending_strain_limit: object,
    radius_of_curvature_limit: object,
) -> Result:
    """Check a continuous pipe's strains against the movement profile along it.

    The pipe (welded steel, HDPE, PVC, HDD-installed) follows the ground, so
    its strains come from the profile's exact derivatives. With s the distance
    along the pipe, u_a, w and u_l its displacement along, vertical (positive
    down) and lateral, and r = D / 2 its outside radius:

    - axial strain: eps_a = du_a/ds, the profile's ``along_strain``
      (tension positive);
    - bending strain in each plane: eps_b,v = r kappa_v and
      eps_b,l = r kappa_l, with kappa_v and kappa_l the profile's
      ``vertical_curvature`` and ``lateral_curvature`` (positive hogging);
    - resultant curvature: |kappa| = sqrt(kappa_v^2 + kappa_l^2), and the
      bending strain at the outermost fiber eps_b = r |kappa|: for a circular
      section the fiber at angle phi has strain
      -r (kappa_v cos(phi) + kappa_l sin(phi)), largest at r |kappa|;
    - tensile strain: eps_t = max(eps_a, 0) + r |kappa|;
    - compressive strain: eps_c = min(eps_a, 0) - r |kappa| (negative);
    - radius of curvature: R = 1 / |kappa|, infinite where |kappa| = 0.

    These are derived in the M3 (a) spec from the definition of strain, plane
    sections and the geometry of a circle: strain is the change in length over
    the original length, and a fiber y from the neutral axis of a beam bent to
    radius R has strain y / R. The approach, that the pipe follows the ground
    and its strains come from differentiating the displacements, and that
    combined tensile strain is bending plus axial, is Bracegirdle et al.
    (1996), pp. 660, 663.

    The resultant curvature and the combined strains peak where none of the
    source's critical distances are (on an oblique pipe, between the peaks of
    kappa_v and kappa_l), so the check adds rows at the zeros of d|kappa|^2/ds,
    d eps_t/ds and d eps_c/ds, found by root-finding on the source's exact
    derivatives as the source's critical distances are (sampled at 1/8 of its
    feature length, refined to 1e-9 m). They are marked ``critical``.

    Each value is also computed discretely, as practice does from movements
    sampled at an interval h, at every row s, from the source evaluated on the
    pipe's line:

    - axial strain: eps_a,d(s) = (u_a(s + h/2) - u_a(s - h/2)) / h;
    - curvature in each plane, the second difference:
      kappa_d(s) = (w(s + h) - 2 w(s) + w(s - h)) / h^2, which is the
      curvature of the circle through the three displaced points with the
      same small-slope approximation as the analytical curvature;
    - the resultant, bending, combined strains and radius from these, as
      above.

    The discrete values are averages of the analytical ones over the span, so
    in each plane the discrete peak is never the larger. Each check is
    governed by the worse of its analytical and discrete extremes, and both
    are reported with their difference, which shows when the interval is too
    coarse. A row with a sample beyond an end (by more than 1 um) has no
    discrete value; the pipe is not assumed to continue past its ends.

    Parameters
    ----------
    profile : Result
        A movement profile from `garisenda.movement_profile`, which keeps its
        source and utility.
    interval : length
        The span h over which discrete strain is computed, in m if a plain
        number. A design judgment with no default; must be positive.
    interaction : {"greenfield"}
        The soil-structure interaction. A design judgment with no default;
        Phase 1 takes only ``"greenfield"``, the pipe follows the ground.
    tensile_strain_limit, compressive_strain_limit : strain or None
        The largest tensile and compressive strains allowed, as positive
        magnitudes. Pint quantities only (``0.1 * gs.units.percent``,
        ``gs.units.Quantity(1000, "µε")``); a plain number is refused. Design
        judgments with no default; ``None`` means no limit.
    bending_strain_limit : strain or None
        The largest bending strain allowed, as for the strain limits. A
        judgment of its own, because some materials are given a bending limit
        separate from the axial and combined ones; where none is, pass
        ``min(tensile, compressive)``.
    radius_of_curvature_limit : length or None
        The smallest radius of curvature allowed, in m if a plain number.
        ``None`` means no limit.

    Returns
    -------
    Result
        ``analysis`` is ``"continuous_pipe_check"`` and ``subject`` the
        utility's id. ``values`` has every column of the profile, with the
        added rows at the peaks, and, with units in ``attrs["units"]``:

        - ``axial_strain`` (dimensionless): the pipe's, equal to
          ``along_strain`` while greenfield;
        - ``vertical_bending_strain``, ``lateral_bending_strain``
          (dimensionless): r kappa, signed as the curvature;
        - ``resultant_curvature`` (1/m) and ``bending_strain``
          (dimensionless);
        - ``tensile_strain``, ``compressive_strain`` (dimensionless);
        - ``radius_of_curvature`` (m), infinite where the pipe is straight;
        - ``discrete_axial_strain``, ``discrete_vertical_curvature``,
          ``discrete_lateral_curvature``, ``discrete_resultant_curvature``,
          ``discrete_bending_strain``, ``discrete_tensile_strain``,
          ``discrete_compressive_strain``, ``discrete_radius_of_curvature``:
          the discrete values, in the same units, NaN where a row has none.

        ``checks`` has one row per check, in this order, each checked against
        its limit:

        - ``axial_tension``: the largest positive eps_a, against the tensile
          limit;
        - ``axial_compression``: the most negative eps_a, against the
          compressive limit;
        - ``bending``: the largest eps_b, against the bending limit;
        - ``tensile_strain``: the largest eps_t, against the tensile limit;
        - ``compressive_strain``: the most negative eps_c, against the
          compressive limit;
        - ``radius_of_curvature``: the smallest R, against the radius limit.

        Each check's ``analytical`` and ``discrete`` values are the extremes
        of its two columns, with their distances; ``value`` is the worse (the
        larger in size, or the smaller radius), ``governed_by`` says which
        (``"analytical"`` on a tie within 1e-9 or with no discrete value),
        and ``difference`` is discrete - analytical, in the check's unit.
        Utilization is |value| / limit, or limit / R for the radius, and
        ``passes`` is utilization <= 1. A check with no limit has ``limit``
        and ``utilization`` NaN and ``passes`` NA. If no row has a value of
        the check's sign, its value and distance are NaN and it passes. Equal
        extremes, within 1e-9, go to the smallest distance. The method,
        assumptions and inputs are the profile's with this check's added;
        validity and warnings are the recomputed profile's, plus a
        ``"within"`` flag naming the rows with no discrete value and why.

    Raises
    ------
    TypeError
        If a judgment is missing, `profile` isn't a movement profile, or a
        strain limit is a plain number.
    ValueError
        If `interaction` isn't ``"greenfield"``, the interval or a limit isn't
        positive, or the source can't evaluate a point (naming the utility
        and the distances).

    Notes
    -----
    Assumed, and recorded on the result: the pipe follows the ground (no
    soil-structure interaction), its section is circular with strain at the
    outermost fiber, displacements and slopes are small, and axial strain
    never helps the combined strains.
    """
    utility, source = _read_profile(profile)
    interval_m, interval_record = record(
        "interval",
        interval,
        kind="design judgment",
        unit="m",
        plain_number="read as SI",
    )
    interval_m = float(interval_m)
    if not (math.isfinite(interval_m) and interval_m > 0):
        raise ValueError(f"interval must be positive, not {interval_m} m.")
    interaction_record = _read_interaction(interaction)
    limits: dict[str, float] = {}
    limit_records: list[InputRecord] = []
    for name, value in (
        ("tensile_strain_limit", tensile_strain_limit),
        ("compressive_strain_limit", compressive_strain_limit),
        ("bending_strain_limit", bending_strain_limit),
        ("radius_of_curvature_limit", radius_of_curvature_limit),
    ):
        limits[name], entry = _read_limit(name, value)
        limit_records.append(entry)

    radius = utility.diameter / 2
    peaks = _peaks(utility, source, radius)
    distance, is_critical = _add_stations(
        profile.values["distance"].to_numpy(dtype=np.float64),
        profile.values["critical"].to_numpy(dtype=bool),
        peaks,
    )
    values, flags, validity = profile_rows(utility, source, distance, is_critical)
    values = _with_strains(values, radius)
    values = _with_discrete(values, utility, source, interval_m, radius)
    ends = _ends_flag(values, interval_m)
    flags = (*flags, ends)
    validity = worst([validity, ends.verdict])
    checks = _checks(values, limits)

    unlimited = [name for name in LIMITS if math.isnan(limits[name])]
    assumptions = [
        *ASSUMPTIONS,
        f"Discrete strain is computed over an interval h = {interval_m:g} m, "
        "centered on each station: axial strain from the movements at s +- h/2, "
        "curvature in each plane from s - h, s and s + h (the second "
        "difference), with the same small-slope approximation as the "
        "analytical values. Stations closer to an end than that have none.",
    ]
    if unlimited:
        assumptions.append(
            f"No limit was given for {', '.join(unlimited)}: those checks are "
            "reported without a utilization."
        )
    return Result(
        analysis="continuous_pipe_check",
        subject=utility.utility_id,
        values=values,
        checks=checks,
        method=(*profile.method, METHOD),
        assumptions=(*profile.assumptions, *assumptions),
        inputs=(
            *profile.inputs,
            interval_record,
            interaction_record,
            *limit_records,
        ),
        validity=validity,
        warnings=flags,
        source=source,
        asset=utility,
    )


def _read_profile(profile: object) -> tuple[Utility, Source]:
    """Return a movement profile's utility and source, or raise `TypeError`."""
    if not (
        isinstance(profile, Result)
        and profile.analysis == "movement_profile"
        and isinstance(profile.asset, Utility)
        and profile.source is not None
    ):
        what = (
            f"a Result of {profile.analysis!r}"
            if isinstance(profile, Result)
            else type(profile).__name__
        )
        raise TypeError(
            "check_continuous_pipe needs a movement profile, the Result of "
            f"gs.movement_profile(utility, source, spacing=...), not {what}."
        )
    return profile.asset, profile.source


def _read_interaction(interaction: object) -> InputRecord:
    source = None
    if isinstance(interaction, Sourced):
        source = interaction.source
        interaction = interaction.value
    if interaction not in INTERACTIONS:
        raise ValueError(
            f'interaction must be "greenfield", not {interaction!r}: Phase 1 '
            "assesses the pipe as following the ground (SPEC §1.3)."
        )
    return InputRecord("interaction", "greenfield", "design judgment", "name", source)


def _read_limit(name: str, value: object) -> tuple[float, InputRecord]:
    """Return a limit in SI (NaN for none) and its input record."""
    source = None
    unwrapped = value.value if isinstance(value, Sourced) else value
    if unwrapped is None:
        if isinstance(value, Sourced):
            source = value.source
        return math.nan, InputRecord(name, "none", "design judgment", "none", source)
    is_radius = name == "radius_of_curvature_limit"
    magnitude, entry = record(
        name,
        value,
        kind="design judgment",
        unit="m" if is_radius else "dimensionless",
        plain_number="read as SI" if is_radius else "refuse",
    )
    limit = float(magnitude)
    if not (math.isfinite(limit) and limit > 0):
        raise ValueError(f"{name} must be positive, or None for no limit, not {limit}.")
    return limit, entry


def _peaks(utility: Utility, source: Source, radius: float) -> FloatArray:
    """Return where |kappa|, eps_t and eps_c peak along the utility (decision 7)."""
    start, end = (np.asarray(vertex, dtype=np.float64) for vertex in utility.vertices)
    length = float(np.linalg.norm(end - start))
    a, v, lat = directions(start, end)
    feature = float(source.feature_length(start=start, end=end))
    where = f"Utility {utility.utility_id!r}"

    def derivatives(distance: FloatArray) -> tuple[FloatArray, FloatArray]:
        points = start + distance[:, None] * a
        try:
            movement = source.evaluate(
                x=points[:, 0], y=points[:, 1], depth=points[:, 2]
            )
        except ValueError as error:
            raise ValueError(
                f"{where}: {_with_distances(str(error), distance)}"
            ) from error
        return _derivatives(movement, a, v, lat), movement.displacement

    def functions(distance: FloatArray) -> FloatArray:
        return _peak_functions(derivatives(distance)[0], radius)

    # Each function's scale, as find_critical_distances sets it: the largest
    # value over the samples, or what the largest displacement U gives with
    # the feature length f, whichever is larger.
    step = CRITICAL_DISTANCE_SAMPLING * feature
    samples = np.linspace(0.0, length, max(math.ceil(length / step), 1) + 1)
    sampled, displacement = derivatives(samples)
    largest = float(np.max(np.linalg.norm(displacement, axis=1)))
    floor = np.array(
        [
            2 * largest**2 / feature**5,
            largest / feature**2 + radius * largest / feature**3,
            largest / feature**2 + radius * largest / feature**3,
        ]
    )
    scales = np.maximum(np.max(np.abs(_peak_functions(sampled, radius)), axis=0), floor)
    return find_zeros(
        functions,
        length=length,
        step=step,
        tolerance=CRITICAL_DISTANCE_TOLERANCE,
        scales=scales,
    )


def _peak_functions(derivatives: FloatArray, radius: float) -> FloatArray:
    """Return d|kappa|^2/ds, d eps_t/ds and d eps_c/ds, shape (N, 3).

    `derivatives` is ``_derivatives``'s (N, order, direction) array, so
    eps_a = [:, 0, 0], kappa = [:, 1, 1:] and their derivatives one order up.
    """
    strain, strain_gradient = derivatives[:, 0, 0], derivatives[:, 1, 0]
    curvature, curvature_gradient = derivatives[:, 1, 1:], derivatives[:, 2, 1:]
    product = np.sum(curvature * curvature_gradient, axis=1)
    size = np.hypot(curvature[:, 0], curvature[:, 1])
    size_gradient = np.divide(product, size, out=np.zeros_like(product), where=size > 0)
    tension = np.where(strain > 0, 1.0, 0.0)
    result: FloatArray = np.stack(
        [
            2 * product,
            tension * strain_gradient + radius * size_gradient,
            (1 - tension) * strain_gradient - radius * size_gradient,
        ],
        axis=1,
    )
    return result


def _add_stations(
    distance: FloatArray, is_critical: npt.NDArray[np.bool_], peaks: FloatArray
) -> tuple[FloatArray, npt.NDArray[np.bool_]]:
    """Add the peaks to the profile's stations, marked critical.

    A peak within 1 um of a station marks that station critical and leaves its
    distance as it is, so the profile's own rows are unchanged.
    """
    critical = is_critical.copy()
    new: list[float] = []
    for peak in peaks.tolist():
        nearest = int(np.argmin(np.abs(distance - peak)))
        if abs(distance[nearest] - peak) < MERGE_TOLERANCE:
            critical[nearest] = True
        else:
            new.append(peak)
    return merge_stations(
        np.concatenate([distance, new]),
        np.concatenate([critical, np.ones(len(new), dtype=bool)]),
    )


def _with_strains(values: pd.DataFrame, radius: float) -> pd.DataFrame:
    """Add the analytical strains of Mechanics 1-5 to the profile's columns."""
    strain = values["along_strain"].to_numpy(dtype=np.float64)
    vertical = values["vertical_curvature"].to_numpy(dtype=np.float64)
    lateral = values["lateral_curvature"].to_numpy(dtype=np.float64)
    curvature = np.hypot(vertical, lateral)
    bending = radius * curvature
    with np.errstate(divide="ignore"):
        radius_of_curvature = np.where(curvature > 0, 1 / curvature, np.inf)
    columns = {
        "axial_strain": strain.copy(),
        "vertical_bending_strain": radius * vertical,
        "lateral_bending_strain": radius * lateral,
        "resultant_curvature": curvature,
        "bending_strain": bending,
        "tensile_strain": np.maximum(strain, 0.0) + bending,
        "compressive_strain": np.minimum(strain, 0.0) - bending,
        "radius_of_curvature": radius_of_curvature,
    }
    units = dict(values.attrs["units"])
    result = values.assign(**columns)
    result.attrs["units"] = units | UNITS
    return result


def _with_discrete(
    values: pd.DataFrame,
    utility: Utility,
    source: Source,
    interval: float,
    radius: float,
) -> pd.DataFrame:
    """Add the discrete strains of Mechanics 6 (decisions 5 and 6).

    The source is evaluated on the pipe's line at s +- h/2 and s +- h for
    every row s, in one call. Samples beyond an end by more than 1 um give
    NaN; those within 1 um are taken at the end. The source's flags and
    verdicts at the samples are dropped: they lie within h of a station,
    whose verdict stands.
    """
    start, end = (np.asarray(vertex, dtype=np.float64) for vertex in utility.vertices)
    length = float(np.linalg.norm(end - start))
    a, v, lat = directions(start, end)
    station = values["distance"].to_numpy(dtype=np.float64)
    offsets = np.array([-interval / 2, interval / 2, -interval, interval])
    samples = station[None, :] + offsets[:, None]
    beyond = (samples < -MERGE_TOLERANCE) | (samples > length + MERGE_TOLERANCE)
    inside = np.clip(samples[~beyond], 0.0, length)
    points = start + inside[:, None] * a
    try:
        movement = source.evaluate(x=points[:, 0], y=points[:, 1], depth=points[:, 2])
    except ValueError as error:
        raise ValueError(
            f"Utility {utility.utility_id!r}, sampling for discrete strain at an "
            f"interval of {interval:g} m: {_with_distances(str(error), inside)}"
        ) from error
    components = np.full((3, *samples.shape), np.nan)
    for index, direction in enumerate((a, v, lat)):
        components[index][~beyond] = movement.displacement @ direction
    along, vertical, lateral = components
    with np.errstate(invalid="ignore"):
        strain = (along[1] - along[0]) / interval

        def second_difference(column: str, sampled: FloatArray) -> FloatArray:
            middle = values[column].to_numpy(dtype=np.float64)
            result: FloatArray = (sampled[3] - 2 * middle + sampled[2]) / interval**2
            return result

        kappa_v = second_difference("vertical", vertical)
        kappa_l = second_difference("lateral", lateral)
        curvature = np.hypot(kappa_v, kappa_l)
        bending = radius * curvature
        with np.errstate(divide="ignore"):
            radius_of_curvature = np.where(curvature > 0, 1 / curvature, np.inf)
        radius_of_curvature[np.isnan(curvature)] = np.nan
        columns = {
            "discrete_axial_strain": strain,
            "discrete_vertical_curvature": kappa_v,
            "discrete_lateral_curvature": kappa_l,
            "discrete_resultant_curvature": curvature,
            "discrete_bending_strain": bending,
            "discrete_tensile_strain": np.maximum(strain, 0.0) + bending,
            "discrete_compressive_strain": np.minimum(strain, 0.0) - bending,
            "discrete_radius_of_curvature": radius_of_curvature,
        }
    units = dict(values.attrs["units"])
    result = values.assign(**columns)
    result.attrs["units"] = units | DISCRETE_UNITS
    return result


def _ends_flag(values: pd.DataFrame, interval: float) -> Flag:
    """Flag the stations with no discrete axial strain or curvature (decision 6)."""
    missing = (
        values["discrete_axial_strain"].isna()
        | values["discrete_resultant_curvature"].isna()
    )
    length = float(values["distance"].iloc[-1])
    reason = (
        "No discrete value where a sample would fall beyond the pipe's end: "
        f"axial strain within h/2 = {interval / 2:g} m of an end, curvature "
        f"(and so discrete bending, combined strain and radius) within "
        f"h = {interval:g} m. The analytical values cover these stations."
    )
    if length < 2 * interval:
        reason += (
            f" The pipe, {length:g} m long, is shorter than 2h = {2 * interval:g} m, "
            "so no station has a discrete curvature."
        )
    return Flag(
        "within",
        reason,
        f"discrete samples within the pipe (interval h = {interval:g} m)",
        tuple(int(index) for index in np.flatnonzero(missing.to_numpy())),
    )


def _checks(values: pd.DataFrame, limits: dict[str, float]) -> pd.DataFrame:
    """Return the checks table (decisions 4 and 9)."""
    distance = values["distance"].to_numpy(dtype=np.float64)
    rows: list[dict[str, Any]] = []
    for name, column, sign, limit_name, unit in CHECKS:
        analytical, analytical_distance = extreme(
            values[column].to_numpy(dtype=np.float64), distance, sign
        )
        discrete, discrete_distance = extreme(
            values[f"discrete_{column}"].to_numpy(dtype=np.float64), distance, sign
        )
        value, governing_distance, governed_by, difference = governing_value(
            analytical,
            analytical_distance,
            discrete,
            discrete_distance,
            smallest=sign == 0,
        )
        limit = limits[limit_name]
        utilization, passes = _utilization(value, limit, smallest=sign == 0)
        rows.append(
            {
                "check": name,
                "value": value,
                "unit": unit,
                "limit": limit,
                "utilization": utilization,
                "governing_distance": governing_distance,
                "passes": passes,
                "governed_by": governed_by,
                "analytical": analytical,
                "analytical_distance": analytical_distance,
                "discrete": discrete,
                "discrete_distance": discrete_distance,
                "difference": difference,
            }
        )
    table = pd.DataFrame(rows, columns=list(CHECK_COLUMNS))
    return table.astype(CHECK_TYPES)


def governing_value(
    analytical: float,
    analytical_distance: float,
    discrete: float,
    discrete_distance: float,
    *,
    smallest: bool,
) -> tuple[float, float, str, float]:
    """Return the worse of a check's two values (decision 9).

    The worse is the larger in size, or the smaller for a radius
    (`smallest`). On a tie, within 1e-9, and where the discrete value is NaN
    (no station has one), the analytical value governs; where only the
    analytical value is NaN, the discrete one does.

    Returns
    -------
    value, distance : float
        The governing value and where it is.
    governed_by : {"analytical", "discrete"}
        Which governed.
    difference : float
        discrete - analytical, signed as the values are; NaN if either is.
    """
    difference = discrete - analytical
    if math.isnan(discrete):
        return analytical, analytical_distance, "analytical", difference
    if math.isnan(analytical):
        return discrete, discrete_distance, "discrete", difference
    if smallest:
        worse = discrete < analytical * (1 - TIE)
    else:
        worse = abs(discrete) > abs(analytical) * (1 + TIE)
    if worse:
        return discrete, discrete_distance, "discrete", difference
    return analytical, analytical_distance, "analytical", difference


def extreme(values: FloatArray, distance: FloatArray, sign: int) -> tuple[float, float]:
    """Return a column's extreme and its distance, or NaN and NaN if none.

    `sign` +1 is the largest positive value, -1 the most negative and 0 the
    smallest finite value above zero (a radius). Equal extremes, within 1e-9
    of the extreme's size, go to the smallest distance.
    """
    if sign == 0:
        found = np.isfinite(values) & (values > 0)
        if not found.any():
            return math.nan, math.nan
        target = float(np.min(values[found]))
        tied = found & (values <= target * (1 + TIE))
    else:
        signed = sign * values
        found = np.isfinite(signed) & (signed > 0)
        if not found.any():
            return math.nan, math.nan
        target = float(np.max(signed[found]))
        tied = found & (signed >= target * (1 - TIE))
    index = int(np.flatnonzero(tied)[np.argmin(distance[tied])])
    return float(values[index]), float(distance[index])


def _utilization(value: float, limit: float, *, smallest: bool) -> tuple[float, Any]:
    """Return a check's utilization and whether it passes (decision 4)."""
    if math.isnan(limit):
        return math.nan, pd.NA
    if math.isnan(value):
        return math.nan, True
    utilization = limit / value if smallest else abs(value) / limit
    return utilization, bool(utilization <= 1)
