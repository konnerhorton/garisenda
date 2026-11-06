"""Tests for gs.check_continuous_pipe against the M3 (a) spec's acceptance criteria."""

import json
import math

import numpy as np
import pandas as pd
import pytest

import garisenda as gs
from garisenda.utilities._continuous_pipe import governing_value

u = gs.units
REL = 5e-3  # hand calculations (spec, cases A and C): 0.5 %, SPEC §2.4

# Case A (spec, hand calculations).
WIDTH = 9.0
S_MAX = 0.0125331
DEPTH_BELOW_AXIS = 18.0
ROOT3_I = math.sqrt(3) * WIDTH
RADIUS = 0.15

STRAIN_LIMIT = u.Quantity(1000, "µε")


def limits(**changes):
    given = {
        "tensile_strain_limit": STRAIN_LIMIT,
        "compressive_strain_limit": STRAIN_LIMIT,
        "bending_strain_limit": STRAIN_LIMIT,
        "radius_of_curvature_limit": 1000 * u.m,
    }
    given.update(changes)
    return given


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


def case_a_pipe():
    return gs.utilities.perpendicular_utility(
        tunnel(),
        utility_id="A",
        station=0,
        start_offset=-40,
        end_offset=40,
        depth=2.0,
        elevation_reference="axis",
        diameter=0.3,
    )


def case_c_pipe(reverse=False):
    s, c = math.sin(math.radians(45)), math.cos(math.radians(45))
    vertices = [(-40 * s, -40 * c, 2.0), (40 * s, 40 * c, 2.0)]
    if reverse:
        vertices.reverse()
    return gs.utilities.Utility(utility_id="C", vertices=vertices, diameter=0.3)


def check(pipe, source=None, *, spacing=1.0, interval=1.0, **changes):
    profile = gs.movement_profile(pipe, source or trough(), spacing=spacing)
    return gs.check_continuous_pipe(
        profile, interval=interval, interaction="greenfield", **limits(**changes)
    )


@pytest.fixture(scope="module")
def case_a():
    return check(case_a_pipe())


@pytest.fixture(scope="module")
def case_c():
    return check(case_c_pipe())


def row_at(result, distance, tolerance=1e-6):
    values = result.values
    index = int(np.argmin(np.abs(values["distance"].to_numpy() - distance)))
    assert values["distance"].iloc[index] == pytest.approx(distance, abs=tolerance)
    return values.iloc[index]


def check_row(result, name):
    return result.checks.set_index("check").loc[name]


# AC 1: case A, analytical


def test_case_a_at_the_center(case_a):
    row = row_at(case_a, 40.0)
    assert row["axial_strain"] == pytest.approx(-696.29e-6, rel=REL)
    assert row["vertical_curvature"] == pytest.approx(-1.54730e-4, rel=REL)
    assert row["bending_strain"] == pytest.approx(23.210e-6, rel=REL)
    assert row["tensile_strain"] == pytest.approx(23.210e-6, rel=REL)
    assert row["compressive_strain"] == pytest.approx(-719.50e-6, rel=REL)
    assert row["radius_of_curvature"] == pytest.approx(6462.9, rel=REL)


@pytest.mark.parametrize("distance", [40 - ROOT3_I, 40 + ROOT3_I])
def test_case_a_at_root3_i(case_a, distance):
    row = row_at(case_a, distance)
    assert row["axial_strain"] == pytest.approx(310.72e-6, rel=REL)
    assert row["vertical_curvature"] == pytest.approx(6.90499e-5, rel=REL)
    assert row["bending_strain"] == pytest.approx(10.357e-6, rel=REL)
    assert row["tensile_strain"] == pytest.approx(321.08e-6, rel=REL)


@pytest.mark.parametrize(
    ("name", "value", "distance"),
    [
        ("axial_tension", 310.72e-6, 40 - ROOT3_I),
        ("axial_compression", -696.29e-6, 40.0),
        ("bending", 23.210e-6, 40.0),
        ("tensile_strain", 321.08e-6, 40 - ROOT3_I),
        ("compressive_strain", -719.50e-6, 40.0),
        ("radius_of_curvature", 6462.9, 40.0),
    ],
)
def test_case_a_governing_analytical_values(case_a, name, value, distance):
    row = check_row(case_a, name)
    assert row["analytical"] == pytest.approx(value, rel=REL)
    assert row["analytical_distance"] == pytest.approx(distance, rel=REL)
    assert row["value"] == row["analytical"]
    assert row["governing_distance"] == row["analytical_distance"]


