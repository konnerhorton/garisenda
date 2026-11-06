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

## Spec

No topic doc holds this, so the spec is here. It settles the intent's "To settle in the spec" items (decisions 1–14). Every 🟡 proposal below was accepted in review (2026-11-06), with one change: the bending limit is a judgment of its own (decision 2). Bracegirdle et al. (1996) was read on 2026-11-06 from `../hangtu/sandbox/sources/inbox/1996_109.pdf`; Eqs. 7–9 were checked against the page image of p. 662, because the text layer garbles them.

### What the paper says
- **Bracegirdle et al. (1996), p. 660:** "Ground strains may be obtained directly by differentiating the displacements, or from a Gaussian curve fitted to the predicted ground movements."
- **p. 662, §6.1–6.2:** total tensile strain "arises from two components: bending strain due to curvature, and axial strain". Transverse to a single tunnel, the maximum curvature is in sagging at the trough's center, d²S_v/dy² (y = 0) = S_v max/i² (Eq. 7). "Large compressive horizontal ground strains occur at the centre of the trough." The maximum hogging curvature and horizontal tensile strain occur at √3 i, where "under most circumstances, the combination of axial and bending strains produce the greatest tensile strains in pipes": d²S_v/dy² (y = √3 i) = 0.446 S_v max/i² (Eq. 8) and dS_h/dy (y = √3 i) = 0.446 S_v max/(z₀ − z_p) (Eq. 9).
- **p. 663:** "it is assumed that pipes follow ground movements when calculating bending strain"; the axial strain is reduced by a strain reduction factor (out of scope, intent). "Conservative estimates of combined tensile strain ... are obtained by combining the strain due to pipe curvature, assuming the pipe moves with the ground, and maximum tensile ground strain". It also says "bending strains in pipes transverse to tunnels tend to be more severe than for pipes running parallel to tunnels" (TODO #10).
- **Checked by hand:** Eqs. 7 and 8 are the second derivative of S_max e^(−ρ²/2), ρ = y/i: (S_max/i²)(ρ² − 1)e^(−ρ²/2) is −S_max/i² at ρ = 0 and 2e^(−3/2) S_max/i² = 0.44626 S_max/i² at ρ = √3. Eq. 9 is the derivative of u = −(y/(z₀ − z_p)) S, garisenda's linear width method (SPEC §3), whose strain is −(S_max/(z₀ − z_p))(1 − ρ²)e^(−ρ²/2), 0.44626 S_max/(z₀ − z_p) at ρ = √3. Mair's method gives c₁(z₀ − z_p)/i of it (intent).

### Mechanics
Derived here, not cited (intent decision 2). Symbols: s is distance along the pipe; a, v, l are its along, vertical and lateral directions (SPEC §3); u_a, w, u_l the displacement along, vertical (positive down) and lateral (positive to the right); r = D/2 the outside radius.

1. **Axial strain.** Two points on the pipe's axis at s and s + Δs, distance Δs apart, move by u(s) and u(s + Δs). The new distance between them is |Δs a + Δu| = Δs √((1 + Δu_a/Δs)² + (Δw/Δs)² + (Δu_l/Δs)²). The strain, change in length over original length, is Δu_a/Δs + ½((Δw/Δs)² + (Δu_l/Δs)²) + higher terms. The second term is half the slope squared: 5 × 10⁻⁷ at a slope of 10⁻³, 5 × 10⁻⁵ at 10⁻². It is dropped, as the field is a small-displacement one (recorded as an assumption). Then:
   - analytical: ε_a = du_a/ds, the profile's `along_strain`;
   - discrete, over a span h centered on the station: ε_a,d(s) = (u_a(s + h/2) − u_a(s − h/2))/h.
2. **Bending strain at the outermost fiber.** Plane sections stay plane. A length of the neutral axis bent to radius R subtends dφ = ds/R; a fiber a distance y from it, away from the center of curvature, has length (R + y) dφ, so its strain is y/R = yκ. The outermost fiber is at y = r, so |ε_b| = r|κ|. The pipe follows the ground (intent decision 6), so its curvature is the ground's: κ = w''/(1 + w'²)^(3/2) ≈ d²w/ds², with the same small-slope approximation as above. In the vertical plane, ε_b,v = r κ_v with κ_v = `vertical_curvature`; in the lateral plane, ε_b,l = r κ_l with κ_l = `lateral_curvature`. Positive curvature is hogging in the vertical plane (SPEC §3), and in either plane it puts the fiber on the side opposite the positive direction in tension: the crown for vertical, the left side for lateral.
3. **Resultant, for a circular section.** A fiber at angle φ around the section is at r(cos φ, sin φ) in the (v, l) plane, so its bending strain is −r(κ_v cos φ + κ_l sin φ), which is largest over φ at r√(κ_v² + κ_l²). So the peak fiber strain comes from the resultant curvature |κ| = √(κ_v² + κ_l²), and bending is checked on ε_b = r|κ| (intent decision 5). A section that isn't circular would need its own section modulus in each plane, which is why "utilities are circular" is an assumption.
4. **Combined strain.** Axial strain is uniform over the section and bending strain linear across it, so they add: a fiber's strain is ε_a + ε_b(φ), between ε_a − r|κ| and ε_a + r|κ|. Axial strain never counts as helping (intent decision 7):
   - tensile: ε_t = max(ε_a, 0) + r|κ|;
   - compressive: ε_c = min(ε_a, 0) − r|κ| (negative, as compression is, SPEC §8.1).
