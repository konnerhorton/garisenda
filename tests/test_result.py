import json
from dataclasses import dataclass

import pandas as pd
import pytest

import garisenda as gs
from garisenda._inputs import record, record_method
from garisenda._result import (
    CHECK_COLUMNS,
    ZONE_COLUMNS,
    checks_frame,
    empty_checks,
    unit_text,
    value_text,
    zones_frame,
)
from garisenda.sources import Flag, MethodRecord

u = gs.units


def result(**changes):
    values = pd.DataFrame(
        {
            "distance": [0.0, 10.0, 20.0, 30.0],
            "vertical": [0.001, 0.004, 0.003, float("nan")],
            "along_strain": [1e-5, -2e-4, 3e-4, 0.0],
            "vertical_curvature": [2e-5, -4e-5, 1e-5, 0.0],
            "verdict": ["within", "outside", "outside", "within"],
        }
    )
    values.attrs["units"] = {
        "distance": "m",
        "vertical": "m",
        "along_strain": "dimensionless",
        "vertical_curvature": "1/m",
    }
    _, spacing = record(
        "spacing",
        gs.Sourced(5 * u.m, source="Project basis"),
        kind="design judgment",
        unit="m",
        plain_number="read as SI",
    )
    _, volume_loss = record(
        "volume_loss",
        1 * u.percent,
        kind="design judgment",
        unit="dimensionless",
        plain_number="refuse",
    )
    arguments = {
        "analysis": "movement_profile",
        "subject": "W-1",
        "values": values,
        "checks": empty_checks(),
        "method": (MethodRecord("A method", ("a = b",), "A source"),),
        "assumptions": ("One.", "Two."),
        "inputs": (spacing, volume_loss),
        "validity": "outside",
        "warnings": (Flag("outside", "Below the surface.", "depth", (1, 2)),),
    }
    arguments.update(changes)
    return gs.Result(**arguments)


def test_checks_empty_with_columns():
    assert tuple(result().checks.columns) == CHECK_COLUMNS
    assert result().checks.empty


def test_to_frame_is_a_copy_with_units():
    original = result()
    frame = original.to_frame()
    pd.testing.assert_frame_equal(frame, original.values)
    assert frame.attrs["units"]["vertical"] == "m"
    frame.loc[0, "vertical"] = 99.0
    frame.attrs["units"]["vertical"] = "ft"
    assert original.values.loc[0, "vertical"] == 0.001
    assert original.values.attrs["units"]["vertical"] == "m"


def test_to_dict_is_json_ready():
    data = json.loads(json.dumps(result().to_dict(), allow_nan=False))
    assert data["analysis"] == "movement_profile"
    assert data["values"]["distance"] == [0.0, 10.0, 20.0, 30.0]
    assert data["values"]["vertical"][3] is None
    assert data["units"]["vertical_curvature"] == "1/m"
    assert data["checks"] == []
    assert data["inputs"][0] == {
        "name": "spacing",
        "magnitude": 5.0,
        "unit": "m",
        "kind": "design judgment",
        "given_as": "quantity in m",
        "source": "Project basis",
    }
    assert data["inputs"][1]["unit"] == "dimensionless"
    assert data["inputs"][1]["magnitude"] == pytest.approx(0.01)
    assert data["warnings"][0]["points"] == [1, 2]
    assert data["validity"] == "outside"
    assert data["method"][0]["equations"] == ["a = b"]


def test_repr_summary():
    text = repr(result())
    assert text.splitlines()[0] == "movement_profile of 'W-1': outside, 4 stations"
    assert "settlement: largest 0.004 m at 10 m" in text
    assert "tension 0.0003 at 20 m; compression -0.0002 at 10 m" in text
    assert "hogging 2e-05 1/m at 0 m; sagging -4e-05 1/m at 10 m" in text
    assert "outside: Below the surface." in text
    assert "at 2 stations, distance 10 m to 20 m" in text
    assert "2 assumptions" in text


