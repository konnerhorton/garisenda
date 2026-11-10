"""The building check's profile: five panels, its zones, chords and strains."""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest

import garisenda as gs
from garisenda.plot._display import one_in

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
    assert "beam: Burland & Wroth (1974), shear coefficient 3/2\n" in title
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


def zone_rows(result, zone):
    distance = result.values["distance"]
    return (distance >= zone.start - 1e-9) & (distance <= zone.end + 1e-9)


def patches(ax, gid):
    return [item for item in ax.patches if item.get_gid() == gid]


def collections(ax, gid):
    return [item for item in ax.collections if item.get_gid() == gid]


# AC 2: chords and the deflection filled


def test_a_chord_and_a_fill_per_zone(building_check, drawn):
    values = building_check.values
    for zone in building_check.zones.itertuples():
        rows = zone_rows(building_check, zone)
        chord = line(drawn[0], f"chord:zone_{zone.zone}")
        np.testing.assert_allclose(
            chord.get_xdata(), values["distance"][rows], rtol=0, atol=1e-9
        )
        np.testing.assert_allclose(
            chord.get_ydata(), values["chord"][rows] * 1e3, rtol=1e-12
        )
        assert chord.get_linestyle() == "--"
        (fill,) = collections(drawn[0], f"zone_{zone.zone}")
        assert isinstance(fill, mpl.collections.PolyCollection)
        assert texts(drawn[0], f"zone_label:{zone.zone}")[0].get_text() == (
            f"{zone.zone} {zone.mode}"
        )


# AC 3: Delta


def test_each_delta_marked_with_its_ratio(building_check, drawn):
    for zone in building_check.zones.itertuples():
        found = line(drawn[1], f"delta:zone_{zone.zone}")
        sign = -1 if zone.mode == "hogging" else 1
        assert found.get_xdata()[0] == pytest.approx(zone.deflection_distance)
        assert found.get_ydata()[0] == pytest.approx(
            sign * zone.deflection * 1e3, rel=1e-12
        )
        (text,) = texts(drawn[1], f"delta:zone_{zone.zone}")
        assert text.get_text() == (
            f"Δ = {zone.deflection * 1e3:.3g} mm, Δ/L = {one_in(zone.deflection_ratio)}"
        )


def test_delta_ratio_is_written_as_one_in_n(drawn):
    # Zone 2's Delta/L is 3.89e-4: 1/2570.
    (text,) = texts(drawn[1], "delta:zone_2")
    assert text.get_text().endswith("Δ/L = 1/2570")


# AC 5


def test_horizontal_strain_per_zone(building_check, drawn):
    for zone in building_check.zones.itertuples():
        found = line(drawn[3], f"horizontal_strain:zone_{zone.zone}")
        np.testing.assert_allclose(found.get_xdata(), [zone.start, zone.end])
        np.testing.assert_allclose(
            found.get_ydata(), [zone.horizontal_strain * 1e6] * 2, rtol=1e-12
        )


# AC 6


def test_tensile_strains_per_zone(building_check, drawn):
    for zone in building_check.zones.itertuples():
        widths = {}
        for column in ("total_bending_strain", "total_diagonal_strain"):
            found = line(drawn[4], f"{column}:zone_{zone.zone}")
            np.testing.assert_allclose(found.get_xdata(), [zone.start, zone.end])
            np.testing.assert_allclose(
                found.get_ydata(), [getattr(zone, column) * 1e6] * 2, rtol=1e-12
            )
            widths[column.split("_")[1]] = found.get_linewidth()
        other = "diagonal" if zone.governed_by == "bending" else "bending"
        assert widths[zone.governed_by] > widths[other]


def test_the_bands_within_the_range(building_check, drawn):
    ax = drawn[4]
    bottom, top = ax.get_ylim()
    lower = -np.inf
    shown = []
    for band in building_check.categories.bands:
        low, high = lower * 1e6, band.upper_limit * 1e6
        lower = band.upper_limit
        found = patches(ax, f"band:{band.number}")
        if high <= bottom or low >= top:
            assert not found
            continue
        (patch,) = found
        assert patch.get_y() == pytest.approx(max(low, bottom), rel=1e-12)
        assert patch.get_y() + patch.get_height() == pytest.approx(
            min(high, top), rel=1e-12
        )
        shown.append(band.number)
    # Bands 0 to 2 cover the strains and the limit; 3 is clipped at the top.
    assert shown == [0, 1, 2, 3]


def test_the_acceptable_limit_and_the_governing_zone(building_check, drawn):
    ax = drawn[4]
    (limit,) = lines(ax, "damage_category_limit")
    np.testing.assert_allclose(limit.get_ydata(), 1500.0, rtol=1e-12)
    (label,) = texts(ax, "damage_category_limit")
    assert label.get_text() == "acceptable: category 2, 1500 µε"
    governing = check(building_check, "damage_category")
    zone = building_check.zones.set_index("zone").loc[int(governing["zone"])]
    mark = line(ax, "check:damage_category")
    assert mark.get_xdata()[0] == pytest.approx(0.5 * (zone["start"] + zone["end"]))
    assert mark.get_ydata()[0] == pytest.approx(governing["value"] * 1e6, rel=1e-12)
    assert mark.get_ydata()[0] == pytest.approx(
        zone[f"total_{zone['governed_by']}_strain"] * 1e6, rel=1e-12
    )
    (text,) = texts(ax, "check:damage_category")
    assert text.get_text() == (
        f"category 0 (negligible), u = {governing['utilization']:.2f}"
    )


