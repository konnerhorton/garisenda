import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.patches import Rectangle

import garisenda as gs


def line(ax, gid):
    (found,) = [item for item in ax.get_lines() if item.get_gid() == gid]
    return found


# AC 7


def test_returns_a_figure_and_four_axes(case_a):
    fig, axs = gs.plot.profile(case_a)
    assert isinstance(fig, mpl.figure.Figure)
    assert len(axs) == 4
    assert all(ax.figure is fig for ax in axs)


@pytest.mark.parametrize(
    ("panel", "column", "factor"),
    [
        (0, "vertical", 1e3),
        (1, "along", 1e3),
        (1, "lateral", 1e3),
        (2, "along_strain", 1e6),
        (3, "vertical_curvature", 1e3),
        (3, "lateral_curvature", 1e3),
    ],
)
def test_lines_are_the_columns_in_display_units(case_a, panel, column, factor):
    _, axs = gs.plot.profile(case_a)
    drawn = line(axs[panel], column)
    values = case_a.values
    np.testing.assert_allclose(drawn.get_xdata(), values["distance"], rtol=1e-12)
    np.testing.assert_allclose(drawn.get_ydata(), values[column] * factor, rtol=1e-12)


def test_display_units_change_the_lines_and_labels(case_a):
    _, axs = gs.plot.profile(case_a, display_units={"displacement": "m"})
    np.testing.assert_allclose(
        line(axs[0], "vertical").get_ydata(), case_a.values["vertical"], rtol=1e-12
    )
    assert axs[0].get_ylabel() == "Settlement (m)"
    assert axs[2].get_ylabel() == "Strain along (µε)"
    assert axs[3].get_ylabel() == "Curvature (1/km)"
    assert axs[3].get_xlabel() == "Distance along utility (m)"


def test_settlement_axis_points_down(case_a):
    _, axs = gs.plot.profile(case_a)
    assert axs[0].yaxis_inverted()
    assert not axs[2].yaxis_inverted()


def test_governing_values_marked_at_their_distances(case_a):
    _, axs = gs.plot.profile(case_a)
    panels = {"vertical": 0, "along_strain": 2, "vertical_curvature": 3}
    factors = {"vertical": 1e3, "along_strain": 1e6, "vertical_curvature": 1e3}
    for row in case_a.governing().itertuples():
        mark = line(axs[panels[row.column]], f"governing:{row.name}")
        assert mark.get_xdata()[0] == pytest.approx(row.distance, rel=1e-12)
        assert mark.get_ydata()[0] == pytest.approx(
            row.value * factors[row.column], rel=1e-12
        )


def test_critical_stations_ticked(case_a):
    _, axs = gs.plot.profile(case_a)
    values = case_a.values
    expected = values["distance"][values["critical"]]
    for ax in axs:
        np.testing.assert_allclose(line(ax, "critical").get_xdata(), expected)


def test_case_c_shaded_with_the_reason_under_the_figure(case_c):
    _, axs = gs.plot.profile(case_c)
    for ax in axs:
        (shade,) = [
            patch
            for patch in ax.patches
            if isinstance(patch, Rectangle) and patch.get_gid() == "outside"
        ]
        assert shade.get_x() == pytest.approx(0.0)
        assert shade.get_x() + shade.get_width() == pytest.approx(40.0)
    (note,) = [text for text in axs[-1].texts if text.get_gid() == "flags"]
    reason = case_c.warnings[0].reason
    assert note.get_text() == f"Outside (11 stations, 0 to 40 m): {reason}"


def test_case_a_is_not_shaded(case_a):
    _, axs = gs.plot.profile(case_a)
    assert not [patch for ax in axs for patch in ax.patches if patch.get_gid()]
    assert not [text for text in axs[-1].texts if text.get_gid() == "flags"]


def test_offset_axis_only_for_a_built_utility(case_a, case_d):
    _, axs = gs.plot.profile(case_a)
    assert len(axs[0].child_axes) == 1
    _, axs = gs.plot.profile(case_d)
    assert axs[0].child_axes == []


def test_draws_into_given_axes(case_a):
    fig, given = plt.subplots(4, 1, sharex=True)
    before = plt.get_fignums()
    returned_fig, returned = gs.plot.profile(case_a, axs=given)
    assert plt.get_fignums() == before
    assert returned_fig is fig
    assert list(returned) == list(given)
    assert line(given[0], "vertical")


def test_wrong_number_of_axes_raises(case_a):
    _, given = plt.subplots(2, 1)
    with pytest.raises(ValueError, match="4 matplotlib Axes"):
        gs.plot.profile(case_a, axs=given)


# AC 9


def test_leaves_no_global_state(case_c):
    before = dict(mpl.rcParams)
    gs.plot.profile(case_c)
    assert dict(mpl.rcParams) == before


# M2 (a), spec decision 13, AC 9: the notes name each flag's source.


def test_flag_notes_name_their_source(twins_below_the_surface):
    twins = twins_below_the_surface
    _, axs = gs.plot.profile(twins)
    (note,) = [text for text in axs[-1].texts if text.get_gid() == "flags"]
    lines = note.get_text().splitlines()
    assert len(lines) == 2
    for text, flag in zip(lines, twins.warnings, strict=True):
        assert text.startswith("Outside (")
        assert text.endswith(f": {flag.source}: {flag.reason}")


# M3 (a), spec decision 13, AC 15: a check result in six panels

