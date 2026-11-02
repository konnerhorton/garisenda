import pint
import pytest

import garisenda as gs

u = gs.units


def tunnel(**changes):
    arguments = {
        "reference_point": (0, 0),
        "azimuth": 0 * u.degree,
        "diameter": 6,
        "axis_depth": 20,
    }
    arguments.update(changes)
    return gs.sources.IdealizedTunnel(**arguments)


def rotated():
    return gs.sources.IdealizedTunnel(
        reference_point=(100, 200),
        azimuth=30 * u.degree,
        diameter=6.0,
        axis_depth=20.0,
        reference_station=1000,
    )


def test_station_and_offset_of_the_rotated_tunnel():
    # Spec hand calculation: station 1025 m, offset +10 m.
    station, offset = rotated().station_offset(x=121.16025404, y=216.65063509)
    assert station == pytest.approx(1025.0, rel=1e-9)
    assert offset == pytest.approx(10.0, rel=1e-9)


def test_left_of_the_tunnel_is_negative():
    _, offset = rotated().station_offset(x=100 - 8.6602540, y=200 + 5.0)
    assert offset == pytest.approx(-10.0, rel=1e-6)


def test_azimuth_zero_has_its_right_toward_positive_x():
    tunnel = gs.sources.IdealizedTunnel(
        reference_point=(0, 0), azimuth=0 * u.degree, diameter=6, axis_depth=20
    )
    assert tunnel.tangent == pytest.approx((0.0, 1.0))
    assert tunnel.normal == pytest.approx((1.0, 0.0))
    station, offset = tunnel.station_offset(x=[5.0, -5.0], y=[3.0, 3.0])
    assert list(offset) == [5.0, -5.0]
    assert list(station) == [3.0, 3.0]


def test_elevation_with_ground_gives_the_same_depth():
    by_elevation = gs.sources.IdealizedTunnel(
        reference_point=(0, 0),
        azimuth=0 * u.degree,
        diameter=6,
        axis_elevation=80 * u.m,
        ground_elevation=100 * u.m,
    )
    assert by_elevation.axis_depth == pytest.approx(20.0, rel=1e-12)


@pytest.mark.parametrize(
    ("axis", "named"),
    [
        ({}, "none of them"),
        ({"axis_depth": 20, "axis_elevation": 80}, "axis_depth, axis_elevation"),
        ({"axis_elevation": 80}, "axis_elevation"),
        ({"ground_elevation": 100}, "ground_elevation"),
        (
            {"axis_depth": 20, "axis_elevation": 80, "ground_elevation": 100},
            "axis_depth, axis_elevation, ground_elevation",
        ),
    ],
)
def test_axis_must_be_given_one_way(axis, named):
    with pytest.raises(TypeError, match=f"got {named}"):
        gs.sources.IdealizedTunnel(
            reference_point=(0, 0), azimuth=0 * u.degree, diameter=6, **axis
        )


@pytest.mark.parametrize("diameter", [0, -6])
def test_diameter_must_be_positive(diameter):
    with pytest.raises(ValueError, match="diameter must be positive"):
        gs.sources.IdealizedTunnel(
            reference_point=(0, 0),
            azimuth=0 * u.degree,
            diameter=diameter,
            axis_depth=20,
        )


@pytest.mark.parametrize("depth", [3.0, 2.0])
def test_bore_must_not_break_the_surface(depth):
    with pytest.raises(ValueError, match="breaks the ground surface"):
        gs.sources.IdealizedTunnel(
            reference_point=(0, 0), azimuth=0 * u.degree, diameter=6, axis_depth=depth
        )


def test_plain_azimuth_is_refused():
    with pytest.raises(TypeError, match=r"azimuth=30 \* gs\.units\.degree"):
        gs.sources.IdealizedTunnel(
            reference_point=(0, 0), azimuth=30, diameter=6, axis_depth=20
        )


def test_length_in_seconds_is_refused():
    with pytest.raises(pint.DimensionalityError, match="axis_depth"):
        gs.sources.IdealizedTunnel(
            reference_point=(0, 0),
            azimuth=0 * u.degree,
            diameter=6,
            axis_depth=20 * u.s,
        )


@pytest.mark.parametrize("depth", [20, 20 * u.m, 2000 * u.cm])
def test_axis_depth_in_any_length_unit(depth):
    tunnel = gs.sources.IdealizedTunnel(
        reference_point=(0, 0), azimuth=0 * u.degree, diameter=6, axis_depth=depth
    )
    assert tunnel.axis_depth == pytest.approx(20.0, rel=1e-12)


def test_inputs_are_recorded():
    tunnel = gs.sources.IdealizedTunnel(
        reference_point=(0 * u.m, 0 * u.m),
        azimuth=gs.Sourced(30 * u.degree, source="Alignment drawing A-101"),
        diameter=6,
        axis_depth=20,
    )
    records = {entry.name: entry for entry in tunnel.inputs}
    assert set(records) == {
        "reference_point",
        "azimuth",
        "diameter",
        "axis_depth",
        "reference_station",
    }
    assert records["azimuth"].source == "Alignment drawing A-101"
    assert records["azimuth"].given_as == "quantity in deg"
    assert records["diameter"].given_as == "plain number, read as m"
    assert records["reference_station"].given_as == "default, 0 m"
    assert all(entry.kind == "geometry" for entry in tunnel.inputs)
    assert "Idealized straight tunnel" in tunnel.assumptions[0]


def test_non_finite_input_is_refused():
    with pytest.raises(ValueError, match="axis_depth must be finite"):
        gs.sources.IdealizedTunnel(
            reference_point=(0, 0),
            azimuth=0 * u.degree,
            diameter=6,
            axis_depth=float("nan"),
        )
