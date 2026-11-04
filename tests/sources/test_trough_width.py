"""The trough width methods against the spec's hand calculation (M2 (b))."""

import math

import numpy as np
import pytest

import garisenda as gs

u = gs.units
Z0 = 20.0  # M1's tunnel: axis depth 20 m, D = 6 m, crown at 17 m

# Case A: depth -> (K, i) for Mair's method, by hand (spec, "Hand calculation").
MAIR = {0.0: (0.5, 10.0), 10.0: (0.675, 6.75), 15.0: (1.025, 5.125)}
MAIR_CROWN = (1.4916667, 4.475)
# Case B: depth -> i for the linear method with k = 0.5.
LINEAR = {0.0: 10.0, 10.0: 5.0, 15.0: 2.5}


def taylor_k(z):
    """Taylor (1995), Eq. 5."""
    return 0.325 + 0.175 / (1 - z / Z0)


def mair_k(z):
    """Mair & Taylor (1997), Eq. 8."""
    return (0.175 + 0.325 * (1 - z / Z0)) / (1 - z / Z0)


@pytest.mark.parametrize(("depth", "expected"), MAIR.items())
def test_mair_width_against_case_a(depth, expected):
    k, i = expected
    width = gs.sources.mair_trough_width().at(depth=depth, axis_depth=Z0)
    assert width == pytest.approx(i, rel=1e-12)
    assert taylor_k(depth) == pytest.approx(k, rel=1e-12)
    assert mair_k(depth) == pytest.approx(k, rel=1e-12)


@pytest.mark.parametrize("depth", [0.0, 10.0, 15.0, 17.0])
def test_mair_width_is_k_times_depth_to_axis(depth):
    width = gs.sources.mair_trough_width().at(depth=depth, axis_depth=Z0)
    for k in (taylor_k(depth), mair_k(depth)):
        assert width == pytest.approx(k * (Z0 - depth), rel=1e-12)


def test_mair_width_at_the_crown():
    k, i = MAIR_CROWN
    width = gs.sources.mair_trough_width().at(depth=17.0, axis_depth=Z0)
    assert width == pytest.approx(i, rel=1e-12)
    assert mair_k(17.0) == pytest.approx(k, rel=1e-6)


def test_mair_width_is_finite_at_the_axis():
    width = gs.sources.mair_trough_width().at(depth=Z0, axis_depth=Z0)
    assert width == pytest.approx(0.175 * Z0, rel=1e-12)


@pytest.mark.parametrize(("depth", "expected"), LINEAR.items())
def test_linear_width_against_case_b(depth, expected):
    width = gs.sources.linear_trough_width(trough_width_parameter=0.5)
    assert width.at(depth=depth, axis_depth=Z0) == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize(
    ("depth", "mair", "linear"), [(2, 9.35, 9.0), (12, 6.1, 4.0), (17, 4.475, 1.5)]
)
def test_widths_of_case_e(depth, mair, linear):
    assert gs.sources.mair_trough_width().at(depth=depth, axis_depth=Z0) == (
        pytest.approx(mair, rel=1e-12)
    )
    width = gs.sources.linear_trough_width(trough_width_parameter=0.5)
    assert width.at(depth=depth, axis_depth=Z0) == pytest.approx(linear, rel=1e-12)


def test_width_takes_arrays():
    width = gs.sources.mair_trough_width().at(
        depth=np.array([0.0, 10.0]), axis_depth=Z0
    )
    np.testing.assert_allclose(width, [10.0, 6.75], rtol=1e-12)


def test_methods_and_records():
    mair = gs.sources.mair_trough_width()
    assert mair.name == "Mair et al. (1993), clay"
    assert (mair.surface_coefficient, mair.rate) == (0.175, 0.325)
    assert mair.inputs == ()
    assert "Mair & Taylor (1997)" in mair.source
    assert "clays" in mair.assumptions[0]
    linear = gs.sources.linear_trough_width(
        trough_width_parameter=gs.Sourced(0.4, source="Basis of design")
    )
    assert linear.name == "linear"
    assert (linear.surface_coefficient, linear.rate) == (0.0, 0.4)
    (entry,) = linear.inputs
    assert entry.name == "trough_width_parameter"
    assert entry.kind == "design judgment"
    assert entry.source == "Basis of design"
    assert "their choice" in linear.assumptions[0]


def test_linear_without_k_raises_the_judgment_error():
    with pytest.raises(TypeError, match="trough_width_parameter is a required design"):
        gs.sources.linear_trough_width()


@pytest.mark.parametrize("k", [0, -0.5, math.nan, math.inf])
def test_linear_with_k_out_of_range_raises(k):
    with pytest.raises(ValueError, match="trough_width_parameter must be positive"):
        gs.sources.linear_trough_width(trough_width_parameter=k)
