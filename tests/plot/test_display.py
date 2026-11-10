import matplotlib as mpl
import pint
import pytest

import garisenda as gs
from garisenda.plot._display import one_in, resolve
from garisenda.plot._style import style

u = gs.units


def test_defaults():
    display = resolve(None)
    assert display.factor("length") == 1.0
    assert display.factor("displacement") == pytest.approx(1e3)
    assert display.factor("strain") == pytest.approx(1e6)
    assert display.factor("curvature") == pytest.approx(1e3)
    assert display.label("Settlement", "displacement") == "Settlement (mm)"
    assert display.label("Strain along", "strain") == "Strain along (µε)"
    assert display.label("Curvature", "curvature") == "Curvature (1/km)"


def test_a_subset_is_overridden():
    display = resolve({"displacement": "m", "strain": u.percent})
    assert display.factor("displacement") == 1.0
    assert display.factor("strain") == pytest.approx(100.0)
    assert display.factor("curvature") == pytest.approx(1e3)


# AC 10


def test_unknown_kind_raises_listing_the_six():
    kinds = "'length', 'displacement', 'strain', 'curvature', 'angle', 'slope'"
    with pytest.raises(ValueError, match=rf"'stress'.*{kinds}"):
        resolve({"stress": "kPa"})


def test_wrong_dimension_raises():
    with pytest.raises(pint.DimensionalityError, match="strain"):
        resolve({"strain": "m"})


def test_microstrain():
    assert (250 * u.microstrain).m_as("dimensionless") == pytest.approx(2.5e-4)
    assert u.Quantity(1, "µε").m_as("dimensionless") == pytest.approx(1e-6)


def test_style_leaves_no_global_state():
    before = dict(mpl.rcParams)
    with style():
        assert mpl.rcParams["font.size"] == 9
    assert dict(mpl.rcParams) == before


# M3 (b), spec decision 17: angles display in degrees


def test_angle_defaults_to_degrees():
    display = resolve(None)
    assert display.factor("angle") == pytest.approx(180.0 / 3.141592653589793)
    assert resolve({"angle": "radian"}).factor("angle") == 1.0


# M4 (b), AC 12: slopes display in mm/m


def test_slope_defaults_to_mm_per_m():
    display = resolve(None)
    assert display.factor("slope") == pytest.approx(1000.0)
    assert display.label("Slope", "slope") == "Slope (mm/m)"


def test_slope_in_percent():
    display = resolve({"slope": "percent"})
    assert display.factor("slope") == pytest.approx(100.0)
    assert display.symbol("slope") == "%"


def test_slope_with_a_dimension_raises():
    with pytest.raises(pint.DimensionalityError, match="slope"):
        resolve({"slope": "m"})


@pytest.mark.parametrize(
    ("ratio", "text"),
    [(0.002, "1/500"), (1 / 4712, "1/4710"), (1 / 12345, "1/12300"), (0.02, "1/50")],
)
def test_one_in(ratio, text):
    assert one_in(ratio) == text


@pytest.mark.parametrize("ratio", [0.0, -0.001, float("nan")])
def test_one_in_refuses_a_ratio_that_is_not_positive(ratio):
    with pytest.raises(ValueError, match="positive"):
        one_in(ratio)
