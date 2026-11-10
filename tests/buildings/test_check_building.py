"""The building check (docs/work/m4a-building-damage.md, AC 1-12, 16)."""

import json
import math
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

import garisenda as gs
from garisenda._result import CHECK_COLUMNS, ZONE_COLUMNS

u = gs.units

BEAMS = {"BW": gs.buildings.burland_wroth_beam(), "T": gs.buildings.timoshenko_beam()}
LIMITS = gs.presets.preliminary_assessment_limits()


def golden(text):
    """A hand value printed to some digits, and its tolerance.

    The spec's hand calculations are good to 1e-6 relative and then rounded to
    six significant figures, so each is checked to 1e-6 relative plus half a
    unit in its last printed digit.
    """
    value = Decimal(text)
    half_unit = float(Decimal(5).scaleb(value.as_tuple().exponent - 1))
    return pytest.approx(float(value), rel=0, abs=half_unit + 1e-6 * abs(float(value)))


def tunnel(**changes):
    arguments = {
        "reference_point": (0, 0),
        "azimuth": 0 * u.degree,
        "diameter": 6.0,
        "axis_depth": 20.0,
    }
    arguments.update(changes)
    return gs.sources.IdealizedTunnel(**arguments)


def trough_at_depth(volume_loss=1 * u.percent):
    """Case A's trough: z0 = 20 m, D = 6 m, linear width with k = 0.5."""
    return gs.sources.transverse_trough(
        tunnel(),
        volume_loss=volume_loss,
        trough_width=gs.sources.linear_trough_width(trough_width_parameter=0.5),
    )


def wall(start_offset, end_offset, *, reference=None, depth=2.0, height=8.0):
    return gs.buildings.perpendicular_building(
        reference or tunnel(),
        building_id="B-1",
        station=50,
        start_offset=start_offset,
        end_offset=end_offset,
        height=height,
        foundation_depth=depth,
    )


def judgments(**changes):
    arguments = {
        "beam_method": BEAMS["T"],
        "youngs_to_shear_modulus_ratio": 2.6,
        "category_limits": gs.presets.damage_categories(),
        "cutoff": gs.buildings.no_cutoff(),
        "settlement_limit": LIMITS.settlement,
        "slope_limit": LIMITS.slope,
        "acceptable_category": 2,
        "interaction": "greenfield",
    }
    arguments.update(changes)
    return arguments


def check(building, source, beam="T", **changes):
    profile = gs.movement_profile(building, source, spacing=1.0)
    return gs.check_building(profile, **judgments(beam_method=BEAMS[beam], **changes))


def zone(result, number):
    return result.zones.set_index("zone").loc[number]


def checks(result):
    return result.checks.set_index("check")


# Case A: one tunnel, foundation 2 m down, the wall from offset -30 to 30.
CASE_A = {
    1: {
        "length": "21",
        "deflection": "2.67082",
        "offset": "-18.2775",
        "deflection_ratio": "1.27182e-4",
        "horizontal_strain": "1.77148e-4",
        "BW": ("1.78129e-4", "8.82163e-5", "3.55277e-4", "2.07056e-4"),
        "T": ("2.06820e-4", "1.02425e-4", "3.83968e-4", "2.16111e-4"),
    },
    2: {
        "length": "18",
        "deflection": "4.93141",
        "offset": "0",
        "deflection_ratio": "2.73967e-4",
        "horizontal_strain": "-4.22319e-4",
        "BW": ("4.12670e-4", "1.19216e-4", "-9.64855e-6", "1.51465e-4"),
        "T": ("4.52008e-4", "1.30580e-4", "2.96894e-5", "1.56171e-4"),
    },
}
STRAINS = (
    "bending_strain",
    "diagonal_strain",
    "total_bending_strain",
    "total_diagonal_strain",
)
S_MAX_A = 0.01 * math.pi * 36 / 4 / (math.sqrt(2 * math.pi) * 9.0)


@pytest.fixture(scope="module")
def case_a():
    source = trough_at_depth()
    return {beam: check(wall(-30, 30), source, beam) for beam in BEAMS}