def test_case_a_has_no_lateral_bending(case_a):
    assert (case_a.values["lateral_curvature"] == 0).all()
    assert (case_a.values["lateral_bending_strain"] == 0).all()


def test_units_of_the_new_columns(case_a):
    units = case_a.values.attrs["units"]
    assert units["axial_strain"] == "dimensionless"
    assert units["resultant_curvature"] == "1/m"
    assert units["radius_of_curvature"] == "m"
    assert units["vertical_curvature"] == "1/m"
    assert list(case_a.checks["unit"]) == ["dimensionless"] * 5 + ["m"]


# AC 2: Bracegirdle et al. (1996), Eqs. 7-9 (p. 662), three figures


def test_bracegirdle_equations_7_to_9(case_a):
    assert abs(row_at(case_a, 40.0)["vertical_curvature"]) == pytest.approx(
        S_MAX / WIDTH**2, rel=REL
    )
    row = row_at(case_a, 40 + ROOT3_I)
    assert row["vertical_curvature"] == pytest.approx(0.446 * S_MAX / WIDTH**2, rel=REL)
    assert row["axial_strain"] == pytest.approx(
        0.446 * S_MAX / DEPTH_BELOW_AXIS, rel=REL
    )


# AC 4: case C, an oblique pipe at 45 degrees


def test_case_c_at_the_crossing_is_half_case_a(case_a, case_c):
    row = row_at(case_c, 40.0)
    assert row["vertical_curvature"] == pytest.approx(-7.73651e-5, rel=REL)
    assert row["lateral_curvature"] == pytest.approx(0.0, abs=1e-12)
    assert row["axial_strain"] == pytest.approx(-348.14e-6, rel=REL)
    center = row_at(case_a, 40.0)
    for column in ("axial_strain", "vertical_curvature"):
        assert row[column] == pytest.approx(center[column] / 2, rel=1e-9)


def test_case_c_at_the_lateral_peak(case_c):
    row = row_at(case_c, 40 + 9.44366, tolerance=1e-5)
    assert row["critical"]
    assert row["lateral_curvature"] == pytest.approx(3.77500e-5, rel=REL)
    assert row["vertical_curvature"] == pytest.approx(-2.64072e-5, rel=REL)
    assert row["resultant_curvature"] == pytest.approx(4.60695e-5, rel=REL)
    assert row["bending_strain"] == pytest.approx(6.9104e-6, rel=REL)
    assert row["axial_strain"] == pytest.approx(-118.83e-6, rel=REL)
    assert row["tensile_strain"] == pytest.approx(6.9104e-6, rel=REL)
    assert row["compressive_strain"] == pytest.approx(-125.74e-6, rel=REL)


# AC 5: the check's own peaks


def mechanics(result, distance):
    """Mechanics 2-4 from the source evaluated at distances, contracted here."""
    utility, source = result.asset, result.source
    start, end = (np.asarray(vertex, dtype=float) for vertex in utility.vertices)
    a = (end - start) / np.linalg.norm(end - start)
    lateral = np.array([a[1], -a[0], 0.0]) / math.hypot(a[0], a[1])
    vertical = np.cross(lateral, a)
    points = start + distance[:, None] * a
    movement = source.evaluate(x=points[:, 0], y=points[:, 1], depth=points[:, 2])
    strain = np.einsum("i,nij,j->n", a, movement.gradient, a)
    kappa_v = np.einsum("i,nijk,j,k->n", vertical, movement.hessian, a, a)
    kappa_l = np.einsum("i,nijk,j,k->n", lateral, movement.hessian, a, a)
    curvature = np.hypot(kappa_v, kappa_l)
    r = utility.diameter / 2
    return {
        "resultant_curvature": curvature,
        "tensile_strain": np.maximum(strain, 0) + r * curvature,
        "compressive_strain": -(np.minimum(strain, 0) - r * curvature),
    }


