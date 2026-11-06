import math
from dataclasses import dataclass, replace

import numpy as np
import pandas as pd
import pytest

import garisenda as gs
from garisenda._inputs import record_method

u = gs.units
REL = 1e-6  # hand calculation carried to 8 figures (spec, acceptance criteria)
ROOT3 = math.sqrt(3)

GOVERNING = [
    "largest_settlement",
    "largest_tension",
    "largest_compression",
    "largest_hogging",
    "largest_sagging",
]

# The spec's hand table: (V_L, k) -> settlement, tension, compression, hogging,
# sagging, and the distance of tension and hogging (the others are at 20 m).
HAND = {
    (0.01, 0.5): (
        1.1279827e-2,
        2.5168697e-4,
        -5.6399136e-4,
        5.0337393e-5,
        -1.1279827e-4,
        2.6794919,
    ),
    (0.02, 0.5): (
        2.2559654e-2,
        5.0337393e-4,
        -1.1279827e-3,
        1.0067479e-4,
        -2.2559654e-4,
        2.6794919,
    ),
    (0.01, 0.4): (
        1.4099784e-2,
        3.1460871e-4,
        -7.0498920e-4,
        9.8315221e-5,
        -2.2030913e-4,
        6.1435935,
    ),
    (0.02, 0.4): (
        2.8199568e-2,
        6.2921741e-4,
        -1.4099784e-3,
        1.9663044e-4,
        -4.4061825e-4,
        6.1435935,
    ),
}


def crossing(volume_loss=1 * u.percent, trough_width_parameter=0.5, depth=0.0):
    tunnel = gs.sources.IdealizedTunnel(
        reference_point=(0, 0), azimuth=0 * u.degree, diameter=6.0, axis_depth=20.0
    )
    trough = gs.sources.transverse_surface_trough(
        tunnel,
        volume_loss=volume_loss,
        trough_width_parameter=trough_width_parameter,
    )
    utility = gs.utilities.perpendicular_utility(
        tunnel,
        utility_id="W-1",
        station=50,
        start_offset=-20,
        end_offset=20,
        depth=depth,
        elevation_reference="axis",
        diameter=0.3,
    )
    return gs.movement_profile(utility, trough, spacing=5.0)


def check_row(row, volume_loss, k):
    *values, peak = HAND[(volume_loss, k)]
    for name, value in zip(GOVERNING, values, strict=True):
        assert row[name] == pytest.approx(value, rel=REL), name
    assert row["largest_tension_distance"] == pytest.approx(peak, rel=REL)
    assert row["largest_hogging_distance"] == pytest.approx(peak, rel=REL)
    for name in ("largest_settlement", "largest_compression", "largest_sagging"):
        assert row[f"{name}_distance"] == pytest.approx(20.0, rel=1e-12)
    assert row["validity"] == "within"
    assert row["error"] is None


# AC 3: grid


def test_grid_against_the_hand_table():
    table = gs.sweep(
        crossing,
        vary={
            "volume_loss": [1, 2] * u.percent,
            "trough_width_parameter": [0.4, 0.5],
        },
        mode="grid",
    )
    assert table["run"].tolist() == [0, 1, 2, 3]
    expected = [(0.01, 0.4), (0.01, 0.5), (0.02, 0.4), (0.02, 0.5)]
    np.testing.assert_allclose(
        table[["volume_loss", "trough_width_parameter"]].to_numpy(),
        expected,
        rtol=1e-12,
    )
    for (_, row), key in zip(table.iterrows(), expected, strict=True):
        check_row(row, *key)
    attrs = table.attrs
    assert attrs["units"]["volume_loss"] == "dimensionless"
    assert attrs["units"]["largest_settlement"] == "m"
    assert attrs["units"]["largest_sagging"] == "1/m"
    assert attrs["units"]["largest_tension_distance"] == "m"
    assert attrs["run"] == "crossing"
    assert attrs["mode"] == "grid"
    assert attrs["vary"] == ["volume_loss", "trough_width_parameter"]
    fixed = [entry["name"] for entry in attrs["fixed_inputs"]]
    for name in ("axis_depth", "diameter", "station", "depth", "spacing"):
        assert name in fixed
    assert fixed.count("diameter") == 2
    assert "volume_loss" not in fixed
    assert "trough_width_parameter" not in fixed
    assert list(table.columns[-3:]) == ["validity", "warnings", "error"]


