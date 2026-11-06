# M3 (a): Strain checks for continuous pipes

## Intent

### Goal
A caller can check a continuous pipe (welded steel, HDPE, PVC, HDD-installed) against the movement profile along it: axial strain, bending strain in the vertical and lateral planes and their resultant, combined tensile and compressive strain, and radius of curvature. Each is computed analytically from the field's exact derivatives and discretely from movements sampled at an interval the caller gives. The worse of the two governs, and each is checked against a limit the caller gives. The profile figure shows every check against its limit.

### Why
- **SPEC §12.4:** M3 is the utility checks, and once it's done the spreadsheet is replaced for utilities. It splits in two (decision 1): continuous pipes first, then jointed pipes in M3 (b).
- **The checks are mechanics, not a published method** (decision 2). Strain is change in length over original length, bending strain in a beam is y/R, the radius of a curve through three points is geometry, and axial and bending strains add. Bracegirdle et al. (1996) (read 2026-11-06, pp. 659–664) set out the approach: the pipe follows the ground, "ground strains may be obtained directly by differentiating the displacements" (p. 660), and total tensile strain combines bending strain from curvature with axial strain (p. 663). They give closed forms for one Gaussian trough (Eqs. 7–11, pp. 662–663):
  - curvature at the trough's center, S_max/i² (Eq. 7);
  - peak hogging curvature at y = √3 i, 0.446 S_max/i² (Eq. 8);
  - horizontal strain there, 0.446 S_max/(z₀ − z_p), for horizontal movement toward the axis (Eq. 9);
  - the same for the longitudinal trough, 0.242 (Eqs. 10–11; the longitudinal trough is M6).

  Eqs. 7 and 8 match the second derivative of the Gaussian (2e^(−3/2) = 0.446). Eq. 9's field matches garisenda's linear width method at any depth, where u_n = −(o/(z₀ − z)) S, but not Mair's method, whose horizontal movement is 0.325 (z₀ − z)/i of it (0.65 at the surface). These are golden values for the single-tunnel case.
- **Discrete strain is what practice computes.** The spreadsheet being replaced computes strain from sampled movements. Reporting both lets a reviewer compare line by line, and the difference shows when the interval is too coarse. For one Gaussian trough, the three-point curvature at the center is (1 − e^(−a))/a of the exact value, a = s²/(2i²): 0.998 at s = 1 m with i = 10 m, 0.94 at s = i/2, 0.79 at s = i (Claude's hand calculation, 2026-11-06; to be written out in the spec).
- **What depends on it:** M3 (b) builds joint rotation and pullout on the same profile and pipe; M4's building strains reuse the analytical/discrete pattern.

### Constraints
- **SPEC §3:** the check consumes the profile along the asset (`along`, `vertical`, `lateral` and their exact derivatives). It never recalculates the source, except to sample movements at the discrete interval (§3, "Closed-form sources return exact derivatives"). No spline is fitted.
- **SPEC §4:** the discrete interval, the strain and radius-of-curvature limits, and soil–structure interaction are required, keyword-only judgments with no default (decision 4). Interaction is greenfield in Phase 1.
- **SPEC §1.3, Phase 1 assumptions:** greenfield; the pipe follows the ground, with no reduction for its stiffness or for slip (decision 6). Recorded on the result.
- **SPEC §5:** one result shape. Each check reports its utilization and governing location; analytical and discrete values both appear, with their difference.
- **SPEC §7:** every check runs and is reported. Tensile strain is positive (§8.1).
- **SPEC §10:** points that can't be computed (near the utility's ends, for the discrete check) are reported with a reason, never dropped.
- **SPEC §2.4:** golden values from Bracegirdle et al.'s closed forms and from hand calculations written out in the spec, never from the code.
- **Test on segments at any angle** (CLAUDE.md): an oblique pipe has lateral bending, which a perpendicular pipe doesn't.
- **SPEC §9, §12.3:** the profile figure shows each check against its limit, and the user docs and their example are written at close-out. The docs state that utilities are circular and that strain is taken at the outermost fiber (decision 5).