def dense_maxima(result):
    """The largest size of each, every 1 mm, then every 1 um within 1 mm.

    A 1 mm grid alone falls short of a peak by up to (0.5 mm)^2 |f''| / 2,
    about 1.5e-9 of it for a trough with i = 9 m, more than AC 5's 1e-9.
    """
    length = float(result.values["distance"].iloc[-1])
    grid = np.linspace(0.0, length, round(length / 1e-3) + 1)
    found = {}
    for column, values in mechanics(result, grid).items():
        middle = grid[int(np.argmax(values))]
        fine = np.clip(np.linspace(middle - 1e-3, middle + 1e-3, 2001), 0, length)
        found[column] = mechanics(result, fine)[column].max()
    return found


@pytest.fixture
def twins(twins_below_the_surface):
    return gs.check_continuous_pipe(
        twins_below_the_surface, interval=1.0, interaction="greenfield", **limits()
    )


@pytest.mark.parametrize("name", ["case_c", "twins"])
def test_peaks_are_found(name, request):
    result = request.getfixturevalue(name)
    found = dense_maxima(result)
    values = result.values
    for column, largest in found.items():
        sizes = values[column].abs()
        governing = sizes.max()
        assert governing >= largest * (1 - 1e-12)
        assert governing <= largest * (1 + 1e-9)
        assert values["critical"].loc[sizes.idxmax()]


def test_added_rows_are_local_peaks(case_c):
    # On an oblique pipe the resultant curvature and combined strains peak off
    # the source's critical distances; the check's added rows are there.
    profile = gs.movement_profile(case_c_pipe(), trough(), spacing=1.0)
    known = profile.values["distance"].to_numpy()
    distance = case_c.values["distance"].to_numpy()
    added = distance[np.min(np.abs(distance[:, None] - known), axis=1) > 1e-6]
    assert added.size > 0
    assert case_c.values.set_index("distance").loc[added, "critical"].all()
    for peak in added:
        near = np.array([peak - 1e-3, peak, peak + 1e-3])
        values = mechanics(case_c, near)
        assert any(
            column[1] >= column[[0, 2]].max() or column[1] <= column[[0, 2]].min()
            for column in values.values()
        )


def test_profile_rows_are_kept(case_a):
    profile = gs.movement_profile(case_a_pipe(), trough(), spacing=1.0)
    kept = case_a.values.set_index("distance").loc[profile.values["distance"]]
    for column in profile.values.columns:
        if column in ("distance", "critical"):
            continue
        np.testing.assert_array_equal(
            kept[column].to_numpy(), profile.values[column].to_numpy()
        )


# AC 8: limits and utilization


def test_utilization_and_passes(case_a):
    checks = case_a.checks.set_index("check")
    assert checks.loc["tensile_strain", "utilization"] == pytest.approx(
        321.08e-6 / 1000e-6, rel=REL
    )
    assert checks.loc["compressive_strain", "utilization"] == pytest.approx(
        719.50e-6 / 1000e-6, rel=REL
    )
    assert checks.loc["radius_of_curvature", "utilization"] == pytest.approx(
        1000 / 6462.9, rel=REL
    )
    assert checks["passes"].all()


def test_a_utilization_above_one_fails():
    result = check(
        case_a_pipe(),
        compressive_strain_limit=u.Quantity(700, "µε"),
        radius_of_curvature_limit=7000 * u.m,
    )
    checks = result.checks.set_index("check")
    assert not checks.loc["compressive_strain", "passes"]
    assert checks.loc["compressive_strain", "utilization"] > 1
    assert checks.loc["axial_compression", "passes"]
    assert not checks.loc["radius_of_curvature", "passes"]
    assert checks.loc["radius_of_curvature", "utilization"] == pytest.approx(
        7000 / 6462.9, rel=REL
    )


@pytest.mark.parametrize(
    ("limit", "names"),
    [
        ("tensile_strain_limit", ["axial_tension", "tensile_strain"]),
        ("compressive_strain_limit", ["axial_compression", "compressive_strain"]),
        ("bending_strain_limit", ["bending"]),
        ("radius_of_curvature_limit", ["radius_of_curvature"]),
    ],
)
def test_a_limit_of_none(limit, names):
    result = check(case_a_pipe(), **{limit: None})
    checks = result.checks.set_index("check")
    for name in checks.index:
        row = checks.loc[name]
        if name in names:
            assert math.isnan(row["limit"])
            assert math.isnan(row["utilization"])
            assert row["passes"] is pd.NA
            assert math.isfinite(row["value"])
        else:
            assert row["passes"] is not pd.NA
    assert any(limit in text for text in result.assumptions)
    entry = next(entry for entry in result.inputs if entry.name == limit)
    assert (entry.value, entry.given_as) == ("none", "none")


