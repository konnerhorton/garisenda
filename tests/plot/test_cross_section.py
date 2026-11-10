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


def test_returns_a_figure_and_three_axes(case_a):
    fig, axs = gs.plot.cross_section(case_a)
    assert isinstance(fig, mpl.figure.Figure)
    assert len(axs) == 3


def test_trough_matches_the_source_at_the_surface(case_a):
    _, (top, middle, _) = gs.plot.cross_section(case_a)
    trough = line(top, "vertical")
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
    horizontal = np.asarray(line(middle, "horizontal").get_ydata())
    # Offset is x here, so u_n (positive right) is u_x.
    expected = movement.displacement[:, 0] * 1e3
    np.testing.assert_allclose(horizontal[sampled], expected, rtol=1e-12, atol=1e-15)
    assert horizontal[200] == 0.0
    # The trough draws the ground toward its axis: left on the right, and back.
    assert np.all(horizontal[201:] < 0)
    assert np.all(horizontal[:200] > 0)


def test_utility_stations_marked_from_values(case_a):
    _, (top, middle, _) = gs.plot.cross_section(case_a)
    values = case_a.values
    stations = line(top, "stations:vertical")
    np.testing.assert_allclose(stations.get_xdata(), values["offset"], rtol=1e-12)
    np.testing.assert_allclose(
        stations.get_ydata(), values["vertical"] * 1e3, rtol=1e-12
    )
    horizontal = line(middle, "stations:horizontal")
    # Case A runs from offset -20 to 20, so along is positive right.
    np.testing.assert_allclose(
        horizontal.get_ydata(), values["along"] * 1e3, rtol=1e-12, atol=1e-15
    )


def test_inflection_points_marked(case_a):
    _, axs = gs.plot.cross_section(case_a)
    for ax in axs[:2]:
        marks = [item for item in ax.get_lines() if item.get_gid() == "inflection"]
        assert sorted(item.get_xdata()[0] for item in marks) == [-10.0, 10.0]


def test_only_settlement_points_down(case_a):
    _, axs = gs.plot.cross_section(case_a)
    assert [ax.yaxis_inverted() for ax in axs] == [True, False, True]


def test_tunnel_and_utility_in_the_section(case_a, case_c):
    _, (_, _, bottom) = gs.plot.cross_section(case_a)
    bore = patch(bottom, "tunnel", Circle)
    assert bore.center == (0.0, 20.0)
    assert bore.radius == 3.0
    assert bottom.yaxis_inverted()
    assert bottom.get_aspect() == 1.0
    _, (_, _, bottom) = gs.plot.cross_section(case_c)
    band = patch(bottom, "utility", Rectangle)
    # Case C: invert at elevation 97.0, ground 100.0, diameter 0.6: axis 2.7 m.
    assert band.get_x() == pytest.approx(-20.0)
    assert band.get_width() == pytest.approx(40.0)
    assert band.get_y() == pytest.approx(2.7 - 0.3)
    assert band.get_height() == pytest.approx(0.6)


def test_case_c_stations_ringed_with_the_reason(case_c):
    _, (top, middle, bottom) = gs.plot.cross_section(case_c)
    for ax in (top, middle):
        ringed = line(ax, "outside")
        np.testing.assert_allclose(ringed.get_xdata(), case_c.values["offset"])
    (note,) = [text for text in bottom.texts if text.get_gid() == "flags"]
    assert case_c.warnings[0].reason in note.get_text()


def test_display_units(case_a):
    _, (top, middle, bottom) = gs.plot.cross_section(
        case_a, display_units={"displacement": "m", "length": "ft"}
    )
    assert top.get_ylabel() == "Settlement at the surface (m)"
    assert middle.get_ylabel() == "Horizontal at the surface (m)"
    assert bottom.get_xlabel() == "Offset from tunnel axis (ft)"
    assert patch(bottom, "tunnel", Circle).radius == pytest.approx(3.0 / 0.3048)


def test_a_direct_utility_raises_naming_the_plan_figure(case_d):
    with pytest.raises(ValueError, match="plan figure"):
        gs.plot.cross_section(case_d)


def test_draws_into_given_axes(case_a):
    fig, given = plt.subplots(3, 1, sharex=True)
    before = plt.get_fignums()
    returned_fig, _ = gs.plot.cross_section(case_a, axs=given)
    assert plt.get_fignums() == before
    assert returned_fig is fig


# AC 9


