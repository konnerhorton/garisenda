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

## Spec

No topic doc holds the figures' rules beyond SPEC §9's sentences, so the spec is here. It settles the intent's "To settle" items; each 🟡 is a proposal for review. It was checked against SPEC §5.1, §6, §9, §10 and §12.3–12.4, the M4 (a) spec, and the code of `gs.plot` and `gs.check_building` as merged.

### What the code says (beyond the intent)
- **The cross-section's contract is `axs`, not `ax`.** The intent's constraint quotes `cross_section(result, *, ax=None, ...)`, but it takes `axs=` (three panels: settlement, horizontal movement, the section) and returns `(fig, axs)`, as SPEC §9 allows for a multi-panel figure. It stays as it is.
- **The result doesn't hold the damage categories.** `category_limits` is recorded in `inputs` as text (`"<name> (0 up to 0.05 %; ...)"`), and `zones` has each zone's `category`, `label` and `severity`, but not the bands' limits. The intent's constraint ("drawn from the `DamageCategories` the caller passed, which the result records") needs them (decision 3).
- **Everything else the panels draw is in the result:** `values` has `vertical`, `vertical_slope`, `along_strain`, `zone`, `chord` and `deflection`, with rows at each zone's ends and Δ; `zones` has `mode`, `start`, `end`, `length`, `deflection`, `deflection_distance`, `deflection_ratio`, `horizontal_strain`, `total_bending_strain`, `total_diagonal_strain`, `tensile_strain`, `governed_by`, `category`, `label`, `severity`; `checks` has `settlement`, `slope`, `zone_1…n` and `damage_category` with their limits.
- **`d = w − c` is continuous across zone ends:** it is zero at both ends of every zone, so `deflection` draws as one line, with gaps only outside the assessed range (NaN).
- **The slope check is on |slope|,** at `governing_distance`; the row at that distance is in `values` (Stage 1's extremes are critical distances), so its signed `vertical_slope` can be read there.
- **A building's movement profile** (not a check) is drawn in the ground's four panels, labeled "Distance along utility". That label is wrong for a wall.

### Changes
- **SPEC §5.1:** a result keeps, beside its source and asset, a building check's damage categories, outside the views (decision 3).
- **SPEC §6 and §9:** display units gain a kind, `slope`, defaulting to mm/m (decision 4).
- **SPEC §9:** one sentence for the building check's profile (decision 1) and one for the cross-section's wall (decision 7).
- **SPEC §12.4:** M4 (b), and so M4, done, at close-out.
- **`src/garisenda/_result.py`:** `Result.categories` (decision 3).
- **`src/garisenda/buildings/_check.py`:** sets it.
- **`src/garisenda/plot/_display.py`:** the `slope` kind.
- **`src/garisenda/plot/_profile.py`:** the building check's five panels; "Distance along wall" for any result whose asset is a `Building`.
- **`src/garisenda/plot/_cross_section.py`:** the wall drawn as a wall, with its zones and cut-off (decision 7).
- **Docs site:** a new guide, `guides/buildings.md`, with its example `examples/buildings.py`; a building section on `figures/profile.md` and `figures/cross-section.md`, from their examples; the guide in `zensical.toml`'s nav (decision 9).
- **Close-out:** `README.md`'s status line, `CHANGELOG.md`'s Unreleased section, `CLAUDE.md`'s status sentence and "Next" (M5).

### Decisions

**The unit (intent 🟡 1)**

1. 🟡 **One unit.** The guide's figures come from its example, and the figures are reviewed by looking at the guide's. M1 (c) made the same call.

**The profile (intent 🟡 2)**

2. 🟡 **A building check is drawn in five panels**, top to bottom, against distance along the wall (`axs` takes five). A building's movement profile keeps the ground's four.

   On every panel:
   - **Zones:** each inner zone end is a thin vertical line (`gid="zone_end"`). Hogging and sagging each have one color on every panel; a flat zone is gray.
   - **The cut-off:** where the assessed range ends inside the wall (the first zone's start is after the wall's first station, or the last zone's end before its last), a dotted vertical line at each end (`gid="cutoff"`), and the part beyond hatched (`gid="beyond_cutoff"`), labeled "beyond the cut-off: not assessed" on the top panel. With `no_cutoff()`, the range is the whole wall and nothing is drawn.
   - **As now:** verdict shading, critical ticks, the offset axis on top, flag notes under the figure.

   The panels:
   1. **Settlement** (`vertical`, displacement, down +, axis inverted): the settlement solid; each zone's `chord` thin and dashed (`gid="chord:zone_<n>"`); the area between them filled in the zone's mode color (`gid="zone_<n>"`), which is the deflection the method assesses, as Mair, Taylor & Burland draw it; each zone labeled at the top with its number and mode (`gid="zone_label:<n>"`); the settlement limit, and the `settlement` check marked with its utilization. Chords are construction lines, not discrete values; there are no discrete values on this figure, so dashing them can't be misread, and the title says "chords dashed".
   2. **Deflection from the chord** (`deflection`, d = w − c, displacement, axis inverted as the settlement's, so a hogging zone rises as the wall does): the line, and each zone's Δ marked at (`deflection_distance`, −Δ in hogging, +Δ in sagging) with "Δ = 3.2 mm, Δ/L = 1/4700" (`gid="delta:zone_<n>"`). A flat zone has no mark, and is labeled "flat: no deflection" at its middle (`gid="flat:zone_<n>"`). No limit: the method doesn't check Δ/L on its own. Δ/L is written as 1/n, with n to 3 significant figures, as practice writes it.
   3. **Slope** (`vertical_slope`, the new `slope` kind, "settlement increasing along +"): the line, the slope limit as ± lines (the check is on |slope|), labeled with its value and as 1/n ("slope limit: 2 mm/m (1/500)"), and the `slope` check marked at the signed `vertical_slope` of its governing row, with its utilization.
   4. **Horizontal strain** (`along_strain`, strain, tension +): the line, and each zone's ε_h (`horizontal_strain`) as a level line across the zone in its mode color (`gid="horizontal_strain:zone_<n>"`). No limit.
   5. **Tensile strain by zone** (strain, tension +): for each zone, ε_bt (`total_bending_strain`) and ε_dt (`total_diagonal_strain`) as level lines across the zone (`gid="total_bending_strain:zone_<n>"`, `"total_diagonal_strain:zone_<n>"`), the one `governed_by` names thick, the other thin, labeled "bending" or "diagonal" and with the zone's category label; the category bands from the result's categories (decision 3) shaded in the background, alternating grays, each labeled at the right with its label and severity (`gid="band:<number>"`); the acceptable category's upper limit as the limit line ("acceptable: category 2, 0.15 %"; `gid="damage_category_limit"`); the governing zone marked at the middle of its level line with "category 1 (very slight), u = 0.42" (`gid="check:damage_category"`). A zone's strain is a beam's over the whole zone, not at a point, so it is a level line, not a curve, and the mark's position along the zone isn't a value.

   Considered and rejected: the ground's four panels with zones added (the intent's reasons), and Δ on the settlement panel alone (a few mm on tens of mm can't be read).

   **Title:** "Building check along <id>", then the beam method and the cut-off as recorded in `inputs` ("Burland & Wroth beam, cut-off at 2.5 i; chords dashed").

   **Scale (TODO #11's rule):** limit lines set a panel's scale, as on the pipe panels. On panel 5 the bands don't: the scale covers the zones' strains, the acceptable limit, and the upper limit of the band holding the largest strain when it is finite, so the governing band shows whole and the bands beyond are clipped. Drawing all of Table 2 (to 0.3 % and beyond) would flatten strains of a few hundred µε.

3. 🟡 **`Result.categories`: the result keeps a building check's `DamageCategories`**, beside `source` and `asset`, outside the views (`repr=False, compare=False`; not in `to_dict()`, where `inputs` already gives the bands as text). `None` for every other analysis. SPEC §5.1 already says a result keeps "its source and asset ... so a figure can draw what the table doesn't hold"; this is the same case.
   - Considered: parsing the input record's text (fragile, and text is for reading); the bands in `zones.attrs` (attrs are lost on many pandas operations and are building-only metadata on a generic table); a bands table among the views (the record already states them, and a view per check type doesn't scale).

4. 🟡 **Display units gain `slope`, defaulting to mm/m.** 1/500 is 2 mm/m, which reads well on an axis; percent and microstrain-style units are accepted (any dimensionless unit, as `strain`). A slope limit's label also gives 1/n. Δ/L has no axis, so no kind: it is written as 1/n in labels. The cross-section accepts `slope` and doesn't use it, as it does `strain`.

5. 🟡 **Edge cases draw, with their reason (SPEC §10):**
   - **No zone** (a wall wholly beyond the cut-off): panels 1, 3 and 4 draw as usual, the whole wall hatched beyond the cut-off; panels 2 and 5 draw no zone lines and say "no zone: the wall is wholly beyond the cut-off" (`gid="no_zone"`). The flag's reason is under the figure as for any flag.
   - **A flat zone:** decision 2, panel 2; on panel 5 its strains are ε_h's alone and draw as any zone's.
   - **A limit of `None`:** no line, and "no settlement limit", "no slope limit" or "no acceptable category" on the panel (`gid="no_limit"`), as the pipe panels do. With no acceptable category, the governing zone is still marked, with its category and "no limit".
   - **The last band accepted** (limit ∞): no line, and "acceptable: category 4 to 5, no upper limit".

6. 🟡 **The figure never recalculates.** Every drawn value is a column of `values`, `zones` or `checks` times its display factor, or a band limit of `result.categories`. Positions that aren't values (a zone's middle for a label or mark) are drawing only.

**The cross-section (intent 🟡 3)**

7. 🟡 **The wall is drawn as a wall** on the section panel: an outline from its foundation depth up to its height H above it (`gid="building"`), between its offsets, labeled with its id and H. The section's depth range includes the wall's top, above the ground when H is more than the foundation depth. For a building check, also:
   - each inner zone end as a tick on the wall's base (`gid="zone_end"`), and each zone's number and mode written inside the wall above its base (`gid="zone_label:<n>"`); offsets come from `values`' rows at those distances, which exist;
   - the cut-off, where there is one inside the wall (decision 2), as a dotted vertical line on all three panels (`gid="cutoff"`).

   The trough panels already draw at the wall's foundation depth; for a `Building` they say "at foundation level (depth 2 m)".
   
   The interim line at foundation depth goes.

8. 🟡 **The deformed wall isn't drawn exaggerated** (intent, out of scope). The profile's panel 2 shows the deflection to scale on its own axis, and an exaggerated drawing needs a magnification the reader has to keep in mind. Later, if users ask.

**The guide (intent 🟡 5)**

9. 🟡 **`guides/buildings.md`, "Buildings", after "Jointed pipes" in the nav**, from one script, `examples/buildings.py`, with invented geometry. Its sections:
   1. **A wall over one tunnel:** `perpendicular_building` from station and offsets, with height and foundation depth; `movement_profile`; `check_building` with every judgment from a preset (`burland_wroth_beam()`, `youngs_to_shear_modulus_ratio(structure="masonry")`, `damage_categories()`, `trough_width_cutoff(multiple=2.5)`, `preliminary_assessment_limits()`, acceptable category 2, `"greenfield"`). The printed result, then `result.zones` and `result.checks`, each column read in a sentence.
   2. **The figures:** the profile and the cross-section, read panel by panel: where the zones fall, the chord and Δ, Stage 1, ε_h, the strains on the bands.
   3. **The judgments and what changes them,** each a sentence or two with what it does to this wall: the beam method (Timoshenko's gives larger strains), E/G (masonry or framed), the category limits and the acceptable category, the cut-off (none, or a multiple of i, and why cutting can be unconservative), the Stage 1 limits, the foundation depth (the trough at depth is narrower). Each says that it is a judgment with no default, and points to the preset's caveats.
   4. **Twin tunnels:** a wall over two, with several zones; its profile.
   5. **The depth limit:** a deep foundation flagged `outside`, and what the flag says.
   6. **A sweep** over volume loss, with each run's governing category.
   7. **Sources:** the method is Mair, Taylor & Burland (1996)'s statement of Burland & Wroth (1974), Burland et al. (1977) and Boscardin & Cording (1989), whose originals haven't been read; the Timoshenko beam and Eq. 10's general form are garisenda's derivation; the depth limit is Harris & Franzius (2006) as Jones (2022) reports it, also unread. So results are for trying the method, not for design, as the trough's pages say. No internal references.

   **The figure pages** gain a section each: "A building check" on `figures/profile.md` (the five panels, read briefly, pointing to the guide), and "A building" on `figures/cross-section.md`, each drawn by its page's script.

### Sources
- **mair1996:** Mair, Taylor & Burland (1996), pp. 715–717, verified 2026-11-10 (M4 (a)) for the zones, chord, Δ, Eqs. 7–10 and Table 2. The figures draw only those. 🔬 The intent cites Fig. 3 for the drawing of zones, chord and Δ; its page hasn't been checked, so the guide doesn't cite Fig. 3 until it is read against the page image.
- No new calculation, so no new golden values. The figure's tests compare drawn data with the result's values (criteria below).

### Acceptance criteria

The example for 1–8: a tunnel 20 m deep, 6 m in diameter, volume loss 1.5 %, k = 0.5; a wall from offset −30 m to +30 m, H = 9 m, foundation depth 1.5 m, spacing 1 m; checked with the presets, the Burland & Wroth beam, a 2.5i cut-off and acceptable category 2. Its zones are hogging, sagging, hogging, and the cut-off falls inside the wall on both sides. Drawn data are compared with the result's values times the display factor, to 1e-12 relative.

1. **Five panels:** `gs.plot.profile` of a building check returns five Axes with the labels "Settlement (mm)", "Deflection from chord (mm)", "Slope (mm/m)", "Horizontal strain (µε)", "Tensile strain (µε)", and "Distance along wall (m)" on the bottom. `axs` of any other length raises `ValueError` naming the five panels. A building's movement profile has four panels and "Distance along wall (m)".
2. **Settlement panel:** the `vertical` line is the column; each `chord:zone_<n>` line is the `chord` column over that zone's rows; one `zone_<n>` fill per zone; the settlement limit at the check's limit; `check:settlement` at its value and distance.
3. **Deflection panel:** the `deflection` line is the column (NaN beyond the cut-off); each `delta:zone_<n>` mark is at (`deflection_distance`, ∓Δ by mode), and its text gives Δ in mm and Δ/L as 1/n (n = 1/`deflection_ratio` to 3 significant figures).
4. **Slope panel:** the line is `vertical_slope` in mm/m; `slope_limit` lines at ±2 mm/m with the label "2 mm/m (1/500)"; `check:slope` at the signed `vertical_slope` of the row at its governing distance.
5. **Horizontal strain panel:** the line is `along_strain`; each `horizontal_strain:zone_<n>` runs from the zone's `start` to `end` at its `horizontal_strain`.
6. **Tensile strain panel:** each zone's two level lines at `total_bending_strain` and `total_diagonal_strain` over [`start`, `end`], the governing one thicker; one `band:<number>` per band of `result.categories` within the scale, at its limits; `damage_category_limit` at 1500 µε; `check:damage_category` on the governing zone's line, with its category label and utilization. The y range includes the largest strain, the limit and the governing band's upper limit.
7. **Zones and cut-off on every panel:** two `zone_end` lines at the inner zone ends; two `cutoff` lines at the first zone's start and last zone's end; `beyond_cutoff` hatches outside. With `no_cutoff()` there are none.
8. **Cross-section:** the `building` outline spans the wall's offsets, from the foundation depth to H above it, and the section's y range includes its top; `zone_end` ticks at the offsets of the rows at the inner zone ends; `cutoff` lines on all three panels; the trough panels say "at foundation level (depth 1.5 m)". A building's movement profile draws the outline with no zone marks.
9. **Edge cases (SPEC §10):**
   - A wall wholly beyond the cut-off draws five panels with `no_zone` notes on panels 2 and 5 and its flag under the figure, and doesn't raise.
   - A wall 500 m from the tunnel with `no_cutoff()` (one flat zone) draws `flat:zone_1` and no `delta:` mark.
   - `settlement_limit=None`, `slope_limit=None` and `acceptable_category=None` each draw `no_limit` with its text and no limit line; the governing zone is still marked.
   - Acceptable category 4 (unbounded) draws no limit line and says so.
10. **Twin tunnels:** a wall over twin tunnels with five zones draws five `zone_<n>` fills, four `zone_end` lines and five `delta:` marks.
11. **`Result.categories`:** a building check's is the `DamageCategories` passed; every other analysis's is `None`; it isn't in `to_dict()`, and two results differing only in it compare equal.
12. **Display units:** `slope` defaults to mm/m; `{"slope": "percent"}` draws the slope panel in % with the label "Slope (%)"; a unit with a dimension raises `pint.DimensionalityError`; an unknown kind's error lists `slope`.
13. **The plot contract:** `rcParams` unchanged after drawing; drawing into given `axs` creates no figure; the result is unchanged after drawing (its `values`, `zones` and `checks` equal copies taken before).
14. **Docs:** `examples/buildings.py`, `profile.py` and `cross-section.py` run; the site builds with `--strict` and no `griffe:` warning; `tests/test_published_text.py` passes over the new pages and strings.
15. **Looked at:** the generated figures are checked by eye against decisions 2, 5 and 7 once the tests pass, in a new session if cheaper.
