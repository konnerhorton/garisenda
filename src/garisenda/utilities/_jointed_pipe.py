"""Joint and barrel checks for a jointed pipe."""

import math
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from garisenda._inputs import InputRecord, Sourced, judgments, preset_caveats, record
from garisenda._result import CHECK_COLUMNS, CHECK_TYPES, Result
from garisenda._units import units
from garisenda.profile._movement_profile import MERGE_TOLERANCE
from garisenda.sources._critical import find_zeros
from garisenda.sources._movement import MethodRecord, Source
from garisenda.sources._transverse_trough import (
    CRITICAL_DISTANCE_SAMPLING,
    CRITICAL_DISTANCE_TOLERANCE,
)
from garisenda.utilities._continuous_pipe import (
    ASSUMPTIONS as BARREL_ASSUMPTIONS,
)
from garisenda.utilities._continuous_pipe import (
    METHOD as BARREL_METHOD,
)
from garisenda.utilities._continuous_pipe import (
    FloatArray,
    _barrel,
    _interval_assumption,
    _read_interaction,
    _read_limit,
    _read_limits,
    _read_profile,
    _unlimited_assumption,
    _utilization,
    along_line,
    extreme,
)
from garisenda.utilities._utility import Utility

METHOD = MethodRecord(
    "Joint rotation and opening for a jointed pipe",
    (
        "rigid pipes of length L whose joints follow the ground; every position "
        "s is a possible joint",
        "joint rotation in each plane: theta_v(s) = (w(s + L) - 2 w(s) + "
        "w(s - L)) / L = L kappa_v,d, and theta_l likewise from u_l",
        "joint rotation: theta = sqrt(theta_v^2 + theta_l^2)",
        "joint opening: Delta(s) = u_a(s + L/2) - u_a(s - L/2) = L eps_a,d, "
        "positive opening",
        "outer opening: Delta + r theta, r = D / 2 (reported, not checked)",
        "worst joint: the largest theta and the largest positive Delta over s",
        "the barrel: the continuous-pipe check with interval h = L",
    ),
    "Geometry, derived by garisenda, not cited (gs.check_jointed_pipe's "
    "docstring states it); individual joints as Bracegirdle et al. (1996), p. "
    "661 allow; rigid joints for strain, p. 663.",
)

JOINT_UNITS = {
    "joint_vertical_rotation": "rad",
    "joint_lateral_rotation": "rad",
    "joint_rotation": "rad",
    "joint_opening": "m",
    "joint_outer_opening": "m",
}

JOINT_ASSUMPTIONS = (
    "The pipe is a chain of rigid pipes of length L whose joints are points on "
    "its axis that follow the ground, so the joints take all of the ground's "
    "bending and stretch into their rotation and opening. Every position along "
    "the pipe is taken as a possible joint, and the worst is reported (given "
    "joint locations aren't supported yet).",
    "The barrel is checked as a continuous pipe with rigid joints, following "
    "the ground (Bracegirdle et al. 1996, p. 663): it takes all of the ground's "
    "bending and stretch into its strain. Each idealization is conservative for "
    "its own quantity.",
    "Slopes are small: a joint's rotation is the difference of the two chords' "
    "slopes, without tan^-1, and the change in chord length from the along "
    "movement is dropped.",
    "The joint opening is checked at the pipe's axis. The outer opening, "
    "Delta + r theta, and the closure (the most negative opening) are reported "
    "but not checked: Table 2 of Bracegirdle et al. (1996) limits rotation and "
    "pull-out separately, and gives no limit for closure.",
)


