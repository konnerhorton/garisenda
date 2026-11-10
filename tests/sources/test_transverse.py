import math

import numpy as np
import pytest

import garisenda as gs

u = gs.units
REL = 1e-6  # hand calculation carried to 8 figures (spec, acceptance criteria)


def tunnel(**changes):
    arguments = {
        "reference_point": (0, 0),
        "azimuth": 0 * u.degree,
        "diameter": 6.0,
        "axis_depth": 20.0,
    }
    arguments.update(changes)
    return gs.sources.IdealizedTunnel(**arguments)


def trough(tunnel_=None, **changes):
    arguments = {"volume_loss": 1 * u.percent, "trough_width_parameter": 0.5}
    arguments.update(changes)
    return gs.sources.transverse_surface_trough(tunnel_ or tunnel(), **arguments)


# Spec hand calculation: o, S, u_n, dS/do, d2S/do2, du_n/do, d2u_n/do2.
SURFACE = [
    (0.0, 1.1279827e-2, 0.0, 0.0, -1.1279827e-4, -5.6399136e-4, 0.0),
    (
        5.0,
        9.9544126e-3,
        -2.4886031e-3,
        -4.9772063e-4,
        -7.4658094e-5,
        -3.7329047e-4,
        6.8436587e-5,
    ),
    (10.0, 6.8415611e-3, -3.4207805e-3, -6.8415611e-4, 0.0, 0.0, 6.8415611e-5),
    (
        17.320508,
        2.5168697e-3,
        -2.1796731e-3,
        -4.3593461e-4,
        5.0337393e-5,
        2.5168697e-4,
        0.0,
    ),
    (
        20.0,
        1.5265586e-3,
        -1.5265586e-3,
        -3.0531172e-4,
        4.5796758e-5,
        2.2898379e-4,
        -1.5265586e-5,
    ),
    (-10.0, 6.8415611e-3, 3.4207805e-3, 6.8415611e-4, 0.0, 0.0, -6.8415611e-5),
]


def close(actual, expected, scale):
    # Relative to the value, or to the column's scale where the value is zero
    # (a zero in the table is zero only to the table's 8 figures).
    assert actual == pytest.approx(expected, rel=REL, abs=REL * scale)


def test_trough_width_and_maximum_settlement():
    source = trough()
    assert source.trough_width == pytest.approx(10.0, rel=REL)
    assert source.maximum_settlement == pytest.approx(0.011279827, rel=REL)


@pytest.mark.parametrize("row", SURFACE, ids=lambda row: f"o={row[0]}")
def test_surface_golden_values(row):
    o, settlement, normal, d_s, d2_s, d_n, d2_n = row
    movement = trough().evaluate(x=o, y=0.0, depth=0.0)
    # Tunnel along +y, so n = +x and the offset is x.
    close(movement.displacement[0, 2], settlement, 1e-2)
    close(movement.displacement[0, 0], normal, 1e-3)
    close(movement.gradient[0, 2, 0], d_s, 1e-3)
    close(movement.gradient[0, 0, 0], d_n, 1e-4)
    close(movement.hessian[0, 2, 0, 0], d2_s, 1e-4)
    close(movement.hessian[0, 0, 0, 0], d2_n, 1e-4)
    assert movement.displacement[0, 1] == 0
    assert movement.verdict.tolist() == ["within"]
    assert movement.flags == ()


def test_rotated_tunnel_in_global_components():
    rotated = tunnel(
        reference_point=(100, 200), azimuth=30 * u.degree, reference_station=1000
    )
    movement = trough(rotated).evaluate(x=121.16025404, y=216.65063509, depth=0)
    np.testing.assert_allclose(
        movement.displacement[0], [-2.9624828e-3, 1.7103903e-3, 6.8415611e-3], rtol=REL
    )
    np.testing.assert_allclose(
        movement.gradient[0, 2, :2], [-5.9249657e-4, 3.4207805e-4], rtol=REL
    )
    assert movement.gradient[0, 2, 2] == 0


def test_arrays_of_points():
    movement = trough().evaluate(
        x=[0.0, 10.0, -10.0], y=[0.0, 5.0, 50.0], depth=[0, 0, 0]
    )
    assert movement.displacement.shape == (3, 3)
    assert movement.hessian.shape == (3, 3, 3, 3)
    assert movement.displacement[1, 2] == pytest.approx(movement.displacement[2, 2])


