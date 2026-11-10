"""The building check's profile: five panels, its zones, chords and strains."""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest

import garisenda as gs

LABELS = (
    "Settlement (mm)",
    "Deflection from chord (mm)",
    "Slope (mm/m)",
    "Horizontal strain (µε)",
    "Tensile strain (µε)",
)


def line(ax, gid):
    (found,) = [item for item in ax.get_lines() if item.get_gid() == gid]
    return found


def lines(ax, gid):
    return [item for item in ax.get_lines() if item.get_gid() == gid]


def texts(ax, gid):
    return [item for item in ax.texts if item.get_gid() == gid]


def check(result, name):
    return result.checks.set_index("check").loc[name]


def row_at(result, where):
    found = np.flatnonzero(
        np.isclose(result.values["distance"], where, rtol=0, atol=1e-9)
    )
    return result.values.iloc[found[0]]


@pytest.fixture(scope="module")
def drawn(building_check):
    fig, axs = gs.plot.profile(building_check)
    yield axs
    plt.close(fig)


# AC 1


def test_five_panels_with_their_labels(drawn):
    assert len(drawn) == 5
    assert tuple(ax.get_ylabel() for ax in drawn) == LABELS
    assert drawn[-1].get_xlabel() == "Distance along wall (m)"
    assert drawn[0].yaxis_inverted()
    assert drawn[1].yaxis_inverted()
    assert not drawn[2].yaxis_inverted()


@pytest.mark.parametrize("count", [4, 6])
def test_another_number_of_axs_names_the_five_panels(building_check, count):
    fig, axs = plt.subplots(count, 1)
    names = (
        "settlement, deflection from chord, slope, horizontal strain, tensile strain"
    )
    with pytest.raises(ValueError, match=f"5 matplotlib Axes.*{names}"):
        gs.plot.profile(building_check, axs=axs)
    plt.close(fig)


def test_a_buildings_movement_profile_has_four_panels(make_building_check):
    result = make_building_check()
    building = result.asset
    profile = gs.movement_profile(building, result.source, spacing=1.0)
    fig, axs = gs.plot.profile(profile)
    assert len(axs) == 4
    assert axs[-1].get_xlabel() == "Distance along wall (m)"
    plt.close(fig)


def test_the_title_gives_the_beam_and_the_cutoff(drawn):
    title = drawn[0].get_figure()._suptitle.get_text()
    assert title.startswith("Building check along W-1\n")
    assert "Burland & Wroth (1974), shear coefficient 3/2 beam" in title
    assert "cut-off: 2.5 i from each trough's axis" in title
    assert "chords dashed" in title


# AC 2, 3, 4, 5: the lines are the columns in display units


@pytest.mark.parametrize(
    ("panel", "column", "factor"),
    [
        (0, "vertical", 1e3),
        (1, "deflection", 1e3),
        (2, "vertical_slope", 1e3),
        (3, "along_strain", 1e6),
    ],
)
def test_lines_are_the_columns(building_check, drawn, panel, column, factor):
    found = line(drawn[panel], column)
    values = building_check.values
    np.testing.assert_allclose(found.get_xdata(), values["distance"], rtol=1e-12)
    np.testing.assert_allclose(
        found.get_ydata(), values[column] * factor, rtol=1e-12, equal_nan=True
    )


def test_deflection_is_nan_beyond_the_cutoff(building_check, drawn):
    drawn_nan = np.isnan(np.asarray(line(drawn[1], "deflection").get_ydata()))
    assert drawn_nan.any()
    np.testing.assert_array_equal(drawn_nan, building_check.values["deflection"].isna())


# AC 2


def test_settlement_limit_and_check(building_check, drawn):
    settlement = check(building_check, "settlement")
    (limit,) = lines(drawn[0], "settlement_limit")
    np.testing.assert_allclose(limit.get_ydata(), settlement["limit"] * 1e3, rtol=1e-12)
    mark = line(drawn[0], "check:settlement")
    assert mark.get_xdata()[0] == pytest.approx(settlement["governing_distance"])
    assert mark.get_ydata()[0] == pytest.approx(settlement["value"] * 1e3, rel=1e-12)
    (text,) = texts(drawn[0], "check:settlement")
    assert f"u = {settlement['utilization']:.2f}" in text.get_text()


# AC 4


def test_slope_limits_and_check(building_check, drawn):
    limits = lines(drawn[2], "slope_limit")
    assert sorted(float(item.get_ydata()[0]) for item in limits) == pytest.approx(
        [-2.0, 2.0], rel=1e-12
    )
    (label,) = texts(drawn[2], "slope_limit")
    assert label.get_text() == "slope limit: 2 mm/m (1/500)"
    slope = check(building_check, "slope")
    signed = row_at(building_check, slope["governing_distance"])["vertical_slope"]
    mark = line(drawn[2], "check:slope")
    assert mark.get_xdata()[0] == pytest.approx(slope["governing_distance"])
    assert mark.get_ydata()[0] == pytest.approx(signed * 1e3, rel=1e-12)
    assert abs(signed) == pytest.approx(slope["value"], rel=1e-12)
    (text,) = texts(drawn[2], "check:slope")
    assert f"u = {slope['utilization']:.2f}" in text.get_text()


# AC 12, the panel


def test_slope_in_percent(building_check):
    fig, axs = gs.plot.profile(building_check, display_units={"slope": "percent"})
    assert axs[2].get_ylabel() == "Slope (%)"
    np.testing.assert_allclose(
        line(axs[2], "vertical_slope").get_ydata(),
        building_check.values["vertical_slope"] * 100,
        rtol=1e-12,
    )
    plt.close(fig)


# AC 13: the plot contract


def test_the_contract(building_check):
    before = dict(mpl.rcParams)
    tables = {
        name: getattr(building_check, name).copy()
        for name in ("values", "zones", "checks")
    }
    fig, axs = plt.subplots(5, 1, sharex=True)
    figures = plt.get_fignums()
    returned, _ = gs.plot.profile(building_check, axs=axs)
    assert returned is fig
    assert plt.get_fignums() == figures
    assert dict(mpl.rcParams) == before
    for name, table in tables.items():
        assert getattr(building_check, name).equals(table)
    plt.close(fig)


def test_the_fixture_has_three_zones_and_a_cutoff_on_both_sides(building_check):
    zones = building_check.zones
    assert list(zones["mode"]) == ["hogging", "sagging", "hogging"]
    assert zones["start"].iloc[0] > 0
    assert zones["end"].iloc[-1] < building_check.values["distance"].iloc[-1]
