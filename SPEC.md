# garisenda — Product Specification

**Status:** Draft.

**What belongs here:** decisions that constrain more than one feature, plus scope and phasing. Per-feature detail lives in that feature's spec (the `## Spec` section of `docs/work/<id>.md`, or a topic doc under `docs/`). Detail for later phases is held in `docs/drafts/` until those phases start. Update this file in the same commit as any change that alters a decision. How the process works: the `spec-driven-development` skill.

**Conventions**
- **Decided**: agreed in review.
- 🟡 **Proposed**: Claude's proposed default, awaiting review.
- ❓ **Open**: needs input (collected in §13).
- 🔬 **Research**: tracked in [TODO.md](docs/TODO.md).

**Document map**
| Document | Contents |
|---|---|
| `SPEC.md` (this file) | Scope, phasing, cross-cutting decisions |
| `docs/work/<id>.md` | Intent, spec and plan for each unit of work |
| [`docs/drafts/`](docs/drafts/) | Notes for later work, including the scope discussion this spec came from |
| [`docs/TODO.md`](docs/TODO.md) | Research items and pending decisions |
| [`CLAUDE.md`](CLAUDE.md) | Working conventions and commands |

---

## 1. Scope and phasing

**Purpose (decided 2026-10-31):** garisenda estimates ground movements caused by tunneling and excavation, and assesses their effect on utilities and structures. It starts with greenfield closed-form and empirical methods, and makes them traceable: every result records its inputs, its method, its source and the limits it was checked against. It does not replace numerical analysis. A result outside a method's validity says so (§5.2), and that flag is how the engineer knows a numerical model is needed.

The name is the Garisenda, the leaning tower in Bologna whose lean comes from settlement of its foundations.

### 1.1 Users and distribution
- **Persona (decided):** a geotechnical or tunnel engineer with beginner-to-intermediate Python.
  - They think in **scripts and functions** more than objects, so every analysis is a plain function.
  - **The engineer who checks an assessment is often not the one who ran it.** So every result carries what it took to check it (§4, §5), and every assessment has a figure (§9).
- **Distribution (decided):** open source, MIT license, published on PyPI and public GitHub, developed independently. No project data is used in development or testing: real project documents stay on the machine where the work is done.
- **Name (decided 2026-10-31):** published on PyPI as **`garisenda`** (unclaimed when checked on 2026-10-31), imported as `import garisenda as gs`.

### 1.2 Boundaries
- **garisenda takes its inputs as plain data** (decided): numbers, pint quantities and DataFrames. Volume loss, ground parameters and geometry come from the caller, whatever produced them. garisenda imports no other engineering package.
- **Volume loss is an input** (decided): estimating it from face pressure or empirical ranges is not garisenda's job. garisenda turns a volume loss into movements and impacts.
- **Geometry arrives ready to use** (decided 2026-10-31): one flat coordinate system and one length unit for every table (§8.1). Importing GIS datasets, converting coordinate systems and datums, and building alignments happen before data reaches garisenda.

### 1.3 Scope

**Phasing principle (decided 2026-11-01):** replace existing workflows first, then improve on them. Within Phase 1, the input that replaces the spreadsheet comes first, and real geometry builds on it.

**Phase 1: greenfield assessment in 3D, with spreadsheet-style input (decided 2026-11-01).** A greenfield assessment of individual utilities and buildings for one or more tunnels, with closed-form and empirical methods and figures for every result. **There is one analysis, always in 3D** (§3). How the geometry is entered is the user's choice:
- **By station and offset:** the traditional assessment, a direct replacement for the spreadsheet. A utility or a building's wall is given by a station along a tunnel, start and end offsets, and a depth or elevation, and is built as a straight line perpendicular to the tunnel at that station (§8.3). The tunnel can be an idealized straight tunnel (no ends) or a real alignment.
- **As polylines:** tunnel alignments, utilities and buildings loaded in 3D.

Either way the analysis returns the expected greenfield movements and strains along each asset, with flags where the method's assumptions fail.

| Area | Phase 1 content |
|---|---|
| **Tunnel movements** | Steady-state transverse Gaussian trough at the surface and below it; trough width from a given k at the surface, and at depth by a named method (M2 (b)); horizontal movements; several tunnels by superposition. The trough is applied perpendicular to each tunnel segment, then the 3D field with the longitudinal trough (M6) |
| **Geometry** | Idealized straight tunnels and real alignments; assets built from station and offset, or loaded as polylines; flags for tunnel ends, curves, runs parallel to a tunnel and sharp vertices (M5) |
| **Utilities** | Continuous pipes (welded steel, HDPE, PVC, HDD-installed) and jointed pipes (cast iron, ductile iron, clay, concrete); axial and bending strain, joint pullout and rotation; discrete and analytical strain, both computed and compared (§7) |
| **Buildings** | A wall built from station and offsets (it may straddle a tunnel), or a wall or footprint polyline, each edge a wall. Deflection ratio and horizontal strain per wall; damage category |
| **Soil–structure interaction** | None in Phase 1: assets follow the ground (§4) |