def test_the_range_holds_the_strains_the_limit_and_the_governing_band(
    building_check, drawn
):
    bottom, top = drawn[4].get_ylim()
    zones = building_check.zones
    largest = zones[["total_bending_strain", "total_diagonal_strain"]].max().max()
    governing_band = building_check.categories.category(zones["tensile_strain"].max())
    for level in (largest, 1.5e-3, governing_band.upper_limit):
        assert bottom < level * 1e6 < top


# AC 7: zone ends and the cut-off on every panel


def test_zone_ends_and_the_cutoff_on_every_panel(building_check, drawn):
    zones = building_check.zones
    distance = building_check.values["distance"]
    for ax in drawn:
        ends = sorted(float(item.get_xdata()[0]) for item in lines(ax, "zone_end"))
        np.testing.assert_allclose(ends, zones["end"].iloc[:-1], rtol=0, atol=1e-9)
        cut = sorted(float(item.get_xdata()[0]) for item in lines(ax, "cutoff"))
        np.testing.assert_allclose(
            cut, [zones["start"].iloc[0], zones["end"].iloc[-1]], rtol=0, atol=1e-9
        )
        hatched = sorted(
            (item.get_x(), item.get_x() + item.get_width())
            for item in patches(ax, "beyond_cutoff")
        )
        np.testing.assert_allclose(
            hatched,
            [
                (distance.iloc[0], zones["start"].iloc[0]),
                (zones["end"].iloc[-1], distance.iloc[-1]),
            ],
            rtol=0,
            atol=1e-9,
        )
    assert texts(drawn[0], "beyond_cutoff")
    assert not texts(drawn[1], "beyond_cutoff")


def test_no_cutoff_draws_none(make_building_check):
    result = make_building_check(cutoff=gs.buildings.no_cutoff())
    fig, axs = gs.plot.profile(result)
    for ax in axs:
        assert not lines(ax, "cutoff")
        assert not patches(ax, "beyond_cutoff")
        assert len(lines(ax, "zone_end")) == len(result.zones) - 1
    plt.close(fig)


# AC 10: twin tunnels


def test_twin_tunnels_draw_five_zones(twin_building_check):
    result = twin_building_check
    assert len(result.zones) == 5
    fig, axs = gs.plot.profile(result)
    fills = [
        item for item in axs[0].collections if str(item.get_gid()).startswith("zone_")
    ]
    assert len(fills) == 5
    for ax in axs:
        assert len(lines(ax, "zone_end")) == 4
    marks = [
        item for item in axs[1].get_lines() if str(item.get_gid()).startswith("delta:")
    ]
    assert len(marks) == 5
    plt.close(fig)


# AC 9: the edge cases draw, with their reason


def test_a_wall_wholly_beyond_the_cutoff(make_building_check):
    result = make_building_check(wall={"start_offset": 40, "end_offset": 100})
    assert result.zones.empty
    fig, axs = gs.plot.profile(result)
    assert len(axs) == 5
    for panel in (1, 4):
        (note,) = texts(axs[panel], "no_zone")
        assert note.get_text() == "no zone: the wall is wholly beyond the cut-off"
    for ax in axs:
        assert not lines(ax, "zone_end")
        assert not lines(ax, "cutoff")
        (hatched,) = patches(ax, "beyond_cutoff")
        assert hatched.get_width() == pytest.approx(60.0)
    assert not lines(axs[4], "check:damage_category")
    bands = [item for item in axs[4].patches if str(item.get_gid()).startswith("band")]
    assert not bands
    assert not [item for item in axs[1].get_lines() if "delta:" in str(item.get_gid())]
    (flags,) = texts(axs[-1], "flags")
    assert "no zone is assessed" in flags.get_text()
    plt.close(fig)
    fig, section = gs.plot.cross_section(result)
    assert not [item for item in section[2].get_lines() if item.get_gid() == "zone_end"]
    plt.close(fig)


def test_a_flat_zone(make_building_check):
    result = make_building_check(
        wall={"start_offset": 500, "end_offset": 560}, cutoff=gs.buildings.no_cutoff()
    )
    assert list(result.zones["mode"]) == ["flat"]
    fig, axs = gs.plot.profile(result)
    (note,) = texts(axs[1], "flat:zone_1")
    assert note.get_text() == "flat: no deflection"
    assert not lines(axs[1], "delta:zone_1")
    assert lines(axs[3], "horizontal_strain:zone_1")
    assert lines(axs[4], "total_bending_strain:zone_1")
    plt.close(fig)


@pytest.mark.parametrize(
    ("judgment", "panel", "text", "limit"),
    [
        ("settlement_limit", 0, "no settlement limit", "settlement_limit"),
        ("slope_limit", 2, "no slope limit", "slope_limit"),
        ("acceptable_category", 4, "no acceptable category", "damage_category_limit"),
    ],
)
def test_no_limit(make_building_check, judgment, panel, text, limit):
    result = make_building_check(**{judgment: None})
    fig, axs = gs.plot.profile(result)
    (note,) = texts(axs[panel], "no_limit")
    assert note.get_text() == text
    assert not lines(axs[panel], limit)
    (mark,) = texts(axs[4], "check:damage_category")
    if judgment == "acceptable_category":
        assert mark.get_text() == "category 0 (negligible), no limit"
    plt.close(fig)


def test_the_last_band_accepted(make_building_check):
    result = make_building_check(acceptable_category=4)
    fig, axs = gs.plot.profile(result)
    assert not lines(axs[4], "damage_category_limit")
    (note,) = texts(axs[4], "no_limit")
    assert note.get_text() == "acceptable: category 4 to 5, no upper limit"
    assert texts(axs[4], "check:damage_category")
    plt.close(fig)
