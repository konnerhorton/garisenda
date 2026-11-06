"""Tests for gs.check_jointed_pipe against the M3 (b) spec's acceptance criteria."""

import math

import numpy as np
import pandas as pd
import pytest

import garisenda as gs

u = gs.units

EXACT = 1e-9  # closed forms evaluated exactly (spec, Tolerance)
PRINTED = 2e-5  # the spec's printed values, rounded to five or six figures
DISTANCE = 1e-6  # m, governing distances (spec, Tolerance)

# Cases J-A, J-B and J-C (spec, Hand calculations), on M3 (a)'s cases.
WIDTH = 9.0
DEPTH_BELOW_AXIS = 18.0
S_MAX = 0.01 * math.pi * 6.0**2 / 4 / (math.sqrt(2 * math.pi) * WIDTH)
RADIUS = 0.15
OBLIQUE = math.radians(45)

NO_LIMITS = {
    "joint_rotation_limit": None,
    "joint_pullout_limit": None,
    "tensile_strain_limit": None,
    "compressive_strain_limit": None,
    "bending_strain_limit": None,
    "radius_of_curvature_limit": None,
}

STRAIN_LIMIT = u.Quantity(1000, "µε")
BARREL_LIMITS = {
    "tensile_strain_limit": STRAIN_LIMIT,
    "compressive_strain_limit": STRAIN_LIMIT,
    "bending_strain_limit": STRAIN_LIMIT,
    "radius_of_curvature_limit": 1000 * u.m,
}


def tunnel():
    return gs.sources.IdealizedTunnel(
        reference_point=(0, 0), azimuth=0 * u.degree, diameter=6.0, axis_depth=20.0
    )


def trough():
    return gs.sources.transverse_trough(
        tunnel(),
        volume_loss=1 * u.percent,
        trough_width=gs.sources.linear_trough_width(trough_width_parameter=0.5),
    )


def perpendicular_pipe(start_offset=-40.0, end_offset=40.0, diameter=0.3):
    return gs.utilities.perpendicular_utility(
        tunnel(),
        utility_id="A",
        station=0,
        start_offset=start_offset,
        end_offset=end_offset,
        depth=2.0,
        elevation_reference="axis",
        diameter=diameter,
    )


def oblique_pipe(reverse=False):
    s, c = math.sin(OBLIQUE), math.cos(OBLIQUE)
    vertices = [(-40 * s, -40 * c, 2.0), (40 * s, 40 * c, 2.0)]
    if reverse:
        vertices.reverse()
    return gs.utilities.Utility(utility_id="C", vertices=vertices, diameter=0.3)


def profile_of(pipe, source=None, spacing=1.0):
    return gs.movement_profile(pipe, source or trough(), spacing=spacing)


def arguments(length=4.0, **changes):
    given = {
        "pipe_lengths": {("spun_grey_iron", 0.3): length},
        "pipe_type": "spun_grey_iron",
        "interaction": "greenfield",
        **NO_LIMITS,
    }
    given.update(changes)
    return given


def check(pipe, length=4.0, source=None, **changes):
    return gs.check_jointed_pipe(
        profile_of(pipe, source), **arguments(length=length, **changes)
    )


@pytest.fixture(scope="module")
def case_ja():
    return check(perpendicular_pipe(), 4.0)


@pytest.fixture(scope="module")
def case_jb():
    return check(perpendicular_pipe(), 9.0)


@pytest.fixture(scope="module")
def case_jc():
    return check(oblique_pipe(), 4.0)


@pytest.fixture(scope="module")
def profile():
    return profile_of(perpendicular_pipe())


# The closed forms (spec, Hand calculations): the settlement w and the
# horizontal movement toward the axis u_n at offset o.


def settlement(offset):
    return S_MAX * math.exp(-(offset**2) / (2 * WIDTH**2))


def toward_axis(offset):
    return -(offset / DEPTH_BELOW_AXIS) * settlement(offset)


