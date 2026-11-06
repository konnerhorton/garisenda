"""Reversing a pipe leaves its checks unchanged (M3 (a) AC 12)."""

import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import garisenda as gs

u = gs.units


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
    return gs.check_continuous_pipe(
        gs.movement_profile(pipe, SOURCE, spacing=2.0),
        interval=1.0,
        interaction="greenfield",
        tensile_strain_limit=u.Quantity(1000, "µε"),
        compressive_strain_limit=u.Quantity(1000, "µε"),
        bending_strain_limit=u.Quantity(1000, "µε"),
        radius_of_curvature_limit=1000 * u.m,
    )


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
        assert behind["passes"] == ahead["passes"]
        if math.isnan(ahead["value"]):
            continue
        # The governing distance is L - d, or a tied extreme there of equal
        # value (ties go to the smallest distance either way).
        mirrored = length - behind["governing_distance"]
        column = {
            "axial_tension": "axial_strain",
            "axial_compression": "axial_strain",
            "bending": "bending_strain",
            "radius_of_curvature": "radius_of_curvature",
        }.get(ahead["check"], ahead["check"])
        distance = forward.values["distance"].to_numpy()
        nearest = int(np.argmin(np.abs(distance - mirrored)))
        assert distance[nearest] == pytest.approx(mirrored, abs=1e-6)
        assert forward.values[column].iloc[nearest] == pytest.approx(
            ahead["value"], rel=1e-9
        )