# AC 4: paired


def test_paired_against_the_hand_table():
    table = gs.sweep(
        crossing,
        vary={
            "volume_loss": [1 * u.percent, 2 * u.percent],
            "trough_width_parameter": np.array([0.5, 0.4]),
        },
        mode="paired",
    )
    assert len(table) == 2
    check_row(table.iloc[0], 0.01, 0.5)
    check_row(table.iloc[1], 0.02, 0.4)
    assert table.attrs["mode"] == "paired"


def test_one_input_needs_no_mode():
    table = gs.sweep(crossing, vary={"volume_loss": [1, 2] * u.percent})
    assert len(table) == 2
    check_row(table.iloc[1], 0.02, 0.5)
    assert table.attrs["mode"] is None


# AC 5: a sweep row equals a direct call (SPEC §11)


def test_each_row_equals_a_direct_call():
    vary = {
        "volume_loss": [0.5, 1.5] * u.percent,
        "trough_width_parameter": [0.35, 0.6],
    }
    table = gs.sweep(crossing, vary=vary, mode="grid")
    for (_, row), (volume_loss, k) in zip(
        table.iterrows(),
        [(a, b) for a in vary["volume_loss"] for b in vary["trough_width_parameter"]],
        strict=True,
    ):
        direct = crossing(volume_loss=volume_loss, trough_width_parameter=k)
        for item in direct.governing().itertuples():
            assert row[item.name] == item.value
            assert row[f"{item.name}_distance"] == item.distance
        assert row["validity"] == direct.validity
        assert row["warnings"] == len(direct.warnings)


# AC 6: errors


def test_a_run_through_the_bore_is_recorded():
    table = gs.sweep(crossing, vary={"depth": [0.0, 20.0, 2.7]})
    assert table["error"].iloc[0] is None
    assert table["error"].iloc[1].startswith("ValueError: Utility 'W-1'")
    assert table["validity"].iloc[1] is None
    assert np.isnan(table["largest_settlement"].iloc[1])
    assert table["depth"].tolist() == [0.0, 20.0, 2.7]
    assert table["validity"].iloc[2] == "outside"
    assert table["warnings"].iloc[2] == 1


def test_every_run_raising_raises_the_first_error():
    def fails(depth):
        raise ValueError(f"failed at {depth}")

    with pytest.raises(ValueError, match=r"failed at 1$"):
        gs.sweep(fails, vary={"depth": [1, 2]})


def test_a_varied_input_run_ignores_raises():
    def ignores(volume_loss):
        return crossing()

    with pytest.raises(ValueError, match=r"run 1 was given volume_loss=.*pass"):
        gs.sweep(ignores, vary={"volume_loss": [1, 2] * u.percent})


def test_a_misnamed_input_raises():
    def misnamed(vl):
        return crossing(volume_loss=vl)

    with pytest.raises(ValueError, match="no input record named vl"):
        gs.sweep(misnamed, vary={"vl": [1, 2] * u.percent})


def test_an_input_outside_vary_that_changes_raises():
    def drifts(volume_loss):
        return crossing(volume_loss=volume_loss, trough_width_parameter=volume_loss.m)

    with pytest.raises(ValueError, match="trough_width_parameter isn't in vary"):
        gs.sweep(drifts, vary={"volume_loss": [1, 2] * u.percent})