def closed_form(distance, length, angle=math.pi / 2):
    """Return theta_v, theta_l and Delta at a distance along the pipe."""

    def offset(s):
        return (s - 40.0) * math.sin(angle)

    def second(function, s):
        return (
            function(offset(s + length))
            - 2 * function(offset(s))
            + function(offset(s - length))
        ) / length

    vertical = second(settlement, distance)
    lateral = math.cos(angle) * second(toward_axis, distance)
    opening = math.sin(angle) * (
        toward_axis(offset(distance + length / 2))
        - toward_axis(offset(distance - length / 2))
    )
    return vertical, lateral, opening


def row_at(result, distance, tolerance=1e-6):
    values = result.values
    index = int(np.argmin(np.abs(values["distance"].to_numpy() - distance)))
    assert values["distance"].iloc[index] == pytest.approx(distance, abs=tolerance)
    return values.iloc[index]


def check_row(result, name):
    return result.checks.set_index("check").loc[name]


# AC 1: case J-A at the center joint


def test_case_ja_at_the_center(case_ja):
    row = row_at(case_ja, 40.0)
    vertical, _, opening = closed_form(40.0, 4.0)
    assert row["joint_vertical_rotation"] == pytest.approx(vertical, rel=EXACT)
    assert row["joint_lateral_rotation"] == 0.0
    assert row["joint_rotation"] == pytest.approx(-vertical, rel=EXACT)
    assert row["joint_opening"] == pytest.approx(opening, rel=EXACT)
    # The spec's printed values and their center closed forms.
    assert vertical == pytest.approx(
        -2 * S_MAX * (1 - math.exp(-(4.0**2) / (2 * WIDTH**2))) / 4.0, rel=EXACT
    )
    assert vertical == pytest.approx(-5.89338e-4, rel=PRINTED)
    assert math.degrees(vertical) == pytest.approx(-0.033767, rel=PRINTED)
    assert opening == pytest.approx(
        -(4.0 / DEPTH_BELOW_AXIS) * S_MAX * math.exp(-(4.0**2) / (8 * WIDTH**2)),
        rel=EXACT,
    )
    assert opening == pytest.approx(-2.71722e-3, rel=PRINTED)


def test_case_ja_outer_opening(case_ja):
    values = case_ja.values
    expected = values["joint_opening"] + RADIUS * values["joint_rotation"]
    pd.testing.assert_series_equal(
        values["joint_outer_opening"], expected, check_names=False
    )


def test_case_ja_lateral_rotation_is_exactly_zero(case_ja):
    lateral = case_ja.values["joint_lateral_rotation"].dropna()
    assert (lateral == 0.0).all()


# AC 2: case J-B, and the joint columns are L times the discrete ones


def test_case_jb_at_the_center(case_jb):
    row = row_at(case_jb, 40.0)
    vertical, _, opening = closed_form(40.0, 9.0)
    assert row["joint_vertical_rotation"] == pytest.approx(vertical, rel=EXACT)
    assert row["joint_opening"] == pytest.approx(opening, rel=EXACT)
    assert vertical == pytest.approx(-1.09587e-3, rel=PRINTED)
    assert opening == pytest.approx(-5.53023e-3, rel=PRINTED)
    assert vertical / 9.0 == pytest.approx(-1.21763e-4, rel=PRINTED)
    assert opening / 9.0 == pytest.approx(-614.47e-6, rel=PRINTED)


def test_case_jb_barrel_is_case_b_at_h_9(case_jb):
    continuous = gs.check_continuous_pipe(
        profile_of(perpendicular_pipe()),
        interval=9.0,
        interaction="greenfield",
        **BARREL_LIMITS,
    ).values.set_index("distance")
    jointed = case_jb.values.set_index("distance")
    shared = continuous.index.intersection(jointed.index)
    assert len(shared) == len(continuous)
    for column in continuous.columns:
        if column.startswith("discrete_"):
            np.testing.assert_allclose(
                jointed.loc[shared, column],
                continuous.loc[shared, column],
                rtol=EXACT,
                atol=0,
            )


