"""Damage categories (docs/work/m4a-building-damage.md, AC 8)."""

import math

import pytest

import garisenda as gs

Band = gs.buildings.Band


def table():
    return gs.presets.damage_categories().value


@pytest.mark.parametrize(
    ("strain", "number", "label", "severity"),
    [
        (0.0, 0, "0", "negligible"),
        (-1e-4, 0, "0", "negligible"),
        (0.0004, 0, "0", "negligible"),
        # A strain exactly on a boundary falls in the lower band.
        (0.0005, 0, "0", "negligible"),
        (0.00050001, 1, "1", "very slight"),
        (0.00075, 1, "1", "very slight"),
        (0.0010, 2, "2", "slight"),
        (0.0015, 2, "2", "slight"),
        (0.0020, 3, "3", "moderate"),
        (0.0030, 3, "3", "moderate"),
        (0.0031, 4, "4 to 5", "severe to very severe"),
        (1.0, 4, "4 to 5", "severe to very severe"),
    ],
)
def test_table_2_bands(strain, number, label, severity):
    band = table().category(strain)
    assert (band.number, band.label, band.severity) == (number, label, severity)


def test_table_2_limits():
    limits = [band.upper_limit for band in table().bands]
    assert limits == pytest.approx([0.0005, 0.00075, 0.0015, 0.003, math.inf])
    assert table().name == "Mair, Taylor & Burland (1996), Table 2"


def test_band_by_number():
    assert table().band(2).upper_limit == pytest.approx(0.0015)
    with pytest.raises(ValueError, match="categories are 0, 1, 2, 3, 4"):
        table().band(5)


@pytest.mark.parametrize(
    ("bands", "message"),
    [
        ([], "at least one band"),
        (
            [
                Band(0, "0", "a", 0.002),
                Band(1, "1", "b", 0.001),
                Band(2, "2", "c", math.inf),
            ],
            "must be positive and increase",
        ),
        (
            [
                Band(0, "0", "a", 0.001),
                Band(1, "1", "b", 0.001),
                Band(2, "2", "c", math.inf),
            ],
            "must be positive and increase",
        ),
        (
            [Band(0, "0", "a", 0.0), Band(1, "1", "b", math.inf)],
            "positive and increase",
        ),
        ([Band(0, "0", "a", 0.001), Band(1, "1", "b", 0.002)], "must be unbounded"),
        ([Band(0, "0", "a", 0.001), Band(0, "1", "b", math.inf)], "distinct"),
    ],
)
def test_bad_tables_raise(bands, message):
    with pytest.raises(ValueError, match=message):
        gs.buildings.DamageCategories(name="mine", bands=bands)


def test_a_custom_table():
    custom = gs.buildings.DamageCategories(
        name="client",
        bands=[Band(1, "low", "acceptable", 0.001), Band(2, "high", "not", math.inf)],
    )
    assert custom.category(0.001).label == "low"
    assert custom.category(0.0011).label == "high"


def test_cutoffs():
    assert gs.buildings.no_cutoff().name == "none: the whole wall"
    cutoff = gs.buildings.trough_width_cutoff(multiple=2.5)
    assert cutoff.multiple == 2.5
    assert cutoff.name == "2.5 i from each trough's axis"
    with pytest.raises(TypeError, match="multiple is a required design judgment"):
        gs.buildings.trough_width_cutoff()
    for bad in (0.0, -1.0, math.inf, math.nan):
        with pytest.raises(ValueError, match="multiple must be positive"):
            gs.buildings.trough_width_cutoff(multiple=bad)
