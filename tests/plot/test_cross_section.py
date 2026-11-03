import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.patches import Circle, Rectangle

import garisenda as gs


def line(ax, gid):
    (found,) = [item for item in ax.get_lines() if item.get_gid() == gid]
    return found


def patch(ax, gid, kind):
    (found,) = [
        item for item in ax.patches if isinstance(item, kind) and item.get_gid() == gid
    ]
    return found


# AC 8


def test_returns_a_figure_and_two_axes(case_a):
    fig, axs = gs.plot.cross_section(case_a)
    assert isinstance(fig, mpl.figure.Figure)
    assert len(axs) == 2


def test_trough_matches_the_source_at_the_surface(case_a):
    _, (top, _) = gs.plot.cross_section(case_a)
    trough = line(top, "trough")
    offset = np.asarray(trough.get_xdata())
    assert len(offset) == 401
    # The wider of the utility's offsets (20 m) and 3i (30 m).
    assert offset[0] == pytest.approx(-30.0)
    assert offset[-1] == pytest.approx(30.0)
    source = case_a.source
    sampled = [0, 100, 200, 333, 400]
    # The tunnel runs along +y through (0, 0), so offset is x and station is y.
    movement = source.evaluate(
        x=offset[sampled], y=np.full(len(sampled), 50.0), depth=np.zeros(5)
    )
    np.testing.assert_allclose(
        np.asarray(trough.get_ydata())[sampled],
        movement.displacement[:, 2] * 1e3,
        rtol=1e-12,
    )
    toward = np.asarray(line(top, "toward_axis").get_ydata())
    # Offset is x here, so u_n is u_x; toward the axis is -sign(o) u_n.
    expected = -np.sign(offset[sampled]) * movement.displacement[:, 0] * 1e3
    np.testing.assert_allclose(toward[sampled], expected, rtol=1e-12, atol=1e-15)
    assert toward[200] == 0.0
    assert np.all(toward >= 0)  # the trough draws the ground toward its axis


def test_utility_stations_marked_from_values(case_a):
    _, (top, _) = gs.plot.cross_section(case_a)
    values = case_a.values
    stations = line(top, "stations")
    np.testing.assert_allclose(stations.get_xdata(), values["offset"], rtol=1e-12)
    np.testing.assert_allclose(
        stations.get_ydata(), values["vertical"] * 1e3, rtol=1e-12
    )
    toward = line(top, "stations_toward_axis")
    expected = -np.sign(values["offset"]) * values["along"] * 1e3
    np.testing.assert_allclose(toward.get_ydata(), expected, rtol=1e-12, atol=1e-15)


def test_inflection_points_marked(case_a):
    _, (top, _) = gs.plot.cross_section(case_a)
    marks = [item for item in top.get_lines() if item.get_gid() == "inflection"]
    assert sorted(item.get_xdata()[0] for item in marks) == [-10.0, 10.0]


def test_tunnel_and_utility_in_the_section(case_a, case_c):
    _, (_, bottom) = gs.plot.cross_section(case_a)
    bore = patch(bottom, "tunnel", Circle)
    assert bore.center == (0.0, 20.0)
    assert bore.radius == 3.0
    assert bottom.yaxis_inverted()
    assert bottom.get_aspect() == 1.0
    _, (_, bottom) = gs.plot.cross_section(case_c)
    band = patch(bottom, "utility", Rectangle)
    # Case C: invert at elevation 97.0, ground 100.0, diameter 0.6: axis 2.7 m.
    assert band.get_x() == pytest.approx(-20.0)
    assert band.get_width() == pytest.approx(40.0)
    assert band.get_y() == pytest.approx(2.7 - 0.3)
    assert band.get_height() == pytest.approx(0.6)


def test_case_c_stations_ringed_with_the_reason(case_c):
    _, (top, bottom) = gs.plot.cross_section(case_c)
    ringed = line(top, "outside")
    np.testing.assert_allclose(ringed.get_xdata(), case_c.values["offset"])
    (note,) = [text for text in bottom.texts if text.get_gid() == "flags"]
    assert case_c.warnings[0].reason in note.get_text()


def test_display_units(case_a):
    _, (top, bottom) = gs.plot.cross_section(
        case_a, display_units={"displacement": "m", "length": "ft"}
    )
    assert top.get_ylabel() == "Movement at the surface (m)"
    assert bottom.get_xlabel() == "Offset from tunnel axis (ft)"
    assert patch(bottom, "tunnel", Circle).radius == pytest.approx(3.0 / 0.3048)


def test_a_direct_utility_raises_naming_the_plan_figure(case_d):
    with pytest.raises(ValueError, match="plan figure"):
        gs.plot.cross_section(case_d)


def test_draws_into_given_axes(case_a):
    fig, given = plt.subplots(2, 1, sharex=True)
    before = plt.get_fignums()
    returned_fig, _ = gs.plot.cross_section(case_a, axs=given)
    assert plt.get_fignums() == before
    assert returned_fig is fig


# AC 9


def test_leaves_no_global_state(case_c):
    before = dict(mpl.rcParams)
    gs.plot.cross_section(case_c)
    assert dict(mpl.rcParams) == before
