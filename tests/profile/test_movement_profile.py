import dataclasses
import json
import math

import numpy as np
import pandas as pd
import pytest

import garisenda as gs

u = gs.units
REL = 1e-6  # hand calculation carried to 8 figures (spec, acceptance criteria)
ROOT3 = math.sqrt(3)

COLUMNS_BUILT = [
    "distance",
    "x",
    "y",
    "depth",
    "station",
    "offset",
    "along",
    "vertical",
    "lateral",
    "along_strain",
    "along_strain_gradient",
    "vertical_slope",
    "vertical_curvature",
    "lateral_slope",
    "lateral_curvature",
    "critical",
    "verdict",
]
MOVEMENT_COLUMNS = COLUMNS_BUILT[6:15]

# M1 (a)'s table: o, S, u_n, dS/do, d2S/do2, du_n/do, d2u_n/do2.
TABLE = {
    0.0: (1.1279827e-2, 0.0, 0.0, -1.1279827e-4, -5.6399136e-4, 0.0),
    5.0: (
        9.9544126e-3,
        -2.4886031e-3,
        -4.9772063e-4,
        -7.4658094e-5,
        -3.7329047e-4,
        6.8436587e-5,
    ),
    10.0: (6.8415611e-3, -3.4207805e-3, -6.8415611e-4, 0.0, 0.0, 6.8415611e-5),
}
# Scales for zeros in the table, per column (spec: 1e-12 of the column's scale
# for exact zeros; a table zero is zero to its 8 figures).
SCALES = {
    "along": 3.4e-3,
    "vertical": 1.1e-2,
    "lateral": 3.4e-3,
    "along_strain": 5.6e-4,
    "along_strain_gradient": 6.8e-5,
    "vertical_slope": 6.8e-4,
    "vertical_curvature": 1.1e-4,
    "lateral_slope": 5.6e-4,
    "lateral_curvature": 6.8e-5,
}


def tunnel():
    return gs.sources.IdealizedTunnel(
        reference_point=(0, 0), azimuth=0 * u.degree, diameter=6.0, axis_depth=20.0
    )


def trough(tunnel_=None):
    return gs.sources.transverse_surface_trough(
        tunnel_ or tunnel(), volume_loss=1 * u.percent, trough_width_parameter=0.5
    )


def built(source, **changes):
    arguments = {
        "utility_id": "W-1",
        "station": 50,
        "start_offset": -20,
        "end_offset": 20,
        "depth": 0,
        "elevation_reference": "axis",
        "diameter": 0.3,
    }
    arguments.update(changes)
    return gs.utilities.perpendicular_utility(source.tunnel, **arguments)


def case_a(spacing=5.0, **changes):
    source = trough()
    return gs.movement_profile(built(source, **changes), source, spacing=spacing)


def row_at(result, distance):
    values = result.values
    index = int(np.argmin(np.abs(values["distance"] - distance)))
    assert values["distance"].iloc[index] == pytest.approx(distance, abs=1e-6)
    return values.iloc[index]


def close(row, expected):
    for column, value in expected.items():
        scale = SCALES.get(column, abs(value))
        assert row[column] == pytest.approx(value, rel=REL, abs=REL * scale), column


def exactly_zero(values, column):
    assert np.max(np.abs(values[column])) <= 1e-12 * SCALES[column], column


# AC 5: stations


def test_case_a_stations():
    values = case_a().values
    expected = [0, 20 - 10 * ROOT3, 5, 10, 15, 20, 25, 30, 35, 20 + 10 * ROOT3, 40]
    np.testing.assert_allclose(values["distance"], expected, rtol=1e-12, atol=1e-12)
    assert values["critical"].tolist() == [
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        False,
    ]


def test_spacing_larger_than_the_utility_gives_ends_and_critical_points():
    values = case_a(spacing=100.0).values
    expected = [0, 20 - 10 * ROOT3, 10, 20, 30, 20 + 10 * ROOT3, 40]
    np.testing.assert_allclose(values["distance"], expected, rtol=1e-12, atol=1e-12)


