import garisenda as gs

u = gs.units

tunnel = gs.sources.IdealizedTunnel(
    reference_point=(1000, 2000) * u.m,
    azimuth=30 * u.degree,
    diameter=6.0 * u.m,
    axis_depth=20.0 * u.m,
    reference_station=500 * u.m,
)
sewer = gs.utilities.perpendicular_utility(
    tunnel,
    utility_id="Sewer",
    station=620 * u.m,
    start_offset=-15 * u.m,
    end_offset=15 * u.m,
    elevation=96.4 * u.m,
    ground_elevation=100.0 * u.m,
    elevation_reference="invert",
    diameter=0.6 * u.m,
)
print("vertices (x, y, depth of the axis), m:")
print(sewer.vertices.round(3))

station, offset = tunnel.station_offset(x=sewer.vertices[:, 0], y=sewer.vertices[:, 1])
print("station, m:", station.round(3))
print("offset, m:", offset.round(3))
