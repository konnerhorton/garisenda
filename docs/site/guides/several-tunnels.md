# Several tunnels

Twin bores, or a tunnel crossing another: each tunnel has its own trough, with its own volume loss and trough width parameter, and `gs.superpose` adds their movements. The sum is a source like any other, so `gs.movement_profile`, the figures and `gs.sweep` take it unchanged.

```python
--8<-- "several-tunnels.py"
```

```text
--8<-- "several-tunnels.txt"
```

![The cross-section through both bores](../img/generated/several-tunnels-cross-section.png)

![The profile along the water main over both troughs](../img/generated/several-tunnels-profile.png)

## The second tunnel

`tunnel.parallel(offset=..., diameter=..., axis_depth=...)` builds a tunnel parallel to `tunnel`, `offset` to its right (negative to the left), with the same azimuth and stationing, so a point has the same station from either. Its depth and diameter are required again, not copied: stacked and unequal bores are common, and copying them would be a silent default. Give the axis as `axis_depth`, or as `axis_elevation` with `ground_elevation`, as for any tunnel. `offset=0` stacks the bores.

A tunnel that isn't parallel, such as one crossing at an angle, is built with `gs.sources.IdealizedTunnel` as usual. Any idealized tunnels can be superposed.

## Superposing

`gs.superpose(north=..., south=...)` takes two or more sources by name, and returns a source whose movement, and each of its derivatives, is the sum of theirs. Superpositions nest: `gs.superpose(twins=gs.superpose(...), east=...)`.

The names carry through to the result:

- **Inputs** are recorded under their source's name: `north.volume_loss`, `south.volume_loss`, or `twins.north.volume_loss` when nested. The superposition adds the two constants its critical distances are found with.
- **Flags** keep the source they came from. Above, the water main is below the surface and the trough is a surface method, so both tunnels flag every station, and the summary and the figures say which flag is which.
- **The verdict** at each station is the worst of the sources'.

`gs.superpose` raises if the tunnels don't share a ground surface (two `ground_elevation`s that differ) or if their bores overlap. A point inside any tunnel's bore raises, naming the tunnel.

Two troughs closer than about twice their width merge into one peak between the axes; further apart, each peak moves off its axis, toward the other tunnel. So the profile doesn't use each trough's own peaks: it finds where the combined field peaks along the utility, from its exact derivatives, and puts a station there.

## What superposition assumes

Each tunnel's movement is calculated as if the others weren't there, and the movements add. **Interaction between tunnels isn't modeled**: the second bore through ground already disturbed by the first usually has a larger volume loss, and the trough over twin bores can be eccentric, shifted toward the second. garisenda doesn't adjust either. Set each tunnel's volume loss as your judgment of it, through its own trough's `volume_loss`; above, the south bore, driven second, is given 1.5 %. The result records the assumption.

## The figures

The cross-section draws each tunnel parallel to the utility's reference tunnel (the one it was built from) at its offset and depth, named and dimensioned, with its axis dash-dot on every panel. The solid curve is the combined trough, and each tunnel's own trough is dashed, so you can see what was added. A tunnel that isn't parallel isn't drawn in the section, where it would mislead; a note under the figure names it. Its trough is still drawn, since it is part of the movement across the section, and the plan figure, which comes with real alignments, will show it.

The profile figure is unchanged: it draws the result's values.

## Sweeping one tunnel's input

An input named for its source is varied by its record name, `"south.volume_loss"`, and passed to your function with its dots as underscores, `south_volume_loss`, since a Python argument can't hold a dot. The table's column keeps the record name. As in any sweep, every input that isn't varied must stay the same, so `north.volume_loss` stays fixed. See [Sweeps](sweep.md) and [`gs.superpose`](../reference/garisenda.md#garisenda.superpose).
