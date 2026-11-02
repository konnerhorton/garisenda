import functools

import numpy as np
import pint
import pytest

import garisenda as gs
from garisenda._units import to_si

u = gs.units
as_length = functools.partial(to_si, unit="m", plain_number="read as SI")
as_ratio = functools.partial(to_si, unit="dimensionless", plain_number="refuse")


def test_plain_number_is_read_as_si_and_says_so():
    assert to_si("axis_depth", 20, unit="m", plain_number="read as SI") == (
        20.0,
        "plain number, read as m",
    )


def test_quantities_in_other_units_convert():
    meters, given_as = to_si(
        "axis_depth", 2000 * u.cm, unit="m", plain_number="read as SI"
    )
    assert meters == pytest.approx(20.0, rel=1e-12)
    assert given_as == "quantity in cm"


def test_arrays_convert():
    meters, _ = to_si(
        "x", np.array([1.0, 2.0]) * u.km, unit="m", plain_number="read as SI"
    )
    np.testing.assert_allclose(meters, [1000.0, 2000.0])


def test_percent_and_dimensionless_agree():
    percent, _ = to_si(
        "volume_loss", 1 * u.percent, unit="dimensionless", plain_number="refuse"
    )
    ratio, _ = to_si(
        "volume_loss",
        0.01 * u.dimensionless,
        unit="dimensionless",
        plain_number="refuse",
    )
    assert percent == pytest.approx(ratio, rel=1e-12)


def test_plain_ratio_is_refused_with_how_to_write_it():
    with pytest.raises(TypeError, match=r"volume_loss.*0\.5 \* gs\.units\.percent"):
        to_si("volume_loss", 0.01, unit="dimensionless", plain_number="refuse")


def test_plain_angle_is_refused_with_how_to_write_it():
    with pytest.raises(TypeError, match=r"azimuth.*30 \* gs\.units\.degree"):
        to_si("azimuth", 30, unit="radian", plain_number="refuse")


def test_degrees_convert_to_radians():
    radians, _ = to_si("azimuth", 180 * u.degree, unit="radian", plain_number="refuse")
    assert radians == pytest.approx(np.pi, rel=1e-12)


@pytest.mark.parametrize(
    ("name", "value", "unit"),
    [
        ("axis_depth", 20 * u.s, "m"),
        ("azimuth", 30 * u.percent, "radian"),
        ("volume_loss", 1 * u.degree, "dimensionless"),
    ],
)
def test_wrong_dimension_names_the_argument(name, value, unit):
    with pytest.raises(pint.DimensionalityError, match=name):
        to_si(name, value, unit=unit, plain_number="refuse")


def test_non_number_is_refused():
    with pytest.raises(TypeError, match="axis_depth must be a number"):
        to_si("axis_depth", "deep", unit="m", plain_number="read as SI")