@pytest.mark.parametrize("fixture", ["case_ja", "case_jb", "case_jc"])
def test_joint_columns_are_l_times_the_discrete_ones(fixture, request):
    result = request.getfixturevalue(fixture)
    length = 9.0 if fixture == "case_jb" else 4.0
    values = result.values
    for joint, discrete in (
        ("joint_vertical_rotation", "discrete_vertical_curvature"),
        ("joint_lateral_rotation", "discrete_lateral_curvature"),
        ("joint_opening", "discrete_axial_strain"),
    ):
        np.testing.assert_allclose(
            values[joint], length * values[discrete], rtol=1e-12, atol=0
        )


# AC 3: case J-C, oblique


def test_case_jc_off_the_crossing(case_jc):
    row = row_at(case_jc, 49.44365, tolerance=1e-5)
    vertical, lateral, opening = closed_form(row["distance"], 4.0, OBLIQUE)
    assert row["joint_vertical_rotation"] == pytest.approx(vertical, rel=EXACT)
    assert row["joint_lateral_rotation"] == pytest.approx(lateral, rel=EXACT)
    assert row["joint_rotation"] == pytest.approx(math.hypot(vertical, lateral))
    assert row["joint_opening"] == pytest.approx(opening, rel=EXACT)
    assert row["joint_vertical_rotation"] == pytest.approx(-1.05596e-4, rel=PRINTED)
    assert row["joint_lateral_rotation"] == pytest.approx(1.46117e-4, rel=PRINTED)
    assert row["joint_rotation"] == pytest.approx(1.80279e-4, rel=PRINTED)
    assert row["joint_opening"] == pytest.approx(-0.475302e-3, rel=PRINTED)


def test_case_jc_at_the_crossing(case_jc):
    row = row_at(case_jc, 40.0)
    vertical, _, opening = closed_form(40.0, 4.0, OBLIQUE)
    assert row["joint_vertical_rotation"] == pytest.approx(vertical, rel=EXACT)
    assert row["joint_lateral_rotation"] == pytest.approx(0.0, abs=1e-18)
    assert row["joint_opening"] == pytest.approx(opening, rel=EXACT)
    assert vertical == pytest.approx(-3.01944e-4, rel=PRINTED)
    assert opening == pytest.approx(-1.37548e-3, rel=PRINTED)


# AC 4: the barrel is M3 (a)'s, over more rows


def test_the_barrel_is_the_continuous_check():
    pipe = perpendicular_pipe()
    continuous = gs.check_continuous_pipe(
        profile_of(pipe), interval=4.0, interaction="greenfield", **BARREL_LIMITS
    )
    jointed = check(pipe, 4.0, **BARREL_LIMITS)
    six = continuous.checks.set_index("check")
    barrel = jointed.checks.set_index("check").loc[six.index]
    for field in ("analytical", "analytical_distance"):
        np.testing.assert_array_equal(barrel[field], six[field])
    for name in six.index:
        if name == "radius_of_curvature":
            assert barrel.loc[name, "discrete"] <= six.loc[name, "discrete"]
        else:
            assert abs(barrel.loc[name, "discrete"]) >= abs(six.loc[name, "discrete"])
    by_distance = jointed.values.set_index("distance")
    reference = continuous.values.set_index("distance")
    shared = reference.index.intersection(by_distance.index)
    assert len(shared) == len(reference)
    for column in reference.columns:
        if column.startswith("discrete_"):
            np.testing.assert_array_equal(
                by_distance.loc[shared, column], reference.loc[shared, column]
            )


# AC 8: the pipe length table