def test_spacing_as_a_quantity():
    np.testing.assert_allclose(
        case_a(spacing=500 * u.cm).values["distance"], case_a().values["distance"]
    )


def test_missing_spacing_raises_the_judgment_error():
    source = trough()
    with pytest.raises(TypeError, match="spacing is a required design judgment"):
        gs.movement_profile(built(source), source)


@pytest.mark.parametrize("spacing", [0.0, -1.0, float("nan")])
def test_bad_spacing_raises(spacing):
    with pytest.raises(ValueError, match="spacing must be positive"):
        case_a(spacing=spacing)


def test_too_many_stations_raise():
    with pytest.raises(ValueError, match="too fine"):
        case_a(spacing=1e-5)


# AC 6: golden values


@pytest.mark.parametrize("o", [10.0, 5.0, 0.0])
def test_case_a_golden_values(o):
    s, u_n, d_s, d2_s, d_n, d2_n = TABLE[o]
    close(
        row_at(case_a(), o + 20),
        {
            "along": u_n,
            "vertical": s,
            "along_strain": d_n,
            "along_strain_gradient": d2_n,
            "vertical_slope": d_s,
            "vertical_curvature": d2_s,
        },
    )


def test_case_a_named_values_at_inflection():
    close(
        row_at(case_a(), 30),
        {
            "along": -3.4207805e-3,
            "vertical": 6.8415611e-3,
            "along_strain": 0.0,
            "vertical_slope": -6.8415611e-4,
            "vertical_curvature": 0.0,
            "along_strain_gradient": 6.8415611e-5,
        },
    )


def test_case_a_station_offset_and_lateral():
    values = case_a().values
    assert list(values.columns) == COLUMNS_BUILT
    np.testing.assert_allclose(values["station"], 50, rtol=1e-12)
    np.testing.assert_allclose(values["offset"], values["distance"] - 20, atol=1e-12)
    for column in ("lateral", "lateral_slope", "lateral_curvature"):
        exactly_zero(values, column)
    assert set(values["verdict"]) == {"within"}


@pytest.mark.parametrize("o", [10.0, 5.0, 0.0])
def test_case_b_reversed(o):
    # Distance runs from offset 20 to -20, so a = -n and distance = 20 - o.
    # Along, slope and the strain gradient change sign; strain and curvature
    # don't.
    s, u_n, d_s, d2_s, d_n, d2_n = TABLE[o]
    source = trough()
    result = gs.movement_profile(
        built(source, start_offset=20, end_offset=-20), source, spacing=5.0
    )
    close(
        row_at(result, 20 - o),
        {
            "along": -u_n,
            "vertical": s,
            "along_strain": d_n,
            "along_strain_gradient": -d2_n,
            "vertical_slope": -d_s,
            "vertical_curvature": d2_s,
        },
    )


def test_case_b_named_values():
    source = trough()
    result = gs.movement_profile(
        built(source, start_offset=20, end_offset=-20), source, spacing=5.0
    )
    close(
        row_at(result, 10),
        {"along": 3.4207805e-3, "vertical_slope": 6.8415611e-4},
    )


def case_d(spacing):
    utility = gs.utilities.Utility(
        utility_id="G-2", vertices=[(-20, -20, 0), (20, 20, 0)], diameter=0.2
    )
    return gs.movement_profile(utility, trough(), spacing=spacing)


def test_case_d_critical_distances():
    values = case_d(100.0).values
    # With the lateral curvature peaks at o = -+0.74196378 i (M2 (a)).
    expected = [
        *[0, 3.7893738, 14.142136, 17.791319, 28.284271],
        *[38.777224, 42.426407, 52.779169, 40 * 2**0.5],
    ]
    np.testing.assert_allclose(values["distance"], expected, rtol=REL)
    assert values["critical"].tolist() == [False, *[True] * 7, False]