def test_repr_skips_absent_columns():
    values = pd.DataFrame({"distance": [0.0, 1.0], "vertical": [0.0, 0.1]})
    text = repr(result(values=values, warnings=(), validity="within"))
    assert "settlement" in text
    assert "strain" not in text
    assert "curvature" not in text


# AC 1: governing values


def test_governing_reads_the_extremes():
    governing = result().governing().set_index("name")
    assert list(governing.index) == [
        "largest_settlement",
        "largest_tension",
        "largest_compression",
        "largest_hogging",
        "largest_sagging",
    ]
    assert governing.loc["largest_settlement"].to_dict() == {
        "column": "vertical",
        "value": 0.004,
        "unit": "m",
        "distance": 10.0,
        "verdict": "outside",
    }
    assert governing.loc["largest_compression", "value"] == -2e-4
    assert governing.loc["largest_hogging", "distance"] == 0.0
    assert governing.loc["largest_hogging", "verdict"] == "within"


def test_governing_with_no_value_of_a_sign_is_nan_not_zero():
    values = pd.DataFrame(
        {
            "distance": [0.0, 10.0],
            "along_strain": [-1e-4, -2e-4],
            "verdict": ["within", "within"],
        }
    )
    governing = result(values=values).governing().set_index("name")
    tension = governing.loc["largest_tension"]
    assert pd.isna(tension["value"])
    assert pd.isna(tension["distance"])
    assert tension["verdict"] is None
    assert governing.loc["largest_compression", "value"] == -2e-4
    text = repr(result(values=values, warnings=()))
    assert "strain along: tension none; compression -0.0002 at 10 m" in text


def test_governing_tie_goes_to_the_smaller_distance():
    values = pd.DataFrame(
        {
            "distance": [0.0, 10.0, 20.0],
            "along_strain": [3e-4, -1e-4, 3e-4 * (1 + 1e-12)],
        }
    )
    governing = result(values=values).governing().set_index("name")
    assert governing.loc["largest_tension", "distance"] == 0.0
    assert governing.loc["largest_tension", "verdict"] is None


def test_governing_leaves_out_absent_columns():
    values = pd.DataFrame({"distance": [0.0, 1.0], "vertical": [0.0, 0.1]})
    governing = result(values=values).governing()
    assert governing["name"].tolist() == ["largest_settlement"]


def test_equality_compares_tables_by_content():
    first = result()
    second = result(values=first.values.copy())
    assert first == second
    changed = first.values.copy()
    changed.loc[0, "vertical"] = 0.002
    assert first != result(values=changed)
    assert first != result(subject="W-2")
    assert first != "W-1"


# M2 (a), spec decision 13, AC 9: each flag names the source it came from.


def test_a_flag_from_a_lone_source_is_shown_as_before():
    data = result().to_dict()
    assert data["warnings"][0]["source"] == ""
    assert "  outside: Below the surface." in repr(result()).splitlines()


def test_a_flag_shows_its_source():
    flag = Flag("outside", "Below the surface.", "depth", (1, 2), source="twins.north")
    named = result(warnings=(flag,))
    assert named.to_dict()["warnings"][0]["source"] == "twins.north"
    assert "  outside: twins.north: Below the surface." in repr(named).splitlines()


def test_twins_below_the_surface_flag_each_tunnel(twins_below_the_surface):
    twins = twins_below_the_surface
    assert set(twins.values["verdict"]) == {"outside"}
    assert [flag.source for flag in twins.warnings] == ["north", "south"]
    stations = len(twins.values)
    for flag in twins.warnings:
        assert flag.verdict == "outside"
        assert flag.points == tuple(range(stations))
    data = json.loads(json.dumps(twins.to_dict(), allow_nan=False))
    assert [warning["source"] for warning in data["warnings"]] == ["north", "south"]
    text = repr(twins)
    for flag in twins.warnings:
        assert f"outside: {flag.source}: {flag.reason}" in text