@pytest.mark.parametrize(
    ("vary", "mode", "error", "match"),
    [
        (
            {"volume_loss": [1] * u.percent, "trough_width_parameter": [0.5]},
            None,
            TypeError,
            "mode is required with 2",
        ),
        ({"volume_loss": [1] * u.percent}, "grid", TypeError, "mode is for two"),
        (
            {"volume_loss": [1] * u.percent, "trough_width_parameter": [0.5]},
            "zip",
            ValueError,
            'mode must be "grid"',
        ),
        ({"a": [1], "b": [1], "c": [1], "d": [1]}, "grid", TypeError, "one to 3"),
        ({}, None, TypeError, "one to 3"),
        ({"volume_loss": []}, None, ValueError, "is empty"),
        ({"volume_loss": 1 * u.percent}, None, TypeError, "one-dimensional"),
        (
            {"volume_loss": [1, 2] * u.percent, "trough_width_parameter": [0.5]},
            "paired",
            ValueError,
            "equal length",
        ),
    ],
)
def test_bad_arguments_raise_before_any_run(vary, mode, error, match):
    calls = []

    def counts(**kwargs):
        calls.append(kwargs)
        return crossing()

    with pytest.raises(error, match=match):
        gs.sweep(counts, vary=vary, mode=mode)
    assert calls == []


def test_run_must_return_a_result():
    with pytest.raises(TypeError, match="returned dict"):
        gs.sweep(lambda volume_loss: {}, vary={"volume_loss": [1] * u.percent})


# M2 (a), spec decision 12, AC 13: inputs named for their source.


def twins(south_volume_loss=1 * u.percent, north_volume_loss=1 * u.percent):
    north = gs.sources.IdealizedTunnel(
        reference_point=(0, 0), azimuth=0 * u.degree, diameter=6.0, axis_depth=20.0
    )
    south = north.parallel(offset=15.0, diameter=6.0, axis_depth=20.0)
    source = gs.superpose(
        north=gs.sources.transverse_surface_trough(
            north, volume_loss=north_volume_loss, trough_width_parameter=0.5
        ),
        south=gs.sources.transverse_surface_trough(
            south, volume_loss=south_volume_loss, trough_width_parameter=0.5
        ),
    )
    utility = gs.utilities.perpendicular_utility(
        north,
        utility_id="W-1",
        station=50,
        start_offset=-30,
        end_offset=60,
        depth=0.0,
        elevation_reference="axis",
        diameter=0.3,
    )
    return gs.movement_profile(utility, source, spacing=2.5)


def test_a_dotted_name_is_passed_with_underscores():
    calls = []

    def run(**keywords):
        calls.append(keywords)
        return twins(**keywords)

    table = gs.sweep(run, vary={"south.volume_loss": [1.0, 1.5, 2.0] * u.percent})
    assert [list(call) for call in calls] == [["south_volume_loss"]] * 3
    assert list(table.columns[:2]) == ["run", "south.volume_loss"]
    assert table["south.volume_loss"].tolist() == pytest.approx(
        [0.01, 0.015, 0.02], rel=1e-12
    )
    assert table.attrs["vary"] == ["south.volume_loss"]
    assert table.attrs["units"]["south.volume_loss"] == "dimensionless"
    fixed = [entry["name"] for entry in table.attrs["fixed_inputs"]]
    assert "north.volume_loss" in fixed
    assert "south.volume_loss" not in fixed


def test_a_dotted_run_that_varies_the_wrong_tunnel_raises():
    def run(south_volume_loss):
        return twins(north_volume_loss=south_volume_loss)

    with pytest.raises(ValueError, match=r"run 0 was given south\.volume_loss=.*pass"):
        gs.sweep(run, vary={"south.volume_loss": [1.5, 2.0] * u.percent})


@pytest.mark.parametrize(
    ("vary", "match"),
    [
        ({"a.b-c": [1, 2]}, r"'a\.b-c' must be an input record's name"),
        ({"a.b": [1, 2], "a_b": [1, 2]}, r"'a\.b' and 'a_b'.*as a_b"),
        ({3: [1, 2]}, "3 must be an input record's name"),
    ],
)
def test_keys_that_dont_become_one_keyword_each_raise(vary, match):
    def run(**keywords):
        raise AssertionError("run before the arguments were checked")

    with pytest.raises(TypeError, match=match):
        gs.sweep(run, vary=vary, mode="grid" if len(vary) > 1 else None)


# M2 (b), plan step 1: a method record in a sweep (AC 9, with stand-ins)


