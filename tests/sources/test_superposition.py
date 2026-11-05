"""Several tunnels by superposition (M2 (a), spec decisions 1-5, ACs 1, 4, 8-11)."""

import math

import numpy as np
import pytest

import garisenda as gs
from garisenda.sources._superposition import ASSUMPTION, METHOD

u = gs.units
REL = 1e-6  # hand calculation carried to 8 figures (spec, acceptance criteria)


def north_tunnel(**changes):
    arguments = {
        "reference_point": (0, 0),
        "azimuth": 0 * u.degree,
        "diameter": 6.0,
        "axis_depth": 20.0,
    }
    arguments.update(changes)
    return gs.sources.IdealizedTunnel(**arguments)


def trough(tunnel, volume_loss=1.0, k=0.5):
    return gs.sources.transverse_surface_trough(
        tunnel, volume_loss=volume_loss * u.percent, trough_width_parameter=k
    )


def twins(offset, *, axis_depth=20.0, volume_loss=1.0, k=0.5):
    north = north_tunnel()
    south = north.parallel(offset=offset, diameter=6.0, axis_depth=axis_depth)
    return gs.superpose(north=trough(north), south=trough(south, volume_loss, k))


def case_a():
    return twins(15.0)


def case_b():
    return twins(30.0)


def case_c():
    return twins(15.0, axis_depth=30.0, volume_loss=1.5, k=0.4)


def utility(depth=0.0, start_offset=-30, end_offset=60):
    return gs.utilities.perpendicular_utility(
        north_tunnel(),
        utility_id="W-1",
        station=50,
        start_offset=start_offset,
        end_offset=end_offset,
        depth=depth,
        elevation_reference="axis",
        diameter=0.3,
    )


def profile(source, **changes):
    return gs.movement_profile(utility(**changes), source, spacing=2.5)


def at_offset(result, offset, tolerance=1e-9):
    values = result.values
    index = int(np.argmin(np.abs(values["offset"] - offset)))
    assert values["offset"].iloc[index] == pytest.approx(offset, abs=tolerance)
    return values.iloc[index]


# AC 1: o, vertical (S), along (u_n; the utility runs toward +n).
CASES = {
    "A": (
        case_a,
        [
            (7.5, 1.7028921e-2, 0.0),
            (0.0, 1.4941851e-2, 2.7465178e-3),
            (15.0, 1.4941851e-2, -2.7465178e-3),
            (22.5, 9.4118778e-3, -4.2025173e-3),
        ],
    ),
    "B": (
        case_b,
        [
            (15.0, 7.3240475e-3, 0.0),
            (0.0, 1.1405135e-2, 1.8796134e-4),
            (30.0, 1.1405135e-2, -1.8796134e-4),
        ],
    ),
    "C": (
        case_c,
        [
            (0.0, 1.7735179e-2, 3.2276758e-3),
            (7.5, 2.0112626e-2, -2.9338112e-4),
            (15.0, 1.7761808e-2, -2.7465178e-3),
        ],
    ),
}


@pytest.mark.parametrize("case", sorted(CASES))
def test_golden_values(case):
    make, rows = CASES[case]
    result = profile(make())
    for offset, vertical, along in rows:
        row = at_offset(result, offset)
        assert row["vertical"] == pytest.approx(vertical, rel=REL)
        assert row["along"] == pytest.approx(along, rel=REL, abs=REL * 1e-3)
    assert result.validity == "within"


def case_b_peak():
    """Solve case B's (a - x)/(a + x) = exp(-2 a x / i^2) in (0, a) by bisection."""
    a, i = 15.0, 10.0
    low, high = 1e-9, a - 1e-9
    for _ in range(200):
        middle = (low + high) / 2
        if (a - middle) / (a + middle) > math.exp(-2 * a * middle / i**2):
            low = middle
        else:
            high = middle
    return (low + high) / 2


def test_case_b_peaks():
    x = case_b_peak()
    assert x == pytest.approx(14.632437, abs=1e-6)  # the spec's 8 figures
    result = profile(case_b())
    for offset in (15 - x, 15 + x):
        assert at_offset(result, offset, 1e-8)["vertical"] == pytest.approx(
            1.1412031e-2, rel=REL
        )


# AC 4: feature length.


def test_feature_length_is_the_least_of_the_sources():
    ends = {"start": (-30, 50, 0), "end": (60, 50, 0)}
    assert case_c().feature_length(**ends) == pytest.approx(10.0, rel=1e-12)
    east = gs.sources.IdealizedTunnel(
        reference_point=(0, 50), azimuth=90 * u.degree, diameter=6, axis_depth=40
    )
    nested = gs.superpose(outer=case_c(), east=trough(east, k=0.2))
    assert nested.feature_length(**ends) == pytest.approx(8.0, rel=1e-12)


# AC 8: records.