def test_case_d_at_45_degrees():
    # 5 sqrt(2) puts a station at 25 sqrt(2) = 35.355339 m, offset 5.
    result = case_d(5 * 2**0.5)
    assert "station" not in result.values
    close(
        row_at(result, 35.355339),
        {
            "along": -1.7597082e-3,
            "lateral": -1.7597082e-3,
            "vertical": 9.9544126e-3,
            "along_strain": -1.8664524e-4,
            "lateral_slope": -1.8664524e-4,
            "vertical_slope": -3.5194163e-4,
            "along_strain_gradient": 2.4195987e-5,
            "lateral_curvature": 2.4195987e-5,
            "vertical_curvature": -3.7329047e-5,
        },
    )


# AC 8: below the surface


@pytest.mark.parametrize(
    ("reference", "elevation"), [("invert", 97.0), ("crown", 97.6)]
)
def test_case_c_buried_is_outside_with_surface_values(reference, elevation):
    result = case_a(
        depth=None,
        elevation=elevation,
        ground_elevation=100.0,
        elevation_reference=reference,
        diameter=0.6,
    )
    values = result.values
    np.testing.assert_allclose(values["depth"], 2.7, rtol=1e-12)
    assert set(values["verdict"]) == {"outside"}
    assert result.validity == "outside"
    assert len(result.warnings) == 1
    assert result.warnings[0].points == tuple(range(len(values)))
    surface = case_a().values
    for column in ["distance", *MOVEMENT_COLUMNS]:
        np.testing.assert_allclose(values[column], surface[column], rtol=1e-12)


# AC 9: result parts


def test_result_parts():
    result = case_a()
    assert result.analysis == "movement_profile"
    assert result.subject == "W-1"
    units = result.values.attrs["units"]
    assert units["distance"] == "m"
    assert units["along_strain"] == "dimensionless"
    assert units["vertical_curvature"] == "1/m"
    assert set(units) == set(COLUMNS_BUILT) - {"critical", "verdict"}
    assert result.checks.empty
    assert "check" in result.checks.columns
    names = [record.name for record in result.method]
    assert names == [
        "Transverse Gaussian surface trough",
        "Movement profile along a straight line",
    ]
    assert any("greenfield" in text for text in result.assumptions)
    assert any("perpendicular" in text for text in result.assumptions)
    assert any("Idealized straight tunnel" in text for text in result.assumptions)
    inputs = {entry.name: entry for entry in result.inputs}
    assert inputs["spacing"].kind == "design judgment"
    assert inputs["spacing"].value.m_as("m") == 5.0
    assert inputs["volume_loss"].kind == "design judgment"
    assert inputs["utility.station"].kind == "geometry"
    assert inputs["station_merge_tolerance"].kind == "constant or setting"
    assert result.validity == "within"
    assert result.warnings == ()


# AC 10: views on a real profile


def test_views_of_case_a():
    result = case_a()
    frame = result.to_frame()
    frame.loc[0, "vertical"] = 1.0
    assert result.values.loc[0, "vertical"] != 1.0
    data = json.loads(json.dumps(result.to_dict(), allow_nan=False))
    assert data["values"]["critical"][1] is True
    text = repr(result)
    assert text.startswith("movement_profile of 'W-1': within, 11 stations")
    assert "settlement: largest 0.01128 m at 20 m" in text
    assert "sagging -0.0001128 1/m at 20 m" in text
    assert "compression -0.00056399 at 20 m" in text
    assert "lateral" not in text


def test_repr_of_case_c_lists_the_warning_range():
    text = repr(case_a(depth=2.7))
    assert "outside, 11 stations" in text
    assert "at 11 stations, distance 0 m to 40 m" in text


# AC 11: nothing dropped


def test_utility_through_the_bore_raises_naming_it():
    with pytest.raises(ValueError, match=r"Utility 'W-1'.*inside the bore.* 20 m"):
        case_a(depth=20.0)


