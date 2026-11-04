import garisenda as gs

u = gs.units

tunnel = gs.sources.IdealizedTunnel(
    reference_point=(0, 0) * u.m,
    azimuth=0 * u.degree,
    diameter=6.0 * u.m,
    axis_depth=20.0 * u.m,
)

gas_main = gs.utilities.perpendicular_utility(
    tunnel,
    utility_id="Gas main",
    station=80 * u.m,
    start_offset=-25 * u.m,
    end_offset=25 * u.m,
    depth=8.0 * u.m,
    elevation_reference="axis",
    diameter=0.3 * u.m,
)

# Mair et al. (1993)'s width for clay: no arguments, its coefficients are the
# method.
clay = gs.sources.transverse_trough(
    tunnel,
    volume_loss=1.0 * u.percent,
    trough_width=gs.sources.mair_trough_width(),
)
result = gs.movement_profile(gas_main, clay, spacing=1 * u.m)
print(result)
print()

fig, axs = gs.plot.cross_section(result)
fig.savefig("below-the-surface-cross-section.png", dpi=100)
fig, axs = gs.plot.profile(result)
fig.savefig("below-the-surface-profile.png", dpi=100)


# i = k (z0 - z) with your own k, your choice of width at depth.
def linear(trough_width_parameter):
    source = gs.sources.transverse_trough(
        tunnel,
        volume_loss=1.0 * u.percent,
        trough_width=gs.sources.linear_trough_width(
            trough_width_parameter=trough_width_parameter
        ),
    )
    return gs.movement_profile(gas_main, source, spacing=1 * u.m)


table = gs.sweep(linear, vary={"trough_width_parameter": [0.4, 0.5, 0.6]})
columns = ["trough_width_parameter", "largest_settlement"]
print(table[columns].to_string(index=False))
print()

# A sewer beside the bore, below its crown: flagged, not raised.
sewer = gs.utilities.perpendicular_utility(
    tunnel,
    utility_id="Sewer",
    station=80 * u.m,
    start_offset=5 * u.m,
    end_offset=25 * u.m,
    depth=18.5 * u.m,
    elevation_reference="axis",
    diameter=0.6 * u.m,
)
beside = gs.movement_profile(sewer, clay, spacing=1 * u.m)
for flag in beside.warnings:
    print(flag.reason)
fig, axs = gs.plot.cross_section(beside)
fig.savefig("below-the-surface-crown.png", dpi=100)