def test_leaves_no_global_state(case_c):
    before = dict(mpl.rcParams)
    gs.plot.cross_section(case_c)
    assert dict(mpl.rcParams) == before


# M2 (a), spec decision 14, AC 14: several tunnels.

u = gs.units


def north_tunnel():
    return gs.sources.IdealizedTunnel(
        reference_point=(0, 0), azimuth=0 * u.degree, diameter=6.0, axis_depth=20.0
    )


def trough_of(tunnel):
    return gs.sources.transverse_surface_trough(
        tunnel, volume_loss=1 * u.percent, trough_width_parameter=0.5
    )


def over(north, source):
    utility = gs.utilities.perpendicular_utility(
        north,
        utility_id="W-1",
        station=50,
        start_offset=-20,
        end_offset=20,
        depth=0,
        elevation_reference="axis",
        diameter=0.3,
    )
    return gs.movement_profile(utility, source, spacing=5.0)


@pytest.fixture
def twins_a():
    """Case A: equal twins 15 m apart."""
    north = north_tunnel()
    south = north.parallel(offset=15.0, diameter=6.0, axis_depth=20.0)
    return over(north, gs.superpose(north=trough_of(north), south=trough_of(south)))


@pytest.fixture
def crossing():
    """North, and east crossing it at 90 degrees, 30 m up-station of the section."""
    north = north_tunnel()
    east = gs.sources.IdealizedTunnel(
        reference_point=(0, 80), azimuth=90 * u.degree, diameter=6.0, axis_depth=26.0
    )
    return over(north, gs.superpose(north=trough_of(north), east=trough_of(east)))


def gids(ax):
    return {item.get_gid() for item in [*ax.get_lines(), *ax.patches, *ax.texts]}


def test_twins_draw_both_bores_axes_and_troughs(twins_a):
    _, (top, middle, bottom) = gs.plot.cross_section(twins_a)
    north = patch(bottom, "tunnel:north", Circle)
    south = patch(bottom, "tunnel:south", Circle)
    assert north.center == (0.0, 20.0)
    assert south.center == pytest.approx((15.0, 20.0))
    assert {"axis_depth:north", "cover:north", "axis_depth:south", "cover:south"} <= {
        text.get_gid() for text in bottom.texts
    }
    for ax in (top, middle, bottom):
        assert line(ax, "axis:north").get_xdata()[0] == 0.0
        assert line(ax, "axis:south").get_xdata()[0] == pytest.approx(15.0)
        assert "inflection" not in gids(ax)
    for ax, key in ((top, "vertical"), (middle, "horizontal")):
        assert line(ax, key).get_label() == "Combined"
        # Each tunnel's own trough is dashed differently, so the legend
        # tells them apart.
        north, south = (line(ax, f"trough:{name}:{key}") for name in ("north", "south"))
        assert north.get_linestyle() == "--"
        assert south.get_linestyle() == ":"
    assert bottom.get_xlabel() == "Offset from axis of tunnel 'north' (m)"
    assert "note" not in gids(bottom)


def test_twins_combined_trough_is_case_a(twins_a):
    _, (top, middle, _) = gs.plot.cross_section(twins_a)
    combined = line(top, "vertical")
    offset = np.asarray(combined.get_xdata())
    # The utility's offsets (-20 to 20) and each axis +-3i: -30 to 45.
    assert offset[0] == pytest.approx(-30.0)
    assert offset[-1] == pytest.approx(45.0)
    assert offset[200] == pytest.approx(7.5)
    # Case A at o = 7.5: S = 2 S_max exp(-7.5^2 / 200), in mm.
    assert combined.get_ydata()[200] == pytest.approx(1.7028921e-2 * 1e3, rel=1e-6)
    parts = sum(
        np.asarray(line(top, f"trough:{name}:vertical").get_ydata())
        for name in ("north", "south")
    )
    np.testing.assert_allclose(combined.get_ydata(), parts, rtol=1e-12)
    horizontal = np.asarray(line(middle, "horizontal").get_ydata())
    assert horizontal[200] == pytest.approx(0.0, abs=1e-12)


def test_a_crossing_tunnel_isnt_drawn_and_is_noted(crossing):
    _, (top, middle, bottom) = gs.plot.cross_section(crossing)
    assert patch(bottom, "tunnel:north", Circle).center == (0.0, 20.0)
    assert not [p for p in bottom.patches if p.get_gid() == "tunnel:east"]
    assert "axis:east" not in gids(top)
    (note,) = [text for text in bottom.texts if text.get_gid() == "note"]
    assert note.get_text().startswith("east isn't parallel to the reference tunnel")
    assert note.get_text().endswith("the troughs include it.")
    for ax, key in ((top, "vertical"), (middle, "horizontal")):
        line(ax, f"trough:east:{key}")


