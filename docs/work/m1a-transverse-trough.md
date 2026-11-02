# M1 (a): the transverse surface trough over an idealized straight tunnel

## Intent

### Goal
A caller can describe an idealized straight tunnel and evaluate the steady-state transverse Gaussian trough at the ground surface: settlement and horizontal movement at any points (x, y, z), with their exact spatial derivatives, the trough width from a given k, every input recorded with its kind and source, and points outside the method's range flagged, including every point below the surface. This is the first source (SPEC §3) and the numerical core that M1 (b) builds the profile, the result and the figures on.

### Why
- SPEC §12.4: M1 is the first milestone with analysis code. As written it holds nine pieces (units, the input rules, the result shape and verdict, `gs.sweep`, the source interface, the profile, the tunnel and builder, the trough, two figures) plus the docs site from §12.3, which is several sittings of review, not one. So M1 splits in three, as hangtu's large milestones did:
  - **(a) this unit:** units and the input rules, the idealized tunnel, the source interface, the transverse surface trough.
  - **(b)** the station-and-offset builder, the profile along an asset, the result object and its verdict and views, the cross-section and profile figures.
  - **(c)** `gs.sweep`, the docs site (Zensical), and M1's user docs and figures.
- The trough comes first rather than the framework because it is the framework's first real consumer: designing the result object without a calculation to wrap tends to guess wrong. (a) builds only the parts of the framework the trough needs (units, the input kinds, validity as data) and (b) wraps them into the result shape.
- The surface trough settles the geometry, the interface and the math. The subsurface trough (M2) then replaces only how the trough is built at a depth: the width i(z), the maximum settlement at depth and the horizontal movement model, plus the validity rule. That holds only if the interface is 3D from the start (decision 3).
- Everything after it depends on this: the profile (b), utilities (M3), buildings (M4) and several tunnels (M2) all consume this source.

### Constraints
- **SPEC §3:** a closed-form source is a function of points, not a grid; it returns global displacement components (x, y, vertical) and their exact spatial derivatives. No spline, no finite differences inside the source.
- **SPEC §4:** volume loss and the trough width parameter are required keyword-only judgments with no default. Provenance is optional on input and always kept on output.
- **SPEC §2:** golden values come from hand calculations written out in the spec, never from the code. Citations stay 🔬 unverified in this unit (decision 5); nothing is cited as verified until it is checked against the source.
- **SPEC §2.5, §5.2:** outside the method's range is flagged, not raised; only physically impossible inputs raise.
- **SPEC §6, §8.1:** pint first, SI preferred, never guess a unit; settlement positive downward; depth positive downward; offset positive to the right looking up-station.
- **SPEC §8.3:** the idealized tunnel is a reference point (x, y), a plan direction, an axis depth or elevation, and a diameter, with no ends.
- **SPEC §11:** hypothesis properties: trough volume equals volume loss times tunnel area; settlement symmetric about the axis; derivatives match finite differences of the same field.
- **SPEC §12.1:** `pint` and `numpy` are added now, with floors proven by the `lowest` job; `hypothesis` joins the dev group.