# M2 (b), plan step 1: a record holding a named method (AC 8, the views)


def method_record():
    _, entry = record_method(
        "trough_width",
        Method("Mair et al. (1993), clay"),
        kind="design judgment",
        expected=Method,
        how="Write a method.",
    )
    return entry


@dataclass(frozen=True)
class Method:
    name: str


def test_to_dict_shows_a_method_by_name():
    with_method = result(inputs=(*result().inputs, method_record()))
    data = json.loads(json.dumps(with_method.to_dict(), allow_nan=False))
    assert data["inputs"][2] == {
        "name": "trough_width",
        "magnitude": "Mair et al. (1993), clay",
        "unit": "",
        "kind": "design judgment",
        "given_as": "method",
        "source": None,
    }


def test_value_text_and_unit_text_of_a_method():
    entry = method_record()
    assert value_text(entry) == "Mair et al. (1993), clay"
    assert unit_text(entry) == ""
    _, quantity = record(
        "spacing", 5, kind="design judgment", unit="m", plain_number="read as SI"
    )
    assert value_text(quantity) == "5.0 m"
    assert unit_text(quantity) == "m"


def test_views_take_a_method_record():
    with_method = result(inputs=(*result().inputs, method_record()))
    pd.testing.assert_frame_equal(with_method.to_frame(), result().to_frame())
    assert repr(with_method) == repr(result())
    assert with_method == result(inputs=(*result().inputs, method_record()))


# M3 (a) AC 13: the checks table


def test_empty_checks_has_every_column():
    checks = empty_checks()
    assert tuple(checks.columns) == CHECK_COLUMNS
    assert len(CHECK_COLUMNS) == 15
    assert str(checks["passes"].dtype) == "boolean"
    assert str(checks["value"].dtype) == "float64"
    assert str(checks["zone"].dtype) == "Int64"
    assert str(checks["category"].dtype) == "Int64"


def checks_table():
    nan = float("nan")
    columns = {
        "check": ["tensile_strain", "radius_of_curvature", "axial_tension"],
        "value": [3.2e-4, 6462.9, nan],
        "unit": ["dimensionless", "m", "dimensionless"],
        "limit": [1e-3, nan, 1e-3],
        "utilization": [0.32, nan, nan],
        "governing_distance": [24.41, 40.0, nan],
        "passes": pd.array([True, pd.NA, True], dtype="boolean"),
        "governed_by": ["analytical", "analytical", "analytical"],
        "analytical": [3.2e-4, 6462.9, nan],
        "analytical_distance": [24.41, 40.0, nan],
        "discrete": [3.1e-4, float("inf"), nan],
        "discrete_distance": [24.41, 40.0, nan],
        "difference": [-1e-5, float("inf"), nan],
    }
    rows = [
        {name: column[index] for name, column in columns.items()} for index in range(3)
    ]
    return checks_frame(rows)


def test_checks_with_no_limit_round_trip_to_json():
    data = json.loads(
        json.dumps(result(checks=checks_table()).to_dict(), allow_nan=False)
    )
    radius = data["checks"][1]
    assert radius["check"] == "radius_of_curvature"
    assert radius["limit"] is None
    assert radius["utilization"] is None
    assert radius["passes"] is None
    assert radius["discrete"] is None
    assert data["checks"][0]["passes"] is True


def test_summary_lists_each_check():
    text = repr(result(checks=checks_table()))
    assert (
        "tensile_strain: 0.00032 at 24.41 m (analytical), "
        "utilization 0.32 against 0.001" in text
    )
    assert "radius_of_curvature: 6462.9 m at 40 m (analytical), no limit" in text
    assert "axial_tension: none" in text


# M4 (a) AC 16: zones on every result, and the new check columns


