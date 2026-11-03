"""Critical distances by root-finding (M2 (a), spec decisions 8-10, AC 6)."""

import math

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

import garisenda as gs
from garisenda.sources._critical import find_critical_distances

u = gs.units
SAMPLING = 1 / 8
TOLERANCE = 1e-9


def trough(**tunnel_changes):
    arguments = {
        "reference_point": (0, 0),
        "azimuth": 0 * u.degree,
        "diameter": 6.0,
        "axis_depth": 20.0,
    }
    arguments.update(tunnel_changes)
    return gs.sources.transverse_surface_trough(
        gs.sources.IdealizedTunnel(**arguments),
        volume_loss=1 * u.percent,
        trough_width_parameter=0.5,
    )


def find(source, start, end):
    return find_critical_distances(
        source, start=start, end=end, sampling=SAMPLING, tolerance=TOLERANCE
    )


def test_perpendicular_segment_gives_the_analytic_distances():
    source = trough()
    start, end = (-25, 50, 0), (35, 50, 0)
    np.testing.assert_allclose(
        find(source, start, end),
        source.critical_distances(start=start, end=end),
        rtol=0,
        atol=1e-8,
    )


@st.composite
def level_segments(draw):
    diameter = draw(st.floats(2.0, 15.0))
    cover = draw(st.floats(1.0, 50.0))
    tunnel = gs.sources.IdealizedTunnel(
        reference_point=(draw(st.floats(-1e3, 1e3)), draw(st.floats(-1e3, 1e3))),
        azimuth=draw(st.floats(0.0, 360.0)) * u.degree,
        diameter=diameter,
        axis_depth=cover + diameter / 2,
        reference_station=draw(st.floats(-1e3, 1e3)),
    )
    source = gs.sources.transverse_surface_trough(
        tunnel,
        volume_loss=draw(st.floats(0.1, 5.0)) * u.percent,
        trough_width_parameter=draw(st.floats(0.2, 1.0)),
    )
    i = source.trough_width
    station = draw(st.floats(-1e3, 1e3))
    offset = draw(st.floats(-4.0, 4.0)) * i
    # The angle from the tunnel's normal, short of parallel to the tunnel.
    # Within 0.01 degrees of perpendicular (but not at it), the lateral
    # curvature is under 2e-4 of the along curvature, and whether its peaks
    # count depends on where each method puts its threshold on n.l.
    angle = math.radians(
        draw(st.one_of(st.just(0.0), st.floats(0.01, 89.0)))
        * draw(st.sampled_from([-1, 1]))
    )
    length = draw(st.floats(1.0, 20.0)) * i
    t = np.array(tunnel.tangent)
    n = np.array(tunnel.normal)
    p0 = np.array([tunnel.reference_x, tunnel.reference_y])
    begin = p0 + (station - tunnel.reference_station) * t + offset * n
    finish = begin + length * (math.cos(angle) * n + math.sin(angle) * t)
    return source, (*begin, 0.0), (*finish, 0.0), length


def interior(distances, length):
    # A zero at an end is found or not depending on rounding, by either method.
    distances = np.asarray(distances)
    return distances[(distances > 1e-6) & (distances < length - 1e-6)]


@given(level_segments())
def test_a_lone_trough_gives_its_analytic_distances(segment):
    source, start, end, length = segment
    np.testing.assert_allclose(
        interior(find(source, start, end), length),
        interior(source.critical_distances(start=start, end=end), length),
        rtol=0,
        atol=1e-8,
    )


@pytest.mark.parametrize("offset", [5.0, 0.0, 10.0], ids=lambda o: f"o={o}")
def test_segment_parallel_to_the_tunnel_has_none(offset):
    # At offsets 0 and i, every derivative along it is rounding noise about zero.
    distances = find(trough(), (offset, -10, 0), (offset, 30, 0))
    assert distances.shape == (0,)


def test_bore_message_gives_distances():
    # Through the bore at axis depth: |o| < 3 m at distances 17-23 m.
    with pytest.raises(ValueError) as caught:
        find(trough(), (-20, 50, 20), (20, 50, 20))
    message = str(caught.value)
    assert "[" not in message
    assert message == (
        "Points inside the bore can't be evaluated at distances "
        "17.5, 18.75, 20, 21.25, 22.5 m along the segment."
    )


def test_vertical_segment_raises():
    with pytest.raises(ValueError, match="vertical"):
        find(trough(), (40, 0, 0), (40, 0, 10))