def test_bore_error_gives_the_bore_the_utility_and_a_remedy():
    # At 0.5 m spacing, 11 stations lie inside the bore, at |o| < 3 m.
    with pytest.raises(ValueError) as caught:
        case_a(spacing=0.5, depth=19.85, elevation_reference="crown")
    message = str(caught.value)
    assert "[" not in message
    assert message == (
        "Utility 'W-1': Points inside the bore can't be evaluated at 11 points "
        "from 17.5 to 22.5 m along the segment. The bore has its axis at depth "
        "20 m and diameter 6 m, so it spans depths 17 to 23 m. The utility's "
        "axis is at depth 20 m. Check its depth, and its elevation_reference "
        "('crown'), which is converted to the axis with the given diameter."
    )


def test_bore_error_for_a_utility_given_by_vertices():
    utility = gs.utilities.Utility(
        utility_id="G-3", vertices=[(-20, 0, 18), (20, 0, 22)], diameter=0.2
    )
    with pytest.raises(ValueError) as caught:
        gs.movement_profile(utility, trough(), spacing=5.0)
    message = str(caught.value)
    assert message.startswith("Utility 'G-3': Points inside the bore")
    assert message.endswith(
        "The utility's axis is at depths 18 to 22 m. Check its vertices' depths."
    )


# M1 (c) AC 1, 2: governing values and the result's source and asset

# The spec's hand table, row 1 (V_L 1 %, k 0.5): name -> (value, distance).
GOVERNING_A = {
    "largest_settlement": (1.1279827e-2, 20.0),
    "largest_tension": (2.5168697e-4, 20 - 10 * ROOT3),
    "largest_compression": (-5.6399136e-4, 20.0),
    "largest_hogging": (5.0337393e-5, 20 - 10 * ROOT3),
    "largest_sagging": (-1.1279827e-4, 20.0),
}


def test_case_a_governing_values():
    governing = case_a().governing().set_index("name")
    assert list(governing.index) == list(GOVERNING_A)
    for name, (value, distance) in GOVERNING_A.items():
        row = governing.loc[name]
        assert row["value"] == pytest.approx(value, rel=REL), name
        assert row["distance"] == pytest.approx(distance, rel=1e-12), name
        assert row["verdict"] == "within"
    assert (
        governing["unit"].tolist()
        == ["m", "dimensionless", "dimensionless"] + ["1/m"] * 2
    )


def test_result_keeps_its_source_and_asset_outside_the_views():
    source = trough()
    utility = built(source)
    result = gs.movement_profile(utility, source, spacing=5.0)
    assert result.source is source
    assert result.asset is utility
    assert "source" not in result.to_dict()
    assert "asset" not in result.to_dict()
    assert "Trough" not in repr(result)
    assert list(result.to_frame().columns) == COLUMNS_BUILT
    assert dataclasses.replace(result, source=None, asset=None) == result


# M2 (b), AC 1: the trough at depth through movement_profile, on a utility
# built perpendicular at station 50, axis depth 10 m, offsets -30 to 30 m.
# Distance runs toward +n, so along is u_n. (offset, S, u_n), from the M2 (b)
# spec's cases A and B at z = 10 m.
AT_DEPTH = {
    "Mair": (
        gs.sources.mair_trough_width,
        [
            (0.0, 1.67108552e-2, 0.0),
            (6.75, 1.01356460e-2, -3.29408495e-3),
            (10.0, 5.57707713e-3, -2.68525936e-3),
            (-10.0, 5.57707713e-3, 2.68525936e-3),
        ],
    ),
    "linear": (
        lambda: gs.sources.linear_trough_width(trough_width_parameter=0.5),
        [
            (0.0, 2.25596545e-2, 0.0),
            (5.0, 1.36831221e-2, -6.84156105e-3),
            (10.0, 3.05311723e-3, -3.05311723e-3),
            (-5.0, 1.36831221e-2, 6.84156105e-3),
        ],
    ),
}