@pytest.mark.parametrize("beam", BEAMS)
def test_case_a(case_a, beam):
    result = case_a[beam]
    assert result.analysis == "building_check"
    assert result.subject == "B-1"
    assert result.zones["zone"].tolist() == [1, 2, 3]
    assert result.zones["mode"].tolist() == ["hogging", "sagging", "hogging"]
    np.testing.assert_allclose(result.zones["start"], [0, 21, 39], atol=1e-8)
    np.testing.assert_allclose(result.zones["end"], [21, 39, 60], atol=1e-8)
    for number, expected in CASE_A.items():
        row = zone(result, number)
        assert row["length"] == golden(expected["length"])
        assert row["deflection"] * 1000 == golden(expected["deflection"])
        assert row["deflection_distance"] - 30 == golden(expected["offset"])
        assert row["deflection_ratio"] == golden(expected["deflection_ratio"])
        assert row["horizontal_strain"] == golden(expected["horizontal_strain"])
        for column, value in zip(STRAINS, expected[beam], strict=True):
            assert row[column] == golden(value), column
        assert row["category"] == 0
        assert row["label"] == "0"
        assert row["severity"] == "negligible"
    # Zone 2 in closed form: a level chord, Delta = S_max (1 - e^(-1/2)).
    sag = zone(result, 2)
    assert sag["deflection"] == pytest.approx(S_MAX_A * (1 - math.exp(-0.5)), rel=1e-9)
    assert sag["horizontal_strain"] == pytest.approx(
        -0.5 * S_MAX_A * math.exp(-0.5) / 9, rel=1e-9
    )
    assert zone(result, 1)["governed_by"] == "bending"
    assert sag["governed_by"] == "diagonal"
    # Zone 3 is zone 1's mirror.
    one, three = zone(result, 1), zone(result, 3)
    for column in ("length", "deflection", "horizontal_strain", *STRAINS):
        assert three[column] == pytest.approx(one[column], rel=1e-9)
    assert three["deflection_distance"] == pytest.approx(
        60 - one["deflection_distance"], abs=1e-8
    )


@pytest.mark.parametrize("beam", BEAMS)
def test_case_a_checks(case_a, beam):
    result = case_a[beam]
    table = checks(result)
    assert list(table.index) == [
        "settlement",
        "slope",
        "zone_1",
        "zone_2",
        "zone_3",
        "damage_category",
    ]
    settlement = table.loc["settlement"]
    assert settlement["value"] * 1000 == golden("12.5331")
    assert settlement["governing_distance"] == pytest.approx(30, abs=1e-8)
    assert settlement["utilization"] == golden("1.25331")
    assert not settlement["passes"]
    assert settlement["unit"] == "m"
    slope = table.loc["slope"]
    assert slope["value"] == pytest.approx(S_MAX_A * math.exp(-0.5) / 9, rel=1e-9)
    assert slope["governing_distance"] == pytest.approx(21, abs=1e-8)
    assert slope["utilization"] == golden("0.422319")
    assert bool(slope["passes"])
    governing = table.loc["damage_category"]
    assert governing["zone"] == 1
    assert governing["category"] == 0
    assert governing["value"] == golden(CASE_A[1][beam][2])
    assert governing["limit"] == pytest.approx(0.0015)
    assert bool(governing["passes"])
    for number in (1, 2, 3):
        row = table.loc[f"zone_{number}"]
        assert row["zone"] == number
        assert row["value"] == zone(result, number)["tensile_strain"]
        assert math.isnan(row["governing_distance"])
        assert math.isnan(row["analytical"])
        assert math.isnan(row["discrete"])


def test_case_a_values(case_a):
    result = case_a["T"]
    values = result.values
    assert {"zone", "chord", "deflection"} <= set(values.columns)
    assert values.attrs["units"]["chord"] == "m"
    assert values.attrs["units"]["deflection"] == "m"
    assert str(values["zone"].dtype) == "Int64"
    # A zone's end belongs to the zone after it, and the last end to the last.
    at = values.set_index("distance")
    assert at.loc[0.0, "zone"] == 1
    assert values.loc[np.isclose(values["distance"], 21), "zone"].item() == 2
    assert values.loc[np.isclose(values["distance"], 39), "zone"].item() == 3
    assert values["zone"].iloc[-1] == 3
    # Each Delta is a critical row, where |deflection| is Delta.
    for number in (1, 2, 3):
        row = zone(result, number)
        hit = np.isclose(values["distance"], row["deflection_distance"], atol=1e-6)
        assert values.loc[hit, "critical"].all()
        assert abs(values.loc[hit, "deflection"].item()) == pytest.approx(
            row["deflection"], rel=1e-9
        )
    # The deflection is zero at the zone ends and signed as Jones's Delta.
    ends = values[np.isclose(values["distance"], 21) | (values["distance"] == 0)]
    np.testing.assert_allclose(ends["deflection"], 0, atol=1e-15)
    hogging = values[values["zone"] == 1]
    assert (hogging["deflection"] <= 1e-15).all()
    sagging = values[values["zone"] == 2]
    assert (sagging["deflection"] >= -1e-15).all()
    assert (result.zones.attrs["units"]["deflection"]) == "m"


def test_case_b():
    result = check(wall(12, 30), trough_at_depth(), "BW")
    timoshenko = check(wall(12, 30), trough_at_depth(), "T")
    assert result.zones["mode"].tolist() == ["hogging"]
    row = zone(result, 1)
    assert row["length"] == golden("18")
    assert row["deflection"] * 1000 == golden("1.82746")
    assert row["deflection_distance"] + 12 == golden("19.5918")
    assert row["deflection_ratio"] == golden("1.01526e-4")
    assert row["horizontal_strain"] == golden("1.86348e-4")
    expected = {
        "BW": ("1.32665e-4", "7.66508e-5", "3.19013e-4", "2.08564e-4"),
        "T": ("1.56260e-4", "9.02835e-5", "3.42608e-4", "2.16294e-4"),
    }
    for beam, outcome in (("BW", result), ("T", timoshenko)):
        for column, value in zip(STRAINS, expected[beam], strict=True):
            assert zone(outcome, 1)[column] == golden(value), (beam, column)
    table = checks(result)
    assert table.loc["settlement", "value"] * 1000 == golden("5.15253")
    assert table.loc["settlement", "governing_distance"] == 0
    assert table.loc["slope", "value"] == golden("7.63338e-4")
    assert table.loc["slope", "governing_distance"] == 0


