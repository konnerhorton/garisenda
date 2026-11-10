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


def jointed_check(**limits):
    """Case J-A of the M3 (b) spec: case A's pipe in 4 m lengths."""
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
        "joint_rotation_limit": 1.5 * u.degree,
        "joint_pullout_limit": 15 * u.mm,
        "tensile_strain_limit": strain,
        "compressive_strain_limit": strain,
        "bending_strain_limit": u.Quantity(50, "µε"),
        "radius_of_curvature_limit": 5000 * u.m,
    }
    given.update(limits)
    return gs.check_jointed_pipe(
        gs.movement_profile(utility, source, spacing=1.0),
        pipe_lengths={("spun_grey_iron", 0.3 * u.m): 4 * u.m},
        pipe_type="spun_grey_iron",
        interaction="greenfield",
        **given,
    )


@pytest.fixture
def make_jointed():
    return jointed_check


@pytest.fixture
def jointed():
    return jointed_check()


def building_check_with(**changes):
    """The building figures' example: a wall over one tunnel, checked with presets.

    A tunnel 20 m deep, 6 m in diameter, volume loss 1.5 %, k = 0.5; a wall
    from offset -30 m to +30 m, 9 m high on a foundation 1.5 m down; the
    Burland & Wroth beam, a 2.5 i cut-off and acceptable category 2.
    `changes` replace the wall's arguments (``wall``), the trough's
    (``volume_loss``) or the check's judgments.
    """
    tunnel_ = tunnel()
    source = gs.sources.transverse_trough(
        tunnel_,
        volume_loss=changes.pop("volume_loss", 1.5 * u.percent),
        trough_width=gs.sources.linear_trough_width(trough_width_parameter=0.5),
    )
    wall = {
        "building_id": "W-1",
        "station": 50,
        "start_offset": -30,
        "end_offset": 30,
        "height": 9.0,
        "foundation_depth": 1.5,
    }
    wall.update(changes.pop("wall", {}))
    building = gs.buildings.perpendicular_building(tunnel_, **wall)
    limits = gs.presets.preliminary_assessment_limits()
    judgments = {
        "beam_method": gs.buildings.burland_wroth_beam(),
        "youngs_to_shear_modulus_ratio": gs.presets.youngs_to_shear_modulus_ratio(
            structure="masonry"
        ),
        "category_limits": gs.presets.damage_categories(),
        "cutoff": gs.buildings.trough_width_cutoff(multiple=2.5),
        "settlement_limit": limits.settlement,
        "slope_limit": limits.slope,
        "acceptable_category": 2,
        "interaction": "greenfield",
    }
    judgments.update(changes)
    return gs.check_building(
        gs.movement_profile(building, source, spacing=1.0), **judgments
    )


@pytest.fixture(scope="module")
def building_check():
    return building_check_with()


@pytest.fixture
def make_building_check():
    return building_check_with


@pytest.fixture(scope="module")
def twin_building_check():
    """A wall over twin tunnels 25 m apart, with no cut-off: five zones.

    Twins 15 m apart (``twins_below_the_surface``) make one trough with three
    zones; 25 m apart, each tunnel's trough has its own sagging zone.
    """
    north = tunnel()
    south = north.parallel(offset=25.0, diameter=6.0, axis_depth=20.0)
    source = gs.superpose(
        **{
            name: gs.sources.transverse_surface_trough(
                reference, volume_loss=1 * u.percent, trough_width_parameter=0.5
            )
            for name, reference in (("north", north), ("south", south))
        }
    )
    building = gs.buildings.perpendicular_building(
        north,
        building_id="W-2",
        station=50,
        start_offset=-30,
        end_offset=55,
        height=9.0,
        foundation_depth=1.5,
    )
    limits = gs.presets.preliminary_assessment_limits()
    return gs.check_building(
        gs.movement_profile(building, source, spacing=1.0),
        beam_method=gs.buildings.burland_wroth_beam(),
        youngs_to_shear_modulus_ratio=2.6,
        category_limits=gs.presets.damage_categories(),
        cutoff=gs.buildings.no_cutoff(),
        settlement_limit=limits.settlement,
        slope_limit=limits.slope,
        acceptable_category=2,
        interaction="greenfield",
    )
