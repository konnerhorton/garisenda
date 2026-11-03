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

## Spec

No topic doc holds this, so the spec is here. Everything marked 🟡 is a proposal for this review.

### Changes
- **SPEC §3:** the source interface gains `critical_distances()` (decision 4); the profile's columns and signs (decisions 6, 7).
- **SPEC §5.1:** the result shape is decided, with the names below (decision 9).
- **SPEC §8.3:** the builder returns a `Utility`; tables in M5; the elevation reference converts with D/2 (decisions 1–3).
- **SPEC §12.4:** M1's row: the figures move from (b) to (c) (intent decision 1).
- **`pyproject.toml`:** `pandas>=2.1.1,<3`, hangtu's floor, with mypy told pandas ships no types (as hangtu does).
- **New modules:** `garisenda.utilities` (`Utility`, `perpendicular_utility`, `BuildRecord`), `garisenda.profile` (`movement_profile`), `garisenda._result` (`Result`). Public names in `gs`: `utilities`, `movement_profile`, `Result`.

### Decisions

**The utility and its builder**

1. 🟡 **`gs.utilities.Utility(*, utility_id, vertices, diameter)`**, frozen. `vertices` is an (N, 3) array of x, y, depth in m (or a pint array), `diameter` a length. It can be made directly (M5's loaders will), and then has `built=None`. Raises: fewer than two vertices; any vertex non-finite or above the surface (depth < 0); a zero-length segment; diameter ≤ 0. 🟡 **More than two vertices raise** in M1 (b), naming M5, because a bent polyline needs the curvature terms of SPEC §3; collinear ones too, to keep one rule.
2. 🟡 **`gs.utilities.perpendicular_utility(tunnel, *, utility_id, station, start_offset, end_offset, diameter, elevation_reference, depth=None, elevation=None, ground_elevation=None) -> Utility`.** The two vertices are p = p₀ + (station − s₀) t + offset n at each offset, at the axis depth. The level is given as `depth`, or `elevation` with `ground_elevation`, as for the tunnel (SPEC §8.2). `elevation_reference` is required, with no default (SPEC §8.3). Raises: start and end offsets equal; an axis above the surface. The returned utility has a `BuildRecord` (the tunnel, station, start and end offsets, `"perpendicular"`), its inputs (kind `"geometry"`), and the assumption "Built perpendicular to the tunnel at station <s> m, whatever its real orientation (SPEC §1.3)".
3. 🟡 **The elevation reference converts with D/2:** axis depth = depth − D/2 for `"invert"`, the depth itself for `"axis"`, and depth + D/2 for `"crown"` (the same in elevation, with the signs reversed). The diameter is the one given, so the wall thickness is ignored: an invert or crown measured inside the pipe puts the axis off by the wall thickness, a few mm to a few cm. Recorded as an assumption when the reference isn't `"axis"`.

**Stations (intent decision 2)**

4. 🟡 **`source.critical_distances(*, start, end) -> ndarray`** is added to the `Source` protocol: for a straight segment from `start` to `end` (each (x, y, depth) in m), the distances from `start` where the source's quantities peak or change sign, sorted, within [0, L]. For the surface trough these are where the segment's offset crosses 0, ±i and ±√3 i. Offset is linear in distance along a straight segment, so each crossing is solved exactly; a segment at constant offset (parallel to the tunnel) has none.
5. **Stations** are 0, L, every multiple of `spacing` below L, and the critical distances. Two stations closer than 1 µm are merged into one, keeping the critical one, so a critical point on the spacing grid isn't listed twice. `spacing` is a required keyword-only design judgment with no default, a length > 0. 🟡 More than 1,000,000 stations raise, saying the spacing is too fine for the utility's length.

**The profile (SPEC §3)**

6. **Directions** on a straight segment, with components in the order (x, y, depth):
   - along: a = (end − start) / L;
   - lateral: l, horizontal and to the right looking along a: l = (a_y, −a_x, 0) / |(a_x, a_y)| (intent decision 5). A vertical segment has no lateral direction and raises.
   - vertical: v = l × a, which for a level segment is (0, 0, 1), so vertical is settlement, positive downward.
7. 🟡 **Columns of the values table**, keyed by `distance` (m) from the start. Each displacement component is u·e for e = a, v, l, and its derivatives with respect to distance are exact: d(u·e)/ds = e·∇u·a and d²(u·e)/ds² = e_i H_ijk a_j a_k.
   - `x`, `y`, `depth` (m); `station`, `offset` (m), relative to the reference tunnel, only for a built utility;
   - `along`, `vertical`, `lateral` (m);
   - `along_strain` (dimensionless, d along/ds, tension positive, SPEC §8.1) and `along_strain_gradient` (1/m);
   - `vertical_slope` (dimensionless) and `vertical_curvature` (1/m);
   - `lateral_slope` (dimensionless) and `lateral_curvature` (1/m);
   - `critical` (bool): the station is one of the source's critical distances;
   - `verdict` (str): the source's verdict at the station.
   Units in `df.attrs["units"]` (SPEC §6). `along_strain` is the ground's strain along the utility; M3 decides what part of it the pipe takes.
8. **`gs.movement_profile(utility, source, *, spacing) -> Result`**, with `spacing` declared through `@judgments`. Anything the source raises (a station inside the bore, say) is re-raised naming the utility, so nothing is dropped (SPEC §10).

**The result (SPEC §5.1)**

9. 🟡 **`gs.Result`**, frozen, shared by every analysis:
   - `analysis` (str, e.g. `"movement_profile"`) and `subject` (str, the utility id);
   - `values`: the DataFrame of decision 7;
   - `checks`: a DataFrame with the columns `check`, `value`, `limit`, `utilization`, `governing_distance`, `passes`, empty until M3;
   - `method`: the source's `MethodRecord`s and one for the profile (how stations and derivatives were built);
   - `assumptions`: the source's, the utility's, and 🟡 "Assets follow the ground: greenfield, no soil–structure interaction (SPEC §1.3)";
   - `inputs`: every `InputRecord`: the source's, the utility's and `spacing`;
   - `validity`: the worst verdict over the stations and flags (SPEC §5.2);
   - `warnings`: every `Flag`, with `points` as row positions in `values`.
10. 🟡 **Views, which never recalculate:** `to_frame()` returns a copy of `values` with its attrs; `to_dict()` returns plain JSON types (values by column, units, checks, method, assumptions, inputs as name, magnitude, unit, kind, given_as and source, validity, warnings); `repr()` is a short text summary, as hangtu's results are: the analysis and subject, the validity and each warning with the distance range it covers, the station count, the largest settlement, horizontal strain (tension and compression) and vertical curvature (sagging and hogging) with their distances, and the number of assumptions.

### Hand calculation (golden values)
The tunnel and trough of M1 (a): reference point (0, 0), azimuth 0° (along +y, so n = +x), D = 6.0 m, z₀ = 20.0 m, k = 0.5, V_L = 1.0 %, i = 10.0 m. Values at offset o come from M1 (a)'s table.

**A. Perpendicular utility at the surface.** `perpendicular_utility(station=50, start_offset=-20, end_offset=20, depth=0, elevation_reference="axis", diameter=0.3)`, spacing 5 m. L = 40 m, a = n, l = (0, −1, 0), so lateral is zero; offset = distance − 20.
- Critical distances: offsets −√3 i, −i, 0, i, √3 i give 2.6794919, 10, 20, 30, 37.320508 m.
- Stations: 0, 2.6794919, 5, 10, 15, 20, 25, 30, 35, 37.320508, 40 (11; 10, 20, 30 merged).
- Because a = n, along = u_n, `along_strain` = du_n/do, `along_strain_gradient` = d²u_n/do², `vertical_slope` = dS/do, `vertical_curvature` = d²S/do². At distance 30 (o = i): along = −3.4207805e-3 m, vertical = 6.8415611e-3 m, `along_strain` = 0, `vertical_slope` = −6.8415611e-4, `vertical_curvature` = 0, `along_strain_gradient` = 6.8415611e-5 1/m. At distance 25 (o = 5) and 20 (o = 0), the rows of M1 (a)'s table likewise.
- Every station is `within`; `station` is 50 and `offset` = distance − 20 in every row.

**B. The same utility reversed** (start offset 20, end −20): a = −n. Strain and curvature don't depend on the direction, so `along_strain` and `vertical_curvature` are unchanged at the same offset; along, `vertical_slope` and `along_strain_gradient` (a derivative of strain with respect to distance, which now runs the other way) change sign. (Corrected in build step 4: the spec first listed `along_strain_gradient` as unchanged.) At distance 10 (o = 10): along = +3.4207805e-3 m, `vertical_slope` = +6.8415611e-4.

**C. Buried, given by elevation.** As A, but `elevation=97.0` with `ground_elevation=100.0`, `elevation_reference="invert"`, `diameter=0.6`: axis depth = 3.0 − 0.3 = 2.7 m. With `"crown"` at 97.6: 2.4 + 0.3 = 2.7 m. Every station is `outside`, with M1 (a)'s below-surface flag, and the values equal A's (the surface trough ignores depth).

**D. A utility at 45° to the tunnel**, made directly: `Utility(vertices=[(-20, -20, 0), (20, 20, 0)])`. a = (1, 1, 0)/√2, l = (1, −1, 0)/√2, v = (0, 0, 1). With c = 1/√2: n·a = n·l = c, and offset o = x = −20 + c·distance.
- Critical distances: (o + 20)/c for o = −√3 i, −i, 0, i, √3 i: 3.7893738, 14.142136, 28.284271, 42.426407, 52.779169 m.
- At o = 5 (distance 35.355339 m): along = lateral = c·u_n = −1.7597082e-3 m; vertical = 9.9544126e-3 m; `along_strain` = `lateral_slope` = c²·du_n/do = −1.8664524e-4; `vertical_slope` = c·dS/do = −3.5194163e-4; `along_strain_gradient` = `lateral_curvature` = c³·d²u_n/do² = 2.4195987e-5 1/m; `vertical_curvature` = c²·d²S/do² = −3.7329047e-5 1/m.
- This checks the lateral direction and sign, and the sin²θ scaling of curvature and axial strain with crossing angle (TODO #10).

### Acceptance criteria
Tolerance 1e-6 relative, as in M1 (a), for values carried to 8 figures; exact zeros checked to 1e-12 of the column's scale, since they come out of rotations.

1. **Builder geometry:** case A's vertices are (−20, 50, 0) and (20, 50, 0); on a rotated tunnel (M1 (a)'s, azimuth 30°, reference station 1000), a utility at station 1025 has both vertices at station 1025 and the offsets asked for, and is perpendicular (a·t = 0 to 1e-12).
2. **Builder record:** the `BuildRecord`, the inputs with kind `"geometry"`, and the perpendicular assumption naming the station.
3. **Elevation reference:** case C gives 2.7 m for invert and crown, and 2.7 m for `"axis"` at depth 2.7; a missing `elevation_reference` raises a `TypeError` naming it; an unknown one raises, listing the three; depth and elevation together, or elevation without ground, raise.
4. **Utility checks:** each raise of decision 1, including three vertices naming M5.
5. **Stations:** case A's 11 stations exactly, with `critical` true at the five critical distances; case D's critical distances; a spacing larger than L gives the ends and the critical points; a missing `spacing` raises the judgment error; spacing ≤ 0 raises; too many stations raise.
6. **Golden values:** cases A, B and D at the stations given, through `movement_profile`.
7. **Exact derivatives along the utility** (hypothesis, over tunnel, trough and a straight utility at any angle and level): `along_strain`, `vertical_slope` and `lateral_slope` match central finite differences of `along`, `vertical` and `lateral` along the utility, and the second derivatives those of the first, using `movement_profile` on short utilities around a point.
8. **Below the surface:** case C is `outside` at every station; `validity` is `outside`; the warning lists every row; the values equal case A's.
9. **Result parts:** `values` keyed by `distance` with the columns of decision 7 and their units; `checks` empty with its columns; `method`, `assumptions` (including greenfield and perpendicular) and `inputs` (including `spacing` as a design judgment) complete; `validity` the worst verdict.
10. **Views:** `to_frame()` equals `values` and changing it leaves the result unchanged; `to_dict()` round-trips through `json.dumps`; `repr()` names the analysis, subject, validity, warnings with their distance ranges, and the extremes of case A at the right distances (settlement 1.1279827e-2 m at 20 m).
11. **Nothing dropped:** a perpendicular utility through the bore raises, naming the utility and the stations inside the bore.
12. **Docstrings** of every public name state inputs and outputs with units, conventions and assumptions; ruff's numpy docstring rules pass.
13. **Dependencies:** pandas added with its floor, passing the `lowest` job; mypy strict passes.

## Plan

Six build commits, each with ruff check, ruff format check, mypy and pytest green, and each kept near 300 changed lines (M1 (a)'s lesson): source, docstrings and tests for one piece per commit.

### 1. `M1 (b): add the utility and the perpendicular builder`
- `src/garisenda/utilities/__init__.py`, `src/garisenda/utilities/_utility.py`: `Utility` (frozen; checks of decision 1), `BuildRecord`, `perpendicular_utility()` (decisions 2–3), using `record()` for every input and the tunnel's `tangent`, `normal` and `reference_station`.
- `src/garisenda/__init__.py`: export `utilities`.
- Tests: `tests/utilities/test_utility.py`: AC 1, 2, 3, 4.

### 2. `M1 (b): add critical distances to the source interface`
- `src/garisenda/sources/_movement.py`: `critical_distances(*, start, end)` on the `Source` protocol.
- `src/garisenda/sources/_transverse.py`: the surface trough's, from the offsets of the segment's ends (decision 4).
- Tests: `tests/sources/test_transverse.py`: case A's and case D's critical distances; a segment parallel to the tunnel has none; a segment that reaches only some crossings returns only those (AC 5, in part).

### 3. `M1 (b): add the result and its views`
- `pyproject.toml`, `uv.lock`: `pandas>=2.1.1,<3`; mypy override for `pandas.*` (no types shipped), as hangtu has.
- `src/garisenda/_result.py`: `Result` (decision 9), `to_frame()`, `to_dict()`, `repr()` (decision 10). The summary's extremes read named columns and are skipped when a column is absent, so later analyses reuse it.
- `src/garisenda/__init__.py`: export `Result`.
- Tests: `tests/test_result.py`, on a `Result` built by hand: `to_frame()` is a copy with attrs; `to_dict()` through `json.dumps`; `repr()` lists validity, warnings by distance range and extremes (AC 10, in part).

### 4. `M1 (b): add the movement profile`
- `src/garisenda/profile/__init__.py`, `src/garisenda/profile/_movement_profile.py`: `movement_profile()` with `@judgments(spacing=...)`: stations (decision 5), directions (decision 6), the columns (decision 7) from the source's gradient and Hessian, re-raising the source's errors naming the utility (decision 8), and the `Result`.
- `src/garisenda/__init__.py`: export `movement_profile`.
- Tests: `tests/profile/test_movement_profile.py`: cases A–D (AC 5, 6, 8), result parts (AC 9), the bore (AC 11), `repr()` extremes for case A (AC 10).

### 5. `M1 (b): add property tests for the profile`
- `tests/profile/test_movement_profile_properties.py` (hypothesis): AC 7, finite differences of the profile's displacements and first derivatives along utilities at any angle and level. The tunnel and trough strategies are copied from M1 (a)'s property tests rather than shared (M1 (a) plan, step 4); if a third copy is needed, they move to `conftest.py`.

### 6. `M1 (b): close out`
- Run the `lowest` job locally, then `git checkout uv.lock`.
- `docs/work/m1b-movement-profile.md`: `## Result`, each acceptance criterion met or not, with evidence.
- `SPEC.md`: the 🟡 items this unit settled (§3 critical distances and the profile, §5.1 the result, §8.3 the builder) marked decided.
- `CLAUDE.md`: the "Next" sentence points to M1 (c); a convention line if one emerged.

## Result

Built in six commits as planned; ruff, ruff format, mypy strict and 139 tests pass, and the tests pass on the dependency floors (numpy 1.26.0, pandas 2.1.1, pint 0.24.4).

| AC | Met | Evidence |
|---|---|---|
| 1. Builder geometry | Yes | `tests/utilities/test_utility.py`: `test_case_a_vertices`, `test_rotated_tunnel_vertices_at_station_and_offsets` (station 1025, offsets, a·t < 1e-12) |
| 2. Builder record | Yes | `test_build_record_inputs_and_assumption` |
| 3. Elevation reference | Yes | `test_case_c_elevation_reference` (invert and crown give 2.7 m), `test_axis_reference_by_depth`, `test_missing_elevation_reference_names_it`, `test_unknown_elevation_reference_lists_the_three`, `test_level_given_ambiguously_raises` |
| 4. Utility checks | Yes | `test_three_vertices_raise_naming_m5`, `test_bad_vertices_raise`, `test_bad_diameter_raises`, `test_empty_id_raises` |
| 5. Stations | Yes | `tests/sources/test_transverse.py` (critical distances, cases A and D, parallel, partial, 3D); `tests/profile/test_movement_profile.py`: `test_case_a_stations` (11 stations, five critical), `test_case_d_critical_distances`, spacing larger than L, missing, ≤ 0 and too fine |
| 6. Golden values | Yes | Cases A, B and D at 1e-6 relative. Hand calculation B was wrong about `along_strain_gradient`, which changes sign on reversal; corrected in the spec (build step 4) and in SPEC §3 |
| 7. Exact derivatives | Yes | `tests/profile/test_movement_profile_properties.py`: central differences along utilities at any plan angle, pitch (±30°) and level, to 1e-6 of the scale |
| 8. Below the surface | Yes | `test_case_c_buried_is_outside_with_surface_values` |
| 9. Result parts | Yes | `test_result_parts` |
| 10. Views | Yes | `tests/test_result.py`; `test_views_of_case_a` (settlement 0.01128 m at 20 m), `test_repr_of_case_c_lists_the_warning_range` |
| 11. Nothing dropped | Yes | `test_utility_through_the_bore_raises_naming_it` (names the utility and the station at 20 m) |
| 12. Docstrings | Yes | ruff's numpy docstring rules pass on `src/`; each public name gives units, signs and assumptions |
| 13. Dependencies | Yes | `pandas>=2.1.1,<3`, the floor run above; mypy strict passes |

Beyond the plan:
- The inputs also record `station_merge_tolerance` (1 µm) as a constant or setting, as the trough records its surface tolerance (SPEC §4).
- When a source raises for some stations, the message adds their distances along the utility to the indices the source names.
- The summary reports the extremes decision 10 lists (settlement, strain along, vertical curvature), not the lateral curvature, which is zero for a perpendicular utility.