def test_case_c_records():
    source = case_c()
    result = profile(source)
    for inputs in (source.inputs, result.inputs):
        records = {entry.name: entry for entry in inputs}
        assert records["north.volume_loss"].value.magnitude == pytest.approx(0.01)
        assert records["south.volume_loss"].value.magnitude == pytest.approx(0.015)
        assert records["south.offset"].value == 15 * u.m
        assert records["south.axis_depth"].value == 30 * u.m
        assert records["south.volume_loss"].kind == "design judgment"
        sampling = records["critical_distance_sampling"]
        assert sampling.value.magnitude == pytest.approx(1 / 8)
        assert sampling.kind == "constant or setting"
        tolerance = records["critical_distance_tolerance"]
        assert tolerance.value == 1e-9 * u.m
        assert tolerance.kind == "constant or setting"
        assert "volume_loss" not in records
    names = [entry.name for entry in source.method]
    assert names == ["Transverse Gaussian surface trough", "Superposition"]
    assert source.method[-1] == METHOD
    assert len(source.assumptions) == len(set(source.assumptions))
    assert source.assumptions[-1] == ASSUMPTION
    assert set(source.assumptions) == {*source.sources["north"].assumptions, ASSUMPTION}
    assert result.assumptions.count(ASSUMPTION) == 1
    assert [entry.name for entry in result.method].count("Superposition") == 1


def test_sources_are_kept_in_order_and_read_only():
    source = case_a()
    assert list(source.sources) == ["north", "south"]
    with pytest.raises(TypeError):
        source.sources["east"] = source.sources["north"]


# AC 9: flags and errors.


def test_below_the_surface_is_flagged_by_each_source():
    result = profile(case_a(), depth=5.0)
    assert (result.values["verdict"] == "outside").all()
    assert result.validity == "outside"
    assert [flag.source for flag in result.warnings] == ["north", "south"]
    stations = tuple(range(len(result.values)))
    assert all(flag.points == stations for flag in result.warnings)


def test_worst_verdict_per_point():
    movement = case_a().evaluate(x=[0.0, 7.5], y=[0.0, 0.0], depth=[0.0, 5.0])
    assert movement.verdict.tolist() == ["within", "outside"]
    assert [flag.points for flag in movement.flags] == [(1,), (1,)]


def test_point_inside_a_bore_names_its_source():
    with pytest.raises(ValueError, match=r"^south: .*inside the bore"):
        case_a().evaluate(x=15.0, y=0.0, depth=20.0)


def test_profile_through_a_bore_names_the_distances():
    with pytest.raises(
        ValueError,
        match=r"^Utility 'W-1': south: .*inside the bore can't be evaluated "
        r"at distances [\d., ]+ m along the segment\.$",
    ):
        profile(case_a(), depth=20.0, start_offset=8, end_offset=30)


# AC 10: inconsistent inputs (case E).


def test_overlapping_parallel_bores_raise():
    with pytest.raises(ValueError, match=r"north and south overlap.* 5 m apart"):
        twins(5.0)
    twins(6.0)  # touching


@pytest.mark.parametrize("azimuth", [0.0, 17.3, 45.0, 90.0, 133.7, 251.9, 315.0])
@pytest.mark.parametrize("diameter", [2.0, 3.25, 6.0, 11.7])
def test_touching_bores_built_with_parallel_never_raise(azimuth, diameter):
    # The offset is recovered from the twin's coordinates, so it can come out
    # a rounding error under D; touching bores are still allowed.
    first = gs.sources.IdealizedTunnel(
        reference_point=(123.4, -56.7),
        azimuth=azimuth * u.degree,
        diameter=diameter,
        axis_depth=20.0,
    )
    for side in (-1, 1):
        twin = first.parallel(
            offset=side * diameter, diameter=diameter, axis_depth=20.0
        )
        gs.superpose(first=trough(first), twin=trough(twin))


def crossing(axis_depth):
    east = gs.sources.IdealizedTunnel(
        reference_point=(0, 50),
        azimuth=90 * u.degree,
        diameter=6,
        axis_depth=axis_depth,
    )
    return gs.superpose(north=trough(north_tunnel()), east=trough(east))


def test_crossing_bores_raise_when_too_close_in_depth():
    with pytest.raises(ValueError, match=r"north and east overlap.* 4 m apart"):
        crossing(24.0)
    crossing(26.0)


def test_the_same_tunnel_twice_overlaps_itself():
    tunnel = north_tunnel()
    with pytest.raises(ValueError, match="overlap"):
        gs.superpose(first=trough(tunnel), second=trough(tunnel, volume_loss=2))


def by_elevation(south_ground=None, south_depth=None):
    north = north_tunnel(axis_depth=None, axis_elevation=80, ground_elevation=100)
    if south_depth is None:
        south = north.parallel(
            offset=30, diameter=6, axis_elevation=80, ground_elevation=south_ground
        )
    else:
        south = north.parallel(offset=30, diameter=6, axis_depth=south_depth)
    return gs.superpose(north=trough(north), south=trough(south))


