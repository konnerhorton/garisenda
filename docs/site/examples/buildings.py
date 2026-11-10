import garisenda as gs

u = gs.units

tunnel = gs.sources.IdealizedTunnel(
    reference_point=(0, 0) * u.m,
    azimuth=0 * u.degree,
    diameter=6.0 * u.m,
    axis_depth=20.0 * u.m,
)


def trough(volume_loss=1.5 * u.percent):
    return gs.sources.transverse_trough(
        tunnel,
        volume_loss=volume_loss,
        trough_width=gs.sources.linear_trough_width(trough_width_parameter=0.5),
    )


def wall(foundation_depth=1.5 * u.m):
    # A wall square to the tunnel, from 30 m left of its axis to 30 m right.
    return gs.buildings.perpendicular_building(
        tunnel,
        building_id="Wall A",
        station=50 * u.m,
        start_offset=-30 * u.m,
        end_offset=30 * u.m,
        height=9 * u.m,
        foundation_depth=foundation_depth,
    )


limits = gs.presets.preliminary_assessment_limits()
# Every judgment is passed by name; none has a default.
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


def check(building, source, **changes):
    profile = gs.movement_profile(building, source, spacing=1 * u.m)
    return gs.check_building(profile, **(judgments | changes))


# 1. A wall over one tunnel
result = check(wall(), trough())
print(result)
print()
print(
    result.zones[
        [
            "zone",
            "mode",
            "start",
            "end",
            "deflection",
            "deflection_ratio",
            "horizontal_strain",
            "total_bending_strain",
            "total_diagonal_strain",
            "governed_by",
            "label",
        ]
    ].to_string(index=False, float_format="{:.3g}".format)
)
print()
print(
    result.checks[
        ["check", "value", "unit", "limit", "utilization", "passes", "zone"]
    ].to_string(index=False, float_format="{:.3g}".format)
)
print()

# 2. The figures
fig, axs = gs.plot.profile(result)
fig.savefig("buildings-profile.png", dpi=100)
fig, axs = gs.plot.cross_section(result)
fig.savefig("buildings-cross-section.png", dpi=100)


# 3. The judgments, and what each does to this wall
def governing(found):
    row = found.checks.set_index("check").loc["damage_category"]
    zone = found.zones.set_index("zone").loc[row["zone"]]
    return (
        f"{row['value'] * 1e6:.0f} µε in zone {row['zone']} ({zone['mode']}, "
        f"{zone['governed_by']}), category {zone['label']}"
    )


print("as above:          ", governing(result))
for name, changes in {
    "Timoshenko beam:   ": {"beam_method": gs.buildings.timoshenko_beam()},
    "framed, E/G 12.5:  ": {
        "youngs_to_shear_modulus_ratio": gs.presets.youngs_to_shear_modulus_ratio(
            structure="framed"
        )
    },
    "no cut-off:        ": {"cutoff": gs.buildings.no_cutoff()},
}.items():
    print(name, governing(check(wall(), trough(), **changes)))
print(
    "at the surface:    ",
    governing(check(wall(foundation_depth=0 * u.m), trough())),
)
print()

# 4. Twin tunnels, 25 m apart: each trough has its own sagging zone
south = tunnel.parallel(offset=25 * u.m, diameter=6.0 * u.m, axis_depth=20.0 * u.m)
twins = gs.superpose(
    north=trough(),
    south=gs.sources.transverse_trough(
        south,
        volume_loss=1.5 * u.percent,
        trough_width=gs.sources.linear_trough_width(trough_width_parameter=0.5),
    ),
)
long_wall = gs.buildings.perpendicular_building(
    tunnel,
    building_id="Wall B",
    station=50 * u.m,
    start_offset=-30 * u.m,
    end_offset=55 * u.m,
    height=9 * u.m,
    foundation_depth=1.5 * u.m,
)
over_twins = check(long_wall, twins)
print(
    over_twins.zones[
        ["zone", "mode", "start", "end", "tensile_strain", "label"]
    ].to_string(index=False, float_format="{:.3g}".format)
)
print("governing:", governing(over_twins))
print()
fig, axs = gs.plot.profile(over_twins)
fig.savefig("buildings-twins.png", dpi=100)

# 5. A deep foundation: outside the one range found for the method
basement = check(wall(foundation_depth=5 * u.m), trough())
print("validity:", basement.validity)
for flag in basement.warnings:
    if flag.verdict == "outside":
        print(flag.reason)
print()


# 6. A sweep over volume loss
def building_at(volume_loss):
    return check(wall(), trough(volume_loss))


table = gs.sweep(building_at, vary={"volume_loss": [0.5, 1, 1.5, 2, 3] * u.percent})
print(
    table[
        [
            "volume_loss",
            "settlement",
            "settlement_passes",
            "damage_category",
            "damage_category_category",
            "damage_category_passes",
        ]
    ].to_string(index=False, float_format="{:.3g}".format)
)
