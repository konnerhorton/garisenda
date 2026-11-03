# Conventions

```python
--8<-- "conventions.py"
```

```text
--8<-- "conventions.txt"
```

## Plan

Every input in a site uses **one flat coordinate system and one length unit**: x and y in plan, with no datum or projection recorded.

A tunnel's **plan direction** is an azimuth, clockwise from the +y axis, so it is a bearing when +y is north. An azimuth must be a quantity (`30 * u.degree`), because 30 could be degrees or radians.

**Station** is distance along a tunnel in plan, from its reference point, where it is `reference_station` (0 unless given, so spreadsheet stations can be used as they are). **Offset** is horizontal and perpendicular to the tunnel, **positive to the right looking toward increasing station**. Above, the tunnel heads 30° east of north, so the sewer's start, at offset -15 m, is to the north-west of the axis.

## Depth and elevation

**Depth is positive downward** from the ground surface. In Phase 1 the ground surface is flat: give depths, or elevations with the ground elevation, in the site's one length unit.

A utility's level is at its invert, axis or crown, and the builder's `elevation_reference` says which; it has no default. garisenda works with the axis: the axis is D/2 above an invert and D/2 below a crown. Above, the sewer's invert is at elevation 96.4 m under ground at 100.0 m, so its axis is at depth 3.6 - 0.3 = 3.3 m.

## Signs

| Quantity | Positive |
|---|---|
| Settlement (`vertical`) | downward |
| Horizontal movement across a tunnel | to the right, toward increasing offset |
| `along` | toward increasing distance along the utility |
| `lateral` | to the right, looking along the utility |
| Strain (`along_strain`) | tension |
| Curvature (`vertical_curvature`) | hogging; sagging is negative |

Settlement positive downward makes a trough's curvature negative (sagging) over the tunnel and positive (hogging) toward its edges.

Distance along a utility runs from its first vertex, which for a built utility is its start offset. Reversing a utility changes the sign of `along`, the slopes and `along_strain_gradient`, but not of settlement, strain or curvature.

## Units

Results are in SI: lengths and movements in m, strains dimensionless, curvatures in 1/m, with each column's unit in `result.values.attrs["units"]`. Figures show movements in mm, strains in microstrain and curvatures in 1/km, unless `display_units=` says otherwise; every axis label gives its unit.
