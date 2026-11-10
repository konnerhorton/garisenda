import garisenda as gs

u = gs.units

tunnel = gs.sources.IdealizedTunnel(
    reference_point=(0, 0) * u.m,
    azimuth=0 * u.degree,
    diameter=6.0 * u.m,
    axis_depth=20.0 * u.m,
)
trough = gs.sources.transverse_surface_trough(
    tunnel, volume_loss=1.0 * u.percent, trough_width_parameter=0.5
)
gas_main = gs.utilities.perpendicular_utility(
    tunnel,
    utility_id="Gas main",
    station=80 * u.m,
    start_offset=-30 * u.m,
    end_offset=20 * u.m,
    depth=0 * u.m,
    elevation_reference="axis",
    diameter=200 * u.mm,
)
result = gs.movement_profile(gas_main, trough, spacing=2 * u.m)

fig, axs = gs.plot.profile(result)
fig.savefig("profile.png", dpi=100)

fig, axs = gs.plot.profile(result, display_units={"displacement": "in"})
fig.savefig("profile-inches.png", dpi=100)

# A building check: a wall 9 m high on a foundation 1.5 m down.
wall = gs.buildings.perpendicular_building(
    tunnel,
    building_id="Wall A",
    station=80 * u.m,
    start_offset=-30 * u.m,
    end_offset=30 * u.m,
    height=9 * u.m,
    foundation_depth=1.5 * u.m,
)
at_depth = gs.sources.transverse_trough(
    tunnel,
    volume_loss=1.5 * u.percent,
    trough_width=gs.sources.linear_trough_width(trough_width_parameter=0.5),
)
limits = gs.presets.preliminary_assessment_limits()
check = gs.check_building(
    gs.movement_profile(wall, at_depth, spacing=1 * u.m),
    beam_method=gs.buildings.burland_wroth_beam(),
    youngs_to_shear_modulus_ratio=gs.presets.youngs_to_shear_modulus_ratio(
        structure="masonry"
    ),
    category_limits=gs.presets.damage_categories(),
    cutoff=gs.buildings.trough_width_cutoff(multiple=2.5),
    settlement_limit=limits.settlement,
    slope_limit=limits.slope,
    acceptable_category=2,
    interaction="greenfield",
)
fig, axs = gs.plot.profile(check)
fig.savefig("profile-building.png", dpi=100)
