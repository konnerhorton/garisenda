# Getting started

One crossing from start to finish: a tunnel, its settlement trough, a water main crossing it, the movement along the water main, the two figures, and a sweep over the trough's inputs. The geometry is invented.

```python
--8<-- "getting-started.py:tunnel"
```

An `IdealizedTunnel` is the tunnel of a traditional assessment: straight, with no ends, its axis at a depth below a flat ground surface. Give every quantity with its unit from `gs.units`; a plain number is read in SI where that's unambiguous, and refused where it isn't (an angle could be degrees or radians).

## The trough

```python
--8<-- "getting-started.py:trough"
```

The transverse surface trough is Gaussian: with i = k z₀ the trough width, A the tunnel's area and V_L the volume loss,

\[
S_{max} = \frac{V_L A}{\sqrt{2\pi}\, i}, \qquad S(o) = S_{max} \exp\left(-\frac{o^2}{2 i^2}\right)
\]

where o is the offset from the tunnel axis. Horizontal movement is toward the axis, (o / z₀) S(o). The equations are on [`transverse_surface_trough`](reference/sources.md#garisenda.sources.transverse_surface_trough).

The volume loss and k are **design judgments**, so they have no defaults: leave one out and garisenda says what it depends on and how to set it. A volume loss must be a quantity (`1.0 * u.percent`), because 0.5 could mean 0.5 % or 50 %.

!!! warning "The trough's sources aren't verified yet"
    The method is cited to Peck (1969) for the Gaussian form and to O'Reilly & New (1982) for the trough width, the volume relation and horizontal movement, but the citations haven't yet been checked against the sources themselves. Until they are, no validity range is checked for k, volume loss or cover, and the result says so in its assumptions. Treat results as trials of the library, not as design values.

## The utility

```python
--8<-- "getting-started.py:utility"
```

`perpendicular_utility` builds the spreadsheet's input, a utility crossing square to the tunnel at a station, from one offset to another, as a line in 3D. Distance along the utility runs from the start offset to the end offset. The `elevation_reference` says which point of the pipe the depth is at (its invert, axis or crown), and has no default: survey data comes in all three, and a wrong guess moves the pipe by its diameter. See [Conventions](conventions.md) for station, offset, depth and signs.

## The movement along it

```python
--8<-- "getting-started.py:profile"
```

```text
--8<-- "getting-started.txt"
```

`movement_profile` evaluates the trough at stations along the water main: its ends, every `spacing` between them, and the trough's critical points, where settlement, strain or curvature peak or change sign, so no peak is missed whatever the spacing. The spacing is a judgment too. The text above is the result's summary, its `repr()`; the full table is `result.values` (or `result.to_frame()`), with units in `result.values.attrs["units"]`.

Every result has the same parts:

- `values`: one row per station, keyed by `distance` along the utility, with the movement (`along`, `vertical`, `lateral`), the strain along it, slopes and curvatures, and each station's verdict;
- `governing()`: the extremes, the largest settlement, tension, compression, hogging and sagging, with where they occur;
- `validity` and `warnings`: whether every station is within the method's range, and what's flagged where;
- `inputs`, `method` and `assumptions`: every input as used with its source, the equations and their sources, and what the method assumes and garisenda can't check.

```python
--8<-- "getting-started.py:governing"
```

### What the assumptions mean

Each result lists its assumptions in `result.assumptions`. For this one:

- **Steady state:** the trough is the final one, long after the face has passed. The movements while the face approaches aren't considered.
- **Transverse trough only:** the trough across the tunnel is used; the longitudinal trough ahead of the face isn't.
- **Gaussian trough:** settlement follows the normal curve above.
- **Ground moves toward the tunnel axis,** which sets horizontal movement from settlement.
- **The surface trough is applied at each point's plan position, whatever its depth.** Below the surface the trough is narrower, so a buried utility's settlement and curvature are underestimated. Every station below the surface is flagged *outside*, and the figures mark it. [Below the surface](guides/below-the-surface.md) gives the trough at depth.
- **No validity range is checked** for k, volume loss or cover, because the sources are unverified (above).
- **Idealized straight tunnel:** no ends, shafts, curves or junctions.
- **Perpendicular:** a utility built from station and offset crosses square to the tunnel, whatever its real angle.
- **Greenfield:** the utility follows the ground. Its stiffness and its interaction with the soil are ignored, which is usually conservative for a flexible pipe. Whether the pipe can take the movement is a separate check: `gs.check_continuous_pipe` or `gs.check_jointed_pipe` (see [Continuous pipes](guides/continuous-pipes.md) and [Jointed pipes](guides/jointed-pipes.md)).

## The figures

```python
--8<-- "getting-started.py:figures"
```

![The cross-section at the water main's station](img/generated/getting-started-cross-section.png)

The [cross-section](figures/cross-section.md) shows the trough across the tunnel at the water main's station, with the water main's stations on it, and the tunnel and water main to scale.

![The profile along the water main](img/generated/getting-started-profile.png)

The [profile](figures/profile.md) shows the movement, strain and curvature along the water main, with the governing values marked.

## A sweep

Volume loss and k are judgments, so the next question is how much the answer depends on them. `gs.sweep` runs a function you write over values of one to three inputs and tabulates the governing values, one row per run:

```python
--8<-- "getting-started.py:sweep"
```

Settlement and strain are in m and dimensionless (the table's units are in `table.attrs["units"]`). The [sweep guide](guides/sweep.md) covers the rest.