def test_bending_reads_only_its_own_limit():
    result = check(
        case_a_pipe(),
        tensile_strain_limit=u.Quantity(1, "µε"),
        compressive_strain_limit=u.Quantity(1, "µε"),
        bending_strain_limit=u.Quantity(46.42, "µε"),
    )
    bending = check_row(result, "bending")
    assert bending["limit"] == pytest.approx(46.42e-6)
    assert bending["utilization"] == pytest.approx(0.5, rel=REL)


def test_a_check_with_nothing_of_its_sign_passes():
    # 10 m of pipe over the trough's center: compression only, no tension.
    pipe = gs.utilities.perpendicular_utility(
        tunnel(),
        utility_id="short",
        station=0,
        start_offset=-5,
        end_offset=5,
        depth=2.0,
        elevation_reference="axis",
        diameter=0.3,
    )
    row = check_row(check(pipe), "axial_tension")
    assert math.isnan(row["value"])
    assert math.isnan(row["governing_distance"])
    assert row["passes"]


# AC 10, AC 11: judgments and the profile


JUDGMENTS = ["interval", "interaction", *limits()]


def arguments(**changes):
    given = {"interval": 1.0, "interaction": "greenfield", **limits()}
    given.update(changes)
    return given


@pytest.fixture(scope="module")
def profile():
    return gs.movement_profile(case_a_pipe(), trough(), spacing=5.0)


@pytest.mark.parametrize("name", JUDGMENTS)
def test_each_judgment_is_required(profile, name):
    given = arguments()
    del given[name]
    with pytest.raises(TypeError, match=f"missing {name}.*no default"):
        gs.check_continuous_pipe(profile, **given)


@pytest.mark.parametrize(
    "name",
    ["tensile_strain_limit", "compressive_strain_limit", "bending_strain_limit"],
)
def test_a_plain_number_strain_limit_is_refused(profile, name):
    with pytest.raises(TypeError, match="needs a pint quantity"):
        gs.check_continuous_pipe(profile, **arguments(**{name: 0.001}))


def test_interaction_must_be_greenfield(profile):
    with pytest.raises(ValueError, match='"greenfield"'):
        gs.check_continuous_pipe(profile, **arguments(interaction="slip"))


@pytest.mark.parametrize("value", [0.0, -1.0, math.inf])
def test_interval_must_be_positive(profile, value):
    with pytest.raises(ValueError, match="interval must be positive"):
        gs.check_continuous_pipe(profile, **arguments(interval=value))


@pytest.mark.parametrize("name", list(limits()))
@pytest.mark.parametrize("size", [-1.0, math.inf])
def test_limits_must_be_zero_or_positive(profile, name, size):
    unit = u.m if name == "radius_of_curvature_limit" else u.dimensionless
    with pytest.raises(ValueError, match=f"{name} must be zero or positive"):
        gs.check_continuous_pipe(profile, **arguments(**{name: size * unit}))


def test_a_zero_limit_allows_nothing():
    # M3 (b), decision 11: infinity and fail for a nonzero value; a zero
    # radius limit gives 0 and passes.
    result = check(
        case_a_pipe(),
        tensile_strain_limit=0 * u.dimensionless,
        compressive_strain_limit=0 * u.dimensionless,
        bending_strain_limit=0 * u.dimensionless,
        radius_of_curvature_limit=0 * u.m,
    )
    checks = result.checks.set_index("check")
    for name in ("axial_tension", "axial_compression", "bending", "tensile_strain"):
        assert checks.loc[name, "utilization"] == math.inf
        assert not checks.loc[name, "passes"]
    assert checks.loc["radius_of_curvature", "utilization"] == 0
    assert checks.loc["radius_of_curvature", "passes"]


def test_a_zero_limit_passes_a_zero_value():
    from garisenda.utilities._continuous_pipe import _utilization

    assert _utilization(0.0, 0.0, smallest=False) == (0.0, True)
    assert _utilization(1e-9, 0.0, smallest=False) == (math.inf, False)