**Phase 1 assumptions (decided 2026-11-01).** Stated in the docs and recorded on every result (§5.1) when they apply:
- **Greenfield:** utilities and buildings follow the ground, with no reduction for their stiffness. This is conservative for strain.
- **Built perpendicular:** an asset built from station and offset is perpendicular to the tunnel whatever its real orientation, which is current practice and taken as conservative. For one transverse trough and a straight, level pipe, the perpendicular pipe bounds every crossing angle (shown in M3 (a)'s spec, [`docs/work/m3a-continuous-pipes.md`](docs/work/m3a-continuous-pipes.md), "The perpendicular bound"); 🔬 superposed troughs, pipes that change depth and assets parallel to a tunnel are TODO #10. The builder records this on the asset, and the result carries it.
- **Idealized straight tunnel:** no ends, shafts, curves or junctions, and the face long passed. Nothing about those can be flagged, because the tunnel has none.
- **Utilities are circular, and strain is taken at the outermost fiber** (decided 2026-11-06, M3 (a)), from the utility's outside diameter (§7).
- **Jointed pipes are rigid pipes whose joints follow the ground** (decided 2026-11-06, M3 (b), [`docs/work/m3b-jointed-pipes.md`](docs/work/m3b-jointed-pipes.md)): a chain of rigid pipes of length L, each joint a point on the axis that moves with the ground, and every position a possible joint. For the barrel's strains the joints are taken as rigid and the barrel follows the ground (Bracegirdle et al. 1996, p. 663). Each idealization is conservative for its own quantity.
- **Buildings follow the greenfield trough at foundation level, as beams** (decided 2026-11-10, M4 (a), [`docs/work/m4a-building-damage.md`](docs/work/m4a-building-damage.md)): a wall's movement is the source evaluated at its foundation depth (§13 Q4), with no stiffness of its own, and the wall is a beam of height H (foundation to eaves) and unit width spanning each zone of hogging or sagging (Mair, Taylor & Burland 1996, §4). Stage 1 is taken on the same trough. A foundation depth of 0 gives the published surface check; below the surface the trough is narrower and deeper, so the check is more onerous.
- **Transverse trough only, until M6:** the longitudinal trough is not considered, so runs parallel to a tunnel are flagged rather than assessed.

Conditions that the geometry shows (an asset near a real alignment's end, on a curve, or parallel to it) are flags, not assumptions.

**Soil–structure interaction (decided 2026-11-01).** A single reduction factor is not offered: the reduction depends on the pipe's size and on its stiffness relative to the soil, so one factor for everything is worse than none. The intended approach is a beam on springs along the real geometry (a 1D numerical model, §1.4), which is a later phase because of its size. ❓ Whether closed-form relative-stiffness methods are added before that, inside their stated range and flagged outside it, is §13 Q1.

**Later phases** (held in `docs/drafts/` when they start):
- Soil–structure interaction as a beam on springs, for utilities and buildings.
- Station-and-offset input at a crossing angle (skewed assets).
- Ground surface as its own geometry (a surface table), replacing Phase 1's single elevation (§8.2).
- Buildings from public GIS data (footprints and heights), once importing them is solved upstream (§1.2).
- Embedded retaining walls and excavations, staged construction, rail (cant and twist), mining and other sources of movement.

### 1.4 Non-goals
- **Numerical analysis** (FE, FD). garisenda flags where it's needed. The one planned exception is a 1D beam on springs for soil–structure interaction, in a later phase (§1.3).
- **Estimating volume loss** (§1.2).
- **Deriving ground parameters** from test data. garisenda takes them as given and records where they came from (§4).
- **GIS import and coordinate conversion** (§1.2).
- **Structural design of the affected asset.** garisenda compares movements and strains with limits; it doesn't design a repair or a protective measure.

## 2. Sources and verification

### 2.1 Governing sources
**Buildings** (decided 2026-11-10, M4 (a)) cite Mair, Taylor & Burland (1996), Eqs. 7–10 and Tables 1–2, after Burland & Wroth (1974), Burland et al. (1977) and Boscardin & Cording (1989) (🔬, TODO #7); the beam with any shear coefficient (the Timoshenko form, 6/5) and Eq. 10's general form are garisenda's own derivation, with Jones (2022) as a check. Each unit of work adds the sources it relies on, verified against the source itself, to the bibliography (§2.2); the first were verified in M2 (b) (2026-11-04). Candidates from the scope discussion (`docs/drafts/scope-discussion.md`) are not citations until verified. Secondary sources (software manuals, reviews) are never cited for equations, **except a review by the method's own authors that states the equation in full** (decided 2026-11-04, M2 (b), [`docs/work/m2b-subsurface.md`](docs/work/m2b-subsurface.md)): it is cited naming the original ("Mair & Taylor (1997), Eq. 8, after Mair et al. (1993)"), and the original stays 🔬 in `docs/TODO.md` until read. **A table of limits quoted in a verified source** may be cited from it the same way, naming the original ("Bracegirdle et al. (1996), Table 2, after Attewell et al. (1986)"; decided 2026-11-06, M3 (a)). **An equation that can't be read with certainty, or whose derivation can't be checked, isn't used** (decided 2026-11-06, M3 (b)): Bracegirdle et al. (1996)'s Eq. 3 (horizontal movement, smudged) and Eq. 5 (a bound on joint rotation, which exceeds the joint geometry only for some pipe lengths) wait until a clean copy and Attewell et al. (1986) are read (TODO #4).

### 2.2 Citation format
- 🟡 **In docstrings:** `Source: <author or body> (<year>), <document>, Eq. <n> / Table <n> / Fig. <n> / p. <n>`. Always the edition or year and the equation, table, figure or page.
- **Bibliography:** `docs/reference/sources.md` (created 2026-11-04, M2 (b)), one entry per source, with its short key and the date it was verified.
- **Never cite from memory** (decided, skill rule). An unverified citation is marked 🔬 and tracked in `docs/TODO.md`.
- **Published text cites only what a reader can follow** (decided 2026-11-10, TODO #19): docstrings, assumptions, sources, caveats and messages, the docs site and the README never refer to this spec, the TODO list, a milestone or a unit's decisions. A derivation garisenda makes is stated in the docstring as its own, not cited. Comments may keep internal references. `tests/test_published_text.py` checks every string literal in the package.

### 2.3 Conflicts between sources
- 🟡 The unit's spec says which source governs and why. Where practice uses more than one method (trough width, subsurface movement, soil–pipe interaction), **the method is a required argument** (§4). garisenda doesn't pick between methods silently.
- **Digitized charts are not shipped** (decided 2026-10-31): they can't be verified to the source's precision and their copyright is unclear. A method that exists only as a chart is either replaced by its closed form or supplied by the user as their own table, recorded as such on the result.

### 2.4 Verification
- **Golden values** come from a worked example in the source, or a hand calculation written out in the unit's spec with its inputs, steps and source. Never from running the code.
- 🟡 **Tolerance:** 0.5 % relative by default. A test that needs another states why (a value read from a chart, a source that rounds).
- 🟡 **Analytical derivatives are checked against finite differences** of the same field, and discrete strains against analytical ones on a smooth field (§7).

### 2.5 Validity limits
- 🟡 **Outside a method's range, the result is flagged, not raised** (§5.2). An assessment along a long utility needs every point's result, including the ones that need numerical analysis. garisenda raises only for inputs that are physically impossible or inconsistent (a negative diameter, a utility below its own tunnel's invert when the method assumes otherwise).
- The limits for each method, and what counts as "marginal", are in its spec and docstring, with their source.
- **The building damage check is `outside` where z_f/z₀ ≥ 0.2** for any tunnel (decided 2026-11-10, M4 (a)), with z_f the foundation depth and z₀ the axis depth, after Harris & Franzius (2006) as reported by Jones (2022, p. 490) (🔬, TODO #7). Their reason (the surface trough) is removed by taking the trough at foundation level, but basements and piles still change what following it means, so the limit stays. Below it, a `within` flag says the method states no range of its own. A wall wholly beyond the cut-off has no zone, reported with a `within` flag, never dropped.
- **The subsurface trough applies only above the tunnel crown** (decided 2026-11-04, M2 (b); Bracegirdle et al. 1996, p. 660). A point deeper than the crown and outside the bore is `outside` and gets the trough at crown level, with depth derivatives zero, so every point still has a value; the same limit is applied to the linear width method by garisenda's choice. No `marginal` band: no source gives one.

## 3. Architecture: sources and assessments

- **Sources produce a movement field; assessments consume it** (decided 2026-10-31). A source is anything that causes ground movement (a tunnel, later an excavation). An assessment is anything affected by it (a utility, a building).
- **Assessments consume a profile along the asset** (decided 2026-11-01): stations at distances along the asset, and at each station the displacement along the asset, across it (vertical and lateral), and their exact derivatives with respect to distance along the asset. This is the boundary every source produces and every assessment consumes, so the transverse trough and the 3D field are interchangeable to the assessments, their results and their figures.
- **A closed-form source is a function, not a grid** (decided 2026-11-01). The profile is built by evaluating the source at the asset's stations. A grid is evaluated only to draw a figure, never for a calculation.
- **One analysis, always in 3D** (decided 2026-11-01). However the geometry was entered (§8.3), every asset is a 3D polyline and every tunnel a 3D alignment by the time the analysis sees them. There is no separate section analysis.
- **The source interface** (decided 2026-11-02, M1 (a), [`docs/work/m1a-transverse-trough.md`](docs/work/m1a-transverse-trough.md)): given points (x, y, depth), with depth positive downward so settlement has the sign of the vertical coordinate, `source.evaluate()` returns plain SI arrays: the displacement (x, y, settlement), its gradient, its Hessian and its third derivative (added in M2 (a), for the peaks of curvature), a verdict per point and the flags. Derivatives that are zero for a source (with respect to depth for the surface trough) are returned as exact zeros, not left out, so a source that adds them (M2) changes nothing downstream. A source also carries its input records, methods and assumptions for the result, and gives, for a straight segment, the distances along it where its quantities peak or change sign (`critical_distances()`, decided 2026-11-03, M1 (b)), so the profile never misses a peak between stations, and the length over which its field changes along a segment (`feature_length()`, decided 2026-11-03, M2 (a)), to tie a sampling interval to. It also gives the range of a segment within a multiple of the trough width i of each transverse trough's axis in plan (`trough_extent(start=, end=, multiple=)`, decided 2026-11-10, M4 (a), for a building's cut-off), with i at the segment's depth; a trough at depth gives it only on a level segment, and a superposition gives the hull of its sources' ranges, so the ground between two tunnels is kept.
- **The profile** (decided 2026-11-03, M1 (b), [`docs/work/m1b-movement-profile.md`](docs/work/m1b-movement-profile.md)) resolves the source onto the asset at stations: its ends, the source's critical distances and every `spacing` between, a required judgment. Columns `along`, `vertical` and `lateral` (along positive toward increasing distance, vertical positive downward, lateral positive to the right looking along the asset, as offset is), with `along_strain`, `along_strain_gradient`, `vertical_slope`, `vertical_curvature`, `lateral_slope` and `lateral_curvature`, the exact derivatives with respect to distance. Reversing an asset changes the sign of along, the slopes and `along_strain_gradient` (derivatives of odd order in distance), not of the strains or curvatures. `gs.movement_profile(asset, source, *, spacing)` returns it as a `Result` (§5.1), along a utility's axis or a building's wall at its foundation level (decided 2026-11-10, M4 (a), [`docs/work/m4a-building-damage.md`](docs/work/m4a-building-damage.md)); it is the ground's movement, so it takes no `interaction`, which applies to the asset's response (M3).
- **The transverse trough at depth** (decided 2026-11-04, M2 (b), [`docs/work/m2b-subsurface.md`](docs/work/m2b-subsurface.md)): `gs.sources.transverse_trough(tunnel, *, volume_loss, trough_width)`, where the width method is a required judgment, `gs.sources.mair_trough_width()` (clay; Mair & Taylor 1997, after Mair et al. 1993) or `gs.sources.linear_trough_width(trough_width_parameter=k)`. Both give i(z) = c₀ z₀ + c₁ (z₀ − z), the same volume V_L A at every depth, and horizontal movement from constant volume, u_n = −c₁ (o/i) S, toward a point (c₀/c₁) z₀ below the axis (Taylor 1995). Its derivatives with respect to depth are nonzero and exact, and it finds its critical distances by root-finding, since i varies along a segment that changes depth. M1's `transverse_surface_trough` stays, and the linear method at z = 0 equals it.
- 🟡 **The transverse trough is a 2D source placed in 3D:** it is applied perpendicular to each tunnel segment and assumes the segment is long and straight. Stations near a real alignment's end, a curve, or a run parallel to the tunnel are flagged (M5). An idealized straight tunnel has none of these, and the result records that it was idealized (§1.3). The 3D field (M6) adds the longitudinal trough.
- **Several sources combine by superposition** (decided 2026-11-03, M2 (a), [`docs/work/m2a-several-tunnels.md`](docs/work/m2a-several-tunnels.md)): `gs.superpose(north=..., south=...)` returns a source whose movement and derivatives are the sums of its sources' and whose verdict is the worst of theirs, recorded on the result as an assumption, with interaction between tunnels not modeled. Each source's inputs and flags are named for it (`north.volume_loss`). Inputs that disagree (two ground elevations, overlapping bores) raise. Its critical distances are found by root-finding on the exact derivatives along the segment, not taken from its sources: two overlapping troughs peak between their axes. Any number of sources, idealized or real.
- **Closed-form sources return exact derivatives** (decided 2026-11-06, M3 (a), [`docs/work/m3a-continuous-pipes.md`](docs/work/m3a-continuous-pipes.md)). Assessments use them for analytical strain, and evaluate the source at points of their own only to sample it at the discrete interval for discrete strain and to find the peaks of their own quantities (resultant curvature, combined strain), which aren't among the source's critical distances (§7). No spline is fitted to an analytical field. A spline is needed only for movements given as data (a numerical model's output, survey data), which comes later.
- 🟡 **Where a polyline bends**, the asset's own curvature adds terms to the strains along it; the profile accounts for them, and a vertex sharper than a limit set in M5's spec is flagged.

## 4. Inputs

Every input to a calculation is one of these kinds, treated differently because each goes wrong in a different way.

| Kind | Examples | Rule |
|---|---|---|
| **Ground parameter** | Soil modulus, trough width parameter where it is measured | Required argument. No default. |
| **Design judgment** | Volume loss, trough width method, soil–structure interaction (greenfield in Phase 1), allowable strain, pullout and rotation limits, pipe lengths, building properties for the damage method, discrete strain interval | Required, keyword-only argument. **No default** (decided). |
| **Constant or setting** | Gaussian volume factor, unit conversions | Defaulted, documented, overridable. Recorded on the result. |
| **Geometry** (decided 2026-11-02, M1 (a)) | Tunnel reference point, direction, depth and diameter; asset coordinates | Data, not a judgment: required where the calculation can't do without it, recorded on the result. A default only where it's a convention, not a guess (the station at an idealized tunnel's reference point is 0 unless given). |

- **No judgment has a default.** A missing judgment is an error that names it, says what it depends on, and how to set it.
- **Presets are opt-in** (decided 2026-10-31). Where practice has standard values (nominal pipe lengths, published limits), garisenda can ship them as **named, cited presets** the user passes explicitly, for example `pipe_lengths=gs.presets.<name>`. A preset is a choice someone made, recorded on the result by name and source. It is never applied without being asked for.
- **The first presets** (decided 2026-11-06, M3 (b), [`docs/work/m3b-jointed-pipes.md`](docs/work/m3b-jointed-pipes.md)) live in `gs.presets`: `cast_iron_joint_limits(*, joint)` (Bracegirdle et al. 1996, Table 2, after Attewell et al. 1986), `iron_strain_limits(*, material)` (Table 4) and `grey_iron_tensile_strain_limit(*, diameter, situation)` (p. 662, after Herbert & Leach 1990). A preset's row is a required keyword, and an unknown row is an error listing the rows. Each value is a `gs.presets.Preset`, a `Sourced` that also carries caveats: its source names the preset call, the row, the paper, the table or page and whom the paper quotes, and a check adds the caveats of every preset among its inputs to the result's assumptions, once each. No pipe length preset yet (TODO #5).
- **Building presets** (decided 2026-11-10, M4 (a), [`docs/work/m4a-building-damage.md`](docs/work/m4a-building-damage.md)): `youngs_to_shear_modulus_ratio(*, structure)` (`"masonry"` 2.6, p. 716; `"framed"` 12.5, §4.5, p. 717), `damage_categories()` (Table 2, p. 715, after Boscardin & Cording 1989; a boundary strain falls in the lower band) and `preliminary_assessment_limits()` (10 mm and 1/500 as 2 mm/m, §5.2, p. 717), all from Mair, Taylor & Burland (1996), each with caveats naming whom the paper quotes.
- **Limits are project-specific judgments with literature provenance** (decided 2026-10-31). Each limit is given with its value and where it came from; a preset of limits from a published source is allowed under the rule above.
- **Soil–structure interaction is a judgment** (decided 2026-10-31; revised 2026-11-01). Greenfield (no reduction) has to be chosen explicitly, like any other value, so adding methods later doesn't change existing calls. 🟡 Named `interaction`, keyword-only; Phase 1 accepts only `"greenfield"`. A single reduction factor is not accepted (§1.3).
- **Provenance is optional on input and always kept on output** (decided 2026-11-02, M1 (a)). An argument can be a plain value or `gs.Sourced(value, source=...)`. Either way the result records the value used, its kind, how it was given, and its source when one was given.
- **The missing-judgment error** (decided 2026-11-02) comes from a decorator that holds, for each judgment, what it depends on and how to set it; the judgments stay required keyword-only arguments in the signature, never a sentinel default (M1 (a)).

## 5. Results

### 5.1 One result shape
Every analysis returns a `gs.Result` with the same parts (decided 2026-11-03, M1 (b); exact names in [`docs/work/m1b-movement-profile.md`](docs/work/m1b-movement-profile.md)):
- **values:** the computed quantities, with units. For an asset, a table **keyed by distance along the asset** (decided 2026-11-01), with the x, y, z of each station as extra columns, and the station and offset relative to the reference tunnel for an asset built from them (§8.3);
- **checks:** each quantity against its limit, with the utilization and the governing location; for the utility checks, the analytical and discrete values, their difference and which governed (decided 2026-11-06, M3 (a)); for a jointed pipe, joint rotation and pullout after the barrel's checks, as discrete values only, since a joint exists only at a spacing (decided 2026-11-06, M3 (b)); two nullable integer columns, `zone` and `category`, are NA except on a building check's zone and damage-category rows (decided 2026-11-10, M4 (a), [`docs/work/m4a-building-damage.md`](docs/work/m4a-building-damage.md));
- **zones:** a building check's zones of hogging and sagging, one row per zone (its ends, Δ, Δ/L, the strains, the category), empty with its columns for every other analysis (decided 2026-11-10, M4 (a));
- **method:** the methods, their sources and the equations used;
- **assumptions:** what the method assumes and garisenda can't check, such as the Phase 1 assumptions (§1.3) and superposition (§3);
- **inputs:** every input used, with its kind and source (§4); a value is a quantity, or for a named method (a trough width method) its name (decided 2026-11-04, M2 (b)). No two share a name (decided 2026-11-10, TODO #22): the asset's are named for it (`utility.diameter`, `building.height`), a superposition's for each source (`north.diameter`), and a single source's, the check's and the profile's settings keep their own names;
- **validity:** the verdict (§5.2), with the limit that set it;
- **warnings:** everything that was flagged.

**Governing values** (decided 2026-11-03, M1 (c), [`docs/work/m1c-figures-sweep-docs.md`](docs/work/m1c-figures-sweep-docs.md)): `Result.governing()` tabulates the extremes of `values` (settlement, tension and compression along, hogging and sagging), each with its distance and verdict; a sign with no value is NaN, never zero. The summary, `gs.sweep` and the figures read it, so they agree. A result also keeps its source and asset (a `Utility` or a `Building`), and a building check its damage categories (decided 2026-11-10, M4 (b)), outside the views, so a figure can draw what the table doesn't hold.

**One calculation, many views** (decided 2026-11-03, M1 (b)): `.to_dict()` (JSON-ready), `.to_frame()`, a short text summary as its `repr()`, as in hangtu, and the figures (§9). Views never recalculate, so two views can't disagree.

### 5.2 Validity verdict
🟡 Each result has one of three verdicts, the worst over its checks, inputs and locations:
- **`within`:** every input is inside the method's stated range.
- **`marginal`:** within range but near a limit, by a margin set in the method's spec.
- **`outside`:** at least one input or location outside the range. The result is still computed, and says which input, where, and which limit. **This is the flag for numerical analysis.**

Pass/fail on a check is separate from validity.

### 5.3 Sensitivity runs
**Every calculation can be run over arrays of one to three of its inputs** (decided 2026-11-03) with one function, `gs.sweep(run, *, vary={name: array, ...}, mode="grid" | "paired")` (M1 (c), [`docs/work/m1c-figures-sweep-docs.md`](docs/work/m1c-figures-sweep-docs.md)), where `run` is the user's function from those inputs to a `Result`: the inputs worth varying belong to the source, upstream of the analysis, and a function keeps every step visible. It returns a tidy table: one row per run, with the varied inputs as used, the governing values (§5.1), each check's utilization, pass/fail and the verdict. Fixed inputs are recorded once in `df.attrs`. Each varied value must reach the run's input records, and inputs not varied must not change between runs, or `sweep` raises. `mode` is required with two or more inputs. A run that raises records the error in its row. So every analysis is a pure function of its arguments, with no hidden state and no file reading. Volume loss and the trough width parameter are the obvious inputs to vary. An input named for its source (`"south.volume_loss"`, M2 (a)) is passed to `run` with its dots as underscores (`south_volume_loss`; decided 2026-11-03), and so is a utility's (`"utility.depth"` as `utility_depth`; decided 2026-11-10).

## 6. Units
- 🟡 **SI is the preferred system:** m, mm, kPa, MPa. Strain is dimensionless and reported in microstrain or percent only in views; so is a slope, shown in mm/m (decided 2026-11-10, M4 (b)).
- **Never guess a unit.**
- 🟡 **Pint first:** a scalar input is a pint quantity, and docs and examples write inputs that way. **A plain float is accepted and read as the documented SI unit**, and the result's input echo records which it was.
- **Except where a plain number is ambiguous** (decided 2026-11-02, M1 (a)): an input that practice writes as a percentage (volume loss, strain limits) and an angle must be pint quantities, because `0.5` could be 0.5 % or 50 % and `30` could be degrees or radians. A plain number is an error that names the argument and shows how to write it. One registry, `gs.units`, serves the process.
- DataFrames carry units in `df.attrs["units"]`. **Units never appear in names** (`depth`, not `depth_m`).
- 🟡 Pipe diameters given in nominal inches are accepted as pint quantities; a preset keyed by nominal size says so in its name and docs.

## 7. Utility checks
- **Every check is run by default and all are reported** (decided 2026-10-31): axial strain, bending strain, combined strain (tension and compression), radius of curvature, and for jointed pipes, joint pullout and joint rotation. A check is skipped only when its limit isn't relevant to the pipe type, and the result says so.
- **Discrete and analytical strain are both computed and compared** (decided 2026-10-31). Analytical strain comes from the field's exact derivatives. Discrete strain comes from movements sampled at an interval, as is common in practice. The result reports both and the difference between them, and **the worse of the two governs** (decided 2026-11-06, M3 (a), [`docs/work/m3a-continuous-pipes.md`](docs/work/m3a-continuous-pipes.md)).
- **The discrete interval is a required judgment, with no default** (decided 2026-11-06, M3 (a)) for continuous pipes; the docs use 1 m. For jointed pipes it is the pipe length.
- **The checks are mechanics** (decided 2026-11-06, M3 (a)): strain as change in length over original length, bending strain y/R at the outermost fiber, the radius through three points, axial plus bending strain, derived in the unit's spec, not cited. The pipe follows the ground (§1.3). **Utilities are circular.**
- **Combined strain never counts axial strain as helping** (decided 2026-11-06, M3 (a)): tensile strain is max(axial, 0) plus bending, compressive strain min(axial, 0) minus bending.
- **Pipe lengths are a table keyed by pipe type and diameter** (decided 2026-10-31), supplied by the user or from an opt-in preset (§4). A type and diameter pair that isn't in the table is an error that names it, never filled from the nearest diameter. The result records the length used for each pipe and its source.
- **Joint position is the worst case** over every possible position along the pipe (decided 2026-10-31), unless joint locations are given. Given joint locations wait for M5, which loads utilities with attributes; until then the worst position is the only one (decided 2026-11-06, M3 (b)).
- 🟡 **Bending uses movement across the pipe and axial strain uses movement along it**, both taken from the profile (§3). Bending is reported in both planes, vertical and lateral, and as their resultant, and **checked on the resultant** (decided 2026-11-06, M3 (a)): for a circular section the peak fiber strain comes from the resultant curvature. For an asset built perpendicular to a straight tunnel, lateral bending comes out as zero from the calculation, not by assumption.
- **The continuous-pipe check** (decided 2026-11-06, M3 (a), [`docs/work/m3a-continuous-pipes.md`](docs/work/m3a-continuous-pipes.md)): `gs.check_continuous_pipe(profile, *, interval, interaction, tensile_strain_limit, compressive_strain_limit, bending_strain_limit, radius_of_curvature_limit)`, on a movement profile. Each limit is required and may be given as `None`, which reports that check without a utilization. **A limit may be zero** (decided 2026-11-06, M3 (b), [`docs/work/m3b-jointed-pipes.md`](docs/work/m3b-jointed-pipes.md)), for every check: nothing is allowed, so a nonzero value has utilization ∞ and fails, and a zero value passes; a negative limit is an error. Discrete strain is centered on each station: axial strain over a span of the interval, curvature as the second difference over three points an interval apart, independent of the profile's spacing. A station within that reach of an end has no discrete value, flagged (§10). The check adds stations at the peaks of resultant curvature and combined strain.
- **The jointed-pipe check** (decided 2026-11-06, M3 (b), [`docs/work/m3b-jointed-pipes.md`](docs/work/m3b-jointed-pipes.md)): `gs.check_jointed_pipe(profile, *, pipe_lengths, pipe_type, interaction, joint_rotation_limit, joint_pullout_limit, tensile_strain_limit, compressive_strain_limit, bending_strain_limit, radius_of_curvature_limit)`. `pipe_lengths` is a mapping `{(pipe_type, outside_diameter): length}`, or a `Sourced` one, matched within 1 µm; `pipe_type` is a design judgment, not carried by the utility. The rotation limit is an angle and refuses a plain number. The joint geometry is garisenda's own, derived in the unit's spec, not cited (§1.3):
  - **Rotation** at a joint at s, between the chords to its neighbors at s ± L: θ_v = (w(s + L) − 2w(s) + w(s − L))/L, likewise θ_l, checked on the resultant θ. This is L times the discrete curvature at interval L.
  - **Pullout** is the opening between the pipes centered at s ± L/2: Δ = u_a(s + L/2) − u_a(s − L/2), checked on its largest positive value. This is L times the discrete axial strain at interval L. The openings along a run sum to the ground's stretch.
  - **The outer opening Δ + rθ and the largest closure are reported, not checked:** Table 2 limits rotation and pullout separately, and gives no limit for closure.
  - **The barrel** is the continuous-pipe check at interval L, over every row, so its discrete columns and the joint columns are one calculation.
  - **The worst joint is found exactly,** at the zeros of d(θ²)/ds and dΔ/ds from the source's derivatives, and at the ends of each feasible range (s ∈ [L, ℓ − L] for rotation, [L/2, ℓ − L/2] for opening). Outside them a joint would have a neighbor beyond the pipe: no value, flagged. A pipe too short for any joint position leaves that check undetermined (NaN, `passes` NA), never a pass.

## 8. Conventions

### 8.1 Coordinates and signs
- **One flat coordinate system and one length unit** for every table in a site (decided 2026-10-31). No datum or projection is recorded in Phase 1; if figures need a datum label, an optional label is added to the site then.
- **Plan direction** (decided 2026-11-02, M1 (a)) is an azimuth clockwise from the +y axis (a bearing when +y is north), for idealized tunnels and alignments alike.
- 🟡 **Station and offset:** station is distance along a tunnel's alignment in plan, from its first point (or from the reference point of an idealized tunnel). Offset is horizontal and perpendicular to the alignment in plan, positive to the right looking in the direction of increasing station.
- 🟡 **Settlement is positive downward.** Displacements returned by a source are global components (x, y and vertical), so they add across sources.
- 🟡 **Tensile strain is positive.**
- **Horizontal movement is positive to the right in every view** (decided 2026-11-03, M1 (c)): in a transverse section, toward increasing offset. The literature's convention, positive toward the tunnel centerline, isn't used: it kinks at the axis and differs from the one the rest of garisenda uses.
- 🟡 **Depth is positive downward** from the ground surface.

### 8.2 Ground surface
- **Phase 1: a single ground elevation, or depth only** (decided 2026-10-31). The ground surface becomes its own geometry in a later phase.
- 🟡 Each geometry table gives **either** an `elevation` column **or** a `depth` column, and the column name says which. Elevations need the ground elevation to convert, given on the `Site` (§8.4) or as an argument; an analysis that uses depths only never sets one. Nothing is converted by assumption.

### 8.3 Geometry tables
Every table describes 3D geometry. Station-and-offset input is a way of building it, not a separate kind of table.

**Tunnels:**
- 🟡 **A real alignment:** an ordered table of points (x, y, and elevation or depth of the axis) with a diameter, so it is a set of straight segments with known ends and stationing.
- 🟡 **An idealized straight tunnel** (decided 2026-11-01): a reference point (x, y), a plan direction, the axis depth or elevation, and a diameter, with no ends. It is the tunnel of a traditional assessment, and the result records that it was idealized.
- **Several tunnels** (decided 2026-11-03): each is its own alignment or idealized tunnel, with its own trough. For spreadsheet-style input, a twin tunnel is built with `tunnel.parallel(offset=..., diameter=..., axis_depth=...)` (M2 (a)): parallel at a plan offset, with stationing aligned, and its depth and diameter given again, never copied. Station and offset stay relative to the asset's reference tunnel.

**Utilities and buildings, loaded as polylines:**
- **Utilities are x, y, z tables** (decided 2026-10-31): one row per vertex, keyed by `utility_id`, with a pipe type, diameter and material.
- **Buildings are polylines** (decided 2026-10-31; revised 2026-11-01): a vertex table (`building_id`, vertex order, x, y) and a building table (height, foundation level, building properties as judgments). An open polyline is a single wall; a closed one is a footprint, and its edges are the walls.

**Utilities and buildings, built from station and offset** (decided 2026-11-01):
- Given a reference tunnel, a station, start and end offsets, and a depth or elevation, a builder returns a straight polyline perpendicular to the tunnel at that station: a `Utility` (decided 2026-11-03, M1 (b)), the same object M5's table loaders will return, so the table form is decided there. A utility takes its diameter, and 🟡 its pipe type and material from M3, where they are first used; a building its height, foundation level and properties. A building may straddle the tunnel.
- **A building is a wall** (decided 2026-11-10, M4 (a), [`docs/work/m4a-building-damage.md`](docs/work/m4a-building-damage.md)): `gs.buildings.Building(*, building_id, vertices, foundation_depth, height)`, two plan points, level at its foundation depth (≥ 0), with H from foundation level to the eaves. `gs.buildings.perpendicular_building(tunnel, *, building_id, station, start_offset, end_offset, height, foundation_depth=None, foundation_elevation=None, ground_elevation=None)` builds one as `perpendicular_utility` does, its level given by exactly one of the depth or the elevation with the ground elevation; it has no elevation reference, since a wall has no section. Its inputs are recorded as `building.<name>`. Stepped foundations come with polylines (M5).
- **The builder records how the asset was built** (reference tunnel, station, "perpendicular"), and the result carries it as an assumption (§1.3; decided 2026-11-03, M1 (b)). The builder is named for what it builds (perpendicular), so skewed assets come later as their own builder and existing calls don't change; perpendicularity is never an unstated default.
- 🟡 **At a vertex of a real alignment** the perpendicular is ambiguous, so the builder raises an error naming the vertex and the station; it never picks a side.
- 🟡 **A built asset whose ends fall where the trough is still significant is flagged**, because strains beyond its ends aren't checked. The margin that counts as significant is set in M3's spec.

**Both:**
- **A utility's elevation reference is a required argument** (decided 2026-11-03, M1 (b)) (`"invert"`, `"axis"` or `"crown"`), converted to the axis using the diameter. Survey data comes in all three, and a wrong guess shifts the pipe by its diameter. The conversion uses D/2 and ignores the wall thickness, recorded as an assumption (M1 (b)).

### 8.4 The site
- **A thin `Site` bundle** (decided 2026-10-31) holds the tables for one assessment: the ground surface (§8.2), tunnels, utilities and buildings. It validates that they are consistent (units, one of depth or elevation) and carries them together. It does no analysis; the analyses stay plain functions that can also take the tables directly.

### 8.5 Naming and API
- **Plain functions on plain data**; keep objects thin.
- **Names are written out in full** (`volume_loss`, not `vl`; `trough_width_parameter`, not `k`). Symbols belong in docstrings and labels.
- **Judgment arguments are keyword-only.**
- **Error messages** say what is wrong, where, and what to do.
- **A public calculation's docstring is its reference entry:** equation, inputs and outputs with units, validity range, assumptions, source.
- American spelling.

## 9. Figures
- **Figures are part of every assessment** (decided 2026-10-31): they are needed for the deliverable in every case, and are the fastest check that a result is sensible.
- **One plot contract** (decided 2026-11-03, M1 (c)): `gs.plot.<name>(result, *, ax=None, display_units=None) -> (fig, ax)`, using matplotlib; a multi-panel figure takes `axs=` and returns `(fig, axs)`, as `plt.subplots` does. Styling is applied in a context, never as global state. A figure draws from the result and never recalculates the result's values; it may evaluate the result's source on a grid to draw the field (§3). Display units are given per kind of quantity (length, displacement, strain, curvature, angle, slope), defaulting to m, mm, microstrain, 1/km, degrees and mm/m (slope decided 2026-11-10, M4 (b)), and every axis label states its unit. Flagged stations are marked on every figure, with each flag's reason under it (§10).
- **Each milestone ships the figures for what it builds** (decided 2026-11-03; M1 (c) shipped the profile and the cross-section). The core figure of Phase 1 is the profile along an asset: movement, strain and each check against its limit, plotted against distance along the asset, with flagged locations marked. Alongside it: a plan of the tunnels and assets with flagged stations marked, and, for an asset built from station and offset, the cross-section at that station (tunnels, trough and asset in place), the figure of a traditional assessment. For a utility check (decided 2026-11-06, M3 (a)) the profile adds axial, bending and combined strain, and the curvature panel carries the radius limit as 1/R; analytical values are solid, discrete dashed, and each limit is a line. For a jointed pipe (decided 2026-11-06, M3 (b)) it adds joint rotation, in degrees, and joint opening, each with its limit, and marks the largest closure, which isn't checked; the barrel's discrete values are at the pipe length. Display units gain angle, defaulting to degrees. A building check's profile (decided 2026-11-10, M4 (b)) is drawn in five panels against distance along the wall at its foundation level: settlement, with each zone's chord dashed and the deflection between them filled; the deflection from the chord, with each zone's Δ and Δ/L; the slope; the horizontal strain, with each zone's ε_h; and each zone's tensile strains on the damage categories' bands, with the acceptable category's limit. Its movement panels show the trough at the utility's depth, and say which depth (decided 2026-11-04, M2 (b)); a source with only a surface trough is drawn and labeled at the surface, since that is what it gives at any depth. With several tunnels (decided 2026-11-03, M2 (a)) it draws each tunnel parallel to the reference tunnel, the combined trough and each tunnel's own, each dashed differently; a tunnel that isn't parallel is named in a note and left to the plan figure.
- Figures are checked by eye at close-out, not only by tests.

## 10. Data quality
- **Never drop data silently.** A point, pipe or facade that can't be computed is reported in the result with the reason, not skipped.
- **Never fill missing data.** A building without a height or a pipe without a diameter is an error or a flag, never a guessed value.

## 11. Testing
- pytest; golden values per §2.4; behavior at and beyond each validity limit is tested.
- 🟡 Property-based tests (hypothesis) for physics that must hold: the Gaussian trough's volume equals the volume loss times the tunnel area; settlement is symmetric about the axis; strains are exact derivatives of the field.
- 🟡 Every analysis has a test that a `gs.sweep` row equals a direct call with the same inputs (§5.3).
- **Hand calculations run through the one analysis** (decided 2026-11-03, M1 (b)): golden values written as 2D cross-section calculations are checked through station-and-offset input, so the traditional case tests the same code as every other. The builders are tested on their own: an asset built at a station is the right polyline, perpendicular, with its provenance recorded.
- **No project data in tests.** Real crossings are reproduced locally on the work machine, not in the repo; tests use invented geometry.

## 12. Engineering

### 12.1 Environment and distribution
- **Python ≥ 3.12** and `uv` (decided 2026-11-02, M0). CI on Windows, macOS and Linux × Python 3.12–3.14, with a job on the oldest allowed dependency versions.
- **Tooling follows hangtu**, the author's other library, so the two work the same way (decided 2026-11-02, M0): `uv_build`; the version only in `pyproject.toml`; ruff for lint and format, with numpy-convention docstring checks on `src/`; strict pytest with **warnings as errors**, so a stray warning fails the run and an expected one is asserted. **One deliberate difference: mypy in strict mode on `src/`**, because the judgment arguments (§4) and the result shape (§5.1) are contracts across modules. A `# type: ignore` names the error code and says why.
- **Dependencies** (decided 2026-11-03, M1 (c)): `pint`, `numpy`, `pandas`, `matplotlib` (`>=3.8`, hangtu's floor), each with a floor proven in CI, added when code first uses them. The docs tools are a `docs` dependency group, not runtime dependencies. Adding another needs a decision here.
- MIT license.
- **Release to PyPI on a `v*` tag** (decided 2026-11-02, M0), with trusted publishing (`release.yml`): the tag must match the version in `pyproject.toml`, and the tests run against the built wheel on all three operating systems before upload. A manual run publishes to TestPyPI instead, as a rehearsal.

### 12.2 Package layout
- 🟡 `src/` layout, package `garisenda`, tests mirroring the package. Modules by role: `garisenda.sources` (movement fields), `garisenda.profile` (the profile along an asset, §3), `garisenda.utilities`, `garisenda.buildings`, `garisenda.site`, `garisenda.plot` (figures, §9), `garisenda.presets`; `gs.sweep` at the top level (§5.3).

### 12.3 Docs
- **Docs are written as we go** (decided 2026-11-03, M1 (c)): each milestone's close-out writes the user docs for what it built. The docs site (Zensical, with the API reference from docstrings) is set up as hangtu's is: pages in `docs/site/` (the rest of `docs/` is internal), each page's example a script run before the build so every figure comes from code that runs, a `--strict` build in CI, published to GitHub Pages from `main`, and a test that every public name has a reference entry.

### 12.4 Milestones (Phase 1)
Revised 2026-11-01: spreadsheet-style input first (M1–M4), which replaces the spreadsheet, then real geometry (M5–M6). The analysis is the same throughout (§3).

| ID | Scope | Done when |
|---|---|---|
| M0 | Scaffolding: package, lint, tests, CI | CI green |
| M1 | In three units (decided 2026-11-02): (a) units, the input rules, the idealized straight tunnel, the source interface (§3) and the transverse surface trough with horizontal movement, from a given k; (b) the station-and-offset builder for a utility line, the profile along an asset (§3), the result shape and verdict; (c) the first figures (cross-section and profile), `gs.sweep`, the docs site and M1's user docs | Golden values from verified sources and hand calculations; strains are exact derivatives; profile keyed by distance along the asset; builder tested; figures checked by eye. **Done 2026-11-03**, with the trough's sources still unverified (TODO #2) |
| M2 | In two units (decided 2026-11-03): (a) several tunnels by superposition, the parallel-tunnel builder, critical distances by root-finding, the cross-section with several tunnels; (b) movements below the surface | (a): golden values for twin tunnels from hand calculations; critical distances tested against dense sampling; superposition and per-tunnel inputs recorded; figures checked by eye. **(a) done 2026-11-03.** (b): golden values from the verified subsurface method; depth validity flags tested. **(b), and so M2, done 2026-11-04** |
| M3 | Utility checks, greenfield, in two units (decided 2026-11-06): (a) continuous pipes: axial, bending (both planes and resultant) and combined strain, radius of curvature, each analytical and discrete; (b) jointed pipes: pipe length tables, joint rotation and pullout at the worst joint position, opt-in limit presets for iron pipes | Golden values from hand calculations of the mechanics and from Bracegirdle et al. (1996)'s closed forms; each check against its limit; the profile figure shows every check; a real crossing compared with the spreadsheet locally, with every difference explained. **The spreadsheet is replaced for utilities.** **(a) done 2026-11-06. (b), and so M3, done 2026-11-06**, without the spreadsheet comparison: dropped (2026-11-06) because the spreadsheet isn't trusted as a reference. Checking a real crossing another way is TODO #14 |
| M4 | Buildings, greenfield, in two units (decided 2026-11-10): (a) walls built from station and offset, and the staged damage check (Stage 1's settlement and slope; zones, deflection ratio, horizontal strain, beam strains and damage category), with the cut-off and presets; (b) the building figures and user docs | Golden values from hand calculations of the damage method and Jones (2022)'s worked example; hogging and sagging split tested, including a building straddling a tunnel and twin tunnels; building figures. **The spreadsheet is replaced for buildings.** **(a) done 2026-11-10**, from Mair, Taylor & Burland (1996) with the originals still 🔬 (TODO #7). (b) is next |
| M5 | Real geometry: tunnel alignments as segments with stationing, utilities and buildings loaded as polylines (footprints included), the `Site` (§8.4), the trough per segment, the builders on real alignments, the plan figure | Flags for ends, curves, parallel runs and sharp vertices tested; a polyline loaded as a straight perpendicular line matches the same asset built from station and offset; a real alignment reproduced locally |
| M6 | The 3D field (longitudinal trough) | Matches the transverse trough far from the face; volume conserved; parallel runs assessed rather than only flagged |

🟡 M4 depends only on M2, so it can go before M3 if that's more useful. If M3 or M5 is too big for one unit, it splits (continuous then jointed pipes; utilities then buildings).

## 13. Open questions
1. ❓ **Are closed-form relative-stiffness methods added before the beam on springs** (§1.3), inside their stated range and flagged outside it? Decide after Phase 1's greenfield work and the literature review (TODO #1). The beam on springs itself is decided as the intended approach, in a later phase. Until then, the result says greenfield and that soil–structure interaction would reduce the strains.
2. ❓ **Which subsurface method for granular soil** (TODO #3)? Decided for M2 (b) (2026-11-04): Mair et al. (1993)'s method for clay, as stated in Mair & Taylor (1997), and a width at depth i = k (z₀ − z) from a k the user gives, recorded as their choice (§3). A granular-specific method comes later, as may New & Bowers (1994) for movements close to the tunnel, below the crown.
3. **Does the discrete check govern, the analytical one, or the larger of the two** (§7)? Decided 2026-11-06 (M3 (a)): the worse of the two.
4. **Where is a building wall's movement taken**: at the ground surface or at its foundation level (a subsurface trough)? Decided 2026-11-10 (M4 (a)): at foundation level, from the source evaluated at the foundation depth, which is geometry the builder requires; a depth of 0 gives the surface trough. Stage 1 uses the same trough (§1.3).