def test_different_ground_surfaces_raise():
    with pytest.raises(
        ValueError,
        match=r"don't share a ground surface: north.ground_elevation is 100 m "
        r"and south.ground_elevation is 100.5 m",
    ):
        by_elevation(south_ground=100.5)
    by_elevation(south_ground=100)
    by_elevation(south_depth=20)


def test_ground_surfaces_compared_through_nesting():
    east = gs.sources.IdealizedTunnel(
        reference_point=(0, 50),
        azimuth=90 * u.degree,
        diameter=6,
        axis_elevation=60,
        ground_elevation=101,
    )
    with pytest.raises(ValueError, match=r"outer\.north\.ground_elevation"):
        gs.superpose(outer=by_elevation(south_ground=100), east=trough(east))


# AC 11: arguments.


def test_one_source_raises():
    with pytest.raises(TypeError, match="at least two"):
        gs.superpose(north=trough(north_tunnel()))


def test_positional_source_raises():
    with pytest.raises(TypeError, match="by name"):
        gs.superpose(trough(north_tunnel()), south=case_a().sources["south"])


def test_non_source_raises():
    with pytest.raises(TypeError, match="south isn't a source: it has no evaluate"):
        gs.superpose(north=trough(north_tunnel()), south=north_tunnel())


def test_dotted_name_raises():
    sources = case_a().sources
    with pytest.raises(TypeError, match=r"'a\.b' isn't a Python identifier"):
        gs.superpose(**{"north": sources["north"], "a.b": sources["south"]})


def test_nested_names():
    east = gs.sources.IdealizedTunnel(
        reference_point=(0, 50), azimuth=90 * u.degree, diameter=6, axis_depth=40
    )
    nested = gs.superpose(outer=case_a(), east=trough(east))
    names = [entry.name for entry in nested.inputs]
    assert "outer.north.volume_loss" in names
    assert "outer.south.volume_loss" in names
    assert "east.volume_loss" in names
    assert [entry.name for entry in nested.method].count("Superposition") == 1
    assert nested.assumptions.count(ASSUMPTION) == 1
    assert nested.method[-1] == METHOD
    movement = nested.evaluate(x=[0.0], y=[50.0], depth=[1.0])
    assert [flag.source for flag in movement.flags] == [
        "outer.north",
        "outer.south",
        "east",
    ]


# M2 (b), AC 9: troughs at depth, one of each method, superposed.


def mixed():
    north = north_tunnel()
    south = north.parallel(offset=30.0, diameter=6.0, axis_depth=20.0)
    return gs.superpose(
        north=gs.sources.transverse_trough(
            north,
            volume_loss=1 * u.percent,
            trough_width=gs.sources.mair_trough_width(),
        ),
        south=gs.sources.transverse_trough(
            south,
            volume_loss=1.5 * u.percent,
            trough_width=gs.sources.linear_trough_width(trough_width_parameter=0.4),
        ),
    )


def test_troughs_at_depth_sum():
    source = mixed()
    x = np.array([-12.0, 0.0, 7.5, 15.0, 31.0, 45.0])
    depth = np.array([0.0, 4.0, 10.0, 12.5, 16.0, 19.0])
    y = np.full_like(x, 50.0)
    total = source.evaluate(x=x, y=y, depth=depth)
    parts = [part.evaluate(x=x, y=y, depth=depth) for part in source.sources.values()]
    for name in ("displacement", "gradient", "hessian", "third_derivative"):
        np.testing.assert_allclose(
            getattr(total, name),
            sum(getattr(part, name) for part in parts),
            rtol=1e-14,
            atol=0,
        )


def test_troughs_at_depth_records():
    source = mixed()
    records = {entry.name: entry for entry in source.inputs}
    assert records["north.trough_width"].value == "Mair et al. (1993), clay"
    assert records["south.trough_width"].value == "linear"
    assert records["south.trough_width_parameter"].value.magnitude == 0.4
    assert "north.trough_width_parameter" not in records
    assert records["north.depth_tolerance"].kind == "constant or setting"
    data = profile(source, start_offset=-20, end_offset=50, depth=10.0).to_dict()
    named = {entry["name"]: entry for entry in data["inputs"]}
    assert named["north.trough_width"]["magnitude"] == "Mair et al. (1993), clay"
    assert named["north.trough_width"]["unit"] == ""


def test_troughs_at_depth_flag_below_each_crown_by_source():
    # x = -6 and x = 36 are beside each bore, 19 m deep: below both crowns.
    movement = mixed().evaluate(
        x=np.array([-6.0, 15.0, 36.0]), y=np.full(3, 50.0), depth=np.full(3, 19.0)
    )
    assert list(movement.verdict) == ["outside"] * 3
    assert [flag.source for flag in movement.flags] == ["north", "south"]
    assert all(flag.points == (0, 1, 2) for flag in movement.flags)
    assert "garisenda" not in movement.flags[0].reason
    assert "applied to the linear method by garisenda" in movement.flags[1].reason