def test_a_table_in_inches_matches_a_diameter_in_m(profile):
    diameter = (0.3 * u.m).to("inch")
    result = gs.check_jointed_pipe(
        profile,
        **arguments(pipe_lengths={("spun_grey_iron", diameter): 13.123 * u.ft}),
    )
    entry = next(e for e in result.inputs if e.name == "pipe_length")
    assert entry.value.magnitude == pytest.approx(13.123 * 0.3048)
    assert entry.given_as == "from pipe_lengths, (spun_grey_iron, 0.3 m)"
    assert entry.kind == "design judgment"


def test_a_missing_type_lists_the_types(profile):
    table = {("spun_grey_iron", 0.3): 4.0, ("ductile_iron", 0.3): 5.5}
    with pytest.raises(ValueError, match="no pipe type 'clay'") as error:
        gs.check_jointed_pipe(
            profile, **arguments(pipe_lengths=table, pipe_type="clay")
        )
    assert "'spun_grey_iron', 'ductile_iron'" in str(error.value)


def test_a_missing_diameter_lists_the_diameters(profile):
    table = {("spun_grey_iron", 0.25): 4.0, ("spun_grey_iron", 0.35): 4.0}
    with pytest.raises(ValueError, match=r"no \('spun_grey_iron', 0.3 m\)") as error:
        gs.check_jointed_pipe(profile, **arguments(pipe_lengths=table))
    message = str(error.value)
    assert "0.25, 0.35 m" in message
    assert "nominal size" in message
    assert "nearest diameter" in message


@pytest.mark.parametrize("length", [0.0, -4.0, math.inf])
def test_a_non_positive_length_names_its_key(profile, length):
    table = {("spun_grey_iron", 0.3): length}
    key = r"pipe_lengths\[\('spun_grey_iron', 0.3 m\)\]"
    with pytest.raises(ValueError, match=key):
        gs.check_jointed_pipe(profile, **arguments(pipe_lengths=table))


def test_a_sourced_table_records_its_source(profile):
    table = gs.Sourced({("spun_grey_iron", 0.3): 4.0}, source="Utility records")
    result = gs.check_jointed_pipe(profile, **arguments(pipe_lengths=table))
    entry = next(e for e in result.inputs if e.name == "pipe_length")
    assert entry.source == "Utility records"
    assert entry.value == 4.0 * u.m


def test_a_table_that_isnt_a_mapping_is_refused(profile):
    with pytest.raises(TypeError, match="pipe_lengths must be a mapping"):
        gs.check_jointed_pipe(profile, **arguments(pipe_lengths=4.0))


# AC 9: limits


def test_joint_utilization_and_passes(case_ja):
    result = check(
        perpendicular_pipe(),
        4.0,
        joint_rotation_limit=0.03 * u.degree,
        joint_pullout_limit=2 * u.mm,
    )
    rotation = check_row(result, "joint_rotation")
    assert rotation["limit"] == pytest.approx(math.radians(0.03))
    assert rotation["utilization"] == pytest.approx(
        rotation["value"] / math.radians(0.03)
    )
    assert rotation["unit"] == "rad"
    assert not rotation["passes"]
    pullout = check_row(result, "joint_pullout")
    assert pullout["limit"] == pytest.approx(2e-3)
    assert pullout["utilization"] == pytest.approx(pullout["value"] / 2e-3)
    assert pullout["unit"] == "m"
    assert pullout["passes"]
    for row in (rotation, pullout):
        assert row["governed_by"] == "discrete"
        assert row["discrete"] == row["value"]
        assert row["discrete_distance"] == row["governing_distance"]
        assert math.isnan(row["analytical"])
        assert math.isnan(row["analytical_distance"])
        assert math.isnan(row["difference"])


def test_a_zero_joint_limit_fails_any_movement():
    result = check(
        perpendicular_pipe(),
        4.0,
        joint_rotation_limit=0 * u.degree,
        joint_pullout_limit=0 * u.mm,
    )
    for name in ("joint_rotation", "joint_pullout"):
        row = check_row(result, name)
        assert row["utilization"] == math.inf
        assert not row["passes"]


