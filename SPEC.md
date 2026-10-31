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

**Phase 1: greenfield assessment (decided 2026-10-31).** A greenfield assessment of individual utilities and structures for one or more tunnels, with closed-form and empirical methods and figures for every result. Chosen over starting with the 3D movement field because it gives useful output, and feedback, soonest. The movement-field interface (§3) is designed for 3D from the start, so Phase 1 doesn't have to be redone.

| Area | Phase 1 content |
|---|---|
| **Tunnel movements, transverse** | Steady-state Gaussian trough at the surface and below it; trough width from a given k or a named method; horizontal movements; several tunnels by superposition |
| **Tunnel movements, 3D** | Longitudinal trough and the 3D field (M5), checked against the transverse trough far from the face |
| **Real geometry** | Tunnel alignments and utilities as 3D polylines; movements and strains along a utility; flags for tunnel ends, curves and runs parallel to a tunnel |
| **Utilities** | Continuous pipes (welded steel, HDPE, PVC, HDD-installed) and jointed pipes (cast iron, ductile iron, clay, concrete); axial and bending strain, joint pullout and rotation; discrete and analytical strain, both computed and compared (§7) |
| **Soil–pipe interaction** | Factors given as numbers with a reason, then named methods from a literature review (M4b) |
| **Buildings** | Footprints entered by hand; deflection ratio and horizontal strain per facade; damage category (M6) |

**Later phases** (held in `docs/drafts/` when they start):
- Ground surface as its own geometry (a surface table), replacing Phase 1's single elevation (§8.2).
- Buildings from public GIS data (footprints and heights), once importing them is solved upstream (§1.2).
- Embedded retaining walls and excavations, staged construction, rail (cant and twist), mining and other sources of movement.

### 1.4 Non-goals
- **Numerical analysis** (FE, FD). garisenda flags where it's needed.
- **Estimating volume loss** (§1.2).
- **Deriving ground parameters** from test data. garisenda takes them as given and records where they came from (§4).
- **GIS import and coordinate conversion** (§1.2).
- **Structural design of the affected asset.** garisenda compares movements and strains with limits; it doesn't design a repair or a protective measure.

## 2. Sources and verification

### 2.1 Governing sources
🔬 None verified yet. Each unit of work adds the sources it relies on, verified against the source itself, to the bibliography (§2.2). Candidates from the scope discussion (`docs/drafts/scope-discussion.md`) are not citations until verified. Secondary sources (software manuals, reviews) are never cited for equations.

### 2.2 Citation format
- 🟡 **In docstrings:** `Source: <author or body> (<year>), <document>, Eq. <n> / Table <n> / Fig. <n> / p. <n>`. Always the edition or year and the equation, table, figure or page.
- 🟡 **Bibliography:** `docs/reference/sources.md`, one entry per source, with its short key and the date it was verified.
- **Never cite from memory** (decided, skill rule). An unverified citation is marked 🔬 and tracked in `docs/TODO.md`.

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

## 3. Architecture: sources and assessments