def twins(separation):
    north = tunnel()
    south = north.parallel(offset=separation, diameter=6.0, axis_depth=20.0)
    source = gs.superpose(
        **{
            name: gs.sources.transverse_surface_trough(
                reference, volume_loss=1 * u.percent, trough_width_parameter=0.5
            )
            for name, reference in (("north", north), ("south", south))
        }
    )
    return north, source


@pytest.fixture(scope="module")
def case_c():
    # twins_below_the_surface's tunnels, with the wall at the surface.
    north, source = twins(15.0)
    building = wall(-30, 45, reference=north, depth=0.0)
    return {beam: check(building, source, beam) for beam in BEAMS}


def test_case_c_uses_the_shared_fixtures_tunnels(twins_below_the_surface, case_c):
    shared = twins_below_the_surface.source
    built = case_c["T"].source
    names = ("north.axis_depth", "south.axis_depth", "north.diameter")
    assert [e.value for e in shared.inputs if e.name in names] == [
        e.value for e in built.inputs if e.name in names
    ]


@pytest.mark.parametrize("beam", BEAMS)
def test_case_c(case_c, beam):
    result = case_c[beam]
    assert result.zones["mode"].tolist() == ["hogging", "sagging", "hogging"]
    assert result.zones["end"].iloc[0] - 30 == golden("-7.56962")
    assert result.zones["end"].iloc[1] - 30 == golden("22.5696")
    one = zone(result, 1)
    assert one["length"] == golden("22.4304")
    assert one["deflection"] * 1000 == golden("2.78184")
    assert one["deflection_distance"] - 30 == golden("-18.1187")
    assert one["deflection_ratio"] == golden("1.24021e-4")
    assert one["horizontal_strain"] == golden("1.78939e-4")
    assert one["total_bending_strain"] == golden(
        {"BW": "3.56797e-4", "T": "3.84077e-4"}[beam]
    )
    two = zone(result, 2)
    assert two["length"] == golden("30.1392")
    assert two["deflection"] * 1000 == golden("7.67556")
    assert two["deflection_distance"] - 30 == golden("7.5")
    assert two["deflection_ratio"] == golden("2.54670e-4")
    assert two["horizontal_strain"] == golden("-2.78883e-4")
    assert two["total_diagonal_strain"] == golden(
        {"BW": "9.17941e-5", "T": "9.25256e-5"}[beam]
    )
    three = zone(result, 3)
    for column in ("length", "deflection", "horizontal_strain", *STRAINS):
        assert three[column] == pytest.approx(one[column], rel=1e-7)
    table = checks(result)
    assert table.loc["settlement", "value"] * 1000 == golden("17.0289")
    assert table.loc["settlement", "governing_distance"] - 30 == golden("7.5")
    assert table.loc["slope", "value"] == golden("8.40531e-4")


@pytest.mark.parametrize("beam", BEAMS)
def test_case_d(beam):
    north, source = twins(30.0)
    result = check(wall(-30, 60, reference=north, depth=0.0), source, beam)
    assert result.zones["mode"].tolist() == [
        "hogging",
        "sagging",
        "hogging",
        "sagging",
        "hogging",
    ]
    for end, expected in zip(
        result.zones["end"].iloc[:-1],
        ("-9.95800", "7.54021", "22.4598", "39.9580"),
        strict=True,
    ):
        assert end - 30 == golden(expected)
    three = zone(result, 3)
    assert three["length"] == golden("14.9196")
    assert three["deflection"] * 1000 == golden("2.07027")
    assert three["deflection_distance"] - 30 == golden("15")
    assert three["deflection_ratio"] == golden("1.38762e-4")
    assert three["horizontal_strain"] == golden("2.92690e-4")
    bending, total = {
        "BW": ("1.62774e-4", "4.55464e-4"),
        "T": ("1.94598e-4", "4.87289e-4"),
    }[beam]
    assert three["bending_strain"] == golden(bending)
    assert three["total_bending_strain"] == golden(total)
    outer = {"BW": "2.97218e-4", "T": "3.19763e-4"}[beam]
    sagging = {"BW": "1.11356e-4", "T": "1.14365e-4"}[beam]
    for number in (1, 5):
        assert zone(result, number)["total_bending_strain"] == golden(outer)
    for number in (2, 4):
        assert zone(result, number)["total_diagonal_strain"] == golden(sagging)
    governing = checks(result).loc["damage_category"]
    assert governing["zone"] == 3
    assert governing["value"] == three["tensile_strain"]


@pytest.fixture(scope="module")
def case_e():
    building = gs.buildings.Building(
        building_id="E", vertices=[(-30, -30), (30, 30)], foundation_depth=2, height=8
    )
    source = trough_at_depth()
    return {beam: check(building, source, beam) for beam in BEAMS}