def test_volume_loss_as_percent_or_ratio_is_the_same():
    by_percent = trough(volume_loss=1 * u.percent).evaluate(x=5.0, y=0, depth=0)
    by_ratio = trough(volume_loss=0.01 * u.dimensionless).evaluate(x=5.0, y=0, depth=0)
    np.testing.assert_allclose(
        by_percent.displacement, by_ratio.displacement, rtol=1e-12
    )


def test_plain_volume_loss_is_refused():
    with pytest.raises(TypeError, match=r"volume_loss=0\.5 \* gs\.units\.percent"):
        trough(volume_loss=0.01)


@pytest.mark.parametrize("missing", ["volume_loss", "trough_width_parameter"])
def test_missing_judgment_is_explained(missing):
    arguments = {"volume_loss": 1 * u.percent, "trough_width_parameter": 0.5}
    del arguments[missing]
    with pytest.raises(
        TypeError,
        match=f"missing {missing}. {missing} is a required design judgment "
        "with no default: .*Pass it as",
    ):
        gs.sources.transverse_surface_trough(tunnel(), **arguments)


def test_point_below_the_surface_is_flagged_and_gets_surface_values():
    movement = trough().evaluate(
        x=[5.0, 5.0, 5.0, 5.0], y=[0, 0, 0, 0], depth=[0.0, 0.0005, 2.0, 8.0]
    )
    assert movement.verdict.tolist() == ["within", "within", "outside", "outside"]
    (flag,) = movement.flags
    assert flag.verdict == "outside"
    assert flag.points == (2, 3)
    assert "below the ground surface" in flag.reason
    assert "gs.sources.transverse_trough" in flag.reason
    np.testing.assert_array_equal(movement.displacement[2], movement.displacement[0])
    np.testing.assert_array_equal(movement.gradient[3], movement.gradient[0])


@pytest.mark.parametrize(
    "volume_loss", [0 * u.percent, -1 * u.percent, 100 * u.percent]
)
def test_impossible_volume_loss_raises(volume_loss):
    with pytest.raises(ValueError, match="volume_loss must be more than 0"):
        trough(volume_loss=volume_loss)


@pytest.mark.parametrize("k", [0, -0.5, math.nan])
def test_impossible_k_raises(k):
    with pytest.raises(ValueError, match="trough_width_parameter must be positive"):
        trough(trough_width_parameter=k)


def test_point_above_the_surface_raises():
    with pytest.raises(ValueError, match=r"above the ground surface.*\[1\]"):
        trough().evaluate(x=[0, 0], y=[0, 0], depth=[0, -1])


def test_point_inside_the_bore_raises():
    with pytest.raises(ValueError, match=r"inside the bore.*\[0\]"):
        trough().evaluate(x=1.0, y=0, depth=19.0)


def test_missing_coordinate_raises_naming_the_point():
    with pytest.raises(ValueError, match=r"finite x, y and depth.*\[1\]"):
        trough().evaluate(x=[0, math.nan], y=[0, 0], depth=[0, 0])


def test_unequal_lengths_raise():
    with pytest.raises(ValueError, match="same length"):
        trough().evaluate(x=[0, 1], y=[0], depth=[0, 0])


def test_inputs_are_recorded():
    source = trough(
        volume_loss=gs.Sourced(1 * u.percent, source="Basis of design, section 4.2")
    )
    records = {entry.name: entry for entry in source.inputs}
    assert {
        "volume_loss",
        "trough_width_parameter",
        "surface_tolerance",
        "axis_depth",
    } <= set(records)
    volume = records["volume_loss"]
    assert volume.kind == "design judgment"
    assert volume.value.m_as("dimensionless") == pytest.approx(0.01)
    assert volume.given_as == "quantity in %"
    assert volume.source == "Basis of design, section 4.2"
    k = records["trough_width_parameter"]
    assert (k.kind, k.given_as, k.source) == (
        "design judgment",
        "plain number, read as dimensionless",
        None,
    )
    assert records["surface_tolerance"].kind == "constant or setting"


def test_assumptions_are_recorded():
    text = " ".join(trough().assumptions)
    for phrase in [
        "Steady state",
        "Transverse trough only",
        "Gaussian",
        "toward the tunnel axis",
        "points below the surface are flagged",
        "No validity range is checked",
        "Idealized straight tunnel",
    ]:
        assert phrase in text


def test_method_cites_its_unverified_sources():
    (method,) = trough().method
    assert "🔬" in method.source
    assert "Not verified against the sources yet." in method.source
    assert "S(o) = S_max exp(-o^2 / (2 i^2))" in method.equations