### Out of scope
- **The trough below the surface** (width at depth, Taylor 1995's horizontal movements): M2, as SPEC §12.4 has it. In (a) a point below the surface gets the surface trough's values and is flagged (decision 3).
- **Named trough width methods and k presets** (O'Reilly & New 1982, Mair et al. 1993, Selby 1988): later, once you decide how recommendations are offered (decision 4).
- **Several tunnels and superposition:** M2.
- **The builder, the profile, the result object, figures, `gs.sweep`, the docs site:** M1 (b) and (c).
- **Real alignments, tunnel ends, the longitudinal trough:** M5, M6.
- **Utility and building checks:** M3, M4.

### SPEC sections touched
- **SPEC §12.4:** M1's row records the split into (a), (b) and (c).
- **SPEC §1.3:** the tunnel movements row says the trough width comes from a given k for now, named methods later.
- **SPEC §6:** inputs that practice writes as percentages must be pint quantities (decision 2).
- **SPEC §3:** the 🟡 source interface becomes decided, with its exact signature recorded in this unit's spec.
- **SPEC §2.1, §2.2, `docs/TODO.md` #2:** the sources this unit relies on are named as 🔬 candidates, unverified; TODO #2 stays open.

### Decisions (intent review, 2026-11-02)
1. **M1 splits into (a), (b) and (c), in that order.** Agreed as proposed.
2. **An input that practice writes as a percentage must be a pint quantity.** A plain float for volume loss is an error that says how to write it (`0.5 * gs.units.percent` or `0.005 * gs.units.dimensionless`), because `0.5` could mean 0.5 % or 50 %, and SPEC §6 says never guess a unit. It covers volume loss now and strain limits in M3. Inputs never written as percentages (k, lengths) still accept a plain float read as the documented SI unit.
3. **Surface trough only; every point below the surface is flagged.** It gets the surface trough's values and an `outside` flag with the reason (the surface trough applied below the surface, where the real trough is narrower and unconservative to ignore; the subsurface method is M2). A flag on the result, not a Python warning: the tests treat warnings as errors, and a long utility would emit one per point. So that M2 only replaces how the trough is built, the source takes full (x, y, z) points and returns derivatives with respect to z too; for the surface trough they are exactly zero, and a test says so. Validity is computed per point, so M2 changes the rule, not the shape. Briefly considered and dropped: the subsurface trough in M1 with i = k·(z₀ − z).
4. **k is given directly** (`trough_width_parameter=`), a required judgment. Named methods and presets come later, once you've decided how recommendations are offered.
5. **Citations stay 🔬 unverified for now.** The spec names the candidate sources (Peck 1969 for the Gaussian form, O'Reilly & New 1982 for the volume relation and horizontal movement) as unverified, and golden values come from hand calculations. Docstrings mark the citation 🔬 until TODO #2 is done.
6. **Horizontal movement assumes ground moves toward the tunnel axis**, recorded on the result as an assumption, with no alternative method in this unit.

## Spec

No topic doc holds this, so the spec is here. Everything marked 🟡 is a proposal for this review.

### Changes
- **SPEC §12.4:** M1's row splits into (a), (b) and (c) (intent decision 1).
- **SPEC §1.3:** the tunnel movements row says the trough width comes from a given k for now, named methods later (intent decision 4).
- **SPEC §3:** the source interface is decided as in decisions 4–6 below.
- **SPEC §4:** the provenance wrapper and the missing-judgment error (decisions 2, 3).
- **SPEC §6:** inputs that practice writes as a percentage, and angles, must be pint quantities (intent decision 2; decision 1 below).
- **SPEC §8.1:** the plan direction convention (decision 7).
- **`docs/TODO.md` #2:** notes that M1 (a) uses the candidate equations unverified.
- **New modules:** `garisenda.units` (the registry and input conversion), `garisenda.inputs` (`Sourced`, input records, the judgment decorator), `garisenda.sources` (`IdealizedTunnel`, `transverse_surface_trough`, `Movement`, `Flag`). Public names in `gs`: `units`, `Sourced`, and the `sources` module.

### Decisions

**Units and inputs**

1. **One pint registry, `gs.units`**, as in hangtu, so quantities from the user and from garisenda always mix. Input conversion, in one function every calculation uses:
   - a quantity of the right dimension is converted to SI;
   - a plain number is read as the documented SI unit (m for lengths), and the input record says so (`given_as="plain number, read as m"`);
   - **ratios written as percentages** (volume loss now) and **angles** (the tunnel's direction) refuse a plain number, with an error that names the argument and shows how to write it. 🟡 Angles are added to intent decision 2 for the same reason: `30` could be degrees or radians, and SPEC §6 says never guess;
   - a wrong dimension raises, naming the argument, the expected dimension and what was given.
2. 🟡 **Provenance:** `gs.Sourced(value, source="...")` wraps any input; `source` is free text (a document and section, a project basis of design). Any argument accepts either a bare value or a `Sourced`. The input record keeps `name`, `value` (a pint quantity in SI), `kind` (`"ground parameter"`, `"design judgment"` or `"constant or setting"`, SPEC §4), `source` (or None) and `given_as`.
3. 🟡 **A missing judgment is an error that says what it depends on and how to set it** (SPEC §4). Judgments are required keyword-only arguments in the signature, so editors and mypy see them as required. A decorator, `@judgments(volume_loss="...", trough_width_parameter="...")`, holds the explanation for each and turns Python's bare `missing 1 required keyword-only argument` into `TypeError: volume_loss is required: it depends on the tunneling method, the ground and the workmanship, and is a design judgment with no default. Pass it as a pint quantity, e.g. volume_loss=0.5 * gs.units.percent.` Typed with `ParamSpec`, so the signature survives. Alternative rejected: a sentinel default, which makes the signature look optional.

**The source interface (SPEC §3)**

4. 🟡 **Points are (x, y, depth)**, with depth positive downward from the ground surface (SPEC §8.1), so the vertical displacement and the vertical coordinate have the same sign: settlement is a displacement in the +depth direction. Elevations are converted to depths before the source sees them (by the tunnel here, by the builder in (b)). Arrays of floats in m, or pint arrays, of any equal length.
5. 🟡 **`source.evaluate(x=, y=, depth=) -> Movement`**, a frozen dataclass of numpy arrays in SI, components in the order (x, y, depth):
   - `displacement`, shape (N, 3): u_x, u_y and settlement (m);
   - `gradient`, shape (N, 3, 3): ∂u_i/∂x_j (dimensionless);
   - `hessian`, shape (N, 3, 3, 3): ∂²u_i/∂x_j∂x_k (1/m), symmetric in j, k;
   - `verdict`, shape (N,): `"within"`, `"marginal"` or `"outside"` per point;
   - `flags`: a tuple of `Flag(verdict, reason, limit, points)`, where `points` are the indices it applies to.
   Plain arrays, not pint, because this is the contract between sources and the profile, which is used in bulk; units are fixed by the docstring, and (b) puts them on the profile table (SPEC §6). The profile (b) resolves these onto the asset's direction: the along-asset strain is a·∇u·a, and curvature comes from the Hessian contracted with a twice.
6. 🟡 **A source also carries what the result will need:** `inputs` (the records of decision 2), `method` (name, equations and source of each), and `assumptions` (text). (b) gathers them into the result shape.

**The tunnel**

7. 🟡 **`gs.sources.IdealizedTunnel(*, reference_point, azimuth, diameter, axis_depth=None, axis_elevation=None, ground_elevation=None, reference_station=0)`.**
   - `azimuth` is the plan direction of increasing station, **clockwise from the +y axis**, a pint angle (decision 1). So the unit tangent is t = (sin θ, cos θ) and the unit normal to the right is n = (cos θ, −sin θ). Clockwise from +y is a bearing when +y is north, which is how engineers state directions; it is recorded in SPEC §8.1 because alignments (M5) follow it.
   - The axis is given by `axis_depth`, or by `axis_elevation` with `ground_elevation`; anything else (both, neither, an elevation without the ground) raises, naming the arguments (SPEC §8.2).
   - `reference_station` is the station at `reference_point` (a length, default 0), so spreadsheet stations like 1250 m can be used as they are. It is geometry, not a judgment.
   - `tunnel.station_offset(x=, y=)` returns station s = s₀ + (p − p₀)·t and offset o = (p − p₀)·n.
   - Raises: diameter ≤ 0; axis depth ≤ D/2 (the bore would break the surface).
   - The tunnel records that it was idealized, as an assumption (SPEC §1.3).

**The trough**

8. **`gs.sources.transverse_surface_trough(tunnel, *, volume_loss, trough_width_parameter) -> TransverseSurfaceTrough`**, a frozen source object with `evaluate()`. The name says surface, so the subsurface trough (M2) comes as its own source and existing calls don't change. Equations (🔬 citations unverified, intent decision 5), with o the offset from the axis and z₀ the axis depth:
   - trough width: i = k z₀
   - tunnel area: A = π D²/4
   - maximum settlement: S_max = V_L A / (√(2π) i), from the trough volume √(2π) i S_max = V_L A (🔬 O'Reilly & New 1982)
   - settlement: S(o) = S_max exp(−o²/(2i²)) (🔬 Peck 1969)
   - horizontal movement toward the axis: h(o) = (o / z₀) S(o), so the displacement along n is u_n = −(o/z₀) S (🔬 O'Reilly & New 1982; intent decision 6)
   - global components: u_x = u_n n_x, u_y = u_n n_y, settlement = S.
   - exact derivatives with respect to o, which become the gradient and Hessian through ∂o/∂x = n_x, ∂o/∂y = n_y and ∂o/∂depth = 0:
     - dS/do = −(o/i²) S
     - d²S/do² = (o²/i² − 1) S / i²
     - du_n/do = −(S/z₀)(1 − o²/i²)
     - d²u_n/do² = −(S/z₀)(o/i²)(o²/i² − 3)
   - Everything with respect to station or depth is exactly zero.
9. **Assumptions recorded:** steady state, the face long passed; transverse trough only; Gaussian form; ground moves toward the tunnel axis; the surface trough applied at the point's plan position whatever its depth; idealized straight tunnel; and 🟡 "no validity range is checked for k, volume loss or cover yet: the sources are unverified (TODO #2)", so a `within` verdict is never read as more than it is.
10. **Physically impossible inputs raise** (SPEC §2.5): volume loss ≤ 0 or ≥ 100 %; k ≤ 0; a point above the surface (depth < 0); a point inside the bore (distance to the axis in the section < D/2); NaN or infinite coordinates, naming the point indices (🟡 raise rather than flag: a coordinate that isn't there is a data error, SPEC §10, and the caller fixes it before the analysis).
11. **Per-point validity:** a point at the surface is `within`. 🟡 "At the surface" means depth ≤ 1 mm, a documented setting (`surface_tolerance`, recorded on the source), so a depth that comes out as 1e-12 after converting from an elevation isn't flagged. A point deeper is `outside`, with one flag listing every such point: "surface trough applied below the ground surface; the trough at depth is narrower, so settlement and curvature there are underestimated; the subsurface method is M2". No `marginal` verdict exists yet; the verdict values are defined so that (b) and M2 use them.

### Sources
- **Peck 1969:** Peck, R. B. (1969), "Deep excavations and tunneling in soft ground", 7th ICSMFE, state-of-the-art volume: the Gaussian form. 🔬 Not verified (TODO #2).
- **O'Reilly & New 1982:** O'Reilly, M. P. and New, B. M. (1982), "Settlements above tunnels in the United Kingdom: their magnitude and prediction", Tunnelling '82: i = k z₀, the trough volume relation, and horizontal movement toward the axis. 🔬 Not verified (TODO #2).

Docstrings cite these with the 🔬 mark and no equation number until they are verified.

### Hand calculation (golden values)
Derived from the equations in decision 8, carried to 8 significant figures. Inputs: D = 6.0 m, z₀ = 20.0 m, k = 0.5, V_L = 1.0 %.
- i = 0.5 × 20.0 = 10.0 m
- A = π × 6.0² / 4 = 28.274334 m²
- trough volume V_L A = 0.28274334 m³/m
- S_max = 0.28274334 / (√(2π) × 10.0) = 0.28274334 / 25.066283 = 0.011279827 m

At the surface, by offset o (m):

| o | S (m) | u_n (m) | dS/do | d²S/do² (1/m) | du_n/do | d²u_n/do² (1/m) |
|---|---|---|---|---|---|---|
| 0 | 1.1279827e-2 | 0 | 0 | −1.1279827e-4 | −5.6399136e-4 | 0 |
| 5 | 9.9544126e-3 | −2.4886031e-3 | −4.9772063e-4 | −7.4658094e-5 | −3.7329047e-4 | 6.8436587e-5 |
| 10 (= i) | 6.8415611e-3 | −3.4207805e-3 | −6.8415611e-4 | 0 | 0 | 6.8415611e-5 |
| 17.320508 (= √3 i) | 2.5168697e-3 | −2.1796731e-3 | −4.3593461e-4 | 5.0337393e-5 | 2.5168697e-4 | 0 |
| 20 | 1.5265586e-3 | −1.5265586e-3 | −3.0531172e-4 | 4.5796758e-5 | 2.2898379e-4 | −1.5265586e-5 |
| −10 | 6.8415611e-3 | 3.4207805e-3 | 6.8415611e-4 | 0 | 0 | −6.8415611e-5 |

Checks on the table: S(i) = S_max e^(−1/2); the curvature is zero at o = i; h(i) = (i/z₀) S(i) = 0.5 S(i); the horizontal strain du_n/do is zero at o = i and changes sign there.

**Rotated tunnel, global components.** Same trough; reference point (100, 200) m, azimuth 30°, reference station 1000 m. So t = (0.5, 0.86602540) and n = (0.86602540, −0.5). The point at station 1025 m, offset +10 m:
- x = 100 + 25 × 0.5 + 10 × 0.86602540 = 121.16025 m; y = 200 + 25 × 0.86602540 − 10 × 0.5 = 216.65064 m
- settlement = 6.8415611e-3 m; u_n = −3.4207805e-3 m, so u_x = −2.9624828e-3 m and u_y = 1.7103903e-3 m (toward the axis, which lies to the left)
- ∂S/∂x = dS/do × n_x = −5.9249657e-4; ∂S/∂y = dS/do × n_y = 3.4207805e-4; ∂S/∂depth = 0.

### Acceptance criteria
Tolerance 1e-6 relative for the hand-calculated values, tighter than SPEC §2.4's 0.5 % because the calculation is exact and carried to 8 figures; exact zeros are checked as exactly zero.

1. **Station and offset:** for the rotated tunnel above, `station_offset(x=121.16025, y=216.65064)` gives (1025, 10); a point to the left of the tunnel has a negative offset; azimuth 0° has its right toward +x.
2. **Tunnel inputs:** `axis_elevation=` with `ground_elevation=` gives the same axis depth as `axis_depth=`; each invalid combination raises, naming the arguments; diameter ≤ 0 and axis depth ≤ D/2 raise.
3. **Units:** `volume_loss=1 * u.percent` and `0.01 * u.dimensionless` give identical results; `volume_loss=0.01` and `azimuth=30` raise the errors of decision 1, naming the argument and showing how to write it; `axis_depth=20` and `20 * u.m` and `2000 * u.cm` give identical results, and the first is recorded as a plain number read as m; a length given in seconds raises, naming the argument.
4. **Missing judgment:** omitting `volume_loss` or `trough_width_parameter` raises the error of decision 3, which names the argument and says what it depends on and how to set it.
5. **Golden values:** every value in the surface table, through the public interface (`evaluate()` at the right offsets, with the tunnel along +y), as the displacement, gradient and Hessian entries they map to.
6. **Global components:** the rotated tunnel's point gives the displacements and first derivatives above.
7. **Exact derivatives** (hypothesis, over D, z₀, k, V_L, azimuth and the point): the gradient and Hessian match central finite differences of `evaluate()`'s own displacement and gradient to a tolerance set by the step; the Hessian is symmetric in its last two indices; every derivative with respect to station or depth is exactly zero.
8. **Volume** (hypothesis): the settlement integrated across the trough (over ±10 i) equals V_L A to 1e-6 relative.
9. **Symmetry** (hypothesis): S(o) = S(−o) and u_n(o) = −u_n(−o).
10. **Validity:** a point at depth 0, and one at depth 0.5 mm, is `within`; one at depth 2 m is `outside`, and one flag lists all the deep points' indices with the reason of decision 11; the values below the surface equal the surface values at the same plan position.
11. **Impossible inputs raise:** volume loss 0, −1 % and 100 %; k 0; a point at depth −1 m; a point inside the bore; a NaN coordinate, with the error naming its index.
12. **Inputs and assumptions:** the source's records hold every input with its kind, SI value, `given_as`, and the source text when `Sourced` was used, None otherwise; the assumptions of decision 9 are all present.
13. **Docstrings:** `IdealizedTunnel`, `transverse_surface_trough` and `evaluate` state the equations, inputs and outputs with units, the validity behavior, the assumptions and the 🔬 sources (SPEC §8.5); ruff's numpy docstring rules pass.
14. **Dependencies:** `pint` and `numpy` are added with floors that the `lowest` job passes on; `hypothesis` is in the dev group; mypy strict passes, and each `# type: ignore` names its code and says why.

## Plan

Five build commits, each with ruff check, ruff format check, mypy and pytest green. Dependency floors follow hangtu's (`numpy>=1.26`, `pint>=0.24.4`, `hypothesis>=6.100`), proven by the `lowest` job run locally in commit 5.

### 1. `M1 (a): add units and the input rules`
- `pyproject.toml`: `numpy>=1.26` and `pint>=0.24.4` in `dependencies`; `hypothesis>=6.100` in the dev group; ruff `NPY` rules added now that numpy is a dependency (M0 intent decision 3). `uv.lock`.
- `src/garisenda/units.py`: the registry `units`; `to_si(name, value, *, dimension, unit, plain_number)`, the one conversion every calculation uses, where `plain_number` is `"read as SI"` or `"refuse"` (spec decision 1); returns the SI magnitude and how it was given. Errors name the argument, the expected dimension and how to write it.
- `src/garisenda/inputs.py`: `Sourced` (frozen dataclass: `value`, `source`); `InputRecord` (`name`, `value`, `kind`, `source`, `given_as`); `Kind` literal; `record(name, value, *, kind, dimension, unit, plain_number) -> (float | ndarray, InputRecord)`, which unwraps `Sourced` and calls `to_si`; the `judgments(**explanations)` decorator typed with `ParamSpec` (spec decision 3).
- `src/garisenda/__init__.py`: export `units`, `Sourced`.
- Tests: `tests/test_units.py` (AC 3's generic cases: plain number read as SI and recorded, refused plain numbers for percent and angles, wrong dimension, equal results for m and cm); `tests/test_inputs.py` (AC 4 on a decorated test function, AC 12's record fields with and without `Sourced`); the decorator keeps the wrapped function's signature (`inspect.signature`). AC 14 for mypy.

### 2. `M1 (a): add the idealized straight tunnel`
- `src/garisenda/sources/__init__.py`: the package, exporting `IdealizedTunnel`.
- `src/garisenda/sources/_tunnel.py`: `IdealizedTunnel` (frozen dataclass; keyword-only constructor per spec decision 7; stores the axis depth in m, t and n, the input records and the "idealized" assumption); `station_offset(x=, y=)`.
- Tests: `tests/sources/test_tunnel.py`: AC 1 (the rotated tunnel's point, left is negative, azimuth 0° has its right toward +x), AC 2 (elevation and ground give the same depth; each invalid combination; diameter ≤ 0; axis depth ≤ D/2), AC 3 for `azimuth=30` and `axis_depth=20`.

### 3. `M1 (a): add the source interface and the transverse surface trough`
- `src/garisenda/sources/_movement.py`: `Verdict` literal, `Flag`, `Movement` (frozen dataclass of arrays, spec decision 5, with shape checks), `MethodRecord`, and the `Source` protocol (`evaluate`, `inputs`, `method`, `assumptions`).
- `src/garisenda/sources/_transverse.py`: `transverse_surface_trough()` with `@judgments`, and `TransverseSurfaceTrough.evaluate()`: points converted with `to_si`, the checks of spec decisions 10–11, the equations and derivatives of decision 8 mapped to the gradient and Hessian, the assumptions of decision 9. Docstrings as reference entries (AC 13).
- `src/garisenda/sources/__init__.py`: export `transverse_surface_trough`, `TransverseSurfaceTrough`, `Movement`, `Flag`, `Source`.
- Tests: `tests/sources/test_transverse.py`: AC 5 (the surface table), AC 6 (the rotated tunnel), AC 3 for `volume_loss`, AC 4, AC 10, AC 11, AC 12.

### 4. `M1 (a): add property tests for the trough`
- `tests/sources/test_transverse_properties.py` (hypothesis): AC 7 (finite differences of the gradient and Hessian, Hessian symmetry, exact zeros with respect to station and depth), AC 8 (volume over ±10 i), AC 9 (symmetry).
- `tests/sources/strategies.py`: shared strategies for tunnels, troughs and points, which (b) reuses.

### 5. `M1 (a): close out`
- Run the `lowest` job locally (`UV_RESOLUTION=lowest-direct`, CLAUDE.md), then `git checkout uv.lock`; adjust a floor only if it fails, and say why in the Result.
- `docs/work/m1a-transverse-trough.md`: `## Result`, each acceptance criterion met or not, with evidence.
- `SPEC.md`: 🟡 items this unit settled (§3 source interface, §4 provenance and the decorator, §8.1 plan direction) marked decided.
- `CLAUDE.md`: the "Next" sentence points to M1 (b); a convention line if one emerged (for example, the conversion function every input goes through).
- `docs/TODO.md`: nothing resolved (#2 stays open).