def test_zones_are_empty_with_their_columns_by_default():
    zones = result().zones
    assert tuple(zones.columns) == ZONE_COLUMNS
    assert len(zones) == 0
    assert str(zones["zone"].dtype) == "Int64"
    assert str(zones["category"].dtype) == "Int64"
    assert str(zones["tensile_strain"].dtype) == "float64"
    assert zones.attrs["units"]["deflection"] == "m"
    assert result().to_dict()["zones"] == []


def made_by_analyses():
    tunnel = gs.sources.IdealizedTunnel(
        reference_point=(0, 0), azimuth=0 * u.degree, diameter=6.0, axis_depth=20.0
    )
    source = gs.sources.transverse_surface_trough(
        tunnel, volume_loss=1 * u.percent, trough_width_parameter=0.5
    )
    utility = gs.utilities.perpendicular_utility(
        tunnel,
        utility_id="A",
        station=0,
        start_offset=-40,
        end_offset=40,
        depth=2.0,
        elevation_reference="axis",
        diameter=0.3,
    )
    profile = gs.movement_profile(utility, source, spacing=1.0)
    strain = u.Quantity(1000, "µε")
    limits = {
        "tensile_strain_limit": strain,
        "compressive_strain_limit": strain,
        "bending_strain_limit": strain,
        "radius_of_curvature_limit": 5000 * u.m,
        "interaction": "greenfield",
    }
    return (
        profile,
        gs.check_continuous_pipe(profile, interval=1 * u.m, **limits),
        gs.check_jointed_pipe(
            profile,
            pipe_lengths={("spun_grey_iron", 0.3 * u.m): 4 * u.m},
            pipe_type="spun_grey_iron",
            joint_rotation_limit=1.5 * u.degree,
            joint_pullout_limit=15 * u.mm,
            **limits,
        ),
    )


def test_profiles_and_pipe_checks_have_empty_zones_and_every_check_column():
    for made in made_by_analyses():
        assert tuple(made.zones.columns) == ZONE_COLUMNS
        assert made.zones.empty
        assert tuple(made.checks.columns) == CHECK_COLUMNS
        assert made.checks["zone"].isna().all()
        assert made.checks["category"].isna().all()
        assert str(made.checks["zone"].dtype) == "Int64"


def zones_table():
    return zones_frame(
        [
            {
                "zone": 1,
                "mode": "hogging",
                "start": 0.0,
                "end": 21.0,
                "length": 21.0,
                "deflection": 2.67e-3,
                "deflection_distance": 11.7,
                "deflection_ratio": 1.27e-4,
                "horizontal_strain": 1.77e-4,
                "bending_strain": 1.78e-4,
                "diagonal_strain": 8.8e-5,
                "total_bending_strain": 3.55e-4,
                "total_diagonal_strain": 2.07e-4,
                "tensile_strain": 3.55e-4,
                "governed_by": "bending",
                "category": 1,
                "label": "1",
                "severity": "very slight",
            }
        ]
    )


def test_zones_round_trip_to_json_and_take_part_in_equality():
    made = result(zones=zones_table())
    data = json.loads(json.dumps(made.to_dict(), allow_nan=False))
    (zone,) = data["zones"]
    assert zone["zone"] == 1
    assert zone["category"] == 1
    assert zone["mode"] == "hogging"
    assert made == result(zones=zones_table())
    assert made != result()


def test_a_check_row_with_zone_and_category_round_trips():
    table = checks_frame(
        [
            {
                "check": "damage_category",
                "value": 3.55e-4,
                "unit": "dimensionless",
                "limit": float("inf"),
                "utilization": 0.0,
                "passes": True,
                "zone": 1,
                "category": 1,
            }
        ]
    )
    assert table["zone"].iloc[0] == 1
    assert table["discrete"].isna().all()
    data = json.loads(json.dumps(result(checks=table).to_dict(), allow_nan=False))
    row = data["checks"][0]
    assert row["zone"] == 1
    assert row["category"] == 1
    assert row["limit"] is None
    assert row["governing_distance"] is None