@judgments(
    pipe_lengths="it depends on the pipe's type and size and on who made it. "
    "Pass a mapping {(pipe_type, outside_diameter): length}, e.g. "
    '{("spun_grey_iron", 0.3 * gs.units.m): 4 * gs.units.m}, or a gs.Sourced '
    "holding one.",
    pipe_type="which type an old main is (pit cast or spun, say) is often the "
    'engineer\'s call. Pass the pipe_lengths key, e.g. pipe_type="spun_grey_iron".',
    interaction="it says how the pipe interacts with the ground. Phase 1 takes "
    'only interaction="greenfield": the pipe follows the ground.',
    joint_rotation_limit="it depends on the joint and the main's condition. Pass "
    "an angle, e.g. 1.5 * gs.units.degree, a preset such as "
    'gs.presets.cast_iron_joint_limits(joint="lead_yarn_water_main").rotation, '
    "or None for no limit.",
    joint_pullout_limit="it depends on the joint and the main's condition. Pass "
    "a length, e.g. 15 * gs.units.mm, a preset such as "
    'gs.presets.cast_iron_joint_limits(joint="lead_yarn_water_main").pullout, '
    "or None for no limit.",
    tensile_strain_limit="it depends on the pipe's material and its condition. "
    'Pass a strain, e.g. gs.presets.iron_strain_limits(material="grey_iron")'
    ".tensile, or None for no limit.",
    compressive_strain_limit="it depends on the pipe's material and its "
    'condition. Pass a strain, e.g. gs.presets.iron_strain_limits(material="'
    'grey_iron").compressive, or None for no limit.',
    bending_strain_limit="it depends on the pipe's material; where none is given "
    "separately, pass the tensile limit, or None for no limit.",
    radius_of_curvature_limit="it depends on the pipe's material and joints. "
    "Pass a length, e.g. 500 * gs.units.m, or None for no limit.",
)
def check_jointed_pipe(
    profile: Result,
    *,
    pipe_lengths: object,
    pipe_type: object,
    interaction: object,
    joint_rotation_limit: object,
    joint_pullout_limit: object,
    tensile_strain_limit: object,
    compressive_strain_limit: object,
    bending_strain_limit: object,
    radius_of_curvature_limit: object,
) -> Result:
    """Check a jointed pipe's joints and barrel against the movement profile.

    A jointed pipe (cast iron, ductile iron, clay, concrete) is a chain of
    pipes of length L joined end to end. With s the distance along the line,
    u_a, w and u_l its displacement along, vertical (positive down) and
    lateral, and r = D / 2 its outside radius, the geometry is (derived
    here, not cited):

    1. **The idealization.** Each pipe is rigid, and each joint is a point on
       the axis that moves with the ground, so a pipe is the chord between
       its two joints' displaced positions. For the barrel's strains the
       joints are taken as rigid and the barrel follows the ground
       (Bracegirdle et al. 1996, p. 663). Each idealization is conservative
       for its own quantity.
    2. **Joint rotation.** The angle between the two chords meeting at a
       joint at s, with neighbors at s - L and s + L, to first order in the
       slopes: theta_v(s) = (w(s + L) - 2 w(s) + w(s - L)) / L, and theta_l
       likewise from u_l, signed as the curvatures (positive hogging). The
       rotation of a circular spigot in its socket is the resultant
       theta = sqrt(theta_v^2 + theta_l^2), which is checked. This is the
       continuous check's discrete curvature at interval L, times L.
    3. **Joint opening (pullout).** Each pipe moves along the line with the
       ground's along movement at its midpoint, so the joint at s opens by
       Delta(s) = u_a(s + L/2) - u_a(s - L/2), positive opening: the discrete
       axial strain at interval L, times L. The openings along a run sum to
       the ground's stretch between its end midpoints, no more.
    4. **The outer opening.** A joint rotating by theta opens by r theta on
       one side, so the largest opening around it is Delta + r theta. It is
       reported, not checked: Table 2 limits rotation and pull-out
       separately.
    5. **Every position is a possible joint.** theta(s) and Delta(s) are
       what a joint at s would have, and the worst joint is their peak over
       s, found exactly by root-finding on the source's derivatives at the
       shifted points (as the continuous check finds its peaks), with rows
       added at the peaks and at the ends of each feasible range. A joint
       needs both neighbors on the pipe: s in [L, l - L] for rotation and
       [L/2, l - L/2] for the opening, l the pipe's length.

    Bracegirdle et al. (1996, p. 661) give individual joints as the primary
    method; their Eq. 5 for rotation and the maximum horizontal movement for
    pull-out are conservative shortcuts, not used (the Jointed pipes guide, "Why not
    Eq. 5", says why).

    The barrel is checked exactly as `garisenda.check_continuous_pipe` checks
    it with ``interval=L`` (a jointed pipe's discrete interval is its pipe
    length), over every row of this result. The joint columns are
    that check's discrete columns times L, so the two can't disagree.

    Parameters
    ----------
    profile : Result
        A movement profile from `garisenda.movement_profile`.
    pipe_lengths : mapping or Sourced
        The pipe length table, ``{(pipe_type, outside_diameter): length}``,
        or a `garisenda.Sourced` holding one, whose source is recorded.
        Diameters and lengths are lengths, in m if plain numbers. The
        utility's outside diameter is looked up under `pipe_type`, matched
        within 1 um; a nominal size isn't matched to an outside diameter,
        and nothing is taken from the nearest diameter. A design judgment
        with no default; garisenda ships no pipe length preset.
    pipe_type : str
        The pipe's type, the table's first key. A design judgment with no
        default.
    interaction : {"greenfield"}
        The soil-structure interaction. Phase 1 takes only ``"greenfield"``.
    joint_rotation_limit : angle or None
        The largest joint rotation allowed. A pint quantity only (a plain
        number is refused); zero allows none, ``None`` means no limit. See
        `garisenda.presets.cast_iron_joint_limits`.
    joint_pullout_limit : length or None
        The largest joint opening allowed, in m if a plain number; zero
        allows none, ``None`` means no limit.
    tensile_strain_limit, compressive_strain_limit : strain or None
        As for `garisenda.check_continuous_pipe`. See
        `garisenda.presets.iron_strain_limits`.
    bending_strain_limit : strain or None
        As for `garisenda.check_continuous_pipe`. Table 4 gives none: pass the
        tensile limit or ``None``. See
        `garisenda.presets.iron_strain_limits`.
    radius_of_curvature_limit : length or None
        As for `garisenda.check_continuous_pipe`.

    Returns
    -------
    Result
        ``analysis`` is ``"jointed_pipe_check"`` and ``subject`` the utility's
        id. ``values`` has every column of `garisenda.check_continuous_pipe`
        at h = L, and:

        - ``joint_vertical_rotation``, ``joint_lateral_rotation`` (rad):
          theta_v and theta_l, signed as the curvatures;
        - ``joint_rotation`` (rad): theta;
        - ``joint_opening`` (m): Delta, positive opening;
        - ``joint_outer_opening`` (m): Delta + r theta.

        They are NaN within L (rotation) or L/2 (opening) of an end, under
        the ``"within"`` flag. ``checks`` has the continuous check's six
        rows, then ``joint_rotation`` (the largest theta, unit rad) and
        ``joint_pullout`` (the largest positive Delta, unit m), with only
        their ``discrete`` fields: ``governed_by`` is ``"discrete"``. A pipe
        too short for any joint (l < 2L for rotation, l < L for the
        opening) has that check's value NaN and ``passes`` NA; where
        positions exist but none opens, the pullout is NaN and passes. The
        inputs record ``pipe_type``, ``pipe_length`` (from the table, with
        its source), ``interaction`` and the six limits, and the
        assumptions add every preset's caveats.

    Raises
    ------
    TypeError
        If a judgment is missing, `profile` isn't a movement profile, a
        strain or rotation limit is a plain number, or `pipe_lengths` isn't
        a mapping of (type, diameter) pairs.
    ValueError
        If `pipe_type` is empty or not in the table, the utility's diameter
        isn't in the table under it, a table length isn't positive, a limit
        is negative, or `interaction` isn't ``"greenfield"``.

    Notes
    -----
    Sources: the geometry is derived here, not cited; individual joints
    as Bracegirdle et al. (1996), p. 661 allow; rigid joints for the
    barrel's strain, p. 663.
    """
    utility, source = _read_profile(profile, "check_jointed_pipe")
    type_name, type_record = _read_pipe_type(pipe_type)
    length, length_record = _pipe_length(pipe_lengths, type_name, utility)
    interaction_record = _read_interaction(interaction)
    rotation_limit, rotation_record = _read_limit(
        "joint_rotation_limit",
        joint_rotation_limit,
        unit="radian",
        plain_number="refuse",
    )
    pullout_limit, pullout_record = _read_limit(
        "joint_pullout_limit",
        joint_pullout_limit,
        unit="m",
        plain_number="read as SI",
    )
    limits, limit_records = _read_limits(
        tensile_strain_limit=tensile_strain_limit,
        compressive_strain_limit=compressive_strain_limit,
        bending_strain_limit=bending_strain_limit,
        radius_of_curvature_limit=radius_of_curvature_limit,
    )
    pipe = _length(utility)
    values, flags, validity, checks = _barrel(
        profile,
        utility,
        source,
        length,
        limits,
        extra_peaks=_joint_peaks(utility, source, length),
        ends_reason=_ends_reason(pipe, length),
    )
    values = _with_joints(values, length, utility.diameter / 2)
    checks = pd.concat(
        [
            checks,
            _joint_checks(
                values,
                rotation_limit,
                pullout_limit,
                rotation_determined=pipe >= 2 * length - MERGE_TOLERANCE,
                pullout_determined=pipe >= length - MERGE_TOLERANCE,
            ),
        ],
        ignore_index=True,
    ).astype(CHECK_TYPES)

    assumptions = [
        *BARREL_ASSUMPTIONS,
        _interval_assumption(length, f"the pipe length L = {length:g} m"),
        *JOINT_ASSUMPTIONS,
        *_unlimited_assumption(
            {
                "joint_rotation_limit": rotation_limit,
                "joint_pullout_limit": pullout_limit,
                **limits,
            }
        ),
        *preset_caveats(
            pipe_lengths,
            pipe_type,
            interaction,
            joint_rotation_limit,
            joint_pullout_limit,
            tensile_strain_limit,
            compressive_strain_limit,
            bending_strain_limit,
            radius_of_curvature_limit,
        ),
    ]
    return Result(
        analysis="jointed_pipe_check",
        subject=utility.utility_id,
        values=values,
        checks=checks,
        method=(*profile.method, BARREL_METHOD, METHOD),
        assumptions=(*profile.assumptions, *assumptions),
        inputs=(
            *profile.inputs,
            type_record,
            length_record,
            interaction_record,
            rotation_record,
            pullout_record,
            *limit_records,
        ),
        validity=validity,
        warnings=flags,
        source=source,
        asset=utility,
    )


