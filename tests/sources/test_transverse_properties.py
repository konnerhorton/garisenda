"""Physics the trough must obey, over many inputs (SPEC §11)."""

import math

import numpy as np
from hypothesis import given
from hypothesis import strategies as st

import garisenda as gs

u = gs.units


@st.composite
def troughs(draw):
    diameter = draw(st.floats(2.0, 15.0))
    cover = draw(st.floats(1.0, 50.0))
    tunnel = gs.sources.IdealizedTunnel(
        reference_point=(draw(st.floats(-1e3, 1e3)), draw(st.floats(-1e3, 1e3))),
        azimuth=draw(st.floats(0.0, 360.0)) * u.degree,
        diameter=diameter,
        axis_depth=cover + diameter / 2,
        reference_station=draw(st.floats(-1e3, 1e3)),
    )
    return gs.sources.transverse_surface_trough(
        tunnel,
        volume_loss=draw(st.floats(0.1, 5.0)) * u.percent,
        trough_width_parameter=draw(st.floats(0.2, 1.0)),
    )


def point(source, station, offset):
    """Plan coordinates of a station and offset (in units of i)."""
    tunnel = source.tunnel
    along = station - tunnel.reference_station
    o = offset * source.trough_width
    x = tunnel.reference_x + along * tunnel.tangent[0] + o * tunnel.normal[0]
    y = tunnel.reference_y + along * tunnel.tangent[1] + o * tunnel.normal[1]
    return x, y


offsets = st.floats(-3.0, 3.0)
stations = st.floats(-1e3, 1e3)


@given(troughs(), stations, offsets)
def test_derivatives_match_finite_differences(source, station, offset):
    x, y = point(source, station, offset)
    # Below the crown and clear of the bore, so depth can be stepped both ways.
    depth = (source.tunnel.axis_depth - source.tunnel.diameter / 2) / 2
    step = 1e-4 * source.trough_width
    base = np.array([x, y, depth])
    gradient_scale = source.maximum_settlement / source.trough_width
    hessian_scale = gradient_scale / source.trough_width
    third_scale = hessian_scale / source.trough_width
    movement = source.evaluate(x=x, y=y, depth=depth)
    for j in range(3):
        shift = np.zeros(3)
        shift[j] = step
        ahead = source.evaluate(
            x=base[0] + shift[0], y=base[1] + shift[1], depth=base[2] + shift[2]
        )
        behind = source.evaluate(
            x=base[0] - shift[0], y=base[1] - shift[1], depth=base[2] - shift[2]
        )
        np.testing.assert_allclose(
            (ahead.displacement[0] - behind.displacement[0]) / (2 * step),
            movement.gradient[0, :, j],
            rtol=0,
            atol=1e-6 * gradient_scale,
        )
        np.testing.assert_allclose(
            (ahead.gradient[0] - behind.gradient[0]) / (2 * step),
            movement.hessian[0, :, :, j],
            rtol=0,
            atol=1e-6 * hessian_scale,
        )
        np.testing.assert_allclose(
            (ahead.hessian[0] - behind.hessian[0]) / (2 * step),
            movement.third_derivative[0, :, :, :, j],
            rtol=0,
            atol=1e-6 * third_scale,
        )


@given(troughs(), stations, offsets)
def test_derivatives_are_symmetric_and_zero_in_depth(source, station, offset):
    x, y = point(source, station, offset)
    movement = source.evaluate(x=x, y=y, depth=0.0)
    np.testing.assert_array_equal(movement.hessian, np.swapaxes(movement.hessian, 2, 3))
    assert np.all(movement.gradient[0, :, 2] == 0)
    assert np.all(movement.hessian[0, :, 2, :] == 0)
    assert np.all(movement.hessian[0, :, :, 2] == 0)
    third = movement.third_derivative[0]
    for axes in [(1, 2), (2, 3), (1, 3)]:
        np.testing.assert_array_equal(third, np.swapaxes(third, *axes))
    assert np.all(third[:, 2, :, :] == 0)
    assert np.all(third[:, :, 2, :] == 0)
    assert np.all(third[:, :, :, 2] == 0)
    # Along the station: zero to rounding.
    tangent = np.array([*source.tunnel.tangent, 0.0])
    scale = source.maximum_settlement / source.trough_width
    np.testing.assert_allclose(
        movement.gradient[0] @ tangent, 0.0, rtol=0, atol=1e-12 * scale
    )


@given(troughs())
def test_trough_volume_equals_volume_loss_times_area(source):
    offsets_m = np.linspace(-10, 10, 20001) * source.trough_width
    x, y = point(source, 0.0, offsets_m / source.trough_width)
    settlement = source.evaluate(x=x, y=y, depth=np.zeros_like(x)).displacement[:, 2]
    # The trapezoid rule by hand: numpy.trapezoid is newer than numpy's floor.
    volume = float(np.sum((settlement[1:] + settlement[:-1]) / 2 * np.diff(offsets_m)))
    area = math.pi * source.tunnel.diameter**2 / 4
    assert math.isclose(volume, source.volume_loss * area, rel_tol=1e-6)


@given(troughs(), stations, st.floats(0.0, 3.0))
def test_symmetric_about_the_axis(source, station, offset):
    right = source.evaluate(**_at(source, station, offset))
    left = source.evaluate(**_at(source, station, -offset))
    scale = source.maximum_settlement
    assert math.isclose(
        right.displacement[0, 2],
        left.displacement[0, 2],
        rel_tol=1e-9,
        abs_tol=1e-12 * scale,
    )
    normal = np.array([*source.tunnel.normal, 0.0])
    assert math.isclose(
        right.displacement[0] @ normal,
        -(left.displacement[0] @ normal),
        rel_tol=1e-9,
        abs_tol=1e-12 * scale,
    )


def _at(source, station, offset):
    x, y = point(source, station, offset)
    return {"x": x, "y": y, "depth": 0.0}