@pytest.mark.parametrize("beam", BEAMS)
def test_case_e(case_e, case_a, beam):
    result = case_e[beam]
    assert result.zones["mode"].tolist() == ["hogging", "sagging", "hogging"]
    assert result.zones["end"].iloc[0] == golden("29.6985")
    assert result.zones["end"].iloc[1] == golden("55.1543")
    one = zone(result, 1)
    assert one["length"] == golden("29.6985")
    assert one["deflection"] * 1000 == golden("2.67082")
    assert one["deflection_ratio"] == golden("8.99312e-5")
    assert one["horizontal_strain"] == golden("8.85741e-5")
    bending, total = {
        "BW": ("1.36353e-4", "2.24928e-4"),
        "T": ("1.52553e-4", "2.41127e-4"),
    }[beam]
    assert one["bending_strain"] == golden(bending)
    assert one["total_bending_strain"] == golden(total)
    two = zone(result, 2)
    assert two["length"] == golden("25.4558")
    assert two["deflection_ratio"] == golden("1.93724e-4")
    assert two["horizontal_strain"] == golden("-2.11159e-4")
    total_bending, total_diagonal = {
        "BW": ("5.25523e-5", "7.35408e-5"),
        "T": ("6.80823e-5", "7.47292e-5"),
    }[beam]
    assert two["total_bending_strain"] == golden(total_bending)
    assert two["total_diagonal_strain"] == golden(total_diagonal)
    assert two["governed_by"] == "diagonal"
    assert checks(result).loc["slope", "value"] == golden("5.97249e-4")
    # Against the perpendicular wall of case A, at 45 degrees.
    sine = math.sin(math.radians(45))
    perpendicular = case_a[beam]
    for number in (1, 2, 3):
        oblique, square = zone(result, number), zone(perpendicular, number)
        assert oblique["deflection"] == pytest.approx(square["deflection"], rel=1e-9)
        assert oblique["deflection_ratio"] == pytest.approx(
            sine * square["deflection_ratio"], rel=1e-9
        )
        assert oblique["horizontal_strain"] == pytest.approx(
            sine**2 * square["horizontal_strain"], rel=1e-9
        )
    assert checks(result).loc["slope", "value"] == pytest.approx(
        sine * checks(perpendicular).loc["slope", "value"], rel=1e-9
    )


# Case J: Jones (2022), Examples 13.1 and 13.2.
J_WIDTH = 9.0
J_S_MAX = 0.015 * math.pi * 64 / 4 / (math.sqrt(2 * math.pi) * J_WIDTH)


def jones_tunnel():
    return tunnel(diameter=8.0, axis_depth=18.0)


def jones_trough():
    return gs.sources.transverse_surface_trough(
        jones_tunnel(), volume_loss=1.5 * u.percent, trough_width_parameter=0.5
    )


def jones_wall(start_offset, end_offset):
    return wall(
        start_offset, end_offset, reference=jones_tunnel(), depth=0.0, height=5.6
    )


@pytest.mark.parametrize("beam", BEAMS)
def test_case_j(beam):
    result = check(jones_wall(-25, 6.5), jones_trough(), beam)
    assert result.zones["mode"].tolist() == ["hogging", "sagging"]
    expected = {
        1: (
            "16",
            "4.88003",
            "-16.7506",
            "3.05002e-4",
            "5.72235e-4",
            {"BW": ("1.01229e-3", "6.22703e-4"), "T": ("1.07880e-3", "6.37859e-4")},
            2,
        ),
        2: (
            "15.5",
            "10.1214",
            "-0.860446",
            "6.52994e-4",
            "-1.25380e-3",
            {"BW": ("-3.15795e-4", "4.05387e-4"), "T": ("-2.47931e-4", "4.09685e-4")},
            0,
        ),
    }
    for number, (length, delta, at, ratio, eps_h, totals, category) in expected.items():
        row = zone(result, number)
        assert row["length"] == golden(length)
        assert row["deflection"] * 1000 == golden(delta)
        assert row["deflection_distance"] - 25 == golden(at)
        assert row["deflection_ratio"] == golden(ratio)
        assert row["horizontal_strain"] == golden(eps_h)
        assert row["total_bending_strain"] == golden(totals[beam][0])
        assert row["total_diagonal_strain"] == golden(totals[beam][1])
        assert row["category"] == category
    assert zone(result, 1)["label"] == "2"
    assert zone(result, 1)["severity"] == "slight"
    table = checks(result)
    assert table.loc["damage_category", "category"] == 2
    assert table.loc["damage_category", "zone"] == 1
    assert table.loc["settlement", "value"] == pytest.approx(J_S_MAX, rel=1e-9)
    assert table.loc["settlement", "governing_distance"] == pytest.approx(25)
    assert table.loc["slope", "value"] == golden("2.25237e-3")
    assert table.loc["slope", "governing_distance"] == pytest.approx(16, abs=1e-8)