def test_no_joint_limit_gives_nan_and_na(case_ja):
    for name in ("joint_rotation", "joint_pullout"):
        row = check_row(case_ja, name)
        assert math.isnan(row["limit"])
        assert math.isnan(row["utilization"])
        assert row["passes"] is pd.NA
    assert any("joint_rotation_limit" in text for text in case_ja.assumptions)


@pytest.mark.parametrize(
    ("name", "value"),
    [("joint_rotation_limit", -1 * u.degree), ("joint_pullout_limit", -1 * u.mm)],
)
def test_a_negative_joint_limit_raises(profile, name, value):
    with pytest.raises(ValueError, match=f"{name} must be zero or positive"):
        gs.check_jointed_pipe(profile, **arguments(**{name: value}))


def test_a_plain_number_rotation_limit_is_refused(profile):
    with pytest.raises(TypeError, match="needs a pint quantity"):
        gs.check_jointed_pipe(profile, **arguments(joint_rotation_limit=0.01))


def test_a_plain_number_pullout_limit_is_read_in_m(profile):
    result = gs.check_jointed_pipe(profile, **arguments(joint_pullout_limit=0.015))
    assert check_row(result, "joint_pullout")["limit"] == pytest.approx(0.015)


# AC 10: judgments


JUDGMENTS = [
    "pipe_lengths",
    "pipe_type",
    "interaction",
    "joint_rotation_limit",
    "joint_pullout_limit",
    "tensile_strain_limit",
    "compressive_strain_limit",
    "bending_strain_limit",
    "radius_of_curvature_limit",
]


@pytest.mark.parametrize("name", JUDGMENTS)
def test_a_missing_judgment_names_it(profile, name):
    given = arguments()
    del given[name]
    with pytest.raises(TypeError, match=f"is missing {name}"):
        gs.check_jointed_pipe(profile, **given)


def test_the_profile_is_required():
    with pytest.raises(TypeError, match="check_jointed_pipe needs a movement profile"):
        gs.check_jointed_pipe(perpendicular_pipe(), **arguments())


@pytest.mark.parametrize("pipe_type", ["", "  "])
def test_an_empty_pipe_type_raises(profile, pipe_type):
    with pytest.raises(ValueError, match="pipe_type must be a non-empty string"):
        gs.check_jointed_pipe(profile, **arguments(pipe_type=pipe_type))


def test_every_judgment_is_recorded(profile):
    result = gs.check_jointed_pipe(
        profile,
        **arguments(
            pipe_type=gs.Sourced("spun_grey_iron", source="Survey"),
            joint_rotation_limit=1.5 * u.degree,
            joint_pullout_limit=15 * u.mm,
            **BARREL_LIMITS,
        ),
    )
    entries = {entry.name: entry for entry in result.inputs}
    for name in [
        "pipe_type",
        "pipe_length",
        "interaction",
        "joint_rotation_limit",
        "joint_pullout_limit",
        "tensile_strain_limit",
        "compressive_strain_limit",
        "bending_strain_limit",
        "radius_of_curvature_limit",
    ]:
        assert entries[name].kind == "design judgment"
    assert entries["pipe_type"].value == "spun_grey_iron"
    assert entries["pipe_type"].source == "Survey"
    assert entries["joint_rotation_limit"].value.to("degree").magnitude == (
        pytest.approx(1.5)
    )
    pullout = entries["joint_pullout_limit"].value
    assert pullout.to("m").magnitude == pytest.approx(0.015)
    assert result.analysis == "jointed_pipe_check"
    assert result.subject == "A"
    assert result.checks["check"].tolist() == [
        "axial_tension",
        "axial_compression",
        "bending",
        "tensile_strain",
        "compressive_strain",
        "radius_of_curvature",
        "joint_rotation",
        "joint_pullout",
    ]
