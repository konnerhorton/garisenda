# M1 (b): the station-and-offset builder, the movement profile along a utility and the result

## Intent

### Goal
A caller can build a utility line from station and offset against an idealized tunnel, evaluate a source along it, and get back one result in the shape every later analysis will share (SPEC §5.1): a table of greenfield movements and their exact derivatives keyed by distance along the utility, with the inputs, methods, assumptions, the validity verdict and the warnings, and views as a dict, a DataFrame and a text summary. This is the traditional spreadsheet's movement calculation, run through the one 3D analysis (SPEC §3, §11).

### Why
- SPEC §12.4: M1 (b) is the builder, the profile and the result; M1 (a)'s source has nothing to consume it yet. The figures move to (c) (decision 1).
- The profile is the boundary every assessment consumes (SPEC §3): M3's utility checks and M4's buildings read it, so its columns and sign conventions bind them.
- The result shape is shared by every analysis (SPEC §5.1), and `gs.sweep` (M1 (c)) needs a result with governing values and a verdict to tabulate.

### Constraints
- **SPEC §3:** the profile is stations at distances along the asset, with the displacement along it, across it (vertical and lateral) and their exact derivatives with respect to distance along it; built by evaluating the source at the stations, never from a grid or a spline.
- **SPEC §8.3:** the builder returns a straight polyline perpendicular to the tunnel at the station, named for what it builds, records how it was built, and the result carries "built perpendicular" as an assumption (SPEC §1.3). A utility's elevation reference (`"invert"`, `"axis"`, `"crown"`) is a required argument, converted to the axis with the diameter.
- **SPEC §8.2:** depth or elevation, never converted by assumption; elevations need the ground elevation.
- **SPEC §5:** values keyed by distance along the asset, with x, y, z and, for a built asset, station and offset as extra columns; the verdict is the worst over checks, inputs and locations; views never recalculate.
- **SPEC §6:** DataFrames carry units in `df.attrs["units"]`; no units in names.
- **SPEC §10:** a point that can't be computed is reported, never dropped.
- **SPEC §11:** golden values from M1 (a)'s hand calculation run through station-and-offset input; the builder tested on its own.
- **SPEC §12.1:** `pandas` added with hangtu's floor (`>=2.1.1,<3`).

### Out of scope
- **Utility checks** (strain against limits, pipe types and materials, discrete strain): M3. The result's `checks` part exists and is empty.
- **Several sources and superposition, the trough below the surface:** M2. Every station of a buried utility is flagged `outside` until then, which the result shows.
- **Ends of a built asset where the trough is still significant:** flagged in M3, whose spec sets the margin (SPEC §8.3).
- **Polylines with vertices** (curvature terms of a bent asset, SPEC §3): M5. A bent polyline raises here.
- **Buildings and their builder:** M4.
- **The cross-section and profile figures, `gs.sweep`, the docs site, M1's user docs:** M1 (c) (decision 1).

### SPEC sections touched
- **SPEC §12.4:** M1's row: the figures move from (b) to (c).
- **SPEC §8.3:** the builder returns a `Utility`, and the table form comes in M5 (decision 3).
- **SPEC §5.1:** the result shape becomes decided, with its exact form recorded in this unit's spec.
- **SPEC §3:** the profile's columns and sign conventions (decision 5); the source interface gains the critical points along a segment (decision 2).
- **SPEC §12.1, §12.2:** `pandas` added; the `garisenda.profile` module.

### Decisions (intent review, 2026-11-03)
1. **The figures move to (c)**, with `gs.sweep` and the docs site: figures are checked by eye and shown in the docs, so they belong together, and (b) stays one sitting.
2. **Stations always include each source's critical points; a required `spacing` adds stations between them**, and the user makes it finer as they need. A source supplies, for a straight segment, the distances along it where its quantities peak or change sign (for the surface trough, where the segment crosses the offsets 0, ±i and ±√3 i: the axis, the inflection points and the peaks of curvature and horizontal strain). Stations are the segment's ends, those points, and every `spacing` between, recorded on the result. So a peak is never missed between stations, whatever the spacing. This adds a method to the source interface (SPEC §3). Rejected: spacing alone with a `marginal` flag when it is coarse, which still misses peaks; and explicit stations only.
3. **The builder returns a thin frozen `Utility`**: its id, vertices as (x, y, depth), diameter, how it was built (reference tunnel, station, perpendicular) and its assumptions. The table form (SPEC §8.3) comes in M5, when polylines are loaded from tables and the columns are decided. Pipe type and material come with M3, where they are first used.
4. **`gs.movement_profile(utility, source, *, spacing)`**, the analysis of this unit. No `interaction` argument: the profile is the ground's movement, and soil–structure interaction (SPEC §4) applies to the asset's response, in M3. One source now; M2 widens it to several.
5. **Signs in the profile:** along is positive toward increasing distance; vertical is settlement, positive downward; lateral is positive to the right looking along increasing distance, as offset is (SPEC §8.1). For a built utility, distance runs from the start offset to the end offset.
