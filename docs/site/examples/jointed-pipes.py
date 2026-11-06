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
main = gs.utilities.perpendicular_utility(
    tunnel,
    utility_id="Water main",
    station=0 * u.m,
    start_offset=-40 * u.m,
    end_offset=40 * u.m,
    depth=2.0 * u.m,
    elevation_reference="axis",
    diameter=300 * u.mm,
)
profile = gs.movement_profile(main, trough, spacing=1 * u.m)

# This example's own pipe lengths, for illustration: not a manufacturer's.
# Keyed by pipe type and outside diameter; a pair not in it is an error.
pipe_lengths = gs.Sourced(
    {("spun_grey_iron", 300 * u.mm): 4 * u.m},
    source="this example's own, for illustration",
)

joints = gs.presets.cast_iron_joint_limits(joint="lead_yarn_water_main")
strains = gs.presets.iron_strain_limits(material="grey_iron")
result = gs.check_jointed_pipe(
    profile,
    pipe_lengths=pipe_lengths,
    pipe_type="spun_grey_iron",
    interaction="greenfield",
    joint_rotation_limit=joints.rotation,
    joint_pullout_limit=joints.pullout,
    tensile_strain_limit=strains.tensile,
    compressive_strain_limit=strains.compressive,
    # Table 4 gives no bending limit, and none is invented.
    bending_strain_limit=None,
    radius_of_curvature_limit=None,
)
print(result)
print()

checks = result.checks.set_index("check")
for check, unit in (("joint_rotation", "degree"), ("joint_pullout", "mm")):
    row = checks.loc[check]
    value = u.Quantity(row["value"], row["unit"]).m_as(unit)
    print(
        f"{check}: {value:.3g} {unit} at {row['governing_distance']:.2f} m, "
        f"utilization {row['utilization']:.3f}"
    )
closure = result.values["joint_opening"].min()
print(f"largest closure: {closure * 1e3:.3g} mm, reported, not checked")
print()

fig, axs = gs.plot.profile(result)
fig.savefig("jointed-pipes.png", dpi=100)

# The pullout preset carries a caveat, which the result's assumptions repeat.
(caveat,) = [line for line in result.assumptions if "again conservatively" in line]
print(caveat)
