import garisenda as gs

u = gs.units

tunnel = gs.sources.IdealizedTunnel(
    reference_point=(0, 0) * u.m,
    azimuth=0 * u.degree,
    diameter=6.0 * u.m,
    axis_depth=20.0 * u.m,
)


def crossing(volume_loss, depth):
    trough = gs.sources.transverse_surface_trough(
        tunnel, volume_loss=volume_loss, trough_width_parameter=0.5
    )
    sewer = gs.utilities.perpendicular_utility(
        tunnel,
        utility_id="Sewer",
        station=60 * u.m,
        start_offset=-20 * u.m,
        end_offset=20 * u.m,
        depth=depth,
        elevation_reference="axis",
        diameter=0.6 * u.m,
    )
    return gs.movement_profile(sewer, trough, spacing=1 * u.m)


table = gs.sweep(
    crossing,
    vary={
        "volume_loss": [0.5, 1.0, 1.5] * u.percent,
        "depth": [0, 2, 20] * u.m,
    },
    mode="grid",
)
columns = ["run", "volume_loss", "depth", "largest_settlement", "validity", "warnings"]
print(table[columns].to_string(index=False))
print()
print("run 2:", table.loc[2, "error"])
print()
units = table.attrs["units"]
print("units:", {name: units[name] for name in columns[1:4]})
print("fixed:", [entry["name"] for entry in table.attrs["fixed_inputs"]])