- **Sources produce a movement field; assessments consume it** (decided 2026-10-31). A source is anything that causes ground movement (a tunnel, later an excavation). An assessment is anything affected by it (a utility, a building).
- 🟡 **One interface for every source:** given points (x, y, z), return the displacement components and their spatial derivatives at those points. Designed for 3D from day one, so the transverse trough (M1), the subsurface field (M2) and the 3D field (M5) are interchangeable to every assessment.
- 🟡 **Several sources combine by superposition**, recorded on the result as an assumption.
- 🟡 **Closed-form sources return exact derivatives.** Assessments use them for analytical strain and sample the field for discrete strain (§7). No spline is fitted to an analytical field. A spline is needed only for movements given as data (a numerical model's output, survey data), which comes later.
- 🟡 **The transverse trough is a 2D source placed in 3D**: it is applied perpendicular to each tunnel segment (§8.3), and assumes the segment is long and straight. Points near a segment's end, a curve, or a run parallel to the tunnel are flagged (M3), because there the assumption fails.

## 4. Inputs

Every input to a calculation is one of three kinds, treated differently because each goes wrong in a different way.

| Kind | Examples | Rule |
|---|---|---|
| **Ground parameter** | Soil modulus, trough width parameter where it is measured | Required argument. No default. |
| **Design judgment** | Volume loss, trough width method, soil–pipe interaction factor or method, allowable strain, pullout and rotation limits, pipe lengths, building stiffness ratio, discrete strain interval | Required, keyword-only argument. **No default** (decided). |
| **Constant or setting** | Gaussian volume factor, unit conversions | Defaulted, documented, overridable. Recorded on the result. |

- **No judgment has a default.** A missing judgment is an error that names it, says what it depends on, and how to set it.
- **Presets are opt-in** (decided 2026-10-31). Where practice has standard values (nominal pipe lengths, published limits), garisenda can ship them as **named, cited presets** the user passes explicitly, for example `pipe_lengths=gs.presets.<name>`. A preset is a choice someone made, recorded on the result by name and source. It is never applied without being asked for.
- **Limits are project-specific judgments with literature provenance** (decided 2026-10-31). Each limit is given with its value and where it came from; a preset of limits from a published source is allowed under the rule above.
- **Soil–pipe interaction is a judgment** (decided 2026-10-31), given either as a factor with a stated reason or as a named method that derives it (M4b). Greenfield (no reduction) has to be chosen explicitly, like any other value. The result records which.
- 🟡 **Provenance is optional on input and always kept on output.** An argument can be a plain value or a value with a source. Either way the result records the value used, its kind, and its source when one was given.

## 5. Results

### 5.1 One result shape
🟡 Every analysis returns a result object with the same parts:
- **values:** the computed quantities, with units (for a utility, a table along its length);
- **checks:** each quantity against its limit, with the utilization and the governing location;
- **method:** the methods, their sources and the equations used;
- **inputs:** every input used, with its kind and source (§4);
- **validity:** the verdict (§5.2), with the limit that set it;
- **warnings:** everything that was flagged.

🟡 **One calculation, many views:** `.to_dict()` (JSON-ready), `.to_frame()`, a short text summary, and the figures (§9). Views never recalculate, so two views can't disagree.

### 5.2 Validity verdict
🟡 Each result has one of three verdicts, the worst over its checks, inputs and locations:
- **`within`:** every input is inside the method's stated range.
- **`marginal`:** within range but near a limit, by a margin set in the method's spec.
- **`outside`:** at least one input or location outside the range. The result is still computed, and says which input, where, and which limit. **This is the flag for numerical analysis.**

Pass/fail on a check is separate from validity.

### 5.3 Sensitivity runs
🟡 **Every calculation can be run over arrays of one to three of its inputs** with one function, `gs.sweep(analysis, inputs, vary={name: array, ...}, mode="grid" | "paired")`, returning a tidy table: one row per run, with the varied inputs, the governing values, each check's utilization, pass/fail and the verdict. Fixed inputs are recorded once in `df.attrs`. A run that raises records the error in its row. So every analysis is a pure function of its arguments, with no hidden state and no file reading. Volume loss and the soil–pipe interaction factor are the obvious inputs to vary.

## 6. Units
- 🟡 **SI is the preferred system:** m, mm, kPa, MPa. Strain is dimensionless and reported in microstrain or percent only in views.
- **Never guess a unit.**
- 🟡 **Pint first:** a scalar input is a pint quantity, and docs and examples write inputs that way. **A plain float is accepted and read as the documented SI unit**, and the result's input echo records which it was.
- DataFrames carry units in `df.attrs["units"]`. **Units never appear in names** (`depth`, not `depth_m`).
- 🟡 Pipe diameters given in nominal inches are accepted as pint quantities; a preset keyed by nominal size says so in its name and docs.

## 7. Utility checks
- **Every check is run by default and all are reported** (decided 2026-10-31): axial strain, bending strain, combined strain (tension and compression), radius of curvature, and for jointed pipes, joint pullout and joint rotation. A check is skipped only when its limit isn't relevant to the pipe type, and the result says so.
- **Discrete and analytical strain are both computed and compared** (decided 2026-10-31). Analytical strain comes from the field's exact derivatives. Discrete strain comes from movements sampled at an interval, as is common in practice. The result reports both and the difference between them, and the check governs on the larger unless the spec for that check says otherwise. 🟡
- 🟡 **The discrete interval is a judgment** for continuous pipes. For jointed pipes it is the pipe length.
- **Pipe lengths are a table keyed by pipe type and diameter** (decided 2026-10-31), supplied by the user or from an opt-in preset (§4). A type and diameter pair that isn't in the table is an error that names it, never filled from the nearest diameter. The result records the length used for each pipe and its source.
- **Joint position is the worst case** over every possible position along the pipe (decided 2026-10-31), unless joint locations are given.
- 🟡 **Bending uses movement perpendicular to the pipe axis**, in both planes, and axial strain uses movement along it, both computed from the 3D displacement and the pipe's own direction at each point.

## 8. Conventions

### 8.1 Coordinates and signs
- **One flat coordinate system and one length unit** for every table in a site (decided 2026-10-31). No datum or projection is recorded in Phase 1; if figures need a datum label, an optional label is added to the site then.
- 🟡 **Settlement is positive downward.** Displacements returned by a source are global components (x, y, and vertical), so they add across sources.
- 🟡 **Tensile strain is positive.**
- 🟡 In views of a transverse section only, horizontal movement is reported as positive toward the tunnel centerline, the usual convention in the literature.
- 🟡 **Depth is positive downward** from the ground surface.

### 8.2 Ground surface
- **Phase 1: a single ground elevation, or depth only** (decided 2026-10-31). The ground surface becomes its own geometry in a later phase.
- 🟡 Each geometry table gives **either** an `elevation` column **or** a `depth` column, and the column name says which. Elevations need the site's ground elevation to convert; a site that uses depths only never sets one. Nothing is converted by assumption.

### 8.3 Geometry tables
- 🟡 **Tunnels:** an alignment as an ordered table of points (x, y, and elevation or depth of the axis) with a diameter, so it is a set of straight segments with known ends.
- **Utilities are x, y, z tables** (decided 2026-10-31): one row per vertex, keyed by `utility_id`, with a pipe type, diameter and material.
- 🟡 **A utility's elevation reference is a required argument** (`"invert"`, `"axis"` or `"crown"`), converted to the axis using the diameter. Survey data comes in all three, and a wrong guess shifts the pipe by its diameter.
- **Buildings are footprints** (decided 2026-10-31): a vertex table (`building_id`, vertex order, x, y) and a building table (height, foundation level, and stiffness properties as judgments). Facades are derived from the footprint's edges. A single facade line is also allowed, for a quick check of one wall. Phase 1 footprints are entered by hand.

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
- 🟡 **One plot contract:** `gs.plot.<name>(result, *, ax=None, display_units=None) -> (fig, ax)`, using matplotlib. A figure draws from the result and never recalculates.
- 🟡 **Each milestone ships the figures for what it builds**, starting with M1's transverse trough. The core figure of Phase 1 is the profile along a utility: settlement, strain and each check against its limit, plotted against distance along the pipe, with flagged locations marked.
- Figures are checked by eye at close-out, not only by tests.

## 10. Data quality
- **Never drop data silently.** A point, pipe or facade that can't be computed is reported in the result with the reason, not skipped.
- **Never fill missing data.** A building without a height or a pipe without a diameter is an error or a flag, never a guessed value.

## 11. Testing
- pytest; golden values per §2.4; behavior at and beyond each validity limit is tested.
- 🟡 Property-based tests (hypothesis) for physics that must hold: the Gaussian trough's volume equals the volume loss times the tunnel area; settlement is symmetric about the axis; strains are exact derivatives of the field.
- 🟡 Every analysis has a test that a `gs.sweep` row equals a direct call with the same inputs (§5.3).
- **No project data in tests.** Real crossings are reproduced locally on the work machine, not in the repo; tests use invented geometry.

## 12. Engineering

### 12.1 Environment and distribution
- 🟡 **Python ≥ 3.12** and `uv`. CI on Windows, macOS and Linux × Python 3.12–3.14, with a job on the oldest allowed dependency versions.
- 🟡 **Dependencies:** `pint`, `numpy`, `pandas`, `matplotlib`, each with a floor proven in CI, added when code first uses them. Adding another needs a decision here.
- MIT license.

### 12.2 Package layout
- 🟡 `src/` layout, package `garisenda`, tests mirroring the package. Modules by role: `garisenda.sources` (movement fields), `garisenda.utilities`, `garisenda.buildings`, `garisenda.site`, `garisenda.plot`, `garisenda.presets`.

### 12.3 Docs
- 🟡 **Docs are written as we go:** each milestone's close-out writes the user docs for what it built. The docs site (Zensical, with the API reference from docstrings) is set up in M1.

### 12.4 Milestones (Phase 1)
| ID | Scope | Done when |
|---|---|---|
| M0 | Scaffolding: package, lint, tests, CI | CI green |
| M1 | Framework (inputs, result shape, verdict, `gs.sweep`, units), the movement-field interface (§3), the transverse surface trough with horizontal movement, the first figure | Golden values from verified sources and hand calculations; strains are exact derivatives; figure checked by eye |
| M2 | Movements below the surface, several tunnels | Golden values from the verified subsurface method; depth validity flags tested |
| M3 | Real geometry: tunnel alignments as segments, utilities as 3D polylines, the `Site` (§8.4), the profile along a utility | A real crossing's profile reproduced locally and plotted; flags for ends, curves and parallel runs tested |
| M4a | Utility checks on greenfield movements, with soil–pipe interaction factors given as numbers: continuous and jointed pipes, discrete and analytical strain, pipe length tables | Golden values from the verified definitions; each check against its limit; the profile figure shows every check |
| M4b | Soil–pipe interaction methods from the literature review (TODO #1). **Phase 1's utility assessment is complete here.** | Each method reproduces its source's examples; outside its range is flagged |
| M5 | The 3D field (longitudinal trough) | Matches the transverse trough far from the face; volume conserved |
| M6 | Buildings, footprints entered by hand | Golden values from the verified damage method; facade figures |

🟡 M4b's spec can't start until the literature review is done. If M4a is too big for one unit, it splits into continuous pipes, then jointed pipes.

## 13. Open questions
1. ❓ **Is a beam-on-springs (Winkler) model of the pipe in scope** for M4b, or is everything beyond closed-form relative stiffness flagged for numerical analysis? Decide after the literature review.
2. ❓ **Which subsurface method for granular soil** in M2 (TODO #3)?
3. ❓ **Does the discrete check govern, the analytical one, or the larger of the two** (§7)? The draft says the larger.