def test_a_lone_trough_has_no_names_or_note(case_a):
    _, (top, middle, bottom) = gs.plot.cross_section(case_a)
    assert line(top, "vertical").get_label() == "Trough"
    for ax in (top, middle, bottom):
        assert not {gid for gid in gids(ax) if gid and ":" in gid} - {
            "stations:vertical",
            "stations:horizontal",
        }
    assert "note" not in gids(bottom)


def test_twin_flags_are_named_under_the_section(twins_below_the_surface):
    _, (_, _, bottom) = gs.plot.cross_section(twins_below_the_surface)
    (note,) = [text for text in bottom.texts if text.get_gid() == "flags"]
    for flag in twins_below_the_surface.warnings:
        assert f": {flag.source}: {flag.reason}" in note.get_text()


def test_several_tunnels_leave_no_global_state(crossing):
    before = dict(mpl.rcParams)
    gs.plot.cross_section(crossing)
    assert dict(mpl.rcParams) == before


# M2 (b), spec decision 9, AC 10: the trough at the utility's depth.


def mair(*, depth, start_offset=-20, end_offset=20):
    """M1's tunnel with Mair's trough, a utility at a depth across it."""
    tunnel = north_tunnel()
    source = gs.sources.transverse_trough(
        tunnel,
        volume_loss=1 * u.percent,
        trough_width=gs.sources.mair_trough_width(),
    )
    utility = gs.utilities.perpendicular_utility(
        tunnel,
        utility_id="W-1",
        station=50,
        start_offset=start_offset,
        end_offset=end_offset,
        depth=depth,
        elevation_reference="axis",
        diameter=0.3,
    )
    return gs.movement_profile(utility, source, spacing=5.0)


def test_mair_trough_drawn_at_the_utility_depth():
    _, (top, middle, _) = gs.plot.cross_section(mair(depth=10.0))
    trough = line(top, "vertical")
    offset = np.asarray(trough.get_xdata())
    assert offset[200] == pytest.approx(0.0, abs=1e-12)
    # Case A, z = 10 m, o = 0: S = 1.67108552e-2 m.
    assert trough.get_ydata()[200] == pytest.approx(16.7108552, rel=1e-6)
    assert top.get_ylabel() == "Settlement at depth 10 m (mm)"
    assert middle.get_ylabel() == "Horizontal at depth 10 m (mm)"
    for ax in (top, middle):
        marks = [item for item in ax.get_lines() if item.get_gid() == "inflection"]
        assert sorted(item.get_xdata()[0] for item in marks) == pytest.approx(
            [-6.75, 6.75]
        )


def test_a_surface_trough_is_still_drawn_at_the_surface(case_c):
    _, (top, _, _) = gs.plot.cross_section(case_c)
    assert top.get_ylabel() == "Settlement at the surface (mm)"


def test_a_utility_beside_the_bore_draws_with_a_break():
    result = mair(depth=18.0, start_offset=5, end_offset=20)
    _, (top, middle, _) = gs.plot.cross_section(result)
    for ax, key in ((top, "vertical"), (middle, "horizontal")):
        trough = line(ax, key)
        offset = np.asarray(trough.get_xdata())
        drawn = np.asarray(trough.get_ydata())
        # Inside the bore at 18 m: |o| < sqrt(3^2 - 2^2).
        inside = np.abs(offset) < np.sqrt(5.0)
        assert inside.any()
        assert np.isnan(drawn[inside]).all()
        assert np.isfinite(drawn[~inside]).all()
    assert not result.values.isna().any().any()
    # Below the crown, i is the crown's: 4.475 m.
    marks = [item for item in top.get_lines() if item.get_gid() == "inflection"]
    assert sorted(item.get_xdata()[0] for item in marks) == pytest.approx(
        [-4.475, 4.475]
    )
    assert top.get_ylabel() == "Settlement at depth 18 m (mm)"


def test_a_trough_at_depth_leaves_no_global_state():
    before = dict(mpl.rcParams)
    gs.plot.cross_section(mair(depth=18.0, start_offset=5, end_offset=20))
    assert dict(mpl.rcParams) == before