def test_case_j_stage_1_contours():
    # The 10 mm contour: S(o) = 10 mm at o = sqrt(2 i^2 ln(S_max / 10 mm)).
    contour = math.sqrt(2 * J_WIDTH**2 * math.log(J_S_MAX / 0.010))
    assert contour == golden("13.9811")
    result = check(jones_wall(contour, 30), jones_trough())
    assert checks(result).loc["settlement", "utilization"] == pytest.approx(1, abs=1e-6)
    # The 1/500 slope beyond i: S(o) o / i^2 = 1/500, by bisection.
    low, high = J_WIDTH, 30.0
    for _ in range(200):
        middle = (low + high) / 2
        gradient = J_S_MAX * math.exp(-(middle**2) / (2 * J_WIDTH**2)) * middle
        if gradient / J_WIDTH**2 > 1 / 500:
            low = middle
        else:
            high = middle
    assert low == golden("12.2618")
    result = check(jones_wall(low, 30), jones_trough())
    assert checks(result).loc["slope", "utilization"] == pytest.approx(1, abs=1e-6)


def largest_departure(result, number):
    """Delta by search: every 1 mm along the zone, then every 1 um near the top."""
    row = zone(result, number)
    building, source = result.asset, result.source
    start, end = (np.asarray(vertex, dtype=np.float64) for vertex in building.vertices)
    direction = (end - start) / np.linalg.norm(end - start)

    def settlement(distance):
        points = start + np.asarray(distance)[:, None] * direction
        movement = source.evaluate(x=points[:, 0], y=points[:, 1], depth=points[:, 2])
        return movement.displacement[:, 2]

    s1, s2 = row["start"], row["end"]
    w1, w2 = settlement([s1, s2])

    def departure(distance):
        distance = np.asarray(distance)
        chord = w1 + (w2 - w1) * (distance - s1) / (s2 - s1)
        return np.abs(settlement(distance) - chord)

    coarse = np.arange(s1, s2, 1e-3)
    peak = coarse[int(np.argmax(departure(coarse)))]
    fine = np.arange(max(s1, peak - 1e-3), min(s2, peak + 1e-3), 1e-6)
    return float(np.max(departure(fine)))


@pytest.mark.parametrize(
    ("case", "numbers"), [("a", (1, 2, 3)), ("c", (1, 2, 3)), ("e", (1, 2, 3))]
)
def test_delta_is_exact(case_a, case_c, case_e, case, numbers):
    result = {"a": case_a, "c": case_c, "e": case_e}[case]["T"]
    for number in numbers:
        delta = zone(result, number)["deflection"]
        searched = largest_departure(result, number)
        assert delta >= searched * (1 - 1e-12)
        assert delta <= searched * (1 + 1e-9)


def scaled_to(target):
    """Case A (Timoshenko) with the volume loss scaled so it governs at `target`."""
    base = check(wall(-30, 30), trough_at_depth())
    governing = checks(base).loc["damage_category", "value"]
    return trough_at_depth(volume_loss=target / governing * u.percent)


def test_acceptable_category_at_its_limit():
    at = check(wall(-30, 30), scaled_to(0.0015 * (1 - 1e-12)))
    row = checks(at).loc["damage_category"]
    assert row["category"] == 2
    assert row["utilization"] == pytest.approx(1, abs=1e-11)
    assert bool(row["passes"])
    above = check(wall(-30, 30), scaled_to(0.0015 * (1 + 1e-9)))
    row = checks(above).loc["damage_category"]
    assert row["category"] == 3
    assert not bool(row["passes"])


def test_acceptable_category_none_reports_the_category(case_a):
    result = check(wall(-30, 30), trough_at_depth(), acceptable_category=None)
    table = checks(result)
    for name in ("zone_1", "zone_2", "zone_3", "damage_category"):
        assert math.isnan(table.loc[name, "limit"])
        assert math.isnan(table.loc[name, "utilization"])
        assert table.loc[name, "passes"] is pd.NA
    assert table.loc["damage_category", "category"] == 0
    assert any("acceptable_category" in text for text in result.assumptions)
    entry = {e.name: e for e in result.inputs}["acceptable_category"]
    assert (entry.value, entry.given_as) == ("none", "none")


def test_the_last_band_always_passes():
    result = check(wall(-30, 30), trough_at_depth(), acceptable_category=4)
    row = checks(result).loc["damage_category"]
    assert row["limit"] == math.inf
    assert row["utilization"] == 0
    assert bool(row["passes"])


def test_no_stage_1_limits():
    result = check(
        wall(-30, 30), trough_at_depth(), settlement_limit=None, slope_limit=None
    )
    table = checks(result)
    for name in ("settlement", "slope"):
        assert math.isnan(table.loc[name, "limit"])
        assert table.loc[name, "passes"] is pd.NA
        assert math.isfinite(table.loc[name, "value"])
    assert any("settlement_limit, slope_limit" in text for text in result.assumptions)


@pytest.fixture(scope="module")
def profile_a():
    return gs.movement_profile(wall(-30, 30), trough_at_depth(), spacing=1.0)


