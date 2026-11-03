import matplotlib
import pytest

matplotlib.use("Agg")

import matplotlib.pyplot as plt

import garisenda as gs


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.fixture
def twins_below_the_surface():
    """Twin troughs 15 m apart, a utility 2 m down: outside for both (M2 (a))."""
    u = gs.units
    north = gs.sources.IdealizedTunnel(
        reference_point=(0, 0), azimuth=0 * u.degree, diameter=6.0, axis_depth=20.0
    )
    south = north.parallel(offset=15.0, diameter=6.0, axis_depth=20.0)
    source = gs.superpose(
        **{
            name: gs.sources.transverse_surface_trough(
                tunnel, volume_loss=1 * u.percent, trough_width_parameter=0.5
            )
            for name, tunnel in (("north", north), ("south", south))
        }
    )
    utility = gs.utilities.perpendicular_utility(
        north,
        utility_id="W-1",
        station=50,
        start_offset=-30,
        end_offset=60,
        depth=2.0,
        elevation_reference="axis",
        diameter=0.3,
    )
    return gs.movement_profile(utility, source, spacing=2.5)
