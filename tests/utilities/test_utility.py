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


def case_a(tunnel_=None, **changes):
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
    return gs.utilities.perpendicular_utility(tunnel_ or tunnel(), **arguments)


# AC 1: builder geometry


def test_case_a_vertices():
    utility = case_a()
    np.testing.assert_allclose(
        utility.vertices, [[-20, 50, 0], [20, 50, 0]], atol=1e-12
    )
    assert utility.diameter == 0.3
    assert utility.utility_id == "W-1"


def test_rotated_tunnel_vertices_at_station_and_offsets():
    rotated = tunnel(
        reference_point=(100, 200), azimuth=30 * u.degree, reference_station=1000
    )
    utility = case_a(rotated, station=1025, start_offset=-15, end_offset=35)
    station, offset = rotated.station_offset(
        x=utility.vertices[:, 0], y=utility.vertices[:, 1]
    )
    np.testing.assert_allclose(station, [1025, 1025], rtol=1e-12)
    np.testing.assert_allclose(offset, [-15, 35], rtol=1e-12)
    direction = np.diff(utility.vertices[:, :2], axis=0)[0]
    direction /= np.linalg.norm(direction)
    assert abs(direction @ np.array(rotated.tangent)) < 1e-12


# AC 2: builder record


def test_build_record_inputs_and_assumption():
    reference = tunnel()
    utility = case_a(reference, station=gs.Sourced(50, source="Crossing schedule"))
    assert utility.built == gs.utilities.BuildRecord(
        tunnel=reference,
        station=50.0,
        start_offset=-20.0,
        end_offset=20.0,
        orientation="perpendicular",
        elevation_reference="axis",
    )
    names = [entry.name for entry in utility.inputs]
    assert names == ["station", "start_offset", "end_offset", "diameter", "depth"]
    assert {entry.kind for entry in utility.inputs} == {"geometry"}
    assert utility.inputs[0].source == "Crossing schedule"
    assert len(utility.assumptions) == 1
    assert "perpendicular" in utility.assumptions[0]
    assert "station 50 m" in utility.assumptions[0]


def test_direct_utility_has_no_build_record():
    utility = gs.utilities.Utility(
        utility_id="G-2", vertices=[(-20, -20, 0), (20, 20, 0)], diameter=0.2
    )
    assert utility.built is None
    assert utility.assumptions == ()
    assert [entry.name for entry in utility.inputs] == ["vertices", "diameter"]


def test_vertices_in_other_units():
    utility = gs.utilities.Utility(
        utility_id="G-2",
        vertices=np.array([[0, 0, 1], [1, 0, 1]]) * u.km,
        diameter=300 * u.mm,
    )
    np.testing.assert_allclose(utility.vertices, [[0, 0, 1000], [1000, 0, 1000]])
    assert utility.diameter == pytest.approx(0.3)


def test_vertices_are_read_only():
    with pytest.raises(ValueError):
        case_a().vertices[0, 0] = 1.0


# AC 3: elevation reference


@pytest.mark.parametrize(
    ("reference", "elevation"), [("invert", 97.0), ("crown", 97.6)]
)
def test_case_c_elevation_reference(reference, elevation):
    utility = case_a(
        depth=None,
        elevation=elevation,
        ground_elevation=100.0,
        elevation_reference=reference,
        diameter=0.6,
    )
    np.testing.assert_allclose(utility.vertices[:, 2], [2.7, 2.7], rtol=1e-12)
    assert len(utility.assumptions) == 2
    assert reference in utility.assumptions[1]
    assert "wall thickness" in utility.assumptions[1]
    names = [entry.name for entry in utility.inputs]
    assert names[-2:] == ["ground_elevation", "elevation"]


def test_axis_reference_by_depth():
    utility = case_a(depth=2.7, diameter=0.6)
    np.testing.assert_allclose(utility.vertices[:, 2], [2.7, 2.7])
    assert len(utility.assumptions) == 1


def test_missing_elevation_reference_names_it():
    arguments = {
        "utility_id": "W-1",
        "station": 50,
        "start_offset": -20,
        "end_offset": 20,
        "depth": 0,
        "diameter": 0.3,
    }
    with pytest.raises(TypeError, match="elevation_reference"):
        gs.utilities.perpendicular_utility(tunnel(), **arguments)


def test_unknown_elevation_reference_lists_the_three():
    with pytest.raises(ValueError, match="'invert', 'axis', 'crown'"):
        case_a(elevation_reference="centerline")


@pytest.mark.parametrize(
    "level",
    [
        {"depth": 2.0, "elevation": 97.0, "ground_elevation": 100.0},
        {"depth": None, "elevation": 97.0},
        {"depth": None, "ground_elevation": 100.0},
        {"depth": None},
    ],
)
def test_level_given_ambiguously_raises(level):
    with pytest.raises(TypeError, match="depth, or as elevation with ground_elevation"):
        case_a(**level)


def test_axis_above_the_surface_raises():
    with pytest.raises(ValueError, match="above the ground surface"):
        case_a(depth=0.1, elevation_reference="invert", diameter=0.6)


def test_equal_offsets_raise():
    with pytest.raises(ValueError, match="no length"):
        case_a(start_offset=5, end_offset=5)


def test_non_finite_station_raises():
    with pytest.raises(ValueError, match="station must be finite"):
        case_a(station=float("nan"))


# AC 4: utility checks


def utility(vertices, diameter=0.3, utility_id="G-2"):
    return gs.utilities.Utility(
        utility_id=utility_id, vertices=vertices, diameter=diameter
    )


def test_three_vertices_raise_naming_m5():
    with pytest.raises(ValueError, match="M5"):
        utility([(0, 0, 1), (1, 0, 1), (2, 0, 1)])


@pytest.mark.parametrize(
    ("vertices", "message"),
    [
        ([(0, 0, 1)], "at least two vertices"),
        ([(0, 0, 1), (np.nan, 0, 1)], r"finite.*\[1\]"),
        ([(0, 0, -1), (1, 0, 1)], r"above the ground surface.*\[0\]"),
        ([(0, 0, 1), (0, 0, 1)], "zero length"),
        ([(0, 0), (1, 0)], r"shape \(N, 3\)"),
    ],
)
def test_bad_vertices_raise(vertices, message):
    with pytest.raises(ValueError, match=message):
        utility(vertices)


@pytest.mark.parametrize("diameter", [0.0, -0.3, float("inf")])
def test_bad_diameter_raises(diameter):
    with pytest.raises(ValueError, match="diameter must be positive"):
        utility([(0, 0, 1), (1, 0, 1)], diameter=diameter)


def test_empty_id_raises():
    with pytest.raises(ValueError, match="utility_id"):
        utility([(0, 0, 1), (1, 0, 1)], utility_id="")