CHECK_LINES = [
    (0, "vertical", 1e3, False),
    (1, "along", 1e3, False),
    (1, "lateral", 1e3, False),
    (2, "axial_strain", 1e6, True),
    (3, "vertical_curvature", 1e3, True),
    (3, "lateral_curvature", 1e3, True),
    (3, "resultant_curvature", 1e3, True),
    (4, "vertical_bending_strain", 1e6, False),
    (4, "lateral_bending_strain", 1e6, False),
    (4, "bending_strain", 1e6, True),
    (5, "tensile_strain", 1e6, True),
    (5, "compressive_strain", 1e6, True),
]


def test_a_check_draws_six_panels(checked):
    fig, axs = gs.plot.profile(checked)
    assert len(axs) == 6
    assert all(ax.figure is fig for ax in axs)
    assert axs[2].get_ylabel() == "Axial strain (µε)"
    assert axs[5].get_ylabel() == "Combined strain (µε)"
    assert "1 m" in fig.get_suptitle()


@pytest.mark.parametrize(("panel", "column", "factor", "discrete"), CHECK_LINES)
def test_a_check_draws_each_column_and_its_discrete_one(
    checked, panel, column, factor, discrete
):
    _, axs = gs.plot.profile(checked)
    values = checked.values
    drawn = line(axs[panel], column)
    np.testing.assert_allclose(drawn.get_ydata(), values[column] * factor, rtol=1e-12)
    gid = f"discrete_{column}"
    dashed = [item for item in axs[panel].get_lines() if item.get_gid() == gid]
    if not discrete:
        assert not dashed
        return
    (dashed,) = dashed
    assert dashed.get_color() == drawn.get_color()
    assert dashed.get_linestyle() != drawn.get_linestyle()
    expected = values[f"discrete_{column}"].to_numpy(dtype=float) * factor
    np.testing.assert_allclose(dashed.get_ydata(), expected, rtol=1e-12)
    # gaps where a station has no discrete value (the ends, spec decision 6)
    assert np.isnan(dashed.get_ydata()[0])


@pytest.mark.parametrize(
    ("panel", "name", "levels"),
    [
        (2, "tensile_strain_limit", [1000.0]),
        (2, "compressive_strain_limit", [-1000.0]),
        (3, "radius_of_curvature_limit", [0.2, -0.2]),  # 1/(5000 m), in 1/km
        (4, "bending_strain_limit", [50.0]),
        (5, "tensile_strain_limit", [1000.0]),
        (5, "compressive_strain_limit", [-1000.0]),
    ],
)
def test_a_check_draws_its_limits(checked, panel, name, levels):
    _, axs = gs.plot.profile(checked)
    drawn = [item for item in axs[panel].get_lines() if item.get_gid() == name]
    assert sorted(item.get_ydata()[0] for item in drawn) == pytest.approx(
        sorted(levels), rel=1e-12
    )
    assert [text for text in axs[panel].texts if text.get_gid() == name]


@pytest.mark.parametrize(
    ("panel", "check", "factor"),
    [
        (2, "axial_tension", 1e6),
        (2, "axial_compression", 1e6),
        (3, "radius_of_curvature", None),
        (4, "bending", 1e6),
        (5, "tensile_strain", 1e6),
        (5, "compressive_strain", 1e6),
    ],
)
def test_a_check_marks_each_governing_value(checked, panel, check, factor):
    _, axs = gs.plot.profile(checked)
    row = checked.checks.set_index("check").loc[check]
    mark = line(axs[panel], f"check:{check}")
    assert mark.get_xdata()[0] == pytest.approx(row["governing_distance"], rel=1e-12)
    expected = 1e3 / row["value"] if factor is None else row["value"] * factor
    assert mark.get_ydata()[0] == pytest.approx(expected, rel=1e-12)
    (text,) = [item for item in axs[panel].texts if item.get_gid() == f"check:{check}"]
    assert f"u = {row['utilization']:.2f}" in text.get_text()


def test_a_check_keeps_the_settlement_marker_only(checked):
    _, axs = gs.plot.profile(checked)
    marks = [
        str(item.get_gid())
        for ax in axs
        for item in ax.get_lines()
        if str(item.get_gid()).startswith("governing:")
    ]
    assert marks == ["governing:largest_settlement"]


@pytest.mark.parametrize(
    ("limit", "panels", "note"),
    [
        ("tensile_strain_limit", (2, 5), "no tensile limit"),
        ("bending_strain_limit", (4,), "no bending limit"),
        ("radius_of_curvature_limit", (3,), "no radius limit"),
    ],
)
def test_a_limit_of_none_draws_no_line(make_check, limit, panels, note):
    result = make_check(**{limit: None})
    _, axs = gs.plot.profile(result)
    for panel in panels:
        ax = axs[panel]
        assert not [item for item in ax.get_lines() if item.get_gid() == limit]
        (text,) = [item for item in ax.texts if item.get_gid() == "no_limit"]
        assert text.get_text() == note
    for index, ax in enumerate(axs):
        if index not in panels:
            assert not [item for item in ax.texts if item.get_gid() == "no_limit"]


def test_a_check_shows_the_ends_flag(checked):
    _, axs = gs.plot.profile(checked)
    (note,) = [text for text in axs[-1].texts if text.get_gid() == "flags"]
    assert note.get_text().startswith("Within (2 stations, 0 to 80 m)")


def test_a_check_needs_six_axes(checked):
    _, given = plt.subplots(4, 1)
    with pytest.raises(ValueError, match="6 matplotlib Axes"):
        gs.plot.profile(checked, axs=given)
    _, given = plt.subplots(6, 1, sharex=True)
    _, returned = gs.plot.profile(checked, axs=given)
    assert list(returned) == list(given)


def test_a_check_leaves_no_global_state(checked):
    before = dict(mpl.rcParams)
    gs.plot.profile(checked)
    assert dict(mpl.rcParams) == before
