"""Reversing a wall leaves its check unchanged (m4a-building-damage, AC 14)."""

import math

import numpy as np
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

import garisenda as gs
from garisenda.profile._movement_profile import profile_rows

u = gs.units

CASE_A = gs.sources.transverse_trough(
    gs.sources.IdealizedTunnel(
        reference_point=(0, 0), azimuth=0 * u.degree, diameter=6.0, axis_depth=20.0
    ),
    volume_loss=1 * u.percent,
    trough_width=gs.sources.linear_trough_width(trough_width_parameter=0.5),
)


def case_d():
    north = gs.sources.IdealizedTunnel(
        reference_point=(0, 0), azimuth=0 * u.degree, diameter=6.0, axis_depth=20.0
    )
    south = north.parallel(offset=30.0, diameter=6.0, axis_depth=20.0)
    return gs.superpose(
        north=gs.sources.transverse_surface_trough(
            north, volume_loss=1 * u.percent, trough_width_parameter=0.5
        ),
        south=gs.sources.transverse_surface_trough(
            south, volume_loss=1 * u.percent, trough_width_parameter=0.5
        ),
    )


CASE_D = case_d()

ZONE_VALUES = (
    "length",
    "deflection",
    "deflection_ratio",
    "horizontal_strain",
    "bending_strain",
    "diagonal_strain",
    "total_bending_strain",
    "total_diagonal_strain",
    "tensile_strain",
)


def check(vertices, source, depth):
    building = gs.buildings.Building(
        building_id="W", vertices=vertices, foundation_depth=depth, height=8.0
    )
    return gs.check_building(
        gs.movement_profile(building, source, spacing=2.0),
        beam_method=gs.buildings.timoshenko_beam(),
        youngs_to_shear_modulus_ratio=2.6,
        category_limits=gs.presets.damage_categories(),
        cutoff=gs.buildings.no_cutoff(),
        settlement_limit=10 * u.mm,
        slope_limit=2 * u("mm/m"),
        acceptable_category=2,
        interaction="greenfield",
    )


def assert_reversed(forward, backward, length):
    ahead, behind = forward.zones, backward.zones.iloc[::-1].reset_index(drop=True)
    assert len(ahead) == len(behind)
    assert ahead["mode"].tolist() == behind["mode"].tolist()
    assert ahead["category"].tolist() == behind["category"].tolist()
    for column in ZONE_VALUES:
        np.testing.assert_allclose(
            behind[column], ahead[column], rtol=1e-7, atol=1e-15, err_msg=column
        )
    np.testing.assert_allclose(length - behind["end"], ahead["start"], atol=1e-7)
    np.testing.assert_allclose(length - behind["start"], ahead["end"], atol=1e-7)
    np.testing.assert_allclose(
        length - behind["deflection_distance"],
        ahead["deflection_distance"],
        atol=1e-6,
    )
    first, second = (
        result.checks.set_index("check").loc[["settlement", "slope", "damage_category"]]
        for result in (forward, backward)
    )
    np.testing.assert_allclose(second["value"], first["value"], rtol=1e-9)
    assert second["passes"].tolist() == first["passes"].tolist()
    assert second["category"].tolist() == first["category"].tolist()
    # Stage 1's distance is L - d, or a tie within 1e-9 (the first by distance
    # either way), so a station near a flat peak can take it in one direction
    # and the peak's row in the other.
    for name in ("settlement", "slope"):
        mirrored = length - second.loc[name, "governing_distance"]
        column = "vertical" if name == "settlement" else "vertical_slope"
        at = value_at(forward, column, mirrored)
        assert abs(at) == pytest.approx(first.loc[name, "value"], rel=1e-9)


def value_at(result, column, distance):
    """A profile column at a distance: its row's, or computed there."""
    values = result.values
    nearest = int(np.argmin(np.abs(values["distance"].to_numpy() - distance)))
    if abs(values["distance"].iloc[nearest] - distance) < 1e-6:
        return values[column].iloc[nearest]
    rows, _, _ = profile_rows(
        result.asset, result.source, np.array([distance]), np.array([False])
    )
    return rows[column].iloc[0]


@settings(max_examples=20, deadline=None)
@example(15.0, -2.0000000000000004, 2.0000076293945317)  # a station 7.6 um from L
@given(
    st.floats(15.0, 165.0),
    st.floats(-40.0, -2.0),
    st.floats(2.0, 40.0),
)
def test_reversing_a_wall_over_case_a(angle, start, end):
    # A wall 2 m down, crossing the tunnel (along y) at the origin at `angle`.
    direction = (math.sin(math.radians(angle)), math.cos(math.radians(angle)))
    vertices = [(s * direction[0], s * direction[1]) for s in (start, end)]
    forward = check(vertices, CASE_A, 2.0)
    backward = check(vertices[::-1], CASE_A, 2.0)
    assert_reversed(forward, backward, end - start)


@settings(max_examples=10, deadline=None)
@given(st.floats(-40.0, -5.0), st.floats(35.0, 70.0))
def test_reversing_a_wall_over_case_d(start, end):
    vertices = [(start, 0.0), (end, 0.0)]
    forward = check(vertices, CASE_D, 0.0)
    backward = check(vertices[::-1], CASE_D, 0.0)
    assert_reversed(forward, backward, end - start)