@pytest.mark.parametrize(
    "name",
    [
        "beam_method",
        "youngs_to_shear_modulus_ratio",
        "category_limits",
        "cutoff",
        "settlement_limit",
        "slope_limit",
        "acceptable_category",
        "interaction",
    ],
)
def test_each_judgment_is_required(profile_a, name):
    given = judgments()
    del given[name]
    with pytest.raises(TypeError, match=f"missing {name}"):
        gs.check_building(profile_a, **given)


def test_slope_limit_refuses_a_plain_number(profile_a):
    with pytest.raises(TypeError, match="slope_limit"):
        gs.check_building(profile_a, **judgments(slope_limit=0.002))


def test_youngs_to_shear_modulus_ratio_takes_a_plain_number(profile_a):
    result = gs.check_building(
        profile_a, **judgments(youngs_to_shear_modulus_ratio=2.6)
    )
    entry = {e.name: e for e in result.inputs}["youngs_to_shear_modulus_ratio"]
    assert entry.value.magnitude == 2.6
    assert entry.kind == "design judgment"


@pytest.mark.parametrize(
    ("changes", "error", "message"),
    [
        ({"interaction": "soil_structure"}, ValueError, '"greenfield"'),
        ({"settlement_limit": -1 * u.mm}, ValueError, "settlement_limit"),
        ({"slope_limit": -1 * u.percent}, ValueError, "slope_limit"),
        ({"acceptable_category": 7}, ValueError, "categories are 0, 1, 2, 3, 4"),
        ({"acceptable_category": 2.0}, TypeError, "acceptable_category"),
        ({"acceptable_category": True}, TypeError, "acceptable_category"),
        ({"youngs_to_shear_modulus_ratio": 0}, ValueError, "positive"),
        ({"youngs_to_shear_modulus_ratio": -2.6}, ValueError, "positive"),
        ({"beam_method": "timoshenko"}, TypeError, "beam_method"),
        ({"category_limits": [0.05, 0.075]}, TypeError, "DamageCategories"),
        ({"cutoff": 2.5}, TypeError, "cutoff"),
    ],
)
def test_bad_judgments(profile_a, changes, error, message):
    with pytest.raises(error, match=message):
        gs.check_building(profile_a, **judgments(**changes))


def test_a_zero_limit_is_allowed(profile_a):
    result = gs.check_building(profile_a, **judgments(settlement_limit=0 * u.mm))
    assert checks(result).loc["settlement", "utilization"] == math.inf


def test_inputs_and_caveats(profile_a):
    ratio = gs.presets.youngs_to_shear_modulus_ratio(structure="framed")
    result = gs.check_building(
        profile_a,
        **judgments(
            youngs_to_shear_modulus_ratio=ratio,
            beam_method=gs.Sourced(BEAMS["BW"], source="Basis of design, 4.1"),
        ),
    )
    entries = {entry.name: entry for entry in result.inputs}
    for name in (
        "beam_method",
        "youngs_to_shear_modulus_ratio",
        "category_limits",
        "cutoff",
        "settlement_limit",
        "slope_limit",
        "acceptable_category",
        "interaction",
    ):
        assert entries[name].kind == "design judgment", name
    assert entries["poisson_ratio"].kind == "constant or setting"
    assert entries["poisson_ratio"].value.magnitude == 0.3
    assert entries["beam_method"].value == BEAMS["BW"].name
    assert entries["beam_method"].source == "Basis of design, 4.1"
    assert entries["youngs_to_shear_modulus_ratio"].value.magnitude == 12.5
    assert entries["youngs_to_shear_modulus_ratio"].source == ratio.source
    assert entries["category_limits"].value.startswith(
        "Mair, Taylor & Burland (1996), Table 2 (0 up to 0.05 %; 1 up to 0.075 %"
    )
    assert entries["category_limits"].value.endswith("4 to 5 above)")
    assert entries["category_limits"].source.startswith("gs.presets.damage_categories")
    assert entries["cutoff"].value == "none: the whole wall"
    assert entries["settlement_limit"].value.to("mm").magnitude == pytest.approx(10)
    assert entries["slope_limit"].value.magnitude == pytest.approx(0.002)
    assert entries["acceptable_category"].value == "2"
    # Each preset's caveats, once each, after the check's own assumptions.
    caveats = [
        *ratio.caveats,
        *gs.presets.damage_categories().caveats,
        *LIMITS.settlement.caveats,
    ]
    for caveat in caveats:
        assert result.assumptions.count(caveat) == 1, caveat
    assert result.method[-1].name == "Building damage, staged method"
    assert "3/2 E I" in " ".join(result.method[-1].equations)


def test_the_method_names_the_beam(case_a):
    assert "6/5 E I" in " ".join(case_a["T"].method[-1].equations)
    assert "4/5 + H L^2 G" in " ".join(case_a["T"].method[-1].equations)
    assert "(1 + H L^2 G" in " ".join(case_a["BW"].method[-1].equations)


