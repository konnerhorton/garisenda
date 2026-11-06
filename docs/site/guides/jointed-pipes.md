# Jointed pipes

A jointed pipe (cast iron, ductile iron, clay, concrete) is a chain of pipe lengths joined at sockets. The ground's bending and stretch go into its joints, which rotate and open, as well as into its barrel. `gs.check_jointed_pipe` checks both against the movement profile along it: joint rotation and joint pullout at the worst joint position, and the barrel's strains as [`gs.check_continuous_pipe`](continuous-pipes.md) computes them, with the pipe length as the discrete interval.

```python
--8<-- "jointed-pipes.py"
```

```text
--8<-- "jointed-pipes.txt"
```

![The check of a cast iron water main 2 m deep crossing the tunnel square, in 4 m lengths: the six barrel panels, then joint rotation and joint opening, each with its limit](../img/generated/jointed-pipes.png)

## What it checks

Every check runs and is reported. The barrel's six are the [continuous pipe's](continuous-pipes.md#what-it-checks). The two joint checks come first in the summary:

| check | value | limit | utilization |
|---|---|---|---|
| `joint_rotation` | the largest joint rotation | `joint_rotation_limit` | θ / limit |
| `joint_pullout` | the largest joint opening | `joint_pullout_limit` | Δ / limit |

A joint exists only at a spacing of one pipe length, so the joint checks have only a discrete value: `analytical` is NaN and `governed_by` is `"discrete"`.

In the example the joints are far inside Table 2's limits, and the barrel fails in tension: the ground's 311 µε of axial strain is three times the grey iron limit of 100 µε. Bracegirdle et al. (1996) reduce axial strain by a factor that this greenfield check doesn't apply (see [the strain preset's caveat](../reference/presets.md#garisenda.presets.iron_strain_limits)).

## The joints

The geometry is garisenda's own, derived in the [reference](../reference/garisenda.md#garisenda.check_jointed_pipe), not taken from a paper. The pipe is a chain of rigid lengths L, and each joint moves with the ground.

- **Rotation** is the angle between the two pipe lengths meeting at a joint: the second difference of the movement across the pipe at the joint and one pipe length either side, divided by L. It is reported in the vertical and lateral planes and as their resultant, which is checked, since a spigot rotates in its socket in any direction. An oblique pipe's joints rotate in the lateral plane too.
- **Opening** (pullout) is the difference in along-pipe movement between the midpoints of the two pipe lengths meeting at the joint. The openings along a run add up to the ground's stretch over it, so the joints take that stretch and no more. It is positive when the joint opens. A joint closes in the compression zone over the tunnel. Table 2 gives no limit for closure, so the largest closure is reported in `values` and marked on the figure, but not checked.
- **The outer opening**, Δ + rθ, is the largest opening anywhere around a joint that also rotates, with r half the outside diameter. It is reported, not checked: Table 2 limits rotation and pullout separately, and adding rθ to the pullout would count the rotation twice.

These are the same numbers as the barrel's discrete values at an interval of L: rotation is L times the discrete curvature, and opening is L times the discrete axial strain. A joint check and the barrel's discrete columns are one calculation, so they can't disagree.

### The worst joint

Where the joints are along the pipe isn't known, so every position is treated as a possible joint, and the worst one governs. The rotation and opening lines on the figure are what a joint would have if it were there. The check adds stations at their peaks, found from the field's derivatives, and at the ends of the range where a joint can be, so the reported worst joint is the true one whatever the profile's `spacing`. They are ticked in red with the barrel's.

### The ends

A joint's rotation needs a neighbor one pipe length either side, and its opening the midpoints half a length either side. So there's no rotation within L of an end and no opening within L/2. Those stations are NaN, a gap in the lines, under the same *within* flag as the barrel's discrete values. A pipe shorter than 2L has no position for a rotation, and one shorter than L none for an opening. That check is then reported as not determined: its value is NaN and `passes` is NA, never a pass.

## Pipe lengths

The pipe length is a table, keyed by pipe type and outside diameter:

```python
pipe_lengths = {
    ("spun_grey_iron", 300 * u.mm): 4 * u.m,
    ("spun_grey_iron", 450 * u.mm): 5.5 * u.m,
}
```

`pipe_type` picks the type, and the utility's outside diameter picks the row, matched to within 1 µm, so a table in mm or inches works with a utility in m. A type or diameter not in the table raises an error that lists what the table has. Nothing is taken from the nearest diameter, and a nominal size isn't matched to an outside diameter. Wrap the table in `gs.Sourced` to record where it came from. The result records the length used as the input `pipe_length`, with that source.

`pipe_type` is a judgment: which type an old main is, pit cast or spun, is often the engineer's call. garisenda has no preset for pipe lengths: no citable source for laying lengths has been found yet. The example's table is its own.

## Limits

All ten judgments are required keywords: `pipe_lengths`, `pipe_type`, `interaction` and the six limits. The joint rotation limit is an angle, a pint quantity only (`1.5 * u.degree`), and the pullout limit is a length. As for continuous pipes, `None` means no limit: the check is still computed and reported, with utilization NaN and `passes` NA. A limit of zero means nothing is allowed: any movement fails, with utilization ∞.

### Presets

[`gs.presets`](../reference/presets.md) has the published limits for iron pipes, each passed by name and recorded with its source:

- `cast_iron_joint_limits(joint=...)`: joint rotation and pullout, Table 2 of Bracegirdle et al. (1996), after Attewell et al. (1986), for lead-yarn and rubber-gasket joints in gas and water mains;
- `iron_strain_limits(material=...)`: the allowable increase in tensile and compressive strain for grey and ductile iron, Table 4;
- `grey_iron_tensile_strain_limit(diameter=..., situation=...)`: the tensile limits of Herbert & Leach (1990), as Bracegirdle et al. quote them.

Table 4 gives no bending limit, so the example passes `bending_strain_limit=None`. Passing the tensile limit instead adds nothing, since tensile strain is never less than the bending strain.

Each preset carries caveats, which the result adds to its `assumptions`. Read them. The one on pullout matters most: Bracegirdle et al. give individual joints as the primary method and the maximum horizontal ground movement as a conservative shortcut for pullout. garisenda computes individual joints, so its opening is smaller than that shortcut, about a third of it in the example. Whether Table 2's pullout limits were set with the shortcut in mind can't be checked, so judge how far to trust them. The example prints the caveat in full.

## What it assumes

The result's `assumptions` list them, with the barrel's:

- **Two idealizations, each conservative for its own quantity.** For the joints, the pipe lengths are rigid and the joints follow the ground, so the joints take all the ground's bending and stretch. For the barrel, the joints are rigid and the barrel follows the ground, so the barrel takes all of it (Bracegirdle et al. 1996, p. 663). Both are greenfield: no joint stiffness, slip or soil–structure interaction.
- **Every position is a possible joint**, and the worst governs. Given joint locations come with real alignments, in a later version.
- **Small angles:** rotation is a difference of slopes, not of their arctangents. At slopes of 10⁻³ the two differ by about one part in a million.
- **The opening is checked at the pipe's axis.** The outer opening and the closure are reported only.

## Why not Eq. 5

Bracegirdle et al. (1996) also give a conservative bound on joint rotation for one trough, θ = 2 tan⁻¹(S_max / (√(2π) i)), their Eq. 5. garisenda doesn't use it. Its derivation, in Attewell et al. (1986), hasn't been read, and it doesn't match the worst joint of the geometry for every pipe length: for pipe lengths between about 1.03 i and 2.35 i, the joint at the trough's center rotates more than Eq. 5 gives. Joints computed individually are what the paper gives as the primary method. See [`gs.check_jointed_pipe`](../reference/garisenda.md#garisenda.check_jointed_pipe).

## The figure

`gs.plot.profile` draws a jointed-pipe check in eight panels: the continuous check's six, with the discrete values at the pipe length, then joint rotation (vertical, lateral and resultant, in degrees) and joint opening (at the axis, and the outer opening dashed). Each has its limit as a gray line and its worst joint marked with its value and utilization, and the largest closure is marked as not checked. See [the profile figure](../figures/profile.md#a-jointed-pipe-check).

## Sweeps

A sweep of a function that returns a jointed check has the joint checks in its row, as for the barrel's: `joint_rotation`, `joint_rotation_distance`, `joint_rotation_utilization` and `joint_rotation_passes`, and the same for `joint_pullout`. See [Sweeps](sweep.md).