@dataclass(frozen=True)
class StandIn:
    name: str


def with_method(result, name):
    _, entry = record_method(
        "trough_width",
        StandIn(name),
        kind="design judgment",
        expected=StandIn,
        how="Write a stand-in.",
    )
    return replace(result, inputs=(*result.inputs, entry))


def test_a_method_that_stays_the_same_is_a_fixed_input():
    def run(volume_loss):
        return with_method(crossing(volume_loss=volume_loss), "a")

    table = gs.sweep(run, vary={"volume_loss": [1, 2] * u.percent})
    assert list(table["error"]) == [None, None]
    fixed = {entry["name"]: entry for entry in table.attrs["fixed_inputs"]}
    assert fixed["trough_width"]["magnitude"] == "a"
    assert fixed["trough_width"]["unit"] == ""


def test_a_method_that_changes_between_runs_raises_naming_both():
    def run(volume_loss):
        return with_method(
            crossing(volume_loss=volume_loss), "a" if volume_loss.m < 1.5 else "b"
        )

    with pytest.raises(
        ValueError, match=r"trough_width isn't in vary but changed.*\(a in .*, b in"
    ):
        gs.sweep(run, vary={"volume_loss": [1, 2] * u.percent})


def test_a_method_cant_be_varied():
    def run(trough_width):
        return with_method(crossing(), trough_width)

    with pytest.raises(
        ValueError, match=r"run 0 was given trough_width=.*is a method.*per method"
    ):
        gs.sweep(run, vary={"trough_width": ["a", "b"]})


# M2 (b), AC 9: a sweep of the trough at depth


def at_depth(trough_width):
    tunnel = gs.sources.IdealizedTunnel(
        reference_point=(0, 0), azimuth=0 * u.degree, diameter=6.0, axis_depth=20.0
    )
    trough = gs.sources.transverse_trough(
        tunnel, volume_loss=1 * u.percent, trough_width=trough_width
    )
    utility = gs.utilities.perpendicular_utility(
        tunnel,
        utility_id="W-1",
        station=50,
        start_offset=-30,
        end_offset=30,
        depth=10,
        elevation_reference="axis",
        diameter=0.3,
    )
    return gs.movement_profile(utility, trough, spacing=2.5)


def test_a_sweep_of_k_for_the_linear_method():
    def run(trough_width_parameter):
        return at_depth(
            gs.sources.linear_trough_width(
                trough_width_parameter=trough_width_parameter
            )
        )

    table = gs.sweep(run, vary={"trough_width_parameter": [0.4, 0.5, 0.6]})
    assert list(table["error"]) == [None] * 3
    np.testing.assert_allclose(table["trough_width_parameter"], [0.4, 0.5, 0.6])
    # S_max = Q / i at z = 10 m, i = 10 k, Q = 0.11279827 m^2 (M2 (b) spec).
    np.testing.assert_allclose(
        table["largest_settlement"],
        [2.81995675e-2, 2.25596545e-2, 1.87997117e-2],
        rtol=REL,
    )
    fixed = {entry["name"]: entry for entry in table.attrs["fixed_inputs"]}
    assert fixed["trough_width"]["magnitude"] == "linear"


def test_a_sweep_that_switches_method_raises():
    def run(volume_loss):
        tunnel = gs.sources.IdealizedTunnel(
            reference_point=(0, 0), azimuth=0 * u.degree, diameter=6.0, axis_depth=20.0
        )
        width = (
            gs.sources.mair_trough_width()
            if volume_loss.m > 1.5
            else gs.sources.linear_trough_width(trough_width_parameter=0.5)
        )
        trough = gs.sources.transverse_trough(
            tunnel, volume_loss=volume_loss, trough_width=width
        )
        return gs.movement_profile(
            gs.utilities.perpendicular_utility(
                tunnel,
                utility_id="W-1",
                station=50,
                start_offset=-30,
                end_offset=30,
                depth=10,
                elevation_reference="axis",
                diameter=0.3,
            ),
            trough,
            spacing=2.5,
        )

    # The method changes between runs, so its record does: linear, then Mair's.
    with pytest.raises(
        ValueError,
        match=r"trough_width isn't in vary but changed.*\(linear in .*"
        r"Mair et al\. \(1993\), clay in run 1",
    ):
        gs.sweep(run, vary={"volume_loss": [1, 2] * u.percent})


