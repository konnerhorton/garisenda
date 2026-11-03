import garisenda as gs

u = gs.units

north = gs.sources.IdealizedTunnel(
    reference_point=(0, 0) * u.m,
    azimuth=0 * u.degree,
    diameter=6.0 * u.m,
    axis_depth=20.0 * u.m,
)
# The second bore, 15 m to the right, with its own depth and diameter.
south = north.parallel(offset=15 * u.m, diameter=6.0 * u.m, axis_depth=20.0 * u.m)

water_main = gs.utilities.perpendicular_utility(
    north,
    utility_id="Water main",
    station=120 * u.m,
    start_offset=-25 * u.m,
    end_offset=40 * u.m,
    depth=1.5 * u.m,
    elevation_reference="axis",
    diameter=0.3 * u.m,
)


def twins(south_volume_loss):
    # Each tunnel has its own trough; nothing is shared between them.
    source = gs.superpose(
        north=gs.sources.transverse_surface_trough(
            north, volume_loss=1.0 * u.percent, trough_width_parameter=0.5
        ),
        south=gs.sources.transverse_surface_trough(
            south, volume_loss=south_volume_loss, trough_width_parameter=0.5
        ),
    )
    return gs.movement_profile(water_main, source, spacing=1 * u.m)


result = twins(south_volume_loss=1.5 * u.percent)
print(result)
print()
print([entry.name for entry in result.inputs if "volume_loss" in entry.name])
print()

fig, axs = gs.plot.cross_section(result)
fig.savefig("several-tunnels-cross-section.png", dpi=100)
fig, axs = gs.plot.profile(result)
fig.savefig("several-tunnels-profile.png", dpi=100)

table = gs.sweep(twins, vary={"south.volume_loss": [1.0, 1.5, 2.0] * u.percent})
columns = ["south.volume_loss", "largest_settlement", "largest_settlement_distance"]
print(table[columns].to_string(index=False))