5. **Radius of curvature:** R = 1/|κ|, infinite where κ_v = κ_l = 0.
6. **Discrete curvature, from three points.** Take three points on the displaced pipe at s − h, s and s + h, with displacements w₋, w₀, w₊ in one plane. The circle through three points has curvature 4A/(|P₁P₂| |P₂P₃| |P₁P₃|), with A the triangle's area. Here 2A = |h(w₊ − 2w₀ + w₋)| and the sides are h, h and 2h, each times 1 + O(slope²). So, with the same small-slope approximation as the analytical curvature, κ_d = (w₊ − 2w₀ + w₋)/h², the second difference, in each plane. The discrete resultant, bending, combined strains and radius follow from κ_v,d, κ_l,d and ε_a,d by items 3–5. Keeping the same approximation in both means their difference comes from the interval only.
7. **Discrete values are averages of analytical ones.** (u_a(s + h/2) − u_a(s − h/2))/h is the mean of ε_a over the span, and the second difference is the mean of d²w/ds² weighted by a triangle of base 2h. So, in each plane, the discrete peak never exceeds the analytical one, and the discrete radius is never the smaller. Only the combined strains, which add averages over spans of different length, could have a discrete value larger than the analytical one, and Claude found no smooth field where they do. This is why the discrete value is expected to be the smaller, though nothing assumes it (intent decision 3).

### The perpendicular bound (TODO #10)
For one transverse trough and a level, straight pipe that crosses the tunnel at angle θ in plan (90° is perpendicular), offset from the axis is o = s′ sin θ, with s′ the distance along the pipe from the crossing. A horizontal movement u_n normal to the tunnel resolves into sin θ along the pipe and cos θ across it. So, each with its derivatives taken at o:
- ε_a = sin²θ · du_n/do;
- κ_v = sin²θ · d²S/do²;
- κ_l = sin²θ cos θ · d²u_n/do².