# M3 (a), AC 14: a sweep of a utility check reports each check


def pipe_check(volume_loss=1 * u.percent, depth=2.0, radius_limit=1000 * u.m):
    tunnel = gs.sources.IdealizedTunnel(
        reference_point=(0, 0), azimuth=0 * u.degree, diameter=6.0, axis_depth=20.0
    )
    trough = gs.sources.transverse_trough(
        tunnel,
        volume_loss=volume_loss,
        trough_width=gs.sources.linear_trough_width(trough_width_parameter=0.5),
    )
    utility = gs.utilities.perpendicular_utility(
        tunnel,
        utility_id="A",
        station=0,
        start_offset=-40,
        end_offset=40,
        depth=depth,
        elevation_reference="axis",
        diameter=0.3,
    )
    profile = gs.movement_profile(utility, trough, spacing=1.0)
    limit = u.Quantity(500, "µε")
    return gs.check_continuous_pipe(
        profile,
        interval=1 * u.m,
        interaction="greenfield",
        tensile_strain_limit=limit,
        compressive_strain_limit=limit,
        bending_strain_limit=limit,
        radius_of_curvature_limit=radius_limit,
    )


CHECKS = [
    "axial_tension",
    "axial_compression",
    "bending",
    "tensile_strain",
    "compressive_strain",
    "radius_of_curvature",
]


def test_a_check_sweep_row_equals_a_direct_call():
    volume_losses = [0.5, 1.0, 1.5] * u.percent
    table = gs.sweep(pipe_check, vary={"volume_loss": volume_losses})
    for name in CHECKS:
        for suffix in ("", "_distance", "_utilization", "_passes"):
            assert f"{name}{suffix}" in table.columns
    assert list(table.columns[-3:]) == ["validity", "warnings", "error"]
    for (_, row), volume_loss in zip(table.iterrows(), volume_losses, strict=True):
        direct = pipe_check(volume_loss=volume_loss)
        for item in direct.governing().itertuples():
            assert row[item.name] == item.value
        for check in direct.checks.itertuples():
            assert row[check.check] == check.value
            assert row[f"{check.check}_distance"] == check.governing_distance
            assert row[f"{check.check}_utilization"] == check.utilization
            assert row[f"{check.check}_passes"] == check.passes
    # Compressive strain at 1 % is -719.50 µε (spec, case A), which fails a
    # 500 µε limit; at 0.5 % it is half, and passes.
    assert table["compressive_strain_passes"].tolist() == [True, False, False]
    units = table.attrs["units"]
    assert units["tensile_strain"] == "dimensionless"
    assert units["radius_of_curvature"] == "m"
    assert units["radius_of_curvature_distance"] == "m"
    assert units["bending_utilization"] == "dimensionless"
    assert str(table["bending_passes"].dtype) == "boolean"


def test_a_check_with_no_limit_and_a_failed_run_in_a_sweep():
    def run(depth):
        return pipe_check(depth=depth, radius_limit=None)

    table = gs.sweep(run, vary={"depth": [2.0, 20.0]})
    first, failed = table.iloc[0], table.iloc[1]
    assert first["radius_of_curvature"] > 0
    assert np.isnan(first["radius_of_curvature_utilization"])
    assert first["radius_of_curvature_passes"] is pd.NA
    assert first["bending_passes"]
    assert failed["error"].startswith("ValueError")
    for name in CHECKS:
        assert np.isnan(failed[name])
        assert np.isnan(failed[f"{name}_utilization"])
        assert failed[f"{name}_passes"] is pd.NA


def test_a_sweep_of_profiles_has_no_check_columns():
    table = gs.sweep(crossing, vary={"volume_loss": [1, 2] * u.percent})
    for name in CHECKS:
        assert name not in table.columns
        assert f"{name}_passes" not in table.columns
