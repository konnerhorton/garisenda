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