def _length(utility: Utility) -> float:
    start, end = (np.asarray(vertex, dtype=np.float64) for vertex in utility.vertices)
    return float(np.linalg.norm(end - start))


def _read_pipe_type(pipe_type: object) -> tuple[str, InputRecord]:
    """Return the pipe type and its record, or raise for an empty one."""
    source = None
    if isinstance(pipe_type, Sourced):
        source = pipe_type.source
        pipe_type = pipe_type.value
    if not isinstance(pipe_type, str):
        raise TypeError(
            f"pipe_type must be a string, not {type(pipe_type).__name__} "
            f"({pipe_type!r})."
        )
    if not pipe_type.strip():
        raise ValueError("pipe_type must be a non-empty string, the pipe_lengths key.")
    return pipe_type, InputRecord(
        "pipe_type", pipe_type, "design judgment", "name", source
    )


def _pipe_length(
    table: object, pipe_type: str, utility: Utility
) -> tuple[float, InputRecord]:
    """Look up the pipe length for the utility's diameter."""
    source = None
    if isinstance(table, Sourced):
        source = table.source
        table = table.value
    if not isinstance(table, Mapping):
        raise TypeError(
            "pipe_lengths must be a mapping {(pipe_type, outside_diameter): "
            f"length}}, not {type(table).__name__}."
        )
    rows: dict[str, list[tuple[float, float]]] = {}
    for key, value in table.items():
        if not (isinstance(key, tuple) and len(key) == 2 and isinstance(key[0], str)):
            raise TypeError(
                "pipe_lengths keys must be (pipe_type, outside_diameter) pairs, "
                f"not {key!r}."
            )
        name, diameter = key
        diameter_m = float(
            record(
                f"pipe_lengths[{key!r}] diameter",
                diameter,
                kind="design judgment",
                unit="m",
                plain_number="read as SI",
            )[0]
        )
        length = float(
            record(
                f"pipe_lengths[{key!r}]",
                value,
                kind="design judgment",
                unit="m",
                plain_number="read as SI",
            )[0]
        )
        if not (math.isfinite(length) and length > 0):
            raise ValueError(
                f"pipe_lengths[({name!r}, {diameter_m:g} m)] must be a positive "
                f"length, not {length:g} m."
            )
        rows.setdefault(name, []).append((diameter_m, length))
    if pipe_type not in rows:
        types = ", ".join(repr(name) for name in rows) or "none"
        raise ValueError(
            f"pipe_lengths has no pipe type {pipe_type!r}; its types are {types}."
        )
    diameter = utility.diameter
    for diameter_m, length in rows[pipe_type]:
        if abs(diameter_m - diameter) <= MERGE_TOLERANCE:
            return length, InputRecord(
                "pipe_length",
                length * units.m,
                "design judgment",
                f"from pipe_lengths, ({pipe_type}, {diameter_m:g} m)",
                source,
            )
    diameters = ", ".join(f"{d:g}" for d, _ in sorted(rows[pipe_type]))
    raise ValueError(
        f"pipe_lengths has no ({pipe_type!r}, {diameter:g} m), the outside "
        f"diameter of utility {utility.utility_id!r}; its diameters for "
        f"{pipe_type!r} are {diameters} m. A nominal size isn't matched to an "
        "outside diameter, and nothing is taken from the nearest diameter "
        "(the diameter is the pipe's outside diameter)."
    )


