# Cross-section

The section across the tunnel at a utility's station: the trough, the utility on it, and the tunnel and utility to scale.

```python
--8<-- "cross-section.py"
```

![The cross-section at the duct bank's station](../img/generated/cross-section.png)

## Reading it

Three panels share the offset from the tunnel axis, positive to the right looking toward increasing station:

1. **Settlement** at the ground surface, its axis pointing down.
2. **Horizontal movement** at the ground surface, perpendicular to the tunnel, **positive to the right**, as everywhere in garisenda. The ground moves toward the axis, so it is positive left of the axis and negative right of it.
3. **The section**, to scale: the ground surface, the tunnel's bore and axis, the utility as a band of its diameter at its axis depth, and the axis depth z₀ and cover C.

On the first two, the curve is the trough, drawn past the utility's ends to three trough widths either side of the axis; the points are the utility's stations, from the result's values. The dotted lines are the inflection points, at ±i.

The trough's curve isn't in the result, which holds the utility's stations only, so the figure evaluates the result's source across the section to draw it. That is for drawing only: the utility's own values are never recalculated.

## Flags

The duct bank above is below the ground surface, and the trough is a surface method, so every station is *outside*: the values are the surface's, and the trough at the duct's depth is narrower. Flagged stations are ringed, and each flag's reason is printed under the figure. Nothing flagged is left unmarked.

## When it applies

The cross-section needs a utility built from station and offset (`gs.utilities.perpendicular_utility`), which knows its tunnel and station. A utility given by its vertices has no section to draw at, so `cross_section` raises; it will be drawn in plan by the plan figure, which comes with real alignments.

## Options

`display_units=` takes `length` (m) and `displacement` (mm); `axs=` draws into three axes you already have, as `plt.subplots(3, 1, sharex=True)` returns them. See [`gs.plot.cross_section`](../reference/plot.md#garisenda.plot.cross_section).