@pytest.mark.parametrize("method", sorted(AT_DEPTH))
def test_trough_at_depth_through_the_profile(method):
    width, rows = AT_DEPTH[method]
    source = gs.sources.transverse_trough(
        tunnel(), volume_loss=1 * u.percent, trough_width=width()
    )
    utility = built(source, start_offset=-30, end_offset=30, depth=10)
    result = gs.movement_profile(utility, source, spacing=2.5)
    values = result.values
    np.testing.assert_allclose(values["depth"], 10.0, rtol=1e-12)
    for offset, settlement, along in rows:
        row = row_at(result, offset + 30)
        assert row["offset"] == pytest.approx(offset, abs=1e-9)
        assert row["vertical"] == pytest.approx(settlement, rel=REL)
        assert row["along"] == pytest.approx(along, rel=REL, abs=1e-15)
    assert result.validity == "within"
    records = {entry.name: entry for entry in result.inputs}
    assert records["trough_width"].value == width().name


# TODO #22: input records are named for their owner, and no two share a name.


def test_the_utility_inputs_are_named_for_it():
    result = case_a()
    names = [entry.name for entry in result.inputs]
    assert len(names) == len(set(names))
    assert "diameter" in names
    assert "utility.diameter" in names
    inputs = {entry.name: entry for entry in result.inputs}
    assert inputs["diameter"].value.m_as("m") == 6.0
    assert inputs["utility.diameter"].value.m_as("m") == 0.3


def test_twin_tunnel_inputs_have_unique_names(twins_below_the_surface):
    names = [entry.name for entry in twins_below_the_surface.inputs]
    assert len(names) == len(set(names))
    for name in ("north.diameter", "south.diameter", "utility.diameter"):
        assert name in names
    assert "diameter" not in names


# M4 (a): a building's profile


def building_and_utility(depth=2.0):
    source = gs.sources.transverse_trough(
        tunnel(),
        volume_loss=1 * u.percent,
        trough_width=gs.sources.linear_trough_width(trough_width_parameter=0.5),
    )
    wall = gs.buildings.perpendicular_building(
        source.tunnel,
        building_id="B-1",
        station=50,
        start_offset=-30,
        end_offset=30,
        height=8,
        foundation_depth=depth,
    )
    pipe = built(source, start_offset=-30, end_offset=30, depth=depth)
    return (
        gs.movement_profile(wall, source, spacing=2.5),
        gs.movement_profile(pipe, source, spacing=2.5),
    )


def test_a_building_profile_equals_a_utility_profile_on_the_same_line():
    wall, pipe = building_and_utility()
    assert wall.subject == "B-1"
    assert wall.asset.building_id == "B-1"
    pd.testing.assert_frame_equal(wall.values, pipe.values)
    assert wall.values.attrs == pipe.values.attrs
    assert wall.validity == pipe.validity


def test_the_building_inputs_are_named_for_it():
    wall, _ = building_and_utility()
    names = [entry.name for entry in wall.inputs]
    assert len(names) == len(set(names))
    for name in ("building.height", "building.foundation_depth", "building.station"):
        assert name in names
    assert not any(name.startswith("utility.") for name in names)
    inputs = {entry.name: entry for entry in wall.inputs}
    assert inputs["building.height"].value.m_as("m") == 8.0


def test_bore_error_for_a_building_names_its_foundation():
    wall = gs.buildings.perpendicular_building(
        tunnel(),
        building_id="B-9",
        station=50,
        start_offset=-20,
        end_offset=20,
        height=8,
        foundation_depth=19.0,
    )
    with pytest.raises(ValueError) as caught:
        gs.movement_profile(wall, trough(), spacing=5.0)
    message = str(caught.value)
    assert message.startswith("Building 'B-9': Points inside the bore")
    assert message.endswith(
        "The building's foundation is at depth 19 m. Check its foundation depth "
        "or elevation."
    )