def test_every_judgment_is_recorded(profile):
    result = gs.check_continuous_pipe(
        profile,
        **arguments(
            interaction=gs.Sourced("greenfield", source="Basis of design"),
            radius_of_curvature_limit=None,
        ),
    )
    entries = {entry.name: entry for entry in result.inputs}
    assert entries["interval"].value == 1.0 * u.m
    assert entries["interval"].kind == "design judgment"
    assert entries["interval"].given_as == "plain number, read as m"
    assert entries["interaction"].value == "greenfield"
    assert entries["interaction"].given_as == "name"
    assert entries["interaction"].source == "Basis of design"
    tensile = entries["tensile_strain_limit"]
    assert tensile.value.m_as("dimensionless") == pytest.approx(1e-3)
    assert tensile.given_as == "quantity in µε"
    assert entries["radius_of_curvature_limit"].value == "none"
    assert all(entries[name].kind == "design judgment" for name in JUDGMENTS)
    assert entries["spacing"].value == 5.0 * u.m


@pytest.mark.parametrize("value", ["profile", 3.0, None])
def test_needs_a_movement_profile(value):
    with pytest.raises(TypeError, match="needs a movement profile"):
        gs.check_continuous_pipe(value, **arguments())


def test_a_check_result_is_not_a_profile(case_a):
    with pytest.raises(TypeError, match="continuous_pipe_check"):
        gs.check_continuous_pipe(case_a, **arguments())


# The result's parts (AC 13 in part; the rest with discrete strain)


def test_result_parts(case_a):
    assert case_a.analysis == "continuous_pipe_check"
    assert case_a.subject == "A"
    assert list(case_a.checks["check"]) == [
        "axial_tension",
        "axial_compression",
        "bending",
        "tensile_strain",
        "compressive_strain",
        "radius_of_curvature",
    ]
    assert case_a.method[-1].name == "Strain checks for a continuous pipe"
    assert "Bracegirdle" in case_a.method[-1].source
    assert any("follows the ground" in text for text in case_a.assumptions)
    assert any("circular" in text for text in case_a.assumptions)
    assert case_a.validity == "within"


# AC 3: case B, discrete, from the spec's formulas (exact: 1e-9 relative)

EXACT = 1e-9
AREA = math.pi * 6.0**2 / 4
S_MAX_EXACT = 0.01 * AREA / (math.sqrt(2 * math.pi) * WIDTH)


def settlement(o):
    return S_MAX_EXACT * math.exp(-(o**2) / (2 * WIDTH**2))


def horizontal(o):
    # Toward the axis, along the pipe (linear width method): -(o / (z0 - z)) S.
    return -(o / DEPTH_BELOW_AXIS) * settlement(o)


def discrete_by_hand(o, h):
    strain = (horizontal(o + h / 2) - horizontal(o - h / 2)) / h
    # The settlement is positive down, as the profile's vertical is.
    curvature = (settlement(o + h) - 2 * settlement(o) + settlement(o - h)) / h**2
    bending = RADIUS * abs(curvature)
    return {
        "discrete_axial_strain": strain,
        "discrete_vertical_curvature": curvature,
        "discrete_tensile_strain": max(strain, 0) + bending,
        "discrete_compressive_strain": min(strain, 0) - bending,
    }


@pytest.fixture(scope="module", params=[1.0, 9.0])
def case_b(request):
    return request.param, check(case_a_pipe(), interval=request.param)


def test_case_b_at_the_center_and_root3_i(case_b):
    h, result = case_b
    for distance in (40.0, 40 + ROOT3_I, 40 - ROOT3_I):
        row = row_at(result, distance)
        expected = discrete_by_hand(row["distance"] - 40.0, h)
        for column, value in expected.items():
            assert row[column] == pytest.approx(value, rel=EXACT), column
        assert row["discrete_lateral_curvature"] == 0


def test_case_b_center_ratios(case_b):
    # kappa ratio (1 - e^-a) / a, a = h^2 / 2i^2; axial ratio e^-b, b = h^2 / 8i^2.
    h, result = case_b
    row = row_at(result, 40.0)
    a, b = h**2 / (2 * WIDTH**2), h**2 / (8 * WIDTH**2)
    ratio = row["discrete_vertical_curvature"] / row["vertical_curvature"]
    assert ratio == pytest.approx((1 - math.exp(-a)) / a, rel=EXACT)
    assert row["discrete_axial_strain"] / row["axial_strain"] == pytest.approx(
        math.exp(-b), rel=EXACT
    )


