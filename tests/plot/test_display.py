import matplotlib as mpl
import pint
import pytest

import garisenda as gs
from garisenda.plot._display import resolve
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


def test_unknown_kind_raises_listing_the_four():
    kinds = "'length', 'displacement', 'strain', 'curvature'"
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