With both width methods, u_n = −c₁ (o/i) S (SPEC §3). Then, with ρ = o/i and S = S_max e^(−ρ²/2):
- du_n/do = −c₁ (S_max/i)(1 − ρ²)e^(−ρ²/2);
- d²S/do² = (S_max/i²)(ρ² − 1)e^(−ρ²/2);
- d²u_n/do² = c₁ (S_max/i²) ρ(3 − ρ²)e^(−ρ²/2), whose peaks are the zeros of ρ⁴ − 6ρ² + 3, at ρ = 0.74196 and 2.33441 (M1's lateral-curvature peaks).

Axial strain and vertical curvature scale with sin²θ, so they never exceed the perpendicular case. Lateral curvature adds to the resultant, but on the same factor sin²θ. In units of c₁S_max/i, the combined strains are sin²θ [max(−(1 − ρ²), 0) + λ f(ρ, θ)] e^(−ρ²/2) and sin²θ [min(−(1 − ρ²), 0) − λ f(ρ, θ)] e^(−ρ²/2), with λ = r/(c₁ i) and f = √((ρ² − 1)² + c₁² cos²θ ρ²(3 − ρ²)²). Claude's calculation (2026-11-06), on a grid of θ from 0.5° to 90° in 0.5° steps and ρ from 0 to 6 in steps of 0.001: for c₁ = 0.25, 0.5 and 1 and λ = 0.01, 0.1, 1 and 10, the largest resultant curvature, tensile strain and compressive strain over every θ is the perpendicular one (ratio 1.0000, at θ = 90°). So, **for one trough, at any depth above the crown and with either width method, a pipe built perpendicular bounds the same pipe at any crossing angle.** The argument doesn't cover troughs that are superposed (SPEC §3, M2 (a)), the longitudinal trough or face passage (M6), or a pipe that changes depth. It is the hand calculation TODO #10 asked for. Golden value 3 checks the scaling on an oblique pipe.

### Hand calculations (golden values)
**Case A, one tunnel and a perpendicular pipe:** an idealized tunnel with axis depth z₀ = 20 m and diameter D = 6 m; `transverse_trough` with volume loss V_L = 1 % and `linear_trough_width(trough_width_parameter=0.5)`. The pipe crosses perpendicular at axis depth z_p = 2 m, with outside diameter 0.3 m (r = 0.15 m), from offset −40 m to +40 m (the crossing is at distance 40 m).
- i = 0.5 (20 − 2) = 9 m; V = V_L πD²/4 = 0.282743 m³/m; S_max = V/(√(2π) i) = 0.0125331 m; z₀ − z_p = 18 m.
- **At the center, o = 0** (Eq. 7, and Eq. 9's field there):
  - ε_a = −S_max/(z₀ − z_p) = −696.29 µε;
  - κ_v = −S_max/i² = −1.54730 × 10⁻⁴ 1/m; ε_b = 23.210 µε;
  - ε_t = 23.210 µε; ε_c = −719.50 µε;
  - R = i²/S_max = 6462.9 m.
- **At o = ±√3 i = ±15.5885 m** (Eqs. 8, 9):
  - ε_a = 0.44626 S_max/(z₀ − z_p) = 310.72 µε;
  - κ_v = 0.44626 S_max/i² = 6.90499 × 10⁻⁵ 1/m; ε_b = 10.357 µε;
  - ε_t = 321.08 µε.
- **Governing:** in this case ε_a and κ_v have the same shape, (ρ² − 1)e^(−ρ²/2), so ε_t = S_max (1/(z₀ − z_p) + r/i²)(ρ² − 1)e^(−ρ²/2) where ρ > 1, and it peaks at ρ = √3 exactly, as p. 662 says. The governing analytical values: axial tension 310.72 µε at 24.4115 m (of the two, ±√3 i, the smaller distance); axial compression −696.29 µε at 40 m; bending 23.210 µε at 40 m; tensile 321.08 µε at 24.4115 m; compressive −719.50 µε at 40 m; smallest radius 6462.9 m at 40 m.
- **Lateral:** κ_l = 0 at every station (SPEC §7: from the calculation, not by assumption).

**Case B, discrete, on case A:**
- **At the center**, with a = h²/(2i²) and b = h²/(8i²):
  - κ_v,d = (2S_max/h²)(e^(−a) − 1) = −(S_max/i²)(1 − e^(−a))/a;
  - ε_a,d = (u(h/2) − u(−h/2))/h with u(o) = −(o/(z₀ − z_p)) S_max e^(−o²/2i²), so −(S_max/(z₀ − z_p)) e^(−b).
- **At o = √3 i**, with δ = h/i and g(ρ) = e^(−ρ²/2):
  - κ_v,d = (S_max/i²)(g(√3 + δ) − 2g(√3) + g(√3 − δ))/δ²;
  - ε_a,d = (u(o + h/2) − u(o − h/2))/h.

| h | κ ratio at center | ε_a ratio at center | κ_v,d at center (1/m) | ε_a,d at center | ε_c,d at center | κ_v,d at √3 i (1/m) | ε_a,d at √3 i | ε_t,d at √3 i |
|---|---|---|---|---|---|---|---|---|
| 1 m | 0.996920 | 0.998458 | −1.54254 × 10⁻⁴ | −695.21 µε | −718.35 µε | 6.88370 × 10⁻⁵ | 310.25 µε | 320.57 µε |
| 9 m (= i) | 0.786939 | 0.882497 | −1.21763 × 10⁻⁴ | −614.47 µε | −632.73 µε | 5.30152 × 10⁻⁵ | 272.88 µε | 280.83 µε |

At h = 1 m the analytical values govern every check, by 0.2 to 0.3 %. At h = i the governing compressive strains are both at the center, by symmetry, so the difference is −632.73 − (−719.50) = +86.77 µε. The discrete tensile peak, by contrast, moves off √3 i: 283.27 µε at 16.286 m, against 280.83 µε at √3 i (Claude's dense evaluation of the formulas above). So the table gives values at their stations, not governing values.

**Case C, an oblique pipe at 45°:** case A's tunnel and trough, with the tunnel at azimuth 0 through the origin (so offset is x) and the pipe given by vertices (−40 sin 45°, −40 cos 45°, 2) and (40 sin 45°, 40 cos 45°, 2), level at depth 2 m, crossing at distance 40 m. sin²θ = 0.5 and cos θ = 0.707107.
- **At the crossing:** κ_v = −7.73651 × 10⁻⁵ 1/m; κ_l = 0; ε_a = −348.14 µε. Half of case A, as sin²θ says.
- **At ρ = 0.741964** (o = 6.67767 m, distance 40 + 9.44366 m):
  - κ_l = cos θ sin²θ (S_max/(i(z₀ − z_p))) ρ(3 − ρ²)e^(−ρ²/2) = 3.77500 × 10⁻⁵ 1/m;
  - κ_v = −2.64072 × 10⁻⁵ 1/m;
  - |κ| = 4.60695 × 10⁻⁵ 1/m; ε_b = 6.9104 µε;
  - ε_a = −118.83 µε; ε_t = 6.9104 µε (the axial strain is compressive, so it doesn't help); ε_c = −125.74 µε.

  κ_l is positive: the pipe's lateral direction (a_y, −a_x, 0) is (cos θ, −sin θ, 0), so lateral = u_x cos θ (SPEC §3).

The hand calculations' arithmetic was done by Claude (2026-11-06) from the formulas above. Tolerance 0.5 % (SPEC §2.4), except where the formulas are exact and the code's are too (the discrete values, from four exact evaluations): 1e-9 relative.

### Changes
- **SPEC §3:** the bullet "Closed-form sources return exact derivatives" is decided: an assessment evaluates the source at its own points, the discrete samples and the peaks of its own quantities (decisions 5, 7).
- **SPEC §5.1:** the checks table gains its analytical and discrete columns (decision 11).
- **SPEC §5.3:** `gs.sweep` rows gain each check's value, utilization and pass/fail. SPEC §5.3 already says so, but M1 (c) built no checks, so `_sweep.py` doesn't yet.
- **SPEC §7:** the API, the limits and the discrete definitions (decisions 1–8).
- **SPEC §9:** the profile figure of a check result (decision 13).
- **`docs/reference/sources.md`:** `bracegirdle1996` is also cited for Eqs. 7–9 (p. 662), the approach (pp. 660, 663) and the combined tensile strain (p. 663), verified 2026-11-06.
- **`docs/TODO.md` #10:** the perpendicular bound is written in this spec, for one trough. The user-docs section and M6's numerical check stay, and Bracegirdle et al.'s p. 663 remark on parallel pipes is added.
- **New:** `gs.check_continuous_pipe`; the profile figure draws its result.
- **At close-out:** SPEC §1.3 gains the assumptions that utilities are circular and strain is at the outermost fiber; a user guide page, "Continuous pipes", with its example (1 m interval, decision 4 of the intent), including the perpendicular bound.

### Decisions

**The API (intent: "The API")**

1. 🟡 **`gs.check_continuous_pipe(profile, *, interval, interaction, tensile_strain_limit, compressive_strain_limit, bending_strain_limit, radius_of_curvature_limit) -> Result`**, at the top level beside `gs.movement_profile`. Its name says the pipe is continuous; M3 (b) adds `gs.check_jointed_pipe`, which takes pipe lengths. `profile` is a `Result` from `gs.movement_profile` (its `analysis` is `"movement_profile"` and it keeps its source and asset); anything else raises `TypeError`. The profile is the boundary (SPEC §3), and it carries the caller's `spacing`. Considered and dropped:
   - **A pipe object that carries its limits:** SPEC §8.5 keeps objects thin, and limits are a project's judgment, not the pipe's.
   - **One `limits=` mapping:** a missing key can't be a named missing judgment.
   - **Taking the utility and source and building the profile inside:** it hides the profile, which is a result in its own right.
2. 🟡 **The judgments,** each a required keyword with no default (SPEC §4):
   - `interval`: a length, positive and finite, in m if a plain number. Independent of the profile's `spacing` (decision 5).
   - `interaction`: only `"greenfield"`, recorded as a design judgment by name; anything else raises `ValueError` naming the one value Phase 1 takes (SPEC §4).
   - `tensile_strain_limit`, `compressive_strain_limit`, `bending_strain_limit`: strains, each a positive magnitude, as pint quantities only (a plain number is refused, SPEC §6; `0.1 * gs.units.percent` or `gs.units.Quantity(1000, "µε")`).
   - `radius_of_curvature_limit`: the smallest radius allowed, a positive length.

   The bending limit is a judgment of its own (review, 2026-11-06), because some materials are given a bending limit separate from the axial and combined ones. It is required like the others, not optional: an omitted limit that fell back to the smaller strain limit would be a default for a judgment (SPEC §4). A caller who wants that fallback writes `bending_strain_limit=min(tensile, compressive)`, and the docs show it.

   Each limit can be `None`, given explicitly: no limit for that check (decision 3). A limit that isn't positive raises `ValueError`.
3. 🟡 **A check with no limit is reported without a utilization.** Its row has its values, with `limit` and `utilization` NaN and `passes` missing (pandas `NA`). The result's assumptions say which checks had no limit. That keeps SPEC §7's "every check runs and is reported", and lets a caller with only a tensile limit (iron, Bracegirdle et al.'s Table 4) leave the radius unchecked by saying so. Its input record has the value `"none"` and given-as `"none"`.
4. 🟡 **The checks, and the limit each is checked against:**

   | check | value | limit | utilization |
   |---|---|---|---|
   | `axial_tension` | the largest positive ε_a | tensile | ε / limit |
   | `axial_compression` | the most negative ε_a | compressive | \|ε\| / limit |
   | `bending` | the largest ε_b = r\|κ\| | bending | ε / limit |
   | `tensile_strain` | the largest ε_t | tensile | ε / limit |
   | `compressive_strain` | the most negative ε_c | compressive | \|ε\| / limit |
   | `radius_of_curvature` | the smallest R | radius | limit / R |

   `passes` is utilization ≤ 1. Bending in each plane is reported in `values` and drawn, but not checked: it is checked on the resultant (intent decision 5). If no station has a value of a check's sign (no tension anywhere on a short pipe), its value and distance are NaN and it passes, as `Result.governing()` does (SPEC §5.1).

**Discrete sampling (intent: "Discrete sampling", "The utility's ends", "Peaks")**

5. 🟡 **Centered on each station, independent of `spacing`.** At every row of the result (the profile's stations and the peaks of decision 7), the source is evaluated on the pipe's line at s ± h/2 for ε_a,d and at s ± h for κ_d (s itself is the station), and resolved into along, vertical and lateral as the profile is. Each station gets a discrete value, so the analytical and discrete values are compared at the same places, including the critical distances (intent: "Peaks"). The interval and spacing answer different questions: spacing is where values are reported, the interval is the span practice uses. Tying them would make a fine spacing give a fine interval.
6. 🟡 **At the ends, the point has no discrete value** where a sample would fall beyond the pipe: ε_a,d where s < h/2 or s > L − h/2, and κ_d (and so the discrete bending, combined strain and radius) where s < h or s > L − h, each within the profile's 1 µm merge tolerance. They are NaN, with a flag of verdict `within` that names them and why (SPEC §10), so the validity doesn't change. The analytical values still cover them. If no station has a discrete value (L < 2h), the check still runs, flagged the same way.
   - Considered: sampling the ground beyond the ends, since the field exists there and a pipe built from station and offset is usually a section of a longer line. Dropped: it assumes the pipe continues straight past where the caller ended it, which garisenda can't know. A caller who wants the ends covered can extend the pipe.
   - Samples are on the pipe's own line, within h of a station, so the source's flags at them aren't added; the station's verdict stands.
7. 🟡 **The check finds its own peaks.** The resultant curvature and the combined strains peak where none of the source's critical distances are: on an oblique pipe, between the peaks of κ_v and κ_l (case C). The check adds rows at the zeros, along the pipe, of d|κ|²/ds, dε_t/ds and dε_c/ds, found by root-finding on the source's exact derivatives (including the third, SPEC §3) with the sampling and tolerance of `find_critical_distances` (1/8 of the feature length, refined to 1e-9 m). Each row's profile columns are computed by the same code as the profile's, and it is marked `critical`. Without them, the reported peak could fall short of the true one by a fraction of order (spacing/i)²/8: 0.15 % at 1 m in case A, 12 % at spacing i. Moving that root-finding into the source's `critical_distances` was considered and dropped: ε_t depends on the pipe's radius, which a source doesn't know. Flags' points are renumbered to the new rows.
8. 🟡 **No flag ties the interval to the field's feature length.** No source gives a threshold, and the difference column shows the effect.

**The two values (intent: "Radius of curvature")**

9. 🟡 **The worse governs, per check.** For each check, the analytical value is the extreme over the rows of its analytical column, and the discrete value the extreme over the rows that have one (NaN if none). `value` is the larger in size, or the smaller for the radius, and `governed_by` says which (`"analytical"` on a tie). `difference` is discrete − analytical, in the check's unit and signed as the values are. So a less severe discrete value gives a negative difference for tension and bending, and a positive one for compression and the radius.
10. 🟡 **The radius** is 1/|κ| of the resultant, analytical and discrete, infinite where |κ| = 0 (in `to_dict()` that is `None`, as every non-finite number is).

**The result**

11. 🟡 **Its parts.** `analysis` is `"continuous_pipe_check"` and `subject` the utility's id. `values` keeps every column of the profile, with units, and adds:
    - analytical: `axial_strain` (the pipe's; equal to `along_strain` while greenfield, and kept apart so interaction can make them differ), `vertical_bending_strain`, `lateral_bending_strain` (r κ, signed as the curvature), `resultant_curvature`, `bending_strain` (r|κ|), `tensile_strain`, `compressive_strain`, `radius_of_curvature`;
    - discrete: `discrete_axial_strain`, `discrete_vertical_curvature`, `discrete_lateral_curvature`, `discrete_resultant_curvature`, `discrete_bending_strain`, `discrete_tensile_strain`, `discrete_compressive_strain`, `discrete_radius_of_curvature`.

    `checks` has one row per check in decision 4's order, with columns `check`, `value`, `unit`, `limit`, `utilization`, `governing_distance`, `passes`, `governed_by`, `analytical`, `analytical_distance`, `discrete`, `discrete_distance`, `difference`. `CHECK_COLUMNS` grows to match, and an empty checks table (a movement profile's) has them all. `method` adds a record "Strain checks for a continuous pipe" with the equations of Mechanics 1–6 and the source "Mechanics, derived in the M3 (a) spec; the approach after Bracegirdle et al. (1996), pp. 660, 663". `inputs` adds the six judgments. `validity` and `warnings` are the profile's, plus decision 6's flag. `governing()` is unchanged: it reads the ground's columns, and the checks table holds the pipe's.
12. 🟡 **Assumptions recorded,** after the profile's:
    - the pipe follows the ground, with no reduction for its stiffness or for slip; soil–structure interaction would reduce the strains (SPEC §1.3, §13 Q1);
    - the section is circular and strain is taken at the outermost fiber, from the given outside diameter;
    - small displacements and slopes (Mechanics 1, 2);
    - combined strain never counts axial strain as helping;
    - the discrete interval and where it samples;
    - any check with no limit (decision 3).

    The summary (`repr`) adds one line per check: its value, where, which governed, and its utilization against its limit.

**The figure**

13. 🟡 **`gs.plot.profile` draws a check result in six panels;** a movement profile still gets its four. The panels, sharing distance:
    1. settlement;
    2. horizontal movement;
    3. axial strain, with the tensile and compressive limits;
    4. curvature: vertical, lateral and resultant, with ±1/radius limit;
    5. bending strain: vertical, lateral and resultant, with the bending limit;
    6. combined strain: tensile and compressive, with their limits.

    Analytical values are solid lines and discrete ones dashed, in the same color, with gaps where a station has no discrete value. Limits are thin horizontal lines, labeled with their value. Each check's governing value is marked with its value and utilization. A check with no limit has no limit line, and the panel's note says so. Every line has a `gid` named for its column, and each limit line `"<limit name>"`. `axs=` takes six Axes for a check result. Curvature carries the radius check because a radius is infinite at an inflection and can't be drawn on a linear axis.

14. 🟡 **Golden values run through the one analysis** (SPEC §11): cases A and B through `perpendicular_utility`, case C through a `Utility` given by its vertices.

### Sources
- **bracegirdle1996:** Bracegirdle et al. (1996), Eqs. 7–9 (p. 662), the approach (pp. 660, 663), the combined tensile strain (p. 663). Verified against the source on 2026-11-06.
- The mechanics is derived above (intent decision 2) and needs no source.

### Acceptance criteria
1. **Case A, analytical:** each value of case A at its station (center, ±√3 i), and the governing analytical values and distances of all six checks, within 0.5 %. `lateral_curvature` and the lateral bending strain are exactly zero.
2. **Eqs. 7–9:** for case A, |κ_v| at the center equals S_max/i², and κ_v and ε_a at √3 i equal 0.446 S_max/i² and 0.446 S_max/(z₀ − z_p), within 0.5 % (Bracegirdle et al. round to three figures).
3. **Case B, discrete:** the discrete values of case B's table at h = 1 m and h = 9 m, within 1e-9 relative. `governed_by` is `"analytical"` for every check at h = 1 m, and the compressive strain's `difference` at h = 9 m is +86.77 µε, within 0.5 %.
4. **Case C, oblique:** case C's values at the crossing and at ρ = 0.741964 (at that distance, a station of the profile), within 0.5 %. The analytical values are half of case A's at the crossing, per sin²θ.
5. **The check's own peaks:** for case C and for the twin tunnels of M2 (a)'s tests, the governing resultant curvature, tensile and compressive strains are at least the largest values found by evaluating the source independently every 1 mm along the pipe and computing them from Mechanics 2–4, and exceed them by no more than 1e-9 relative. The rows added for them are marked `critical`.
6. **Discrete converges on analytical:** on case C at h = 0.01 m, every discrete column is within 1e-4 of its analytical column's largest size, at every station with a discrete value (SPEC §2.4). For case A and case C at h = 1 m and 9 m, the discrete peak of each per-plane value is no larger than the analytical one (Mechanics 7).
7. **Ends:** stations within h/2 (axial) or h (curvature) of an end have NaN discrete values, and one `within` flag names them and why; the validity is the profile's. A pipe shorter than 2h has no discrete curvature, is flagged, and its checks are governed by the analytical values.
8. **Limits and utilization:** with limits given, each check's utilization and `passes` follow decision 4; a utilization above 1 fails; the radius utilization is limit/R. With a limit `None`, that check has NaN limit and utilization and `passes` NA, and the assumption names it. The bending check uses `bending_strain_limit` alone, whatever the other limits are.
9. **The worse governs:** the rule of decision 9, including ties and a check with no discrete value, tested on the function that picks the governing value. No smooth field is known to make the discrete value govern (Mechanics 7), so there is no end-to-end case.
10. **Judgments:** each of the six, missing, raises `TypeError` naming it, what it depends on and how to set it. A plain number for a strain limit is refused; `interaction` other than `"greenfield"` raises `ValueError`; a non-positive interval or limit raises `ValueError`. Every judgment appears in `inputs` with its kind and how it was given, `None` included.
11. **Not a profile:** passing anything but a movement profile `Result` raises `TypeError`.
12. **Reversal:** reversing the pipe leaves every check's value and utilization unchanged, and moves each governing distance to L − d.
13. **Result shape:** `to_dict()` is JSON-serializable (infinite radii as `None`), `to_frame()` has the new columns with units, the summary lists each check, and a movement profile's empty checks table has the new columns.
14. **Sweep:** a `gs.sweep` row over volume loss equals a direct call with the same inputs, including each check's value, utilization and pass/fail (SPEC §11).
15. **Figure:** a check result draws six panels, found by `gid`, with the analytical and discrete lines, each limit line, and each governing marker; a limit given as `None` draws no line; a movement profile still draws four panels; `rcParams` are unchanged. Checked by eye at close-out.
16. **Docs:** the API reference has `check_continuous_pipe`, with Mechanics 1–6 in its docstring and the source; the guide page's example runs in the docs build.
