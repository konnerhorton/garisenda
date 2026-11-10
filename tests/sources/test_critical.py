"""Critical distances by root-finding (M2 (a), spec decisions 8-10, AC 6)."""

import math
import re

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

import garisenda as gs
from garisenda.sources._critical import find_critical_distances, find_zeros

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
        "17.5, 18.75, 20, 21.25, 22.5 m along the segment. The bore has its "
        "axis at depth 20 m and diameter 6 m, so it spans depths 17 to 23 m."
    )


def test_bore_message_gives_a_range_past_five_points():
    # Sampled finer through the bore: more than five points inside it.
    with pytest.raises(ValueError) as caught:
        find_critical_distances(
            trough(),
            start=(-20, 50, 20),
            end=(20, 50, 20),
            sampling=0.01,
            tolerance=TOLERANCE,
        )
    message = str(caught.value)
    assert "[" not in message
    assert re.search(
        r"^Points inside the bore can't be evaluated at \d+ points from "
        r"17\.\d+ to 22\.\d+ m along the segment\. The bore",
        message,
    )


def test_vertical_segment_raises():
    with pytest.raises(ValueError, match="vertical"):
        find(trough(), (40, 0, 0), (40, 0, 10))


# M2 (a), step 6: a superposition's critical distances (ACs 5 and 7).


def tunnel_at(**changes):
    arguments = {
        "reference_point": (0, 0),
        "azimuth": 0 * u.degree,
        "diameter": 6.0,
        "axis_depth": 20.0,
    }
    arguments.update(changes)
    return gs.sources.IdealizedTunnel(**arguments)


def surface_trough(tunnel, volume_loss=1.0, k=0.5):
    return gs.sources.transverse_surface_trough(
        tunnel, volume_loss=volume_loss * u.percent, trough_width_parameter=k
    )


def twins(offset, *, axis_depth=20.0, volume_loss=1.0, k=0.5):
    north = tunnel_at()
    south = north.parallel(offset=offset, diameter=6.0, axis_depth=axis_depth)
    return gs.superpose(
        north=surface_trough(north), south=surface_trough(south, volume_loss, k)
    )


def crossing_at_45_degrees():
    east = tunnel_at(reference_point=(10, 50), azimuth=45 * u.degree, axis_depth=30.0)
    return gs.superpose(
        north=surface_trough(tunnel_at()), east=surface_trough(east, 1.5, 0.4)
    )


SUPERPOSITIONS = {
    "A": lambda: twins(15.0),
    "B": lambda: twins(30.0),
    "C": lambda: twins(15.0, axis_depth=30.0, volume_loss=1.5, k=0.4),
    "45 degrees": crossing_at_45_degrees,
}
# The utility of AC 1: perpendicular to north at station 50, offsets -30 to 60.
START, END = np.array([-30.0, 50.0, 0.0]), np.array([60.0, 50.0, 0.0])


def eight_functions(source, distance, start=START, end=END):
    """d/ds, d2/ds2 of along, vertical, lateral and d3/ds3 of vertical, lateral.

    Returned with each function's order, and the scales of decision 9.
    """
    start, end = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
    length = float(np.linalg.norm(end - start))
    a = (end - start) / length
    lateral = np.array([a[1], -a[0], 0.0]) / math.hypot(a[0], a[1])
    vertical = np.cross(lateral, a)
    e = np.stack([a, vertical, lateral])
    points = start + distance[:, None] * a
    m = source.evaluate(x=points[:, 0], y=points[:, 1], depth=points[:, 2])
    orders = [
        np.einsum("ei,nij,j->ne", e, m.gradient, a),
        np.einsum("ei,nijk,j,k->ne", e, m.hessian, a, a),
        np.einsum("ei,nijkl,j,k,l->ne", e, m.third_derivative, a, a, a),
    ]
    feature = source.feature_length(start=start, end=end)
    displacement = np.max(np.linalg.norm(m.displacement, axis=1))
    scales = [
        max(np.max(np.abs(order)), displacement / feature**n)
        for n, order in enumerate(orders, start=1)
    ]
    values = np.concatenate([orders[0], orders[1], orders[2][:, 1:]], axis=1)
    order = np.array([0, 0, 0, 1, 1, 1, 2, 2])
    return values, np.array(scales)[order]


def test_case_b_includes_the_peaks_between_and_over_the_axes():
    source = SUPERPOSITIONS["B"]()
    distances = source.critical_distances(start=START, end=END)
    # The peaks in o: 15 -+ x, x from case B's hand equation, carried to 8 figures.
    for offset in (0.36756261, 15.0, 29.632437):
        assert np.min(np.abs(distances - (offset + 30))) < 1e-6
    # Each is a zero of vertical slope, to 1e-9 of its scale over the segment
    # (the 1e-9 m bisection leaves a slope of about curvature x 1e-9 m).
    targets = np.array([30.36756261, 45.0, 59.632437])
    found = distances[np.argmin(np.abs(distances[:, None] - targets), axis=0)]
    length = float(np.linalg.norm(END - START))
    _, scales = eight_functions(source, np.linspace(0.0, length, 2001))
    values, _ = eight_functions(source, found)
    assert np.all(np.abs(values[:, 1]) < 1e-9 * scales[1])
    # A union of the troughs' own would put the peaks over the axes, at 30 and 60.
    assert np.min(np.abs(distances - 30.0)) > 0.3


