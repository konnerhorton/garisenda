# Profile

The movement along a utility, against distance along it.

```python
--8<-- "profile.py"
```

![The profile along the gas main: settlement, horizontal movement, strain along and curvature](../img/generated/profile.png)

## Reading it

Four panels share distance along the utility, with the offset from the tunnel axis along the top for a utility built from station and offset:

1. **Settlement**, its axis pointing down, so the trough hangs as it does in the ground.
2. **Horizontal movement**: `along` the utility, positive toward increasing distance (to the right on the page), and `lateral`, positive to the right looking along it. For a utility square to the tunnel, all horizontal movement is along it, and lateral is zero.
3. **Strain along** the utility, tension positive.
4. **Curvature**: vertical, hogging positive and sagging negative, and lateral.

Each panel's sign convention is above it on the right. The figure draws the result's values and never recalculates them: lines join the stations, so a finer `spacing` gives a smoother line. The peaks are always stations, so the marked values are exact whatever the spacing.

## Marks

- **Governing values** (`result.governing()`): the largest settlement, tension, compression, hogging and sagging, each a point with its value.
- **Critical stations**: red ticks along the bottom of each panel, where the trough's quantities peak or change sign.
- **Flags**: stations that aren't *within* the method's range are shaded, pink for *outside* and amber for *marginal*, and each flag's reason is printed under the figure with its range of distance. A utility below the ground surface, for one, is shaded over its length. Nothing flagged is left unmarked.

## A continuous-pipe check

A result of `gs.check_continuous_pipe` is drawn in six panels: settlement and horizontal movement as above, then axial strain, curvature (vertical, lateral and resultant), bending strain at the outermost fiber (vertical, lateral and resultant), and combined tensile and compressive strain.

![A continuous-pipe check in six panels](../img/generated/continuous-pipes.png)

- **Analytical and discrete:** analytical values are solid lines, discrete ones dashed in the same color, with gaps near the ends, where a station has no discrete value.
- **Limits:** thin gray lines, labeled with their value: the tensile limit above zero and the compressive limit below it, the bending limit, and the radius limit as ±1/R on the curvature panel, since a radius is infinite where the pipe is straight. A check given no limit draws no line, and its panel says so.
- **Checks:** each check's governing value is marked with its value and utilization (`u`), the radius at its curvature. The largest settlement is marked as for a profile.

The example is on the [Continuous pipes](../guides/continuous-pipes.md) page.

## Options

`display_units=` changes the units of any kind of quantity: `length` (m), `displacement` (mm), `strain` (microstrain) and `curvature` (1/km). The example's second figure shows movement in inches:

![The same profile with movement in inches](../img/generated/profile-inches.png)

`axs=` draws into four axes you already have (six for a check), top to bottom, as `plt.subplots(4, 1, sharex=True)` returns them. The function returns `(fig, axs)`, so you can change anything matplotlib can before saving. See [`gs.plot.profile`](../reference/plot.md#garisenda.plot.profile).