# M1 (b): critical distances along a segment (spec decision 4, AC 5).
ROOT3 = math.sqrt(3)


def test_critical_distances_perpendicular():
    # Case A: x from -20 to 20 at y = 50, offset = distance - 20.
    distances = trough().critical_distances(start=(-20, 50, 0), end=(20, 50, 0))
    expected = [20 - 10 * ROOT3, 10, 20, 30, 20 + 10 * ROOT3]
    np.testing.assert_allclose(distances, expected, rtol=1e-12)
    assert distances[0] == pytest.approx(2.6794919, rel=REL)
    assert distances[-1] == pytest.approx(37.320508, rel=REL)


def test_critical_distances_reversed():
    distances = trough().critical_distances(start=(20, 50, 0), end=(-20, 50, 0))
    expected = [20 - 10 * ROOT3, 10, 20, 30, 20 + 10 * ROOT3]
    np.testing.assert_allclose(distances, expected, rtol=1e-12)


def test_critical_distances_at_45_degrees():
    # Case D: offset = -20 + distance / sqrt(2). Oblique, so lateral curvature
    # also peaks at o = -+0.74196378 i (M2 (a)): s = 17.791319 and 38.777224.
    distances = trough().critical_distances(start=(-20, -20, 0), end=(20, 20, 0))
    expected = [
        3.7893738,
        14.142136,
        17.791319,
        28.284271,
        38.777224,
        42.426407,
        52.779169,
    ]
    np.testing.assert_allclose(distances, expected, rtol=REL)


def test_segment_parallel_to_the_tunnel_has_none():
    distances = trough().critical_distances(start=(5, -10, 0), end=(5, 30, 2))
    assert distances.shape == (0,)


def test_segment_reaching_only_some_crossings():
    # Offsets 5 to 25: only i and sqrt(3) i are crossed.
    distances = trough().critical_distances(start=(5, 0, 0), end=(25, 0, 0))
    np.testing.assert_allclose(distances, [5, 10 * ROOT3 - 5], rtol=1e-12)


def test_crossing_at_an_end_is_included():
    distances = trough().critical_distances(start=(0, 0, 0), end=(10, 0, 0))
    np.testing.assert_allclose(distances, [0, 10], atol=1e-12)


def test_critical_distances_measured_in_3d():
    # A sloping segment: distance along it is longer than in plan.
    distances = trough().critical_distances(start=(-20, 0, 0), end=(20, 0, 30))
    np.testing.assert_allclose(distances[2], 25.0, rtol=1e-12)


def test_critical_distances_bad_segment_raises():
    with pytest.raises(ValueError, match="zero length"):
        trough().critical_distances(start=(1, 1, 1), end=(1, 1, 1))
    with pytest.raises(ValueError, match="three finite values"):
        trough().critical_distances(start=(1, 1), end=(2, 1, 1))


# M2 (a): the third derivative and feature length (spec decisions 6-7, case D).
# o, d3S/do3, d3u_n/do3.
THIRD = [
    (0.0, 0.0, 1.6919741e-5),
    (10.0, 1.3683122e-5, -6.8415611e-6),
    (20.0, -3.0531172e-6, -3.8163965e-6),
]


@pytest.mark.parametrize("row", THIRD, ids=lambda row: f"o={row[0]}")
def test_third_derivative_golden_values(row):
    o, d3_s, d3_n = row
    movement = trough().evaluate(x=o, y=0.0, depth=0.0)
    close(movement.third_derivative[0, 2, 0, 0, 0], d3_s, 1e-5)
    close(movement.third_derivative[0, 0, 0, 0, 0], d3_n, 1e-5)
    assert movement.third_derivative.shape == (1, 3, 3, 3, 3)


def test_movement_refuses_a_misshapen_third_derivative():
    movement = trough().evaluate(x=[0.0, 5.0], y=[0.0, 0.0], depth=[0.0, 0.0])
    with pytest.raises(ValueError, match=r"third_derivative has shape"):
        gs.sources.Movement(
            movement.displacement,
            movement.gradient,
            movement.hessian,
            movement.third_derivative[:, :, :, :, :2],
            movement.verdict,
            movement.flags,
        )


def test_feature_length_is_the_trough_width():
    source = trough(trough_width_parameter=0.4)
    assert source.feature_length(start=(-20, 0, 0), end=(20, 0, 0)) == 8.0
    assert source.feature_length(start=(5, -10, 0), end=(5, 30, 2)) == 8.0
