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