@pytest.mark.parametrize(
    ("h", "column", "distance", "value"),
    [
        (1.0, "discrete_vertical_curvature", 40.0, -1.54254e-4),
        (1.0, "discrete_axial_strain", 40.0, -695.21e-6),
        (1.0, "discrete_compressive_strain", 40.0, -718.35e-6),
        (1.0, "discrete_vertical_curvature", 40 + ROOT3_I, 6.88370e-5),
        (1.0, "discrete_axial_strain", 40 + ROOT3_I, 310.25e-6),
        (1.0, "discrete_tensile_strain", 40 + ROOT3_I, 320.57e-6),
        (9.0, "discrete_vertical_curvature", 40.0, -1.21763e-4),
        (9.0, "discrete_axial_strain", 40.0, -614.47e-6),
        (9.0, "discrete_compressive_strain", 40.0, -632.73e-6),
        (9.0, "discrete_vertical_curvature", 40 + ROOT3_I, 5.30152e-5),
        (9.0, "discrete_axial_strain", 40 + ROOT3_I, 272.88e-6),
        (9.0, "discrete_tensile_strain", 40 + ROOT3_I, 280.83e-6),
    ],
)
def test_case_b_table(h, column, distance, value):
    # The spec's table, to its five or six figures.
    result = check(case_a_pipe(), interval=h)
    assert row_at(result, distance)[column] == pytest.approx(value, rel=5e-5)


def test_case_b_governing():
    checks = check(case_a_pipe(), interval=1.0).checks
    assert (checks["governed_by"] == "analytical").all()
    assert (checks["discrete"].notna()).all()
    coarse = check_row(check(case_a_pipe(), interval=9.0), "compressive_strain")
    assert coarse["discrete_distance"] == pytest.approx(40.0)
    assert coarse["difference"] == pytest.approx(86.77e-6, rel=REL)
    assert coarse["difference"] == coarse["discrete"] - coarse["analytical"]


# AC 6: discrete converges on analytical, and is never the larger per plane

PAIRS = [
    "axial_strain",
    "vertical_curvature",
    "lateral_curvature",
    "resultant_curvature",
    "bending_strain",
    "tensile_strain",
    "compressive_strain",
]


def test_discrete_converges_on_analytical():
    result = check(case_c_pipe(), interval=0.01)
    values = result.values
    for column in PAIRS:
        discrete = values[f"discrete_{column}"]
        has = discrete.notna()
        assert has.sum() > 0
        scale = values[column].abs().max()
        error = (discrete[has] - values[column][has]).abs().max()
        assert error <= 1e-4 * scale, column


@pytest.mark.parametrize("pipe", [case_a_pipe, case_c_pipe])
@pytest.mark.parametrize("h", [1.0, 9.0])
def test_discrete_peak_per_plane_is_no_larger(pipe, h):
    values = check(pipe(), interval=h).values
    for column in ("axial_strain", "vertical_curvature", "lateral_curvature"):
        analytical = values[column]
        discrete = values[f"discrete_{column}"].dropna()
        tolerance = 1e-12 * analytical.abs().max()
        assert discrete.max() <= max(analytical.max(), 0) + tolerance
        assert discrete.min() >= min(analytical.min(), 0) - tolerance


# AC 7: the ends


def test_stations_near_the_ends_have_no_discrete_values():
    h = 3.0
    result = check(case_a_pipe(), spacing=0.5, interval=h)
    values = result.values
    distance = values["distance"]
    length = distance.iloc[-1]
    no_axial = (distance < h / 2 - 1e-6) | (distance > length - h / 2 + 1e-6)
    no_curvature = (distance < h - 1e-6) | (distance > length - h + 1e-6)
    assert (values["discrete_axial_strain"].isna() == no_axial).all()
    for column in (
        "discrete_vertical_curvature",
        "discrete_lateral_curvature",
        "discrete_resultant_curvature",
        "discrete_bending_strain",
        "discrete_tensile_strain",
        "discrete_compressive_strain",
        "discrete_radius_of_curvature",
    ):
        assert (values[column].isna() == no_curvature).all(), column
    flags = [flag for flag in result.warnings if "discrete" in flag.reason]
    assert len(flags) == 1
    assert flags[0].verdict == "within"
    assert flags[0].points == tuple(np.flatnonzero(no_curvature | no_axial))
    assert "h/2 = 1.5 m" in flags[0].reason
    assert "h = 3 m" in flags[0].reason
    profile = gs.movement_profile(case_a_pipe(), trough(), spacing=0.5)
    assert result.validity == profile.validity