def _joint_peaks(utility: Utility, source: Source, length: float) -> FloatArray:
    """Return where theta and Delta peak, and the feasible ranges' ends.

    The zeros of d(theta^2)/ds over s in [L, l - L] and of dDelta/ds over
    [L/2, l - L/2], found by `find_zeros` on the source's exact derivatives
    at the shifted points, with the sampling and tolerance of the source's
    critical distances. The ends of each range are added too, since a peak
    can sit where the function is still rising.
    """
    line = along_line(utility, source)
    pipe, feature = line.length, line.feature
    _, vertical, lateral = line.directions
    step = CRITICAL_DISTANCE_SAMPLING * feature
    tolerance = CRITICAL_DISTANCE_TOLERANCE

    def shifted(distance: FloatArray, offsets: tuple[float, ...]) -> list[Any]:
        """Return the derivatives and displacements at each offset of `distance`."""
        points = np.concatenate([distance + offset for offset in offsets])
        derivatives, displacement = line.derivatives(np.clip(points, 0.0, pipe))
        n = distance.size
        return [
            (derivatives[k * n : (k + 1) * n], displacement[k * n : (k + 1) * n])
            for k in range(len(offsets))
        ]

    def rotation_gradient(t: FloatArray) -> FloatArray:
        """theta_v theta_v' + theta_l theta_l' at s = L + t, shape (N, 1)."""
        (d0, u0), (d1, u1), (d2, u2) = shifted(length + t, (-length, 0.0, length))
        total = np.zeros(t.size)
        for index, direction in ((1, vertical), (2, lateral)):
            theta = (u2 @ direction - 2 * (u1 @ direction) + u0 @ direction) / length
            gradient = (
                d2[:, 0, index] - 2 * d1[:, 0, index] + d0[:, 0, index]
            ) / length
            total = total + theta * gradient
        result: FloatArray = total[:, None]
        return result

    def opening_gradient(t: FloatArray) -> FloatArray:
        """dDelta/ds = eps_a(s + L/2) - eps_a(s - L/2) at s = L/2 + t."""
        (d0, _), (d1, _) = shifted(length / 2 + t, (-length / 2, length / 2))
        result: FloatArray = (d1[:, 0, 0] - d0[:, 0, 0])[:, None]
        return result

    # Each function's scale, as the continuous check sets it: the largest
    # sampled value, or what the largest displacement U gives with the
    # feature length f, whichever is larger. A joint's rotation is about
    # U min(L / f^2, 1 / L) and its opening U min(L / f, 1).
    found: list[FloatArray] = []
    rotation_size = min(length / feature**2, 1 / length)
    opening_size = min(length / feature, 1.0)
    for start, span, function, size in (
        (length, pipe - 2 * length, rotation_gradient, rotation_size),
        (length / 2, pipe - length, opening_gradient, opening_size),
    ):
        if span < -MERGE_TOLERANCE:
            continue
        span = max(span, 0.0)
        found.append(np.array([start, start + span]))
        if span <= tolerance:
            continue
        samples = np.linspace(0.0, span, max(math.ceil(span / step), 1) + 1)
        sampled = function(samples)
        largest = float(
            np.max(np.linalg.norm(line.derivatives(samples + start)[1], axis=1))
        )
        scale = largest * size
        floor = scale**2 / feature if function is rotation_gradient else scale / feature
        scales = np.maximum(np.max(np.abs(sampled), axis=0), [floor])
        zeros = find_zeros(
            function, length=span, step=step, tolerance=tolerance, scales=scales
        )
        found.append(start + zeros)
    if not found:
        return np.empty(0)
    return np.concatenate(found)


