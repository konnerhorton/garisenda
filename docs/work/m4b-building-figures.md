# M4 (b): the building figures and the buildings guide

## Intent

### Goal
A caller who has run `gs.check_building` can draw the two figures of a building assessment from its result, and learn the check from a guide:

- **The profile along the wall** shows what the staged method does, not just its numbers:
  - the settlement at foundation level, the wall split into hogging and sagging zones, each zone's chord, and Δ marked where it occurs;
  - Stage 1's settlement and slope against their limits;
  - the horizontal strain, and each zone's average ε_h;
  - each zone's governing tensile strain against the damage categories, with the acceptable category's limit.
- **The cross-section at the wall's station** draws the wall as what it is, a wall of height H standing on its foundation level over the tunnels, in place of M4 (a)'s interim line.
- **A buildings guide** on the docs site walks through building a wall from station and offset, choosing each judgment (beam method, E/G, category limits, cut-off, Stage 1 limits, acceptable category), reading the zones table and the checks, the two figures, and a sweep.

This closes M4. With it, "the spreadsheet is replaced for buildings" (SPEC §12.4).

### Why
- **SPEC §9:** every assessment has a figure, and each milestone ships the figures for what it builds. M4 (a) shipped only interim drawings (M4 (a) spec, "Changes": `gs.plot.profile` draws the four ground panels, `gs.plot.cross_section` a line at foundation depth).
- **The method is a picture.** Burland & Wroth's method is read off a figure (Mair, Taylor & Burland 1996, Fig. 3: zones split at the inflection points, a chord per zone, Δ the largest departure from it). An engineer checks a building assessment by looking at where the zones fall and whether Δ is in the right place. Without that figure, a wrong zone split or cut-off is invisible in a table.
- **SPEC §12.3:** docs are written as we go. M4 (a) wrote the API reference only; the user docs were left to this unit (M4 (a) intent decision 8).

### Constraints
- **SPEC §9, the plot contract:** `gs.plot.profile(result, *, axs=None, display_units=None) -> (fig, axs)` and `gs.plot.cross_section(result, *, ax=None, display_units=None) -> (fig, ax)`, unchanged. A figure draws from the result and never recalculates its values: zones, chords, Δ, ε_h and the strains come from `result.values`, `result.zones` and `result.checks`. The cross-section may evaluate the source on a grid to draw the trough, as now.
- **SPEC §9, style:** analytical values solid, each limit a line, every axis label states its unit, flagged stations marked with each flag's reason under the figure. Styling through `garisenda.plot._style.style()`; panels found in tests by `gid` (CLAUDE.md).
- **SPEC §10:** a wall with no zone (wholly beyond the cut-off), a flat zone, and a check with no limit (`None`) each draw, with their reason, never silently empty.
- **SPEC §2.3:** no digitized chart ships. Category bands are drawn from the `DamageCategories` the caller passed, which the result records.
- **Sources (TODO #7):** the method comes from Mair, Taylor & Burland (1996), restating originals that haven't been read. The guide says so plainly, in published words (no internal references, CLAUDE.md), as the trough's guide does for its sources.
- **The repo is public:** the guide and figures use invented geometry.

### Out of scope
- **Burland (1995)'s interaction chart** (Δ/L against ε_h, by category, for a given L/H). Drawing it from Eqs. 7–10 rather than digitizing it would be allowed, but each zone has its own L/H, so it's a figure per zone; later, if users ask.
- **The plan figure:** M5, with footprints.
- **The deformed wall drawn exaggerated** on the cross-section. The cross-section is transverse to the tunnel and the wall lies in it, so it could; 🟡 see "To settle in the spec".
- **New calculations.** Anything a figure needs that the result doesn't carry is a 🟡 to settle in the spec (a column added to the result), not computed in the plot.
- **TODO #11** (whether limit lines set a panel's scale) stays as decided: the building panels follow the utility panels' rule.
- **Verifying the originals (TODO #7):** separate.

### SPEC sections touched
- **§9:** the building profile's panels and the cross-section's wall, in one sentence each, as M3 (a) and (b) added theirs.
- **§12.3:** none; the guide follows the existing docs rule.
- **§12.4:** M4 (b) and M4 done at close-out.
- **§5.1:** only if the spec finds the figure needs a column the result lacks.
- **`README.md`**'s status line (building checks no longer "come next"), **`CHANGELOG.md`**, and **`CLAUDE.md`**'s status sentence and "Next" (M5) at close-out.

### 🟡 To settle (intent review)
1. **One unit or two.** Proposed: one. The figures and the guide need each other (the guide's figures come from its example), and the guide is mostly prose around one example. M1 (c) made the same call.
2. **The profile's panels.** Proposed, top to bottom, all against distance along the wall:
   1. **Settlement** at foundation level, with zones shaded hogging and sagging, each zone's chord dashed, the cut-off points as vertical lines, and the settlement limit (Stage 1).
   2. **Deflection from the chord** (`deflection`, d = w − c), per zone, with Δ marked and labeled with Δ/L. Δ is usually a few mm on tens of mm of settlement, so it can't be read off the settlement panel; this panel is where it's checked.
   3. **Slope along the wall**, with the slope limit (Stage 1).
   4. **Horizontal strain** along the wall, with each zone's average ε_h as a level line across the zone.
   5. **Tensile strain per zone** (bending or diagonal, whichever governs, with ε_h), a level line per zone, on the category bands shaded and labeled from `category_limits`, with the acceptable category's limit as the limit line and the governing zone marked.

   Considered: the ground's four panels (M1's) with zones added. They show curvature and lateral movement, which the building check doesn't use, and miss Δ and the categories.
3. **The cross-section.** Proposed: the wall as an outline from foundation level up to H (part of it below the ground surface when the foundation is deep), with the zone ends and cut-off points marked along its base, beside the trough at foundation level as the profile draws it at a utility's depth.
4. **Display units.** No figure draws a slope yet (the ground panels show curvature), and Δ/L has no display unit either. Proposed: a new display kind, `slope`, defaulting to mm/m (readable, and 1/500 is 2 mm/m), with the limit's label also giving "1/n"; Δ/L only in labels, not on an axis.
5. **The guide's example.** Proposed: one wall straddling a single tunnel (hogging, sagging, hogging), checked with the presets; then twin tunnels for several zones; a short section on each judgment and what changes it (beam method, cut-off, foundation depth); the depth-limit flag; a sweep over volume loss with the governing category per run. Figures on the `profile` and `cross-section` figure pages gain a building example too.

### Evidence
- **The interim drawings** (M4 (a)): `src/garisenda/plot/_cross_section.py` draws the wall as a line at foundation depth with `gid="building"`; `gs.plot.profile` falls back to the four ground panels for `analysis == "building_check"`, since it isn't in `PANELS`.
- **What the result already carries** (M4 (a) spec, decision 11): `values` has `zone`, `chord` and `deflection` per row, with rows at the cut-off points and each zone's Δ; `zones` has each zone's mode, ends, Δ and its distance, Δ/L, ε_h, the beam strains, the tensile strain and what governs it, and the category; `checks` has `settlement`, `slope`, `zone_1…n` and `damage_category`. On a first look this is all the proposed panels need.