def test_a_pipe_shorter_than_two_intervals():
    result = check(case_a_pipe(), interval=50.0)
    values = result.values
    assert values["discrete_resultant_curvature"].isna().all()
    assert values["discrete_axial_strain"].notna().any()
    flag = next(flag for flag in result.warnings if "discrete" in flag.reason)
    assert "shorter than 2h = 100 m" in flag.reason
    checks = result.checks.set_index("check")
    for name in ("bending", "tensile_strain", "compressive_strain"):
        assert checks.loc[name, "governed_by"] == "analytical"
        assert math.isnan(checks.loc[name, "discrete"])
        assert math.isnan(checks.loc[name, "difference"])
        assert checks.loc[name, "value"] == checks.loc[name, "analytical"]


# AC 9: the worse governs


@pytest.mark.parametrize(
    ("analytical", "discrete", "smallest", "expected"),
    [
        (3.0e-4, 2.9e-4, False, "analytical"),  # tension, discrete smaller
        (3.0e-4, 3.1e-4, False, "discrete"),  # tension, discrete larger
        (-7.0e-4, -6.0e-4, False, "analytical"),  # compression
        (-7.0e-4, -8.0e-4, False, "discrete"),
        (6000.0, 6500.0, True, "analytical"),  # radius: the smaller governs
        (6000.0, 5500.0, True, "discrete"),
        (3.0e-4, 3.0e-4 * (1 + 1e-10), False, "analytical"),  # a tie
        (6000.0, 6000.0 * (1 - 1e-10), True, "analytical"),
        (3.0e-4, math.nan, False, "analytical"),  # no discrete value
        (math.nan, 3.0e-4, False, "discrete"),
    ],
)
def test_governing_value(analytical, discrete, smallest, expected):
    value, distance, governed_by, difference = governing_value(
        analytical, 1.0, discrete, 2.0, smallest=smallest
    )
    assert governed_by == expected
    chosen = (analytical, 1.0) if expected == "analytical" else (discrete, 2.0)
    assert (value, distance) == chosen
    if math.isnan(analytical) or math.isnan(discrete):
        assert math.isnan(difference)
    else:
        assert difference == discrete - analytical


# AC 13: the result's shape


def test_to_dict_is_json_ready(case_a):
    data = json.loads(json.dumps(case_a.to_dict(), allow_nan=False))
    assert data["units"]["discrete_resultant_curvature"] == "1/m"
    assert [row["check"] for row in data["checks"]] == list(case_a.checks["check"])
    assert data["values"]["discrete_axial_strain"][0] is None


@pytest.fixture(scope="module")
def parallel():
    # Parallel to the tunnel: the field doesn't change along it, so its
    # curvature is exactly zero and its radius infinite everywhere.
    pipe = gs.utilities.Utility(
        utility_id="P", vertices=[(5.0, -20.0, 2.0), (5.0, 20.0, 2.0)], diameter=0.3
    )
    return check(pipe)


def test_infinite_radii_are_none_in_to_dict(parallel):
    values = parallel.values
    assert np.isinf(values["radius_of_curvature"]).all()
    data = json.loads(json.dumps(parallel.to_dict(), allow_nan=False))
    assert all(radius is None for radius in data["values"]["radius_of_curvature"])


def test_a_straight_pipe_passes_with_nothing_to_report(parallel):
    for row in parallel.checks.itertuples():
        assert math.isnan(row.value)
        assert row.passes


def test_to_frame_has_the_new_columns(case_a):
    frame = case_a.to_frame()
    units = frame.attrs["units"]
    for column in [*UNIT_OF, *(f"discrete_{name}" for name in UNIT_OF)]:
        assert column in frame
    for name, unit in UNIT_OF.items():
        assert units[name] == unit
        assert units[f"discrete_{name}"] == unit


UNIT_OF = {
    "axial_strain": "dimensionless",
    "resultant_curvature": "1/m",
    "bending_strain": "dimensionless",
    "tensile_strain": "dimensionless",
    "compressive_strain": "dimensionless",
    "radius_of_curvature": "m",
}


def test_summary_lists_the_six_checks(case_a):
    text = repr(case_a)
    for name in case_a.checks["check"]:
        assert f"  {name}: " in text
    assert "tensile_strain: 0.00032108 at 24.41 m (analytical)" in text