def _ends_reason(pipe: float, length: float) -> str:
    """Return the ends flag's sentence on the joints."""
    reason = (
        f"So no joint rotation within L = {length:g} m of an end and no joint "
        f"opening within L/2 = {length / 2:g} m: a joint there would have a "
        "neighbor beyond the pipe."
    )
    if pipe < length - MERGE_TOLERANCE:
        reason += (
            f" The pipe, {pipe:g} m long, is shorter than L, so no position has "
            "a joint rotation or opening: both joint checks are not determined."
        )
    elif pipe < 2 * length - MERGE_TOLERANCE:
        reason += (
            f" The pipe, {pipe:g} m long, is shorter than 2L = {2 * length:g} m, "
            "so no position has a joint rotation: that check is not determined."
        )
    return reason


def _with_joints(values: pd.DataFrame, length: float, radius: float) -> pd.DataFrame:
    """Add the joint columns, L times the discrete ones."""
    vertical = length * values["discrete_vertical_curvature"].to_numpy(dtype=np.float64)
    lateral = length * values["discrete_lateral_curvature"].to_numpy(dtype=np.float64)
    rotation = np.hypot(vertical, lateral)
    opening = length * values["discrete_axial_strain"].to_numpy(dtype=np.float64)
    columns = {
        "joint_vertical_rotation": vertical,
        "joint_lateral_rotation": lateral,
        "joint_rotation": rotation,
        "joint_opening": opening,
        "joint_outer_opening": opening + radius * rotation,
    }
    units = dict(values.attrs["units"])
    result = values.assign(**columns)
    result.attrs["units"] = units | JOINT_UNITS
    return result


