"""Reversing a jointed pipe leaves its checks unchanged (M3 (b) AC 12)."""

import math

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import garisenda as gs
from garisenda.profile._movement_profile import profile_rows
from garisenda.utilities._continuous_pipe import _with_discrete, _with_strains
from garisenda.utilities._jointed_pipe import _with_joints

u = gs.units
LENGTH = 4.0


def trough():
    tunnel = gs.sources.IdealizedTunnel(
        reference_point=(0, 0), azimuth=0 * u.degree, diameter=6.0, axis_depth=20.0
    )
    return gs.sources.transverse_trough(
        tunnel,
        volume_loss=1 * u.percent,
        trough_width=gs.sources.linear_trough_width(trough_width_parameter=0.5),
    )


SOURCE = trough()


def check(vertices):
    pipe = gs.utilities.Utility(utility_id="P", vertices=vertices, diameter=0.3)
    return gs.check_jointed_pipe(
        gs.movement_profile(pipe, SOURCE, spacing=2.0),
        pipe_lengths={("spun_grey_iron", 0.3): LENGTH},
        pipe_type="spun_grey_iron",
        interaction="greenfield",
        joint_rotation_limit=0.1 * u.degree,
        joint_pullout_limit=1 * u.mm,
        tensile_strain_limit=u.Quantity(1000, "µε"),
        compressive_strain_limit=u.Quantity(1000, "µε"),
        bending_strain_limit=u.Quantity(1000, "µε"),
        radius_of_curvature_limit=1000 * u.m,
    )


COLUMNS = {
    "axial_tension": "axial_strain",
    "axial_compression": "axial_strain",
    "bending": "bending_strain",
    "joint_pullout": "joint_opening",
}


@settings(max_examples=25, deadline=None)
@given(
    st.floats(5.0, 175.0),
    st.floats(-40.0, -2.0),
    st.floats(2.0, 40.0),
)
def test_reversing_the_pipe(angle, start, end):
    # A level pipe 2 m down, crossing the tunnel (along y) at the origin at
    # `angle` in plan, from `start` to `end` m along it.
    direction = (math.sin(math.radians(angle)), math.cos(math.radians(angle)))
    vertices = [(s * direction[0], s * direction[1], 2.0) for s in (start, end)]
    forward = check(vertices)
    backward = check(vertices[::-1])
    length = end - start
    for (_, ahead), (_, behind) in zip(
        forward.checks.iterrows(), backward.checks.iterrows(), strict=True
    ):
        for column in ("value", "utilization"):
            if math.isnan(ahead[column]):
                assert math.isnan(behind[column])
            else:
                assert behind[column] == pytest.approx(ahead[column], rel=1e-9)
        if ahead["passes"] is pd.NA:
            assert behind["passes"] is pd.NA
        else:
            assert behind["passes"] == ahead["passes"]
        if math.isnan(ahead["value"]):
            continue
        # The governing distance is L - d, or a tie (to the smallest distance
        # either way): the value at L - d is the governing value.
        mirrored = length - behind["governing_distance"]
        column = COLUMNS.get(ahead["check"], ahead["check"])
        if ahead["governed_by"] == "discrete" and not column.startswith("joint_"):
            column = f"discrete_{column}"
        assert value_at(forward, column, mirrored) == pytest.approx(
            ahead["value"], rel=1e-9
        )


def value_at(result, column, distance):
    """A column at a distance: its row's, or computed there."""
    values = result.values
    nearest = int(np.argmin(np.abs(values["distance"].to_numpy() - distance)))
    if abs(values["distance"].iloc[nearest] - distance) < 1e-6:
        return values[column].iloc[nearest]
    radius = result.asset.diameter / 2
    rows, _, _ = profile_rows(
        result.asset, result.source, np.array([distance]), np.array([False])
    )
    rows = _with_strains(rows, radius)
    rows = _with_discrete(rows, result.asset, result.source, LENGTH, radius)
    return _with_joints(rows, LENGTH, radius)[column].iloc[0]