def test_not_a_buildings_profile(twins_below_the_surface, case_a):
    with pytest.raises(TypeError, match="along a building"):
        gs.check_building(twins_below_the_surface, **judgments())
    with pytest.raises(TypeError, match="along a building"):
        gs.check_building(case_a["T"], **judgments())
    with pytest.raises(TypeError, match="along a building"):
        gs.check_building(pd.DataFrame(), **judgments())


def test_result_shape(case_a):
    result = case_a["T"]
    assert list(result.zones.columns) == list(ZONE_COLUMNS)
    assert list(result.checks.columns) == list(CHECK_COLUMNS)
    assert str(result.zones["category"].dtype) == "Int64"
    assert result.validity == "within"
    assert result.asset.building_id == "B-1"


# The cut-off, flat walls and the depth limit (AC 2, 9, 10, 16).

CUTOFF = gs.buildings.trough_width_cutoff(multiple=2.5)


@pytest.mark.parametrize("beam", BEAMS)
def test_case_a_with_a_cutoff(case_a, beam):
    result = check(wall(-30, 30), trough_at_depth(), beam, cutoff=CUTOFF)
    whole = case_a[beam]
    assert result.zones["start"].iloc[0] - 30 == golden("-22.5")
    assert result.zones["end"].iloc[-1] - 30 == golden("22.5")
    one = zone(result, 1)
    assert one["length"] == golden("13.5")
    assert one["deflection"] * 1000 == golden("1.36588")
    assert one["deflection_distance"] - 30 == golden("-15.8187")
    assert one["deflection_ratio"] == golden("1.01176e-4")
    assert one["horizontal_strain"] == golden("2.30558e-4")
    bending, total = {
        "BW": ("1.11061e-4", "3.41619e-4"),
        "T": ("1.33668e-4", "3.64226e-4"),
    }[beam]
    assert one["bending_strain"] == golden(bending)
    assert one["total_bending_strain"] == golden(total)
    # Zone 2 is unchanged by the cut-off, and so is Stage 1.
    for column in ("start", "end", "deflection", "horizontal_strain", *STRAINS):
        assert zone(result, 2)[column] == pytest.approx(
            zone(whole, 2)[column], rel=1e-9
        )
    for name in ("settlement", "slope"):
        assert checks(result).loc[name].equals(checks(whole).loc[name])
    # Stations outside the range have no zone, and rows mark its ends.
    values = result.values
    outside = (values["distance"] < 7.5 - 1e-6) | (values["distance"] > 52.5 + 1e-6)
    assert outside.any()
    assert values.loc[outside, "zone"].isna().all()
    assert values.loc[outside, "chord"].isna().all()
    assert values.loc[~outside, "zone"].notna().all()
    for end in (7.5, 52.5):
        hit = np.isclose(values["distance"], end, atol=1e-6)
        assert values.loc[hit, "critical"].all()
    entry = {e.name: e for e in result.inputs}["cutoff"]
    assert entry.value == "2.5 i from each trough's axis"
    assert any("within 2.5 i" in text for text in result.assumptions)


@pytest.mark.parametrize("beam", BEAMS)
def test_case_c_with_a_cutoff(beam):
    north, source = twins(15.0)
    building = wall(-30, 45, reference=north, depth=0.0)
    result = check(building, source, beam, cutoff=CUTOFF)
    assert result.zones["start"].iloc[0] - 30 == golden("-25")
    assert result.zones["end"].iloc[-1] - 30 == golden("40")
    one = zone(result, 1)
    assert one["length"] == golden("17.4304")
    assert one["deflection"] * 1000 == golden("1.84690")
    assert one["deflection_ratio"] == golden("1.05959e-4")
    assert one["horizontal_strain"] == golden("2.05135e-4")
    assert one["total_bending_strain"] == golden(
        {"BW": "3.41290e-4", "T": "3.65948e-4"}[beam]
    )


def test_a_far_wall_is_one_flat_zone():
    result = check(wall(500, 560), trough_at_depth())
    assert result.zones["mode"].tolist() == ["flat"]
    row = zone(result, 1)
    assert row["bending_strain"] == 0
    assert row["diagonal_strain"] == 0
    assert row["deflection"] == 0
    assert math.isnan(row["deflection_distance"])
    assert row["category"] == 0
    assert checks(result).loc["damage_category", "category"] == 0


def test_a_wall_parallel_to_the_tunnel_is_flat():
    building = gs.buildings.Building(
        building_id="P", vertices=[(5, -20), (5, 20)], foundation_depth=2, height=8
    )
    result = check(building, trough_at_depth())
    assert result.zones["mode"].tolist() == ["flat"]
    row = zone(result, 1)
    assert (row["bending_strain"], row["diagonal_strain"]) == (0, 0)
    assert row["horizontal_strain"] == pytest.approx(0, abs=1e-15)
    settlement = S_MAX_A * math.exp(-(5**2) / (2 * 9.0**2))
    assert checks(result).loc["settlement", "value"] == pytest.approx(
        settlement, rel=1e-9
    )