def _joint_checks(
    values: pd.DataFrame,
    rotation_limit: float,
    pullout_limit: float,
    *,
    rotation_determined: bool,
    pullout_determined: bool,
) -> pd.DataFrame:
    """Return the two joint checks."""
    distance = values["distance"].to_numpy(dtype=np.float64)
    rows: list[dict[str, Any]] = []
    for name, column, unit, limit, determined in (
        (
            "joint_rotation",
            "joint_rotation",
            "rad",
            rotation_limit,
            rotation_determined,
        ),
        ("joint_pullout", "joint_opening", "m", pullout_limit, pullout_determined),
    ):
        column_values: FloatArray = values[column].to_numpy(dtype=np.float64)
        value, at = extreme(column_values, distance, 1)
        utilization, passes = _utilization(
            value, limit, smallest=False, determined=determined
        )
        rows.append(
            {
                "check": name,
                "value": value,
                "unit": unit,
                "limit": limit,
                "utilization": utilization,
                "governing_distance": at,
                "passes": passes,
                "governed_by": "discrete",
                "analytical": math.nan,
                "analytical_distance": math.nan,
                "discrete": value,
                "discrete_distance": at,
                "difference": math.nan,
            }
        )
    return pd.DataFrame(rows, columns=list(CHECK_COLUMNS)).astype(CHECK_TYPES)
