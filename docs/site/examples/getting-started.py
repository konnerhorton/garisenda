# --8<-- [start:tunnel]
import garisenda as gs

u = gs.units

tunnel = gs.sources.IdealizedTunnel(
    reference_point=(0, 0) * u.m,
    azimuth=0 * u.degree,
    diameter=6.0 * u.m,
    axis_depth=20.0 * u.m,
)
# --8<-- [end:tunnel]

# --8<-- [start:trough]
trough = gs.sources.transverse_surface_trough(
    tunnel, volume_loss=1.0 * u.percent, trough_width_parameter=0.5
)
# --8<-- [end:trough]

# --8<-- [start:utility]
water_main = gs.utilities.perpendicular_utility(
    tunnel,
    utility_id="Water main",
    station=120 * u.m,
    start_offset=-25 * u.m,
    end_offset=30 * u.m,
    depth=0 * u.m,
    elevation_reference="axis",
    diameter=300 * u.mm,
)
# --8<-- [end:utility]

# --8<-- [start:profile]
result = gs.movement_profile(water_main, trough, spacing=1 * u.m)
print(result)
# --8<-- [end:profile]

# --8<-- [start:governing]
print(result.governing()[["name", "value", "unit", "distance"]].to_string())
# --8<-- [end:governing]

# --8<-- [start:figures]
fig, axs = gs.plot.cross_section(result)
fig.savefig("getting-started-cross-section.png", dpi=100)

fig, axs = gs.plot.profile(result)
fig.savefig("getting-started-profile.png", dpi=100)
# --8<-- [end:figures]


# --8<-- [start:sweep]
def crossing(volume_loss, trough_width_parameter):
    trough = gs.sources.transverse_surface_trough(
        tunnel,
        volume_loss=volume_loss,
        trough_width_parameter=trough_width_parameter,
    )
    return gs.movement_profile(water_main, trough, spacing=1 * u.m)


table = gs.sweep(
    crossing,
    vary={
        "volume_loss": [0.5, 1.0, 1.5] * u.percent,
        "trough_width_parameter": [0.4, 0.5],
    },
    mode="grid",
)
columns = [
    "volume_loss",
    "trough_width_parameter",
    "largest_settlement",
    "largest_tension",
    "largest_sagging",
    "validity",
]
print(table[columns].to_string(index=False))
# --8<-- [end:sweep]
