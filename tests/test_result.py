import json

import pandas as pd
import pytest

import garisenda as gs
from garisenda._inputs import record
from garisenda._result import CHECK_COLUMNS, empty_checks
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
