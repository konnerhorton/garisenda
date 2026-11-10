# Buildings

A building near a tunnel is assessed by its walls. `gs.check_building` takes the movement profile along one wall and runs the staged method of Mair, Taylor & Burland (1996): a preliminary check of settlement and slope (Stage 1), then the wall as a beam, zone by zone, for its tensile strain and damage category (Stage 2). Each wall is checked on its own. The method's originals aren't verified yet, so results are for trying the library, not for design: see [Sources](#sources).

```python
--8<-- "buildings.py"
```

```text
--8<-- "buildings.txt"
```

## A wall over one tunnel

`gs.buildings.perpendicular_building` places a wall square to the tunnel from a station and two offsets, as a utility is placed. It needs the wall's `height` H, from its foundation level to its eaves, and its `foundation_depth`. The wall follows the ground at its foundation level, so the profile is taken there: `gs.movement_profile(wall, source, spacing=...)`, as for a utility. With `gs.sources.transverse_trough`, the trough at foundation level is narrower and deeper than at the surface (see [Below the surface](below-the-surface.md)).

`gs.check_building(profile, ...)` then takes eight judgments, all required, none with a default. The example passes each from a preset: the Burland & Wroth beam, E/G for masonry, the damage categories, a cut-off at 2.5 i, the preliminary limits, acceptable category 2 and a greenfield wall.

### The zones

The method splits the wall where its settlement curve changes from hogging (convex up, at the trough's edges) to sagging (concave up, over the tunnel): at the inflection points, where the curvature is zero. garisenda finds them from the trough's exact derivatives, not from the stations, so they are exact whatever the spacing. Each zone is assessed as a simple beam of its own length L:

- **the chord** joins the settlement at the zone's two ends;
- **the deflection Δ** is the largest departure of the settlement from the chord, and the **deflection ratio** Δ/L the quantity the beam is bent by;
- **the horizontal strain** ε_h is the zone's average ground strain along the wall, the change in along-wall movement over the zone divided by L, tension positive.

`result.zones` has one row per zone. In the example, the wall over one tunnel has three: hogging, sagging over the tunnel, hogging. The two hogging zones are in tension (ε_h = 327 µε), the sagging zone in compression (−600 µε).

### The strains

The wall is a beam of height H and unit width. Hogging bends it about its bottom (t = H, I = H³/3), sagging about its middle (t = H/2, I = H³/12). Given Δ/L, the beam gives the bending strain ε_b at its extreme fiber and the diagonal (shear) strain ε_d, Eqs. 7 and 8 of Mair, Taylor & Burland. Each is combined with ε_h:

- **ε_bt = ε_h + ε_b**, the total bending strain (Eq. 9);
- **ε_dt = 0.35 ε_h + √((0.65 ε_h)² + ε_d²)**, the total diagonal strain, with Poisson's ratio 0.3 (Eq. 10).

The zone's tensile strain is the larger of the two, and `governed_by` says which. Its damage category is the band of `category_limits` it falls in. In the example, the hogging zones govern, in bending, at 475 µε, category 0 (negligible): tension from the ground adds to the bending. In the sagging zone, the compression of −600 µε cancels the bending strain, and the diagonal strain governs at 222 µε.

### The checks

`result.checks` has, in order: `settlement` and `slope` (Stage 1), a `zone_<n>` check per zone, and `damage_category`, the governing zone's. Each zone's check is its tensile strain against the upper limit of the acceptable category, 0.15 % for category 2. A zone's strain is a beam's over the whole zone, not at a point, so its `governing_distance` is NaN. Δ's distance is in `zones`.

In the example the wall fails Stage 1 (18.3 mm of settlement, against 10 mm) and passes Stage 2, at a utilization of 0.32. That is how the staged method is used: Stage 1 screens, and a wall that fails it is assessed in Stage 2.

## The figures

`gs.plot.profile` draws a building check in five panels against distance along the wall:

![The check of a wall 60 m long over one tunnel: settlement with the chords and the deflection filled, the deflection from the chord with each zone's Δ, the slope with its limit, the horizontal strain with each zone's average, and the tensile strain by zone on the damage categories' bands](../img/generated/buildings-profile.png)

1. **Settlement** at foundation level, with each zone's chord dashed and the deflection between them filled, red for hogging and purple for sagging, and the settlement limit. This is where to check the zones: each should end where the curve changes from convex to concave.
2. **Deflection from the chord**, d = w − c, its axis pointing down as the settlement's, with each zone's Δ marked where it occurs and Δ/L written as 1/n. Δ is a few millimeters on tens of millimeters of settlement, so it can't be read off the first panel.
3. **Slope** in mm/m, with the slope limit as ±2 mm/m (1/500): the check is on the slope's size, either way.
4. **Horizontal strain**, with each zone's average ε_h as a level line across it.
5. **Tensile strain by zone:** each zone's ε_bt and ε_dt as level lines, the one that governs thick, on the damage categories' bands. The acceptable category's limit is the gray line, and the governing zone is marked with its category and utilization.

The thin vertical lines are the zone ends. The hatched ends of the wall are beyond the cut-off, not assessed, with a dotted line where the cut-off falls. `display_units={"slope": "percent"}` draws the slope in percent. See [the profile figure](../figures/profile.md#a-building-check).

`gs.plot.cross_section` draws the wall to scale on the section, from its foundation level up to H, with its zone ends ticked on its base and the cut-off dotted; the trough panels show the movement at foundation level:

![The cross-section at the wall's station: the trough at foundation level, and the wall 9 m high over the tunnel, with its three zones](../img/generated/buildings-cross-section.png)

## The judgments

Each judgment changes the answer, and none has a default. The example prints what each does to the wall above.

- **The beam** (`beam_method`): `gs.buildings.burland_wroth_beam()` gives Eqs. 7 and 8 as Mair, Taylor & Burland write them, which imply a shear-deflection coefficient of 3/2. `gs.buildings.timoshenko_beam()` takes Timoshenko's 6/5 for a rectangle, and gives larger strains at the same Δ/L. Here it moves the wall from category 0 to 1 (506 µε against 475).
- **E/G** (`youngs_to_shear_modulus_ratio`): how stiff the wall is in shear against bending. `gs.presets.youngs_to_shear_modulus_ratio(structure="masonry")` is 2.6, `"framed"` 12.5 for a reinforced concrete frame on shallow foundations. A framed wall is soft in shear, so diagonal strain governs: 369 µε here.
- **The damage categories** (`category_limits`) and **the acceptable category** (`acceptable_category`): `gs.presets.damage_categories()` is Table 2 of Mair, Taylor & Burland, after Boscardin & Cording (1989). Practice often accepts category 2 (slight). `None` reports the categories with no pass or fail. A table of your own is a `gs.buildings.DamageCategories`.
- **The cut-off** (`cutoff`): how much of the wall is assessed. `gs.buildings.no_cutoff()` assesses the whole wall. `gs.buildings.trough_width_cutoff(multiple=...)` assesses only the part within that many trough widths i of a trough's axis in plan, with i at foundation level. Practice varies, and garisenda chooses no multiple. Cutting can lower the strains as well as raise them: a zone cut short has a shorter L and a different chord. Here, with no cut-off, the hogging zones run to the wall's ends and give 497 µε, more than the 475 µε with the cut-off. Stage 1 covers the whole wall either way.
- **The Stage 1 limits** (`settlement_limit`, `slope_limit`): `gs.presets.preliminary_assessment_limits()` gives 10 mm and 1/500 (2 mm/m). They were set against the ground surface; garisenda checks them at foundation level, which is more onerous for a foundation below it. A slope must be a quantity (`2 * u("mm/m")`, `0.2 * u.percent`), since 1/500, 0.2 % and 2 mm/m are all in use. `None` reports a value with no limit.
- **The foundation depth**, the wall's own: the trough at depth is narrower, so the same wall at the surface bends less (414 µε here).

Each preset carries caveats, which the result adds to its `assumptions`; read them in [the presets' reference](../reference/presets.md). `interaction` takes only `"greenfield"`: the wall follows the ground with no stiffness of its own, which is usually conservative.

## Twin tunnels

Over two tunnels, the settlement has a sagging zone over each, and the wall has more zones. The example's tunnels are 25 m apart, so each trough keeps its own sagging zone; closer, the two troughs merge into one, with three zones. The cut-off keeps the ground between two tunnels: the assessed range runs from the first point within m i of any trough's axis to the last.

![A wall 85 m long over twin tunnels 25 m apart: five zones, hogging, sagging, hogging, sagging, hogging](../img/generated/buildings-twins.png)

The middle hogging zone, between the tunnels, governs at 582 µε, category 1: it is bent by both troughs.

## The depth limit

The staged method states no range of validity of its own. The one limit found is Harris & Franzius (2006), as Jones (2022) reports it: the staged method on the surface trough applies to foundations above 0.2 of the tunnel's axis depth (z_f/z0 < 0.2), and two or more basement levels or piled foundations are to be assessed separately. garisenda takes the trough at foundation level, but deep basements and piles still change what following the ground means, so a foundation at or below 0.2 z0 is flagged *outside*, over the whole wall, with that reason. The example's 5 m basement over a 20 m deep tunnel is at 0.25. Otherwise a *within* flag says the method has no stated range.

A wall wholly beyond the cut-off has no zone. It is flagged *within* with the reason, Stage 1 still covers it, and `damage_category` isn't determined: its value is NaN and `passes` NA, never a pass.

## Sweeps

A sweep of a function that returns a building check has each check in its row, as for a pipe, and `damage_category_category`, the governing category, for each run. In the example, the wall reaches category 1 at a volume loss of 2 % and category 2 at 3 %. See [Sweeps](sweep.md).

## Sources

The method is Mair, Taylor & Burland (1996), *Prediction of ground movements and assessment of risk of building damage due to bored tunnelling*, §§4–5, Tables 1–2 and Eqs. 7–10. They restate Burland & Wroth (1974), Burland et al. (1977) and Boscardin & Cording (1989), whose originals haven't been read. The beam with any shear coefficient, Timoshenko's among them, and Eq. 10's general form are garisenda's own derivation, checked against Jones (2022), *Soft Ground Tunnel Design*. The depth limit is Harris & Franzius (2006), as Jones (2022) reports it, also unread. So, as for the trough, results are for trying the library, not for design. See [`gs.check_building`](../reference/garisenda.md#garisenda.check_building) for the equations, each with its source.
