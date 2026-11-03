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
duct = gs.utilities.perpendicular_utility(
    tunnel,
    utility_id="Duct bank",
    station=200 * u.m,
    start_offset=-8 * u.m,
    end_offset=24 * u.m,
    depth=1.2 * u.m,
    elevation_reference="crown",
    diameter=0.9 * u.m,
)
result = gs.movement_profile(duct, trough, spacing=2 * u.m)

fig, axs = gs.plot.cross_section(result)
fig.savefig("cross-section.png", dpi=100)
