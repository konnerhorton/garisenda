"""Physics the trough at depth must obey, over many inputs (M2 (b), SPEC §11)."""

import math

import numpy as np
from hypothesis import given
from hypothesis import strategies as st

import garisenda as gs

u = gs.units


@st.composite
def tunnels(draw):
    diameter = draw(st.floats(2.0, 15.0))
    cover = draw(st.floats(1.0, 50.0))
    return gs.sources.IdealizedTunnel(
        reference_point=(draw(st.floats(-1e3, 1e3)), draw(st.floats(-1e3, 1e3))),
        azimuth=draw(st.floats(0.0, 360.0)) * u.degree,
        diameter=diameter,
        axis_depth=cover + diameter / 2,
        reference_station=draw(st.floats(-1e3, 1e3)),
    )


@st.composite
def widths(draw):
    if draw(st.booleans()):
        return gs.sources.mair_trough_width()
    return gs.sources.linear_trough_width(
        trough_width_parameter=draw(st.floats(0.2, 1.0))
    )


@st.composite
def troughs(draw):
    return gs.sources.transverse_trough(
        draw(tunnels()),
        volume_loss=draw(st.floats(0.1, 5.0)) * u.percent,
        trough_width=draw(widths()),
    )


def point(source, station, offset, fraction):
    """A point above the crown: offset in units of i there, depth a fraction of it."""
    tunnel = source.tunnel
    depth = fraction * source.crown_depth
    o = offset * source.width_at(depth)
    along = station - tunnel.reference_station
    x = tunnel.reference_x + along * tunnel.tangent[0] + o * tunnel.normal[0]
    y = tunnel.reference_y + along * tunnel.tangent[1] + o * tunnel.normal[1]
    return np.array([x, y, depth])


offsets = st.floats(-3.0, 3.0)
stations = st.floats(-1e3, 1e3)
# Clear of the surface and the crown, so depth can be stepped both ways.
fractions = st.floats(0.02, 0.98)


def scales(source, depth):
    """Q / i^(n+1) for n = 1, 2, 3: each order's size."""
    i = source.width_at(depth)
    q = source.volume_factor
    return q / i**2, q / i**3, q / i**4


# AC 2: the derivatives against central differences, and symmetric


@given(troughs(), stations, offsets, fractions)
def test_derivatives_match_finite_differences(source, station, offset, fraction):
    base = point(source, station, offset, fraction)
    step = 1e-4 * source.width_at(base[2])
    gradient_scale, hessian_scale, third_scale = scales(source, base[2])
    movement = source.evaluate(x=base[0], y=base[1], depth=base[2])
    for j in range(3):
        shift = np.zeros(3)
        shift[j] = step
        ahead = source.evaluate(
            **dict(zip(("x", "y", "depth"), base + shift, strict=True))
        )
        behind = source.evaluate(
            **dict(zip(("x", "y", "depth"), base - shift, strict=True))
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


@given(troughs(), stations, offsets, fractions)
def test_derivatives_are_symmetric(source, station, offset, fraction):
    x, y, depth = point(source, station, offset, fraction)
    movement = source.evaluate(x=x, y=y, depth=depth)
    np.testing.assert_array_equal(movement.hessian, np.swapaxes(movement.hessian, 2, 3))
    third = movement.third_derivative[0]
    for axes in [(1, 2), (2, 3), (1, 3)]:
        np.testing.assert_array_equal(third, np.swapaxes(third, *axes))


# AC 3: constant volume


@given(troughs(), stations, offsets, fractions)
def test_volume_is_constant(source, station, offset, fraction):
    x, y, depth = point(source, station, offset, fraction)
    gradient = source.evaluate(x=x, y=y, depth=depth).gradient[0]
    terms = np.abs(np.diag(gradient))
    scale = max(float(terms.max()), 1e-300)
    assert abs(float(np.trace(gradient))) <= 1e-12 * scale


# AC 4: the linear method at the surface is M1, for any k


@given(tunnels(), st.floats(0.2, 1.0), st.floats(0.1, 5.0), stations, offsets)
def test_linear_at_the_surface_is_m1(tunnel, k, volume_loss, station, offset):
    mine = gs.sources.transverse_trough(
        tunnel,
        volume_loss=volume_loss * u.percent,
        trough_width=gs.sources.linear_trough_width(trough_width_parameter=k),
    )
    theirs = gs.sources.transverse_surface_trough(
        tunnel, volume_loss=volume_loss * u.percent, trough_width_parameter=k
    )
    x, y, _ = point(mine, station, offset, 0.0)
    a = mine.evaluate(x=x, y=y, depth=0.0)
    b = theirs.evaluate(x=x, y=y, depth=0.0)
    gradient_scale, hessian_scale, third_scale = scales(mine, 0.0)
    pairs = [
        (a.displacement, b.displacement, gradient_scale * mine.width_at(0.0)),
        (a.gradient[..., :2], b.gradient[..., :2], gradient_scale),
        (a.hessian[..., :2, :2], b.hessian[..., :2, :2], hessian_scale),
        (
            a.third_derivative[..., :2, :2, :2],
            b.third_derivative[..., :2, :2, :2],
            third_scale,
        ),
    ]
    for mine_part, theirs_part, scale in pairs:
        np.testing.assert_allclose(
            mine_part, theirs_part, rtol=1e-12, atol=1e-12 * scale
        )


# AC 6: critical distances on level segments are the analytic set at i(z)

ROOTS = (0.0, 1.0, math.sqrt(3))
# 0.74196378 and 2.3344142 in the spec, exactly: the zeros of r^4 - 6 r^2 + 3.
OBLIQUE_ROOTS = (math.sqrt(3 - math.sqrt(6)), math.sqrt(3 + math.sqrt(6)))


@st.composite
def level_segments(draw):
    source = draw(troughs())
    tunnel = source.tunnel
    depth = draw(st.floats(0.0, 1.0)) * source.crown_depth
    i = source.width_at(depth)
    station = draw(st.floats(-1e3, 1e3))
    offset = draw(st.floats(-4.0, 4.0)) * i
    # As M2 (a)'s test: perpendicular, or 0.01 to 89 degrees from it.
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
    return source, (*begin, depth), (*finish, depth), length, angle, i


def interior(distances, length):
    # A zero at an end is found or not depending on rounding.
    distances = np.asarray(distances)
    return distances[(distances > 1e-6) & (distances < length - 1e-6)]


@given(level_segments())
def test_level_segments_give_the_analytic_distances(segment):
    source, start, end, length, angle, i = segment
    roots = ROOTS + (OBLIQUE_ROOTS if angle != 0.0 else ())
    targets = np.array(sorted({sign * root for root in roots for sign in (-1, 1)}))
    _, offsets = source.tunnel.station_offset(
        x=np.array([start[0], end[0]]), y=np.array([start[1], end[1]])
    )
    o_start, o_end = (float(value) for value in offsets)
    expected = np.sort(length * (targets * i - o_start) / (o_end - o_start))
    expected = expected[(expected >= 0) & (expected <= length)]
    np.testing.assert_allclose(
        interior(source.critical_distances(start=start, end=end), length),
        interior(expected, length),
        rtol=0,
        atol=1e-8,
    )
