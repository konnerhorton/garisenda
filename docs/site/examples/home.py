import garisenda as gs

u = gs.units

tunnel = gs.sources.IdealizedTunnel(
    reference_point=(0, 0), azimuth=0 * u.degree, diameter=6.0, axis_depth=20.0
)
trough = gs.sources.transverse_surface_trough(
    tunnel, volume_loss=1 * u.percent, trough_width_parameter=0.5
)
water_main = gs.utilities.perpendicular_utility(
    tunnel,
    utility_id="Water main",
    station=50,
    start_offset=-25,
    end_offset=25,
    depth=1.5,
    elevation_reference="axis",
    diameter=0.3,
)
result = gs.movement_profile(water_main, trough, spacing=1.0)
print(result)

fig, axs = gs.plot.cross_section(result)
fig.savefig("home.png", dpi=100)
