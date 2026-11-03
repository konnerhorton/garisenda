"""The profile's derivatives are exact, along any straight utility (AC 7)."""

import numpy as np
from hypothesis import assume, given
from hypothesis import strategies as st

import garisenda as gs

u = gs.units

# Copied from tests/sources/test_transverse_properties.py rather than shared
# (M1 (a) plan, step 4); a third copy moves them to conftest.py.


@st.composite
def troughs(draw):
    diameter = draw(st.floats(2.0, 15.0))
    cover = draw(st.floats(1.0, 50.0))
    tunnel = gs.sources.IdealizedTunnel(
        reference_point=(draw(st.floats(-1e3, 1e3)), draw(st.floats(-1e3, 1e3))),
        azimuth=draw(st.floats(0.0, 360.0)) * u.degree,
        diameter=diameter,
        axis_depth=cover + diameter / 2,
        reference_station=draw(st.floats(-1e3, 1e3)),
    )
    return gs.sources.transverse_surface_trough(
        tunnel,
        volume_loss=draw(st.floats(0.1, 5.0)) * u.percent,
        trough_width_parameter=draw(st.floats(0.2, 1.0)),
    )


def point(source, station, offset):
    """Plan coordinates of a station and offset (in units of i)."""
    tunnel = source.tunnel
    along = station - tunnel.reference_station
    o = offset * source.trough_width
    x = tunnel.reference_x + along * tunnel.tangent[0] + o * tunnel.normal[0]
    y = tunnel.reference_y + along * tunnel.tangent[1] + o * tunnel.normal[1]
    return x, y


FIRST = {
    "along": "along_strain",
    "vertical": "vertical_slope",
    "lateral": "lateral_slope",
}
SECOND = {
    "along_strain": "along_strain_gradient",
    "vertical_slope": "vertical_curvature",
    "lateral_slope": "lateral_curvature",
}


@given(
    troughs(),
    st.floats(-1e3, 1e3),
    st.floats(-3.0, 3.0),
    st.floats(0.0, 360.0),
    st.floats(-30.0, 30.0),
    st.floats(0.0, 1.0),
)
def test_derivatives_match_finite_differences_along_the_utility(
    source, station, offset, plan_angle, pitch, level
):
    """Profiles starting a step behind, at and ahead of a point."""
    i = source.trough_width
    x, y = point(source, station, offset)
    plan, slope = np.radians(plan_angle), np.radians(pitch)
    direction = np.array(
        [np.sin(plan) * np.cos(slope), np.cos(plan) * np.cos(slope), np.sin(slope)]
    )
    cover = source.tunnel.axis_depth - source.tunnel.diameter / 2
    step = 1e-4 * i
    length = 0.1 * min(i, cover)
    # Every utility stays between the surface and half the cover: deep enough
    # to slope up a length and a step, shallow enough to slope down them.
    depth = length + step + level * cover / 2

    rows = []
    for shift in (-step, 0.0, step):
        start = np.array([x, y, depth]) + shift * direction
        end = start + length * direction
        utility = gs.utilities.Utility(
            utility_id="P", vertices=[start, end], diameter=0.1
        )
        values = gs.movement_profile(utility, source, spacing=length).values
        assume(values["distance"].iloc[0] == 0.0)  # no critical point merged in
        rows.append(values.iloc[0])
    behind, here, ahead = rows

    displacement_scale = source.maximum_settlement
    scales = {
        "along": displacement_scale / i,
        "vertical": displacement_scale / i,
        "lateral": displacement_scale / i,
        "along_strain": displacement_scale / i**2,
        "vertical_slope": displacement_scale / i**2,
        "lateral_slope": displacement_scale / i**2,
    }
    for value, derivative in (*FIRST.items(), *SECOND.items()):
        estimate = (ahead[value] - behind[value]) / (2 * step)
        np.testing.assert_allclose(
            here[derivative], estimate, rtol=0, atol=1e-6 * scales[value]
        )