### Out of scope
- **Jointed pipes:** pipe-length tables, joint rotation and pullout at the worst joint position, and the limit presets for iron pipes. M3 (b).
- **Soil–structure interaction, including Bracegirdle et al.'s strain reduction factor** (Eq. 12, from charts after Attewell et al. 1986): later phases (SPEC §1.3, §13 Q1). The factor depends on soil–pipe interaction, which is worked out then.
- **Bracegirdle et al.'s step (a), the slope criterion S_max/i** (Table 1, after O'Rourke & Trautman 1982): not in M3. Some users may want it, so it's TODO #12.
- **Limit presets for any material:** M3 (b) ships the iron presets (TODO #6). Limits for other materials are TODO #13. In M3 (a) the caller always gives the limits.
- **The longitudinal trough** (Bracegirdle et al. Eqs. 10–11): M6.
- **Movements given as data** (monitoring, numerical output), where only discrete strain is possible: later.

### SPEC sections touched
- **§12.4:** M3's row splits into (a) and (b), and its done-when is reworded (decision 1).
- **§7:** analytical and discrete strain are both computed and the worse governs, now decided (decision 3); the interval is required (decision 4); the checks are mechanics and utilities circular (decisions 2, 5); bending is reported per plane and checked on the resultant (decision 5); combined strain never counts axial strain as helping (decision 7).
- **§13 Q3:** marked decided by decision 3 (kept in place, so the questions aren't renumbered).
- **§2.1:** a table of limits quoted in a verified source may be cited from it, naming the original (decision 8). Used in M3 (b).
- **§1.3:** the assumptions that utilities are circular and strain is taken at the outermost fiber join the Phase 1 assumptions, at close-out.
- **§3, §5.1, §9:** the check's result and figure, at the spec step.
- **`docs/TODO.md`:** #4 updated; #6 decided as opt-in presets; #12 and #13 added.
- **`docs/reference/sources.md`:** Bracegirdle et al. (1996) gains Eqs. 7–9 and pp. 659, 663, at the spec step.

### Decisions (intent review, 2026-11-06)
1. **M3 splits in two.** (a) continuous pipes and the strain checks; (b) jointed pipes, joint rotation and pullout, pipe lengths and the iron presets. Both together, with analytical and discrete strain, are too much for one review. M3's done-when "a real crossing reproduced locally" becomes "compared with the spreadsheet locally, with every difference explained": the spreadsheet is incomplete and implemented poorly, so matching it isn't the goal.
2. **Mechanics is derived, not cited.** The definitions of strain, bending strain y/R, the three-point radius and the sum of axial and bending strain are written out in the spec as derivations, with no citation to a textbook or software manual. Only the approach (the pipe follows the ground, differentiate the displacements) and the closed-form golden values are cited, to Bracegirdle et al. (1996).
3. **Analytical and discrete strain are both computed, and the worse governs.** Analytical strain comes from the profile's exact derivatives; discrete strain from movements sampled at the caller's interval. The result reports both and their difference. This was SPEC §7's 🟡 proposal and settles SPEC §13 Q3. For a smooth trough the discrete peak is the smaller, so analytical usually governs, but nothing assumes it.
4. **The discrete interval is a required judgment, with no default.** The docs and examples use 1 m, so a caller who copies them gets 1 m having chosen it, and the result records it. A default was considered and rejected: the interval changes the answer (short spans exaggerate small differences, long ones smooth the peaks) and SPEC §4 lists it as a judgment.
5. **Utilities are circular, and strain is taken at the outermost fiber.** Bending strain uses the outside radius. Bending is reported in the vertical and lateral planes and as their resultant, and checked on the resultant: for a circular section the peak fiber strain comes from the resultant curvature. Both assumptions are stated in the docs and recorded on the result.
6. **The pipe follows the ground.** No reduction factor, no slip: axial pipe strain equals the ground's strain along the pipe, and the pipe's curvature equals the ground's. The result says soil–structure interaction would reduce them (SPEC §1.3).
7. **Combined strain never counts axial strain as helping.** Tensile strain is max(axial, 0) plus bending; compressive strain is min(axial, 0) minus bending. Conservative, and it needs no extra argument. An option to count it was rejected.
8. **A table of limits quoted in a verified source may be cited from it, naming the original:** "Bracegirdle et al. (1996), Table 2, after Attewell et al. (1986)". It extends SPEC §2.1's rule for equations to tables of limits. The original stays 🔬 until read.

### 🟡 To settle in the spec
- **The API.** Proposed: `gs.utilities.check_strain(profile, *, interval, interaction, limits)` or a pipe object that carries its limits; how the caller names the pipe as continuous; what `limits` holds (tensile and compressive strain, radius of curvature) and whether a check with no limit is reported without a utilization.
- **Discrete sampling.** Where the discrete samples sit relative to the profile's stations (centered on each station, at ±interval), and whether the interval must be the profile's `spacing` or is independent of it.
- **The utility's ends.** The discrete check needs movements an interval beyond each station. At an end, whether the ground beyond is sampled (the field exists there) or the point is flagged as having no discrete value.
- **Peaks.** Analytical peaks come from the source's critical distances. Whether discrete strain is also evaluated at them, so the two are compared at the same place.
- **Radius of curvature:** reported as 1/|κ| of the resultant, analytical and discrete, with an infinite radius where curvature is zero.
- **The perpendicular-bounds argument (TODO #10):** written out as a hand calculation, with lateral bending on an oblique pipe as a test case.
- **Golden values:** Bracegirdle et al. Eqs. 7–9 (Eq. 9 with the linear width method only), the three-point ratio (1 − e^(−a))/a, and an oblique pipe's lateral bending.
