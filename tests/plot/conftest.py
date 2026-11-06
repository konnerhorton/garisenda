import pytest

import garisenda as gs

u = gs.units


def tunnel():
    return gs.sources.IdealizedTunnel(
        reference_point=(0, 0), azimuth=0 * u.degree, diameter=6.0, axis_depth=20.0
    )


def trough():
    return gs.sources.transverse_surface_trough(
        tunnel(), volume_loss=1 * u.percent, trough_width_parameter=0.5
    )


def built(source, **changes):
    arguments = {
        "utility_id": "W-1",
        "station": 50,
        "start_offset": -20,
        "end_offset": 20,
        "depth": 0,
        "elevation_reference": "axis",
        "diameter": 0.3,
    }
    arguments.update(changes)
    return gs.utilities.perpendicular_utility(source.tunnel, **arguments)


@pytest.fixture
def case_a():
    source = trough()
    return gs.movement_profile(built(source), source, spacing=5.0)


@pytest.fixture
def case_c():
    source = trough()
    utility = built(
        source,
        depth=None,
        elevation=97.0,
        ground_elevation=100.0,
        elevation_reference="invert",
        diameter=0.6,
    )
    return gs.movement_profile(utility, source, spacing=5.0)


@pytest.fixture
def case_d():
    utility = gs.utilities.Utility(
        utility_id="G-2", vertices=[(-20, -20, 0), (20, 20, 0)], diameter=0.2
    )
    return gs.movement_profile(utility, trough(), spacing=5.0)


def pipe_check(**limits):
    """Case A of the M3 (a) spec, checked at a 1 m interval."""
    tunnel_ = tunnel()
    source = gs.sources.transverse_trough(
        tunnel_,
        volume_loss=1 * u.percent,
        trough_width=gs.sources.linear_trough_width(trough_width_parameter=0.5),
    )
    utility = gs.utilities.perpendicular_utility(
        tunnel_,
        utility_id="A",
        station=0,
        start_offset=-40,
        end_offset=40,
        depth=2.0,
        elevation_reference="axis",
        diameter=0.3,
    )
    strain = u.Quantity(1000, "µε")
    given = {
        "tensile_strain_limit": strain,
        "compressive_strain_limit": strain,
        "bending_strain_limit": u.Quantity(50, "µε"),
        "radius_of_curvature_limit": 5000 * u.m,
    }
    given.update(limits)
    return gs.check_continuous_pipe(
        gs.movement_profile(utility, source, spacing=1.0),
        interval=1 * u.m,
        interaction="greenfield",
        **given,
    )


@pytest.fixture
def make_check():
    return pipe_check


@pytest.fixture
def checked():
    return pipe_check()
