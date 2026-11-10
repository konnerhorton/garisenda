"""A trough's extent along a segment (docs/work/m4a-building-damage.md, decision 6)."""

import math

import pytest

import garisenda as gs

u = gs.units


def tunnel():
    # Along +y through the origin, so offset is x.
    return gs.sources.IdealizedTunnel(
        reference_point=(0, 0), azimuth=0 * u.degree, diameter=6.0, axis_depth=20.0
    )


def surface():
    # i = 0.5 * 20 = 10 m, so 2.5 i = 25 m.
    return gs.sources.transverse_surface_trough(
        tunnel(), volume_loss=1 * u.percent, trough_width_parameter=0.5
    )


def at_depth():
    # Case A: i at 2 m = 0.5 * (20 - 2) = 9 m, so 2.5 i = 22.5 m.
    return gs.sources.transverse_trough(
        tunnel(),
        volume_loss=1 * u.percent,
        trough_width=gs.sources.linear_trough_width(trough_width_parameter=0.5),
    )


def test_surface_trough_perpendicular():
    extent = surface().trough_extent(start=(-40, 50, 0), end=(40, 50, 0), multiple=2.5)
    assert extent == pytest.approx((15.0, 65.0), abs=1e-12)


def test_surface_trough_reversed():
    extent = surface().trough_extent(start=(40, 50, 0), end=(-40, 50, 0), multiple=2.5)
    assert extent == pytest.approx((15.0, 65.0), abs=1e-12)


def test_surface_trough_at_45_degrees():
    # The wall crosses at 40 sqrt(2); the extent is sqrt(2) m i on each side.
    extent = surface().trough_extent(start=(-40, -40, 0), end=(40, 40, 0), multiple=2.5)
    root2 = math.sqrt(2)
    assert extent == pytest.approx((15 * root2, 65 * root2), rel=1e-12)


def test_trough_at_depth_uses_i_at_the_segment_depth():
    extent = at_depth().trough_extent(start=(-30, 0, 2), end=(30, 0, 2), multiple=2.5)
    assert extent == pytest.approx((7.5, 52.5), abs=1e-12)


def test_clipped_to_the_segment():
    extent = surface().trough_extent(start=(10, 0, 0), end=(60, 0, 0), multiple=2.5)
    assert extent == pytest.approx((0.0, 15.0), abs=1e-12)


@pytest.mark.parametrize("source", [surface(), at_depth()])
def test_a_segment_wholly_beyond_gives_none(source):
    assert source.trough_extent(start=(30, 0, 1), end=(60, 0, 1), multiple=2.5) is None


def test_a_sloping_segment_raises_for_the_trough_at_depth():
    with pytest.raises(ValueError, match="only on a level segment"):
        at_depth().trough_extent(start=(-30, 0, 1), end=(30, 0, 2), multiple=2.5)


@pytest.mark.parametrize(("x", "expected"), [(10.0, (0.0, 30.0)), (30.0, None)])
def test_parallel_segments_are_all_within_or_all_beyond(x, expected):
    for source in (surface(), at_depth()):
        extent = source.trough_extent(start=(x, 0, 1), end=(x, 30, 1), multiple=2.5)
        if expected is None:
            assert extent is None
        else:
            assert extent == pytest.approx(expected)


@pytest.mark.parametrize("multiple", [0.0, -1.0, math.inf, math.nan])
def test_bad_multiple_raises(multiple):
    with pytest.raises(ValueError, match="multiple must be positive"):
        surface().trough_extent(start=(-40, 0, 0), end=(40, 0, 0), multiple=multiple)


def twins(offset=15.0):
    north = tunnel()
    south = north.parallel(offset=offset, diameter=6.0, axis_depth=20.0)
    return gs.superpose(
        **{
            name: gs.sources.transverse_surface_trough(
                part, volume_loss=1 * u.percent, trough_width_parameter=0.5
            )
            for name, part in (("north", north), ("south", south))
        }
    )


def test_superposition_takes_the_hull():
    # Case C: north within -25..25, south within -10..40: offsets -25 to 40.
    extent = twins().trough_extent(start=(-30, 0, 0), end=(45, 0, 0), multiple=2.5)
    assert extent == pytest.approx((5.0, 70.0), abs=1e-12)


def test_superposition_keeps_the_ground_between_the_troughs():
    # 60 m apart with 2.5 i = 25 m: the hull runs over the gap between them.
    extent = twins(60.0).trough_extent(start=(-30, 0, 0), end=(90, 0, 0), multiple=2.5)
    assert extent == pytest.approx((5.0, 115.0), abs=1e-12)


def test_superposition_beyond_every_trough_gives_none():
    assert twins().trough_extent(start=(50, 0, 0), end=(90, 0, 0), multiple=2.5) is None


def test_superposition_names_the_source_of_an_error():
    north = tunnel()
    south = north.parallel(offset=15.0, diameter=6.0, axis_depth=20.0)
    source = gs.superpose(
        north=gs.sources.transverse_surface_trough(
            north, volume_loss=1 * u.percent, trough_width_parameter=0.5
        ),
        south=gs.sources.transverse_trough(
            south,
            volume_loss=1 * u.percent,
            trough_width=gs.sources.linear_trough_width(trough_width_parameter=0.5),
        ),
    )
    with pytest.raises(ValueError, match=r"^south: The trough's extent"):
        source.trough_extent(start=(-30, 0, 1), end=(30, 0, 2), multiple=2.5)
