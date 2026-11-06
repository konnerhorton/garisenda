import math

import garisenda as gs

u = gs.units

tunnel = gs.sources.IdealizedTunnel(
    reference_point=(0, 0) * u.m,
    azimuth=0 * u.degree,
    diameter=6.0 * u.m,
    axis_depth=20.0 * u.m,
)
trough = gs.sources.transverse_trough(
    tunnel,
    volume_loss=1.0 * u.percent,
    trough_width=gs.sources.linear_trough_width(trough_width_parameter=0.5),
)
pipe = gs.utilities.perpendicular_utility(
    tunnel,
    utility_id="Pipe",
    station=0 * u.m,
    start_offset=-40 * u.m,
    end_offset=40 * u.m,
    depth=2.0 * u.m,
    elevation_reference="axis",
    diameter=300 * u.mm,
)
profile = gs.movement_profile(pipe, trough, spacing=1 * u.m)

# This example's own limits, for illustration: not a material's.
tensile = u.Quantity(500, "µε")
compressive = u.Quantity(1000, "µε")
result = gs.check_continuous_pipe(
    profile,
    interval=1 * u.m,
    interaction="greenfield",
    tensile_strain_limit=tensile,
    compressive_strain_limit=compressive,
    # No separate bending limit for this pipe: the smaller of the two.
    bending_strain_limit=min(tensile, compressive),
    radius_of_curvature_limit=2000 * u.m,
)
print(result)
print()

columns = ["check", "value", "utilization", "passes", "governed_by", "difference"]
print(result.checks[columns].to_string(index=False, float_format="{:.4g}".format))
print()

fig, axs = gs.plot.profile(result)
fig.savefig("continuous-pipes.png", dpi=100)

# An interval as long as the trough's width parameter, i = 9 m, is too coarse:
# the discrete compressive strain falls well short of the analytical one.
coarse = gs.check_continuous_pipe(
    profile,
    interval=9 * u.m,
    interaction="greenfield",
    tensile_strain_limit=tensile,
    compressive_strain_limit=compressive,
    bending_strain_limit=min(tensile, compressive),
    radius_of_curvature_limit=2000 * u.m,
)
row = coarse.checks.set_index("check").loc["compressive_strain"]
print(
    f"At a 9 m interval: compressive strain {row['analytical'] * 1e6:.1f} µε "
    f"analytical, {row['discrete'] * 1e6:.1f} µε discrete, difference "
    f"{row['difference'] * 1e6:+.1f} µε; {row['governed_by']} governs."
)
print()


# The same pipe, crossing the tunnel at 45 degrees in plan, level at 2 m.
def crossing_at(angle):
    s, c = math.sin(math.radians(angle)), math.cos(math.radians(angle))
    oblique = gs.utilities.Utility(
        utility_id=f"Pipe at {angle} degrees",
        vertices=[(-40 * s, -40 * c, 2.0), (40 * s, 40 * c, 2.0)] * u.m,
        diameter=300 * u.mm,
    )
    return gs.check_continuous_pipe(
        gs.movement_profile(oblique, trough, spacing=1 * u.m),
        interval=1 * u.m,
        interaction="greenfield",
        tensile_strain_limit=tensile,
        compressive_strain_limit=compressive,
        bending_strain_limit=min(tensile, compressive),
        radius_of_curvature_limit=2000 * u.m,
    )


for angle in (90, 45):
    checks = crossing_at(angle).checks.set_index("check")["value"]
    print(
        f"{angle} degrees: tensile {checks['tensile_strain'] * 1e6:.1f} µε, "
        f"compressive {checks['compressive_strain'] * 1e6:.1f} µε, "
        f"smallest radius {checks['radius_of_curvature']:.0f} m"
    )