def test_case_b_profile_marks_the_peaks_critical():
    source = SUPERPOSITIONS["B"]()
    utility = gs.utilities.perpendicular_utility(
        tunnel_at(),
        utility_id="W-1",
        station=50,
        start_offset=-30,
        end_offset=60,
        depth=0,
        elevation_reference="axis",
        diameter=0.3,
    )
    values = gs.movement_profile(utility, source, spacing=2.5).values
    for offset in (0.36756261, 15.0, 29.632437):
        index = int(np.argmin(np.abs(values["offset"] - offset)))
        assert values["offset"].iloc[index] == pytest.approx(offset, abs=1e-6)
        assert values["critical"].iloc[index]


def subsurface(width):
    return gs.sources.transverse_trough(
        tunnel_at(), volume_loss=1 * u.percent, trough_width=width
    )


def mair():
    return subsurface(gs.sources.mair_trough_width())


def linear():
    return subsurface(gs.sources.linear_trough_width(trough_width_parameter=0.5))


# M2 (b), AC 7: segments that change depth, for the trough at depth. Over
# north (azimuth 0, axis depth 20 m, crown 17 m): from 2 m to 12 m deep;
# crossing the crown beside the bore (its nearest point, the end, is 5.4 m
# from the axis); and at 45 degrees in plan, descending.
SLOPED = {
    "2 to 12 m": ((-30.0, 50.0, 2.0), (30.0, 50.0, 12.0)),
    "crossing the crown": ((-30.0, 50.0, 12.0), (-5.0, 50.0, 22.0)),
    "45 degrees, descending": ((-20.0, 30.0, 1.0), (20.0, 70.0, 15.0)),
}
CASES = {
    **{case: (make, START, END) for case, make in SUPERPOSITIONS.items()},
    **{
        f"{name}, {segment}": (make, *SLOPED[segment])
        for name, make in (("Mair", mair), ("linear", linear))
        for segment in SLOPED
    },
}


@pytest.mark.parametrize("case", sorted(CASES))
def test_nothing_missed_against_dense_sampling(case):
    make, start, end = CASES[case]
    source = make()
    distances = source.critical_distances(start=start, end=end)
    length = float(np.linalg.norm(np.subtract(end, start)))
    feature = source.feature_length(start=start, end=end)
    h = length / math.ceil(length / (feature / 8))
    dense = np.linspace(0.0, length, round(length / (h / 20)) + 1)
    values, scales = eight_functions(source, dense, start, end)
    band = 1e-10 * scales
    sign = np.sign(values)
    changes = (sign[:-1] != sign[1:]) & ~(
        (np.abs(values[:-1]) < band) & (np.abs(values[1:]) < band)
    )
    left, _ = np.nonzero(changes)
    assert left.size  # the test has something to check
    for k in left:
        between = (distances >= dense[k] - 1e-9) & (distances <= dense[k + 1] + 1e-9)
        assert between.any(), f"a sign change at {dense[k]:.6g} m is missed"
    # And each returned distance is a zero of one of the eight functions.
    at, _ = eight_functions(source, distances, start, end)
    assert np.all(np.min(np.abs(at) / scales, axis=1) < 1e-9)


@pytest.mark.parametrize(
    ("make", "end_depth", "width"),
    [(mair, 12.0, 6.1), (linear, 12.0, 4.0), (mair, 19.0, 4.475), (linear, 19.0, 1.5)],
)
def test_feature_length_of_case_e(make, end_depth, width):
    source = make()
    start, end = (-30.0, 50.0, 2.0), (30.0, 50.0, end_depth)
    assert source.feature_length(start=start, end=end) == pytest.approx(
        width, rel=1e-12
    )
    assert source.feature_length(start=end, end=start) == pytest.approx(
        width, rel=1e-12
    )


def test_find_zeros_of_sine_and_cosine():
    def functions(distance):
        return np.stack([np.sin(distance), np.cos(distance)], axis=1)

    zeros = find_zeros(
        functions,
        length=10.0,
        step=0.7,
        tolerance=1e-9,
        scales=np.array([1.0, 1.0]),
    )
    expected = math.pi * np.array([0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
    np.testing.assert_allclose(zeros, expected, atol=1e-9)


def test_find_zeros_keeps_an_exact_zero_at_a_sample_once():
    # Samples at 0, 1, 2, 3, 4: the zero at 2 is a sample, bracketed twice.
    def functions(distance):
        return (distance - 2.0)[:, None]

    zeros = find_zeros(
        functions, length=4.0, step=1.0, tolerance=1e-9, scales=np.array([1.0])
    )
    np.testing.assert_array_equal(zeros, [2.0])


def test_find_zeros_ignores_negligible_values():
    def functions(distance):
        return (1e-12 * np.sin(distance))[:, None]

    zeros = find_zeros(
        functions, length=10.0, step=0.5, tolerance=1e-9, scales=np.array([1.0])
    )
    assert zeros.size == 0
