"""The building and its builder (docs/work/m4a-building-damage.md, AC 13)."""

import numpy as np
import pytest

import garisenda as gs

u = gs.units


def tunnel(**changes):
    arguments = {
        "reference_point": (0, 0),
        "azimuth": 0 * u.degree,
        "diameter": 6.0,
        "axis_depth": 20.0,
    }
    arguments.update(changes)
    return gs.sources.IdealizedTunnel(**arguments)


def built(tunnel_=None, **changes):
    arguments = {
        "building_id": "B-1",
        "station": 50,
        "start_offset": -30,
        "end_offset": 30,
        "height": 8,
        "foundation_depth": 2,
    }
    arguments.update(changes)
    return gs.buildings.perpendicular_building(tunnel_ or tunnel(), **arguments)


def test_placed_by_depth():
    building = built()
    np.testing.assert_allclose(
        building.vertices, [[-30, 50, 2], [30, 50, 2]], atol=1e-12
    )
    assert building.foundation_depth == 2.0
    assert building.height == 8.0
    assert building.building_id == "B-1"


def test_placed_by_elevation():
    building = built(
        foundation_depth=None, foundation_elevation=97.5, ground_elevation=100.0
    )
    np.testing.assert_allclose(building.vertices[:, 2], [2.5, 2.5])
    names = [entry.name for entry in building.inputs]
    assert names[-2:] == ["ground_elevation", "foundation_elevation"]


def test_rotated_tunnel_places_the_wall_square_at_the_station():
    rotated = tunnel(
        reference_point=(100, 200), azimuth=30 * u.degree, reference_station=1000
    )
    building = built(rotated, station=1025, start_offset=-15, end_offset=35)
    station, offset = rotated.station_offset(
        x=building.vertices[:, 0], y=building.vertices[:, 1]
    )
    np.testing.assert_allclose(station, [1025, 1025], rtol=1e-12)
    np.testing.assert_allclose(offset, [-15, 35], rtol=1e-12)


def test_build_record_inputs_and_assumption():
    reference = tunnel()
    building = built(reference, station=gs.Sourced(50, source="Survey"))
    assert building.built == gs.utilities.BuildRecord(
        tunnel=reference,
        station=50.0,
        start_offset=-30.0,
        end_offset=30.0,
        orientation="perpendicular",
        elevation_reference=None,
    )
    names = [entry.name for entry in building.inputs]
    assert names == [
        "station",
        "start_offset",
        "end_offset",
        "height",
        "foundation_depth",
    ]
    assert {entry.kind for entry in building.inputs} == {"geometry"}
    assert building.inputs[0].source == "Survey"
    (assumption,) = building.assumptions
    assert "perpendicular" in assumption
    assert "station 50 m" in assumption


def test_given_by_vertices_matches_the_built_one():
    direct = gs.buildings.Building(
        building_id="B-1",
        vertices=[(-30, 50), (30, 50)],
        foundation_depth=2 * u.m,
        height=8000 * u.mm,
    )
    np.testing.assert_allclose(direct.vertices, built().vertices, atol=1e-12)
    assert direct.height == built().height
    assert direct.built is None
    assert direct.assumptions == ()
    assert [entry.name for entry in direct.inputs] == [
        "vertices",
        "foundation_depth",
        "height",
    ]


def test_vertices_are_read_only():
    with pytest.raises(ValueError):
        built().vertices[0, 0] = 1.0


@pytest.mark.parametrize(
    "level",
    [
        {"foundation_depth": 2.0, "foundation_elevation": 98.0},
        {"foundation_depth": None, "foundation_elevation": 98.0},
        {"foundation_depth": None, "ground_elevation": 100.0},
        {"foundation_depth": None},
    ],
)
def test_level_given_ambiguously_raises(level):
    with pytest.raises(
        TypeError, match="foundation_depth, or as foundation_elevation with"
    ):
        built(**level)


def test_foundation_above_the_ground_raises():
    with pytest.raises(ValueError, match="above the ground surface"):
        built(foundation_depth=None, foundation_elevation=101, ground_elevation=100)


def test_equal_offsets_raise():
    with pytest.raises(ValueError, match="no length"):
        built(start_offset=5, end_offset=5)


@pytest.mark.parametrize("height", [0.0, -1.0])
def test_height_not_positive_raises(height):
    with pytest.raises(ValueError, match="height must be positive"):
        built(height=height)


def test_non_finite_station_raises():
    with pytest.raises(ValueError, match="station must be finite"):
        built(station=float("nan"))


def building(vertices=((0, 0), (1, 0)), **changes):
    arguments = {
        "building_id": "B-2",
        "vertices": vertices,
        "foundation_depth": 1.0,
        "height": 5.0,
    }
    arguments.update(changes)
    return gs.buildings.Building(**arguments)


@pytest.mark.parametrize(
    ("vertices", "message"),
    [
        ([(0, 0), (1, 0), (2, 0)], "Assess each straight wall as its own building"),
        ([(0, 0)], "straight line of two vertices"),
        ([(0, 0), (np.nan, 0)], r"finite.*\[1\]"),
        ([(0, 0), (0, 0)], "same point"),
        ([(0, 0, 1), (1, 0, 1)], r"shape \(2, 2\)"),
    ],
)
def test_bad_vertices_raise(vertices, message):
    with pytest.raises(ValueError, match=message):
        building(vertices)


@pytest.mark.parametrize("depth", [-0.1, float("inf")])
def test_bad_foundation_depth_raises(depth):
    with pytest.raises(ValueError, match="foundation_depth must be zero or more"):
        building(foundation_depth=depth)


def test_direct_height_not_positive_raises():
    with pytest.raises(ValueError, match="height must be positive"):
        building(height=0.0)


def test_empty_id_raises():
    with pytest.raises(ValueError, match="building_id"):
        building(building_id="")