def test_a_wall_beyond_the_cutoff_has_no_zone():
    result = check(wall(30, 60), trough_at_depth(), cutoff=CUTOFF)
    assert result.zones.empty
    assert list(result.zones.columns) == list(ZONE_COLUMNS)
    table = checks(result)
    assert list(table.index) == ["settlement", "slope", "damage_category"]
    row = table.loc["damage_category"]
    assert math.isnan(row["value"])
    assert math.isnan(row["utilization"])
    assert row["passes"] is pd.NA
    assert row["zone"] is pd.NA
    assert row["category"] is pd.NA
    assert math.isfinite(table.loc["settlement", "value"])
    assert result.values["zone"].isna().all()
    flag = next(f for f in result.warnings if f.limit.startswith("cut-off"))
    assert flag.verdict == "within"
    assert "2.5 i" in flag.reason
    assert flag.limit == "cut-off: 2.5 i from each trough's axis"
    assert flag.points == tuple(range(len(result.values)))
    assert result.validity == "within"
    assert "damage_category: not determined, no zone assessed" in repr(result)


def depth_flags(result):
    return [f for f in result.warnings if f.limit.startswith("z_f/z0")]


def test_depth_within_the_limit():
    result = check(wall(-30, 30, depth=2.0), trough_at_depth())
    (flag,) = depth_flags(result)
    assert flag.verdict == "within"
    assert "no range of validity" in flag.reason
    assert "z_f/z0 = 0.1" in flag.reason
    assert flag.points == tuple(range(len(result.values)))
    assert result.validity == "within"


@pytest.mark.parametrize(("depth", "ratio"), [(4.0, "0.2"), (5.0, "0.25")])
def test_depth_at_and_beyond_the_limit(depth, ratio):
    result = check(wall(-30, 30, depth=depth), trough_at_depth())
    (flag,) = depth_flags(result)
    assert flag.verdict == "outside"
    assert f"z_f/z0 = {ratio}" in flag.reason
    assert f"({depth:g} m of 20 m)" in flag.reason
    assert "Harris & Franzius (2006)" in flag.reason
    assert "piled foundations" in flag.reason
    assert flag.limit.startswith("z_f/z0 < 0.2")
    assert flag.points == tuple(range(len(result.values)))
    assert result.validity == "outside"


def test_the_shallower_tunnel_governs_the_depth_limit():
    deep = tunnel(axis_depth=40.0)
    shallow = deep.parallel(offset=30.0, diameter=6.0, axis_depth=15.0)
    width = gs.sources.linear_trough_width(trough_width_parameter=0.5)
    source = gs.superpose(
        deep=gs.sources.transverse_trough(
            deep, volume_loss=1 * u.percent, trough_width=width
        ),
        shallow=gs.sources.transverse_trough(
            shallow, volume_loss=1 * u.percent, trough_width=width
        ),
    )
    result = check(wall(-30, 60, reference=deep, depth=3.0), source)
    (flag,) = depth_flags(result)
    assert flag.verdict == "outside"
    assert flag.source == "shallow"
    assert "z_f/z0 = 0.2 " in flag.reason
    assert result.validity == "outside"
    # Deeper on both, the one within the limit gives no flag of its own.
    within = check(wall(-30, 60, reference=deep, depth=2.0), source)
    (flag,) = depth_flags(within)
    assert flag.verdict == "within"
    assert "z_f/z0 = 0.133" in flag.reason


def test_the_summary(case_a):
    text = repr(case_a["T"])
    lines = text.splitlines()
    assert lines[0] == "building_check of 'B-1': within, 65 stations"
    assert lines[1] == "  stage 1:"
    assert lines[2].startswith("    settlement: 0.012533 m at 30 m")
    assert lines[3].startswith("    slope: 0.00084464 at 21 m")
    assert lines[4] == "  stage 2:"
    assert lines[5] == (
        "    zone 1: hogging, L 21 m, Delta/L 0.0001272, eps_h 0.0001771, "
        "eps_bt 0.000384, category 0 (negligible)"
    )
    assert lines[6].startswith("    zone 2: sagging, L 18 m")
    assert "eps_dt 0.0001562" in lines[6]
    assert lines[8].startswith(
        "    damage_category: zone 1, category 0 (negligible): 0.00038397 (bending)"
    )
    assert "largest" not in text


def test_to_dict_is_json_ready():
    for result in (
        check(wall(-30, 30), trough_at_depth(), acceptable_category=4),
        check(jones_wall(-25, 6.5), jones_trough()),
        check(wall(30, 60), trough_at_depth(), cutoff=CUTOFF),
    ):
        data = json.loads(json.dumps(result.to_dict(), allow_nan=False))
        assert len(data["zones"]) == len(result.zones)
        assert len(data["checks"]) == len(result.checks)
    accepted = check(wall(-30, 30), trough_at_depth(), acceptable_category=4)
    data = accepted.to_dict()
    governing = data["checks"][-1]
    assert governing["check"] == "damage_category"
    assert governing["limit"] is None  # infinity
    assert governing["zone"] == 1
    assert governing["category"] == 0
    assert data["zones"][0]["mode"] == "hogging"
    assert data["zones"][1]["deflection_distance"] == pytest.approx(30)
    assert data["checks"][0]["zone"] is None
