# Continuous pipes

A continuous pipe (welded steel, HDPE, fused PVC, a pipe pulled in by HDD) has no joints to open or rotate: it bends and stretches with the ground. `gs.check_continuous_pipe` checks it against the movement profile along it, for axial strain, bending strain, combined tensile and compressive strain, and radius of curvature, each against a limit you give.

```python
--8<-- "continuous-pipes.py"
```

```text
--8<-- "continuous-pipes.txt"
```

![The check of a pipe 2 m deep crossing the tunnel square: settlement, horizontal movement, axial strain, curvature, bending strain and combined strain, each with its limits](../img/generated/continuous-pipes.png)

## What it checks

The check takes a movement profile (`gs.movement_profile`), not the utility and source: the profile is the boundary between the ground and the pipe, and its stations are where values are reported. Every check runs and is reported:

| check | value | limit | utilization |
|---|---|---|---|
| `axial_tension` | the largest positive axial strain | `tensile_strain_limit` | ε / limit |
| `axial_compression` | the most negative axial strain | `compressive_strain_limit` | \|ε\| / limit |
| `bending` | the largest bending strain at the outermost fiber | `bending_strain_limit` | ε / limit |
| `tensile_strain` | the largest axial plus bending strain | `tensile_strain_limit` | ε / limit |
| `compressive_strain` | the most negative axial minus bending strain | `compressive_strain_limit` | \|ε\| / limit |
| `radius_of_curvature` | the smallest radius | `radius_of_curvature_limit` | limit / R |

A check passes when its utilization is at most 1. `result.checks` has one row per check: its governing value, where it is, its utilization and whether it passes, and the analytical and discrete values behind it.

The strains are mechanics, derived in the [reference](../reference/garisenda.md#garisenda.check_continuous_pipe), with tension positive:

- **Axial strain** is the ground's strain along the pipe.
- **Bending strain** at the outermost fiber is r κ, with r half the outside diameter and κ the curvature. Curvature is reported in the vertical and lateral planes and as their resultant, √(κ_v² + κ_l²), and bending is checked on the resultant: for a circular section, that is where the largest fiber strain is.
- **Combined strain** adds them, and never counts axial strain as helping: tensile strain is max(axial, 0) + r|κ|, and compressive strain is min(axial, 0) − r|κ|. Compression doesn't reduce the tensile strain, nor tension the compressive one.
- **Radius of curvature** is 1/|κ| of the resultant, infinite where the pipe is straight.

## Analytical and discrete

Each value is computed two ways, and the worse governs:

- **Analytical**, from the field's exact derivatives at each station.
- **Discrete**, from movements sampled at the `interval` you give, as a spreadsheet would: axial strain is the change in length over a span of the interval centered on the station, and curvature the second difference of three points an interval apart, centered on it.

The interval is a judgment, with no default: a short one exaggerates small differences in movement, a long one smooths the peaks. The examples use 1 m. It is independent of the profile's `spacing`, which only sets where values are reported.

For a smooth trough the discrete value is an average of the analytical one over its span, so it is the smaller and the analytical value usually governs. `difference` (discrete − analytical) shows how much the interval smooths: at 1 m it is a fraction of a percent here; at 9 m, the trough's width parameter i, the discrete compressive strain is 12 % short. If your spreadsheet's values are well below the analytical ones, its interval is too coarse for the trough. At 9 m the dashed discrete lines part from the solid analytical ones:

![The same check at a 9 m interval, where the discrete values fall short of the analytical ones](../img/generated/continuous-pipes-coarse.png)

The check also adds stations at the peaks of the resultant curvature and the combined strains, found from the field's derivatives, so the reported peak is the true one whatever the spacing. They are ticked in red along the bottom of each panel.

### The ends

Discrete values need movements half an interval (axial strain) or a whole interval (curvature) either side of a station. Near the pipe's ends those samples would fall beyond it, so those stations have no discrete value: they are NaN, with a gap in the dashed line, and one *within* flag names them. The ground beyond the end isn't sampled, because garisenda can't know the pipe continues straight past where you ended it. If it does, extend the pipe. The analytical values still cover these stations.

## Limits

All six judgments are required keywords: `interval`, `interaction` and the four limits. Strain limits are pint quantities, never plain numbers, since 0.1 could be a fraction or a percentage: `u.Quantity(1000, "µε")` or `0.1 * u.percent`. The radius limit is a length.

- **A limit given as `None`** means no limit for that check: it is still computed and reported, with its utilization NaN and `passes` NA, and the assumptions say which check had none.
- **The bending limit is its own**, because some materials have one apart from the axial and combined limits. Where yours doesn't, pass the smaller of the other two, as the example does: `bending_strain_limit=min(tensile, compressive)`.
- **`interaction`** takes only `"greenfield"` in this version: the pipe follows the ground.

garisenda gives no limits for continuous pipes. The example's limits are its own, for illustration.

## What it assumes

The result's `assumptions` list them:

- **The pipe follows the ground**, with no reduction for its stiffness or for slip: its axial strain is the ground's strain along it and its curvature the ground's. Soil–structure interaction would reduce both; it isn't in this version.
- **The pipe is circular**, and strain is taken at its outermost fiber, from the outside diameter you gave the utility.
- **Displacements and slopes are small**, so strain is the derivative of the movement along the pipe and curvature the second derivative of the movement across it.

## A perpendicular pipe bounds an oblique one

For one transverse trough and a straight, level pipe, a pipe that crosses the tunnel square has the largest strains and the smallest radius of any crossing angle. At angle θ in plan, axial strain and vertical curvature are sin²θ of the square crossing's at the same offset, and the lateral curvature that an oblique pipe gains is on the same factor. Checked over every angle, for both width methods and over a range of pipe sizes and trough widths, the square crossing's peaks are never exceeded. The example's last lines show it: at 45°, every strain is half.

So with one tunnel, checking the pipe as if it crossed square is conservative. The argument doesn't cover:

- several tunnels, whose troughs superpose;
- a pipe that changes depth along its length;
- the longitudinal trough ahead of the tunnel face, which isn't in this version. Bracegirdle et al. (1996) note that bending strains in pipes running parallel to a tunnel tend to be less severe than in pipes crossing it.

In those cases, give the pipe's real alignment.

## The figure

`gs.plot.profile` draws a check in six panels: settlement, horizontal movement, axial strain, curvature, bending strain and combined strain. Analytical values are solid and discrete ones dashed in the same color. Limits are thin gray lines labeled with their value; the radius limit is drawn on the curvature panel as ±1/R, since a radius is infinite where the pipe is straight. Each check's governing value is marked with its value and utilization. See [the profile figure](../figures/profile.md).

## Sweeps

A sweep of a function that returns a check has each check's value, distance, utilization and pass/fail in its row, as `<check>`, `<check>_distance`, `<check>_utilization` and `<check>_passes`. See [Sweeps](sweep.md).
