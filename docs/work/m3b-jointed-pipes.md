# M3 (b): jointed pipes

## Intent

### Goal
A caller can check a jointed pipe (cast iron, ductile iron, clay, concrete) against the movement profile along it. The check reports joint rotation and joint pullout at the worst joint position, and the barrel's strains as M3 (a) computes them, with the pipe length as the discrete interval (SPEC §7). Each quantity is checked against a limit the caller gives, or against an opt-in, cited preset of limits for iron pipes from Bracegirdle et al. (1996). The profile figure shows every check against its limit. M3 is then done, once a real crossing has been compared with the spreadsheet locally and every difference explained (SPEC §12.4).

### Why
- **SPEC §12.4:** M3 (b) finishes M3, and with it the spreadsheet is replaced for utilities.
- **Most old mains are jointed.** Cast iron mains with lead-yarn or rubber-gasket joints are the case Bracegirdle et al. (1996) were written for. Their joints usually govern, not the barrel.
- **No published joint-by-joint method can be verified.** No clean copy of Bracegirdle et al. (1996) and no copy of Attewell et al. (1986) can be found (2026-11-06). What has been read:
  - Bracegirdle et al. give only bounds for one Gaussian trough: rotation θ = 2 tan⁻¹(S_max/(√(2π) i)) for transverse pipes (Eq. 5) and tan⁻¹(0.4 S_max/i) for parallel ones (Eq. 6), and pullout equal to the maximum horizontal movement (p. 661). Eq. 3, their horizontal movement, is smudged.
  - Eq. 5 doesn't match the steepest slope of the trough (TODO #4). With Attewell et al. unread, it can't be checked.

  So joint rotation and pullout are defined in this unit's spec as geometry, garisenda's own, derived and not cited, as M3 (a)'s mechanics were (SPEC §7). Golden values come from hand calculations of that geometry (SPEC §2.4).
- **The geometry reuses M3 (a).** Take rigid pipes of length L whose joints follow the ground. The rotation at a joint is then the angle between the chords of the two pipes meeting there: the second difference of the movement across the pipe at s − L, s, s + L, divided by L. That is M3 (a)'s discrete curvature at interval L, times L, in each plane and as the resultant. The worst joint position is the peak of that function of s, found the way M3 (a) finds its own peaks. One way to get pullout (🟡, spec) is to let each pipe move with the along-pipe movement at its midpoint. The opening at a joint is then u(s + L/2) − u(s − L/2): M3 (a)'s discrete axial strain at interval L, times L.
- **Limits:** the iron presets were decided in M3 (a)'s intent (TODO #6): Table 2 (joint rotation and pullout for lead-yarn and rubber-gasket joints, after Attewell et al. 1986, p. 661), and Table 4 and Herbert & Leach (1990)'s grey iron values for strain (p. 662). They are cited from Bracegirdle et al. under SPEC §2.1's rule for a quoted table.
- **What depends on it:** M4's buildings use the same analytical/discrete pattern; M5 runs the check on real alignments, where given joint locations become possible.

### Constraints
- **SPEC §3:** the check consumes the movement profile. It evaluates the source only at points on the pipe's own line, as M3 (a)'s discrete samples do.
- **SPEC §4:** the pipe length, the joint limits, the strain limits and `interaction` are required, keyword-only judgments with no default. Presets are opt-in, passed by name, and recorded with their source.
- **SPEC §7:** every check runs and is reported. A jointed pipe's discrete interval is its pipe length. Pipe lengths are a table keyed by pipe type and diameter, and a pair that isn't in the table is an error. The joint position is the worst case over every position.
- **SPEC §1.3:** greenfield. The barrel follows the ground for its strains, and the joints follow the ground for rotation and pullout. These are two idealizations, each conservative for its own quantity, and both are recorded on the result.
- **SPEC §2.1, §2.4:** Eqs. 3 and 5 aren't used: Eq. 3 can't be read and Eq. 5 can't be checked. Golden values come from hand calculations written out in the spec.
- **SPEC §10:** at the ends, where a joint's neighbor would fall beyond the pipe, nothing is filled. Those positions are flagged, as M3 (a)'s ends are.
- **Test on segments at any angle** (CLAUDE.md): an oblique pipe's joints rotate in the lateral plane too.
- **SPEC §9, §12.3:** the profile figure shows every check, and the user docs and their example are written at close-out.
- **The repo is public:** the spreadsheet comparison is run on the work machine. Only its outcome ("done, differences explained") goes in the repo.

### Out of scope
- **Movement toward the axis** (Eq. 3) as a named horizontal movement method: not offered until a clean copy confirms Eq. 3 (TODO #4).
- **Bracegirdle et al.'s Eq. 5 as a golden value or a reported bound.** The spec compares it with the geometry by hand, to explain the difference, and records the result in TODO #4.
- **Eq. 6 and parallel pipes:** the longitudinal trough is M6.
- **Given joint locations:** M5, with real geometry (decision 4).
- **Pipe-length presets:** none until a citable source is found (decision 2, TODO #5).
- **Joint stiffness, slip and soil–structure interaction:** later phases (SPEC §1.3, §13 Q1).
- **Limits and pipe lengths for other materials:** TODO #13 and #5.
- **The slope criterion:** TODO #12.

### SPEC sections touched
- **§7:** the jointed-pipe check, its API and the definitions of joint rotation and pullout, with how the worst joint position is found. The pipe-length table takes the pipe type from the caller (decision 3); the worst case is the only joint position until M5 (decision 4).
- **§4:** the first shipped presets and their namespace (`gs.presets`).
- **§1.3:** the joint idealization (rigid pipes, joints following the ground) joins the Phase 1 assumptions.
- **§2.1:** Eqs. 3 and 5 are recorded as unusable until verified, at the spec step.
- **§12.4:** M3 marked done at close-out, with the spreadsheet comparison.
- **§3, §5.1, §9:** the check's result and figure, at the spec step.
- **`docs/TODO.md`:** #4 (joint definitions decided, Eq. 5's comparison), #5 (pipe length presets), #6 (presets built).
- **`docs/reference/sources.md`:** Bracegirdle et al. (1996) gains Tables 2 and 4, Eqs. 5–6 (not used) and p. 661.

### Decisions (intent review, 2026-11-06)
1. **The iron joint-limit preset ships Table 2's rotation and pullout limits, with a caveat on pullout.** Bracegirdle et al. pair the pullout limits with a pullout taken as the maximum horizontal movement under Eq. 3's field. That definition is larger than garisenda's joint opening. No clean copy of Bracegirdle et al. and no copy of Attewell et al. (1986) can be found, so how the limits were calibrated can't be checked. The preset's record, the result's assumptions and the docs say that checking garisenda's opening against these limits is unconservative against the published method. Dropping pullout from the preset was considered. It was rejected because the limits are still the only published ones, and the caveat lets the engineer judge them.
2. **No pipe-length preset in M3 (b).** No citable source for nominal laying lengths has been found (TODO #5, which stays open). The caller always gives the pipe lengths.
3. **Pipe lengths are a table keyed by pipe type and diameter, with `pipe_type` given by the caller**, as SPEC §7 has it. The check looks up the utility's outside diameter under the given type. A missing pair is an error that names it, and nothing is filled from the nearest diameter. The result records the length used and the table's source. A single `pipe_length=` was considered. It was dropped to keep SPEC §7's table, which will be what a preset slots into later.
4. **Worst joint position only.** Given joint locations come with real geometry and surveys (M5). SPEC §7's "unless joint locations are given" stays, noted as M5.

### 🟡 To settle in the spec
- **The API.** Proposed: `gs.check_jointed_pipe(profile, *, pipe_lengths, pipe_type, interaction, joint_rotation_limit, joint_pullout_limit, ...strain limits)`, beside `gs.check_continuous_pipe`. Settle the table's form (a mapping or a DataFrame with units), how the diameter is matched (exact, or within a tolerance of nominal against outside diameter), and whether `Utility` should carry its type instead.
- **Pullout.** It could come from the midpoint movement u(s + L/2) − u(s − L/2), from each pipe's average along-pipe movement, or from the whole stretch of one pipe put into one joint. Also to settle: whether the flexural opening θ·D/2 is added, reported apart or combined, and whether a joint closing (negative pullout) is reported.
- **The worst joint position.** The peak over s of the rotation and pullout functions, by root-finding on exact derivatives. Settle whether joints sit at s₀ + kL with s₀ swept over [0, L), the worst joint taken over all of them, or whether every station is treated as a possible joint. They give the same peak; they differ in what the figure shows.
- **Barrel strain at interval L.** SPEC §7 makes the pipe length the discrete interval, so the discrete curvature spans one pipe length either side. Confirm that this, and not a separate `interval`, is what the spreadsheet compares against.
- **The presets' shape:** Table 2 by joint type and diameter, Table 4 by material. Settle how a preset's missing entry is an error, how the result records the preset's name, table and row, and where decision 1's caveat is attached.
- **Golden values:**
  - one Gaussian trough, the joint at the center: θ = 2 S_max (1 − e^(−L²/2i²))/L, with its maximum over L (L ≈ 1.585 i, θ ≈ 0.902 S_max/i; Claude's hand calculation, 2026-11-06, to be written out). The worst position away from the center is checked against dense sampling;
  - pullout from the linear width method's closed-form horizontal movement;
  - an oblique pipe's lateral rotation;
  - Eq. 5 compared with these, to explain the difference (not a golden value).

## Spec

No topic doc holds this, so the spec is here. It settles the intent's "To settle in the spec" items (decisions 1–17). Every 🟡 proposal below was accepted in review (2026-11-06), and decision 8 was confirmed against the spreadsheet. It builds on M3 (a)'s spec (`docs/work/m3a-continuous-pipes.md`), whose mechanics, discrete sampling and result it reuses with the interval set to the pipe length. Bracegirdle et al. (1996) was read again on 2026-11-06 from the same copy as M3 (a) (`../hangtu/sandbox/sources/inbox/1996_109.pdf`). Tables 2 and 4, Eqs. 5–6, the pullout sentence, Herbert & Leach's values and the p. 663 sentence on rigid joints were checked against the page images (pp. 661–663). The text layer garbles them.

### What the paper says
- **p. 661, §5:** "Attewell et al (1986) give guidance for cast iron mains subjected to ground movements, as shown in Table 2." Table 2, "Allowable joint rotation and pull-out", rotation θ in degrees and pull-out R in mm:

  | Description | Rotation θ (°) | Pull-out R (mm) |
  |---|---|---|
  | lead-yarn joint in gas main with history of leaks | none | none |
  | lead-yarn joint in sound gas main | 1.0 | 10 |
  | lead-yarn joint in water mains | 1.5 | 15 |
  | rubber gasket joint in gas or water mains | 2.5 | 25 |

  The rows are by joint and service. None is by diameter, as the intent's 🟡 list supposed.
- **p. 661, after Table 2:** "Where there is sufficient information, or in the case of particularly sensitive services, individual joints may be considered. Alternatively, it may be conservatively assumed that joint rotation, θ, is given by: θ = 2 tan⁻¹(S_v max/(√(2π) i)) (5) where pipes are transverse to the tunnel line, or, θ = tan⁻¹(0.4 S_v max/i) (6) where pipes are parallel to the tunnel line. The above relationships assume the worst conceivable configuration of joints, and in some instances may be excessively conservative. Again conservatively, it may be assumed that the maximum potential pull-out is equal to the maximum predicted horizontal ground displacement due to tunnelling for both longitudinal and transverse directions." Eq. 5 is legible on the page image. What can't be checked is where it comes from (TODO #4).
- **So the paper presents individual joints as the primary method,** and Eq. 5 and the maximum horizontal movement as conservative shortcuts. garisenda computes individual joints. Intent decision 1's caveat stands, but its wording follows this (decision 12): checked against the paper's shortcut, garisenda's opening is smaller, and the shortcut's horizontal field (Eq. 3) can't be read with certainty.
- **p. 662, §6.1:** "Some conservatism is also required when assessing acceptable limits for additional strain due to ground movements in otherwise sound pipes. The criteria given in Table 4 are recommended for application to the simple methodology described in this paper." Table 4, "Recommended allowable increase in strain", in µε:

  | Material | tensile | compressive |
  |---|---|---|
  | pit cast and spun cast grey iron | 100 | 1200 |
  | ductile iron | 500 | 700 |

- **p. 662:** "The criteria in Table 4 are conservative; Herbert and Leach (1990) state that it is reasonable to allow up to 200µε for pipes in grey iron exceeding 300mm in diameter and 150µε for smaller pipes; values of 150 and 100µε respectively being applied in particularly adverse situations." Tensile only.
- **p. 663:** "it is assumed that pipes follow ground movements when calculating bending strain; ... pipe joints are conservatively assumed to be rigid." This is the published basis for checking the barrel of a jointed pipe as a continuous pipe (intent constraint, SPEC §1.3).

### Geometry
Derived here, not cited (intent). The symbols are M3 (a)'s: s is distance along the pipe; u_a, w and u_l are the displacement along it, vertical (positive down) and lateral; r = D/2. L is the pipe length.

1. **The idealization.** The line is a chain of rigid pipes of length L. Each joint is a point on the pipe's axis that moves with the ground. A pipe is then the chord between the displaced positions of its two joints. For the barrel's strains the joints are taken as rigid, and the barrel follows the ground (p. 663; M3 (a)). Each idealization is conservative for its own quantity:
   - joints that follow the ground take all the ground's bending and stretch into their rotation and opening;
   - a barrel that follows the ground takes all of it into its strain.
2. **Joint rotation.** Take a joint at s with neighbors at s − L and s + L. The two chords meeting at s have, in the vertical plane, slopes (w(s) − w(s − L))/L and (w(s + L) − w(s))/L, to first order in the slopes (the change in chord length from u_a is of order strain, dropped as in M3 (a), Mechanics 1). The angle between them is the difference of their slopes, to the same order: θ_v(s) = (w(s + L) − 2w(s) + w(s − L))/L, and likewise θ_l(s) from u_l. As in M3 (a), Mechanics 3, the rotation of a circular spigot in its socket is the resultant θ = √(θ_v² + θ_l²), which is checked. θ_v and θ_l are signed as the curvatures (positive hogging) and reported. This is M3 (a)'s discrete curvature at h = L, times L: θ_v = L κ_v,d.
   - Dropping tan⁻¹: the exact angle between the chords is tan⁻¹ of each slope, differenced. At slopes of 10⁻³ the two differ by about 10⁻⁶ relative, so they are equal for this check. It keeps one small-slope approximation throughout (M3 (a), Mechanics 6).
3. **Joint opening (pullout).** Each pipe moves along the line with the ground's along-pipe movement at its midpoint. The joint at s sits between the pipes centered at s − L/2 and s + L/2, so its opening is Δ(s) = u_a(s + L/2) − u_a(s − L/2), positive when it opens. This is M3 (a)'s discrete axial strain at h = L, times L: Δ = L ε_a,d.
   - **Compatible:** the openings of the joints along a run sum to the difference in movement between the run's end midpoints. So the joints take up exactly the ground's stretch, no more.
   - **The intent's other two candidates.** "The whole stretch of one pipe into one joint", u_a(s + L) − u_a(s), is Δ(s + L/2). It is the same function shifted by L/2, so it has the same worst value over every position. "Each pipe's average movement" weights a pipe's length uniformly, not at its midpoint. It needs quadrature for a general field, and differs from Δ by O(L² ε″). It was dropped for the midpoint, which is exact for the source's closed form and a linear field.
4. **The outer opening.** A joint that rotates by θ opens by rθ on one side of the spigot and closes by rθ on the other. The largest opening anywhere around the joint is Δ + rθ. It is reported, not checked (decision 6).
5. **Every position is a possible joint.** θ(s) and Δ(s) are the rotation and opening a joint would have if it were at s. The worst joint is their peak over s. A run of joints at s₀ + kL gives the same peak, swept over s₀ ∈ [0, L). Reporting the function of s draws one curve, and the peak is found exactly by root-finding (decision 7). A joint at s needs both neighbors on the pipe: s ∈ [L, ℓ − L] for rotation and [L/2, ℓ − L/2] for the opening, where ℓ is the pipe's length.

### Eq. 5 compared with the geometry (TODO #4; not a golden value)
For one Gaussian trough and a perpendicular pipe, take a joint at the trough's center, with x = L/i. By Geometry 2, θ = 2 S_max(1 − e^(−x²/2))/L = (S_max/i) · 2(1 − e^(−x²/2))/x. This is largest at x = 1.5852, where x² e^(−x²/2) = 1 − e^(−x²/2), and there θ = 0.9025 S_max/i. To small angles, Eq. 5 is 2/√(2π) · S_max/i = 0.7979 S_max/i.
- **The geometry exceeds Eq. 5 for 1.026 i < L < 2.347 i.** So Eq. 5 isn't "the worst conceivable configuration of joints" for every pipe length. For L = 4 m and i = 9 m (case J-A), the geometry gives 0.53 of Eq. 5.
- **A reading of where Eq. 5 comes from** (Claude's, not checked against Attewell et al. 1986): 2 tan⁻¹(S_max/(√(2π) i)) is exactly the rotation at the apex of a triangular trough with the same depth S_max and volume √(2π) i S_max as the Gaussian, whose sides each fall S_max over a half-width √(2π) i.
- None of this is reported, and Eq. 5 isn't used. It goes into TODO #4.

### Hand calculations (golden values)
The cases are built on M3 (a)'s cases A and C:
- an idealized tunnel with z₀ = 20 m and D = 6 m;
- V_L = 1 % and `linear_trough_width(trough_width_parameter=0.5)`;
- a pipe at depth 2 m with outside diameter 0.3 m, 80 m long, crossing at distance 40 m;
- i = 9 m, S_max = 0.0125331 m, z₀ − z_p = 18 m, and u_n(o) = −(o/18) S_max e^(−o²/2i²).

The pipe lengths are chosen for the test, not cited.

**Case J-A, perpendicular, L = 4 m:**
- **Center joint (s = 40 m):**
  - θ_v = −2 S_max(1 − e^(−L²/2i²))/L = −5.89338 × 10⁻⁴ rad (−0.033767°); θ_l = 0;
  - Δ = −(L/(z₀ − z_p)) S_max e^(−L²/8i²) = −2.71722 mm, closing.
- **Governing:**
  - rotation 5.89338 × 10⁻⁴ rad at 40 m;
  - opening 1.21274 mm at 24.2821 m, tied with 55.7179 m by symmetry, so the smaller distance is reported;
  - closure −2.71722 mm at 40 m;
  - the largest hogging θ_v is 2.63061 × 10⁻⁴ rad at 24.1537 m.
- **Compared with the shortcut:** the paper's pullout is the largest horizontal movement, S_max e^(−1/2) i/(z₀ − z_p) = 3.80087 mm. For one trough the opening can't exceed it: u_a rises by exactly u_max over each tension zone. Here the opening is 0.319 of it.

**Case J-B, perpendicular, L = 9 m (= i):**
- center joint: θ_v = −1.09587 × 10⁻³ rad, which is 9 m times case B's κ_v,d at the center (−1.21763 × 10⁻⁴ 1/m, h = 9 m); Δ = −5.53023 mm, which is 9 m times case B's ε_a,d (−614.47 µε);
- governing: rotation 1.09587 × 10⁻³ rad at 40 m; opening 2.47619 mm at 23.7327 m; closure −5.53023 mm at 40 m; hogging θ_v 4.91777 × 10⁻⁴ rad at 23.0876 m;
- the barrel's discrete values are case B's at h = 9 m.

**Case J-C, oblique at 45°, L = 4 m** (case C's pipe; u_a = sin θ u_n, u_l = cos θ u_n, offset o = s′ sin θ):
- **At s = 49.44365 m (ρ = 0.741964):** θ_v = −1.05596 × 10⁻⁴ rad; θ_l = +1.46117 × 10⁻⁴ rad; θ = 1.80279 × 10⁻⁴ rad; Δ = −0.475302 mm.
- **At the crossing:** θ_v = −3.01944 × 10⁻⁴ rad; θ_l = 0; Δ = −1.37548 mm.
- **Governing:** rotation 3.01944 × 10⁻⁴ rad at 40 m (the resultant's other local maxima are 1.3475 × 10⁻⁴ at 17.773 m and 62.227 m); opening 0.613843 mm at 17.8635 m; closure −1.37548 mm at 40 m.

The governing values off the center come from Claude's dense evaluation of the closed forms above (2026-11-06): a grid of 2 × 10⁶ to 4 × 10⁶ points, refined by bounded minimization to 10⁻¹² m, written for this spec and independent of garisenda. The center values are closed forms.

**Tolerance.** 1e-9 relative for values at given stations and for the governing values, since both are exact evaluations of the same closed form. 1e-6 m for the governing distances, as M3 (a)'s peaks.

### Changes
- **SPEC §7:** the jointed-pipe check, its API and the joint geometry (decisions 1–10). The worst position is the only joint position until M5 (intent decision 4). A zero limit is allowed for every check (decision 11).
- **SPEC §4:** the first presets, `gs.presets`, and how a preset is recorded (decisions 13–16).
- **SPEC §1.3:** the joint idealization joins the Phase 1 assumptions.
- **SPEC §2.1:** Eqs. 3 and 5 aren't used until verified (TODO #4).
- **SPEC §5.1, §9:** the result and its figure (decisions 8, 17).
- **`docs/reference/sources.md`:** `bracegirdle1996` is also cited for Table 2 and p. 661 (joint rotation and pullout), Table 4 and Herbert & Leach (1990) as quoted (p. 662), and rigid joints for strain (p. 663). Eqs. 5–6 are read but not used.
- **`docs/TODO.md`:**
  - #4: joint definitions decided; the Eq. 5 comparison above.
  - #5: stays open.
  - #6: done.
- **New:** `gs.check_jointed_pipe`; `gs.presets` with three presets. The profile figure draws a jointed-pipe result.
- **At close-out:**
  - a guide page, "Jointed pipes", with its example;
  - M3 marked done in §12.4, after the local comparison with the spreadsheet (intent);
  - `CLAUDE.md`'s "next".

### Decisions

**The API (intent: "The API")**

1. 🟡 **`gs.check_jointed_pipe(profile, *, pipe_lengths, pipe_type, interaction, joint_rotation_limit, joint_pullout_limit, tensile_strain_limit, compressive_strain_limit, bending_strain_limit, radius_of_curvature_limit) -> Result`**, at the top level beside `gs.check_continuous_pipe`. `profile` is a movement profile `Result`, as in M3 (a), decision 1. There's no `interval`: the pipe length is the interval (SPEC §7).
2. 🟡 **The judgments,** each a required keyword with no default (SPEC §4), with M3 (a)'s `interaction` and four limits unchanged, and:
   - `pipe_lengths`: the pipe length table (decision 3);
   - `pipe_type`: a non-empty string, the table's first key. It is recorded as a design judgment: which type an old main is (pit cast or spun, say) is often the engineer's call. `Utility` doesn't carry it. SPEC §8.5 keeps objects thin, and M5, which loads utilities with attributes, can revisit this;
   - `joint_rotation_limit`: an angle, a pint quantity only, since a plain number is refused for angles (CLAUDE.md). `None` means no limit;
   - `joint_pullout_limit`: a length, in m if a plain number, as every length is. `None` means no limit.
3. 🟡 **The pipe length table is a mapping** `{(pipe_type, outside_diameter): length}`, or a `gs.Sourced` holding one, whose source the result records.
   - The diameters and lengths are lengths, in m if plain numbers. A length that isn't positive and finite raises `ValueError` naming its key.
   - The check looks up the utility's outside diameter under `pipe_type`, matched within 1 µm (the profile's merge tolerance), so a table given in inches matches an outside diameter given in m.
   - A missing type raises `ValueError` listing the table's types. A missing diameter raises `ValueError` listing that type's diameters, and says that a nominal size isn't matched to an outside diameter and that nothing is taken from the nearest diameter (SPEC §7).
   - A DataFrame was considered. It was dropped because a mapping needs no column names or unit convention and a preset can be one. A tolerance against nominal sizes was dropped because it would guess.
   - The length used is recorded as the input `pipe_length`, given as `"from pipe_lengths, (<type>, <diameter> m)"`, with the table's source.

**The geometry (intent: "Pullout", "The worst joint position", "Barrel strain at interval L")**

4. 🟡 **Rotation is the resultant of the chord angles** (Geometry 2), checked against `joint_rotation_limit`. θ_v and θ_l are reported.
5. 🟡 **Pullout is the midpoint opening Δ** (Geometry 3), checked against `joint_pullout_limit` on its largest positive value.
6. 🟡 **The outer opening Δ + rθ and the closure are reported, not checked.**
   - **Not adding rθ to pullout:** Table 2 limits rotation and pullout separately. The rotation limit already bounds the opening that rotation makes, so adding rθ would count rotation twice against limits set apart.
   - **Closure:** the largest negative Δ is in `values` and the figure. Table 2 gives no limit for it, so it isn't checked, and the assumptions say so (SPEC §7: "skipped only when its limit isn't relevant").
   - **Alternatives:**
     - check the outer opening against the pullout limit (more conservative);
     - check closure with a seventh limit (a judgment with no source to fill it).
7. 🟡 **The worst position is found exactly.** As M3 (a), decision 7, rows are added at the zeros of d(θ²)/ds and dΔ/ds within each feasible range (Geometry 5). The derivatives are exact: dθ_v/ds = (w′(s + L) − 2w′(s) + w′(s − L))/L and dΔ/ds = ε_a(s + L/2) − ε_a(s − L/2), both from the source's derivatives at the shifted points. They use the sampling and tolerance of `find_critical_distances`. Rows are also added at the ends of each feasible range (s = L, ℓ − L, L/2, ℓ − L/2), because a peak can sit at the range's edge where the function is still rising. Without them a monotonic run near an end would be missed. Every added row is marked `critical`.
8. 🟡 **The barrel is M3 (a)'s check with h = L.** Its six checks, analytical and discrete, the worse governing, are computed exactly as `check_continuous_pipe(..., interval=L)` computes them (SPEC §7). Then θ_v = L κ_v,d, θ_l = L κ_l,d and Δ = L ε_a,d at every row. The joint columns and the barrel's discrete columns are one calculation, so they can't disagree.
   - **Confirmed against the spreadsheet** (review, 2026-11-06): it also uses the pipe length as the interval.
   - **Over every row** (plan, 2026-11-06): the rows added at the peaks of θ and Δ are the peaks of the discrete curvature and axial strain, which `check_continuous_pipe` samples only at its own stations. The barrel checks run over every row, so the values table and the checks table agree, and a discrete governing value can be slightly worse than M3 (a)'s at the same interval.
9. 🟡 **The joint checks sit in the checks table as discrete values.**
   - Rows `joint_rotation` (value θ, unit rad) and `joint_pullout` (value Δ, unit m) come after M3 (a)'s six.
   - `discrete` and `discrete_distance` hold the governing value and its distance; `analytical`, `analytical_distance` and `difference` are NaN; `governed_by` is `"discrete"`. They have no analytical counterpart: a joint exists only at a spacing L.
   - A new `governed_by` value, `"joint"`, was considered. It was dropped as a third category for the same thing.
10. 🟡 **The ends.**
    - **Within reach of an end:** a row within L of an end has no rotation, and one within L/2 has no opening, as M3 (a)'s discrete values have none (decision 6 there). They are NaN, under M3 (a)'s one `within` flag, whose reason names the joints too.
    - **A pipe too short for any joint:**
      - if ℓ < 2L, no position has a rotation;
      - if ℓ < L, none has an opening;
      - that joint check's value is NaN and `passes` is NA. "Not determined" is never shown as a pass. The flag says so.
    - **A positive check with nothing positive:** where positions exist but none opens, the pullout value is NaN and it passes, as M3 (a)'s checks with no value of their sign do.

**Limits**

11. 🟡 **A limit may be zero:** nothing is allowed. Table 2's first row is "none". Utilization is ∞ for a nonzero value, and the check fails. For a zero value, utilization is 0 and it passes. A zero radius limit gives 0 and passes. A negative limit still raises `ValueError`. This relaxes M3 (a)'s "must be positive" for `check_continuous_pipe` too, recorded in SPEC §7, with its test changed. The alternative was to raise for that row and leave it to the engineer. It was dropped because the table gives a value, and the result shows how far it is exceeded only as ∞, which is the table's meaning.
12. **Intent decision 1's caveat, worded from p. 661.** It is attached to the Table 2 pullout preset, and so to the result's assumptions:

    > "Bracegirdle et al. (1996, p. 661) give individual joints as the primary method and, 'again conservatively', the maximum horizontal ground movement as the pull-out. garisenda's opening is computed at individual joints and is smaller than that shortcut (for one trough, at most the maximum horizontal movement, and about a third of it for 4 m pipes in the M3 (b) spec's case J-A). Whether Table 2's pull-out limits, from Attewell et al. (1986), were calibrated with the shortcut can't be checked: Attewell et al. hasn't been read, and Bracegirdle et al.'s horizontal movement (Eq. 3) can't be read with certainty."

**Presets (intent: "The presets' shape")**

13. 🟡 **A preset value is a `Sourced` that also carries caveats.**
    - `gs.presets.Preset(value, source, caveats)` subclasses `Sourced`, so every check takes it where it takes a `Sourced`, with no new argument.
    - Its `source` names the preset, the row, the paper, the table or page, and whom the paper quotes. For example: `"gs.presets.cast_iron_joint_limits(joint='lead_yarn_water_main'): Bracegirdle et al. (1996), Table 2, p. 661, after Attewell et al. (1986), 'lead-yarn joint in water mains'"`.
    - A check adds the caveats of every preset among its inputs to the result's assumptions, once each.
    - The rows are keyword-only judgments with no default. A missing one raises `TypeError` through `judgments`, and an unknown one raises `ValueError` listing the rows.
14. 🟡 **`gs.presets.cast_iron_joint_limits(*, joint)`** returns `.rotation` and `.pullout` (Table 2; the paper's "guidance for cast iron mains", so not named "iron"):

    | `joint` | rotation | pullout |
    |---|---|---|
    | `"lead_yarn_gas_main_with_history_of_leaks"` | 0° | 0 mm |
    | `"lead_yarn_sound_gas_main"` | 1.0° | 10 mm |
    | `"lead_yarn_water_main"` | 1.5° | 15 mm |
    | `"rubber_gasket"` | 2.5° | 25 mm |

    Caveats:
    - both values: Table 2 is Attewell et al. (1986)'s guidance for cast iron mains, as quoted by Bracegirdle et al.; Attewell et al. hasn't been read;
    - the pullout: decision 12's caveat;
    - the first row: "none" is read as zero, so any movement fails (decision 11).
15. 🟡 **`gs.presets.iron_strain_limits(*, material)`** returns `.tensile` and `.compressive` (Table 4):
    - `"grey_iron"` ("pit cast and spun cast grey iron"): 100 and 1200 µε;
    - `"ductile_iron"`: 500 and 700 µε.

    Caveat: these are the allowable increase in strain for otherwise sound pipes (p. 662), recommended with Bracegirdle et al.'s methodology, which reduces axial strain by a factor that garisenda's greenfield check doesn't apply.
    - **No bending limit:** Table 4 gives none, and none is invented. The docs show `bending_strain_limit=None`, or the tensile limit. Tensile strain is at least the bending strain, so with the tensile limit the bending check adds nothing.
16. 🟡 **`gs.presets.grey_iron_tensile_strain_limit(*, diameter, situation)`** returns one value (Herbert & Leach 1990, as quoted on p. 662). `diameter` is `"over_300_mm"` or `"300_mm_or_less"`, and `situation` is `"general"` or `"particularly_adverse"`, giving 200 / 150 and 150 / 100 µε. The caller picks the row, so garisenda doesn't decide whether "300mm in diameter" is nominal or outside. Caveat: tensile only, and Herbert & Leach (1990) hasn't been read.

    No pipe length preset (intent decision 2).

**The result and figure**

17. 🟡 **The result.**
    - **Analysis and subject:** `analysis` is `"jointed_pipe_check"`, and `subject` is the utility's id.
    - **Values:** every column of `check_continuous_pipe` at h = L, plus `joint_vertical_rotation`, `joint_lateral_rotation`, `joint_rotation` (rad), `joint_opening` (m, signed) and `joint_outer_opening` (m, Δ + rθ).
    - **Checks:** M3 (a)'s six rows, then `joint_rotation` and `joint_pullout`.
    - **Method:** M3 (a)'s record (with h = L), plus "Joint rotation and opening for a jointed pipe", with Geometry 2–5's equations and the source "Geometry, derived in the M3 (b) spec; individual joints as Bracegirdle et al. (1996), p. 661 allow; rigid joints for strain, p. 663".
    - **Inputs:** `pipe_type`, `pipe_length`, `interaction` and the six limits.
    - **Assumptions:** M3 (a)'s, with the interval sentence naming the pipe length, plus:
      - rigid pipes of length L, joints that follow the ground, and every position a possible joint;
      - the barrel checked with rigid joints (p. 663);
      - small angles;
      - the opening checked at the axis, with the outer opening and closure reported only;
      - any check with no limit;
      - every preset's caveats.
    - **Summary:** the `repr` lists the eight checks, joints first under a "joints" heading.

    **The figure:** `gs.plot.profile` draws a jointed-pipe result in eight panels. They are M3 (a)'s six, then:
    7. joint rotation: θ_v, θ_l and θ, with the rotation limit;
    8. joint opening: Δ and the outer opening, with the pullout limit, and the closure marked.

    Rotation displays in degrees, a new display kind `"angle"` defaulting to `"degree"`, as Table 2 gives it. Opening displays as a displacement, in mm. The governing joints are marked with value and utilization, as M3 (a)'s checks are. `axs=` takes eight Axes. Lines have `gid`s named for their columns, and limits for their limit names.

### Sources
- **bracegirdle1996:** Bracegirdle et al. (1996), verified against the source on 2026-11-06 (page images, pp. 661–663):
  - Table 2, Eqs. 5–6 (read, not used) and the joint text (p. 661);
  - Table 4 and Herbert & Leach (1990) as quoted (p. 662);
  - rigid joints for strain (p. 663).
- **attewell1986, herbert_leach1990:** 🔬 not read. They are cited only as quoted in Bracegirdle et al. (SPEC §2.1), and named as such in each preset's source.
- The joint geometry is derived above and needs no source.

### Acceptance criteria
1. **Case J-A:** the values at the center joint and the governing rotation, opening and closure with their distances, within the stated tolerances. `joint_lateral_rotation` is exactly zero.
2. **Case J-B:** case J-B's values, and the barrel's discrete columns equal case B's at h = 9 m within 1e-9. At every row, `joint_vertical_rotation` = L × `discrete_vertical_curvature` and `joint_opening` = L × `discrete_axial_strain`, within 1e-12 relative.
3. **Case J-C:** the oblique values at s = 49.44365 m (a station of the profile) and at the crossing, and the governing values.
4. **The barrel is M3 (a)'s, over more rows** (reworded at the plan, 2026-11-06): for case J-A, the six barrel check rows' analytical fields equal `check_continuous_pipe(..., interval=4 m)`'s with the same limits exactly. The discrete columns equal it at every row the two results share. Each discrete governing value is no smaller in size than M3 (a)'s (no larger for the radius).
5. **The worst joint is found:** for cases J-A and J-C and for M2 (a)'s twin tunnels at L = 4 m and 9 m, the governing rotation and opening are at least the largest found by evaluating the source independently every 1 mm over the feasible range, refined every 1 µm within 1 mm of each maximum, and exceed it by no more than 1e-9 relative. The added rows are marked `critical`.
6. **A peak at the range's edge:** a pipe ending where θ is still rising toward the end (case J-A's pipe cut to offsets −40 m to −2 m, L = 4 m) has its governing rotation at s = ℓ − L, not at the last interior station.
7. **The ends and short pipes:** rows within L (rotation) and L/2 (opening) of an end are NaN, under one `within` flag that names them. A pipe shorter than 2L has a NaN rotation with `passes` NA, and one shorter than L the same for pullout.
8. **The pipe length table:**
   - a table in inches matches an outside diameter in m;
   - a missing type and a missing diameter each raise `ValueError` naming the pair and listing what the table has;
   - a non-positive length raises naming its key;
   - a `Sourced` table's source is on the `pipe_length` record.
9. **Limits:**
   - utilization and `passes` for rotation (θ/limit, the limit in rad) and pullout;
   - a zero limit gives ∞ and fails for a nonzero value, and passes for a zero one;
   - `None` gives NaN and NA;
   - a negative limit raises;
   - a plain number for the rotation limit is refused;
   - `check_continuous_pipe` now takes a zero limit too.
10. **Judgments:** each of the ten, missing, raises `TypeError` naming it; `pipe_type` empty raises `ValueError`; all appear in `inputs`.
11. **Presets:**
    - each row of the three presets gives the table's value, as a `Preset` whose source names the call, the paper, the table and page, and the quoted source;
    - a missing row raises `TypeError`, and an unknown one raises `ValueError` listing the rows;
    - the Table 2 pullout preset's caveat (decision 12) appears in the result's assumptions exactly once, and a call with no preset adds none.
12. **Reversal:** reversing the pipe leaves every check unchanged and moves each governing distance to ℓ − d.
13. **Result shape:** `to_dict()` is JSON-serializable, `to_frame()` has the joint columns with units, and the summary lists all eight checks.
14. **Sweep:** a `gs.sweep` row over volume loss equals a direct call, including the joint checks.
15. **Figure:** a jointed-pipe result draws eight panels, found by `gid`, with the joint lines, the limit lines and the governing markers. Rotation is in degrees. A continuous-pipe result still draws six, and a profile four; `rcParams` are unchanged. Checked by eye at close-out.
16. **Docs:**
    - the API reference has `check_jointed_pipe`, with Geometry 1–5 in its docstring and the sources, and `gs.presets`, with each preset's table, source and caveats;
    - the "Jointed pipes" guide's example runs in the docs build and shows decision 12's caveat.

## Plan

Eight build commits, each with lint, format, mypy strict and pytest green. Opus does 1–5, Sonnet does 6–7, and Opus does 8 (figures by eye, the spreadsheet comparison, close-out). A new session starts before 6 and before 8. Items not in the spec are marked 🟡. Following the workflow rule, each SPEC change goes in the commit that makes it true.

### 1. `M3 (b): allow a zero limit` (Opus)
Spec decision 11, for `check_continuous_pipe` first.
- `src/garisenda/utilities/_continuous_pipe.py`:
  - `_read_limit` accepts 0 and still raises for a negative or non-finite limit. The message says "must be zero or positive".
  - `_utilization`: with a zero limit, ∞ and fail for a nonzero value, 0 and pass for a zero value. With a zero radius limit, 0 and pass. The docstring says so.
- `SPEC.md` §7: a zero limit is allowed for every check, and means nothing is allowed.
- Tests: `tests/utilities/test_continuous_pipe.py` changes the zero-limit test from "raises" to AC 9's zero cases (∞/fail, 0/pass, radius 0/pass). Negative limits still raise.

### 2. `M3 (b): split the continuous check into reusable steps` (Opus)
A refactor with no change in behavior. The jointed check runs the same barrel calculation with extra rows (decision 8).
- `src/garisenda/utilities/_continuous_pipe.py`:
  - `_read_limits(**limits) -> (dict, records)`, the loop over the four limits.
  - `_along(utility, source)`: start, direction a, v, lat, length, feature length and a `derivatives(distance)` evaluator, taken from `_peaks`. Both checks use it.
  - `_barrel(profile, utility, source, interval, extra_peaks, ends_reason_extra) -> (values, flags, validity, checks)`: the body from `_peaks` to `_checks`. It merges `extra_peaks` with the analytical peaks through `_add_stations`.
  - `_interval_assumption(interval, what)`, which returns the assumption sentence naming the interval ("a pipe length L = 4 m" for jointed).
  - `check_continuous_pipe` calls them.
  - `_utilization` gains `determined: bool = True`. With `False` (no feasible position) it returns NaN and NA, even with a limit (decision 10). Unused until step 5.
- Tests: the existing suite passes unchanged.

### 3. `M3 (b): add gs.presets` (Opus)
Spec decisions 13–16. Citations checked against the page images as quoted in the spec.
- New `src/garisenda/presets.py` (exported as `gs.presets`):
  - `Preset(Sourced)`, a frozen dataclass with `caveats: tuple[str, ...]`;
  - `cast_iron_joint_limits(*, joint)` returning a frozen `JointLimits(rotation, pullout)`;
  - `iron_strain_limits(*, material)` returning `StrainLimits(tensile, compressive)`;
  - `grey_iron_tensile_strain_limit(*, diameter, situation)`.
  - Each has `@judgments`, so a missing row raises `TypeError`, and an unknown row raises `ValueError` listing the rows. Values are pint quantities (degree, mm, `"µε"` as a string). Sources are as in decision 13. Caveats are decisions 12, 14, 15 and 16 verbatim.
  - Each docstring is the reference entry: its table, source and caveats.
- `src/garisenda/_inputs.py`: `preset_caveats(*values) -> tuple[str, ...]`, the caveats of every `Preset` among the raw arguments, in order, each once.
- `check_continuous_pipe` adds `preset_caveats` of its limits to its assumptions. Decision 13 is "a check", and the strain presets apply to continuous pipes too.
- `src/garisenda/__init__.py` exports `presets`. New `docs/site/reference/presets.md` (`::: garisenda.presets`), added to the `zensical.toml` nav, because `test_every_public_name_has_a_reference_entry` requires it.
- `SPEC.md` §4: the first presets, `gs.presets`, and how a preset is recorded (its source names the call; caveats join the assumptions).
- Tests in new `tests/test_presets.py` (AC 11, first two bullets): every row's value and source, missing and unknown rows, and that `record()` takes a `Preset` as a `Sourced`. `tests/utilities/test_continuous_pipe.py` checks that a strain preset's caveat appears once in the assumptions, and that a call with no preset adds none.

### 4. `M3 (b): add gs.check_jointed_pipe` (Opus)
The inputs, the pipe-length table, the joint columns and the checks, at the rows the barrel already has (profile stations and M3 (a)'s peaks).
- New `src/garisenda/utilities/_jointed_pipe.py`, `check_jointed_pipe(profile, *, pipe_lengths, pipe_type, interaction, joint_rotation_limit, joint_pullout_limit, tensile_strain_limit, compressive_strain_limit, bending_strain_limit, radius_of_curvature_limit)` with `@judgments` for all ten (decisions 1–2). The docstring is the reference entry: Geometry 1–5, the barrel at h = L by reference to `check_continuous_pipe`, inputs and outputs with units, assumptions and sources (AC 16, that part).
  - `_pipe_length(table, pipe_type, diameter) -> (L, InputRecord)` (decision 3). It unwraps a `Sourced` table. Each key's diameter and each length go through `record` (m, read as SI). A non-positive or non-finite length raises naming the key. Matching is within `MERGE_TOLERANCE` (1 µm). A missing type or diameter raises as decision 3 says. The record is `InputRecord("pipe_length", L m, "design judgment", "from pipe_lengths, (<type>, <d> m)", table source)`.
  - `pipe_type`: a non-empty `str`, or `ValueError`, recorded as a design judgment `"name"`.
  - `joint_rotation_limit`: through `record(unit="radian", plain_number="refuse")`. `joint_pullout_limit` in m, read as SI. Both may be `None`, zero allowed, as `_read_limit`.
  - The barrel from `_barrel(..., interval=L)`. Then `joint_vertical_rotation = L·discrete_vertical_curvature`, `joint_lateral_rotation = L·discrete_lateral_curvature`, `joint_rotation = hypot`, `joint_opening = L·discrete_axial_strain`, `joint_outer_opening = Δ + rθ`, with units rad and m (decision 17).
  - The checks: M3 (a)'s six, then `joint_rotation` (largest θ) and `joint_pullout` (largest positive Δ), with the discrete fields only and `governed_by="discrete"` (decision 9). Uses `extreme` and `_utilization`.
  - `method`, `inputs` and `assumptions` as decision 17. Preset caveats are added here too.
- Exported from `src/garisenda/__init__.py`. `docs/site/reference/garisenda.md` gains `::: garisenda.check_jointed_pipe`.
- Tests in new `tests/utilities/test_jointed_pipe.py`, with cases J-A, J-B and J-C as fixtures built from M3 (a)'s cases:
  - AC 1's and AC 3's center and station values (s = 40 m, s = 49.44365 m), to 1e-9 relative;
  - AC 2 (J-B's center values, discrete columns equal to case B's at h = 9 m, the L × identities to 1e-12);
  - AC 4 as reworded;
  - AC 8 (the table: inches, missing type and diameter, non-positive length, `Sourced` source);
  - AC 9 (limits; a plain-number rotation limit refused);
  - AC 10 (the ten judgments, empty `pipe_type`, the inputs).

### 5. `M3 (b): find the worst joint exactly` (Opus)
Spec decisions 7 and 10, and the rest of 17.
- `src/garisenda/utilities/_jointed_pipe.py`:
  - `_joint_peaks(utility, source, L) -> FloatArray`. `find_zeros` (`src/garisenda/sources/_critical.py`) runs on two shifted ranges, with `step` and `tolerance` from `CRITICAL_DISTANCE_SAMPLING` and `CRITICAL_DISTANCE_TOLERANCE`:
    - t ∈ [0, ℓ − 2L], s = L + t, for d(θ²)/ds = 2(θ_v θ_v′ + θ_l θ_l′), where θ′ = (w′(s+L) − 2w′(s) + w′(s−L))/L from `_along`'s `derivatives` at the three shifted points;
    - t ∈ [0, ℓ − L], s = L/2 + t, for dΔ/ds = ε_a(s+L/2) − ε_a(s−L/2).
    - The scales are set as `_peaks` sets them: the sampled maximum, or the floor from U and the feature length.
    - Rows are also added at the range ends L, ℓ − L, L/2 and ℓ − L/2, where the range exists.
    - All of these go to `_barrel` as `extra_peaks`, so they are marked `critical`.
  - Short pipes: if ℓ < 2L, rotation is NaN with `passes` NA (`determined=False`); if ℓ < L, pullout is the same. With positions but none opening, pullout is NaN and passes.
  - The ends flag: `_barrel`'s `within` reason names the joints: no rotation within L, no opening within L/2, and the short-pipe sentence.
  - Assumptions: the full decision 17 list.
- `src/garisenda/_result.py` `__repr__`: when any check starts with `joint_`, the joint checks print first under `joints:`, then the rest under `barrel:` (🟡 the "barrel" heading isn't in the spec).
- Tests in `tests/utilities/test_jointed_pipe.py`:
  - AC 1's governing values and distances, including the J-A opening tie at 24.2821 m. Values to 1e-9 relative, distances to 1e-6 m. `joint_lateral_rotation` is exactly zero.
  - AC 3's governing values.
  - AC 5: J-A, J-C and the `twins_below_the_surface` fixture at L = 4 m and 9 m, against an independent evaluation every 1 mm, refined every 1 µm, within 1e-9. Added rows are `critical`.
  - AC 6 (the cut pipe: governing at ℓ − L).
  - AC 7.
  - AC 11, third bullet: the Table 2 pullout caveat appears once.
  - AC 13 (`to_dict` through `json.dumps`, `to_frame` units, eight check lines in the summary).
  - AC 12 in `tests/utilities/test_jointed_pipe_properties.py`, hypothesis over angle as M3 (a)'s.
  - AC 14 in `tests/test_sweep.py`: a sweep over volume loss equals direct calls, joint checks included. No sweep code change is expected, since `_sweep._table` reads `checks` generically.

### 6. `M3 (b): draw a jointed pipe result in eight panels` (Sonnet)
Spec decision 17's figure.
- `src/garisenda/plot/_display.py`: kind `"angle"`, default `"degree"`, SI `"radian"`.
- `src/garisenda/plot/_profile.py`:
  - `JOINTED_PANELS` = `CHECK_PANELS` plus two panels:
    - joint rotation: θ_v, θ_l, θ, kind `"angle"`, with a `Limit("joint_rotation_limit", "joint_rotation", 1, "rotation limit")`;
    - joint opening: Δ and the outer opening (dashed), kind `"displacement"`, with the pullout limit. The closure is marked with `gid` `closure` 🟡.
  - Panels are chosen by `result.analysis`: `"jointed_pipe_check"` gives eight. `axs=` checks for eight Axes.
  - Joint columns have no discrete twin, so they aren't in `DISCRETE_COLUMN`.
  - The docstring describes the figure.
- `SPEC.md` §9: the jointed-pipe figure.
- Tests in `tests/plot/test_profile.py` (AC 15, automated part):
  - eight panels by `gid`: joint lines, limit lines, `check:joint_rotation`, `check:joint_pullout` and `closure`;
  - the rotation axis in degrees (a limit of 1.5° drawn at y = 1.5);
  - a continuous check still draws six and a profile four;
  - the wrong `axs` count raises;
  - `rcParams` are unchanged.

### 7. `M3 (b): write the jointed pipes guide` (Sonnet)
- New `docs/site/guides/jointed-pipes.md` and `docs/site/examples/jointed-pipes.py`:
  - case J-A's crossing with a pipe-length table stated as the example's own, `pipe_type="spun_grey_iron"` and 🟡 a 4 m length;
  - `gs.presets.cast_iron_joint_limits(joint="lead_yarn_water_main")` and `gs.presets.iron_strain_limits(material="grey_iron")`, with `bending_strain_limit=None`;
  - the eight-panel figure;
  - reading the joint checks, and printing decision 12's caveat from `.assumptions`;
  - what the check assumes: the two idealizations, the axis opening, closure reported only;
  - why Eq. 5 isn't used, linking the reference.
- `zensical.toml` nav. `docs/site/figures/profile.md` shows the jointed figure.
- Tests: `tests/docs/test_site.py` picks up the example. The docs build passes with `--strict` and no `griffe:` warnings (AC 16).

### 8. `M3 (b): check figures and close out` (Opus)
- Check `docs/site/img/generated/` by eye against decision 17 (the rest of AC 15), and fix anything found.
- Run every check:
  - the CI line;
  - Python 3.13 and 3.14;
  - `lowest-direct`, then `git checkout uv.lock`;
  - the docs build.
- **The spreadsheet comparison (SPEC §12.4, intent):** run on the work machine by the user, not in this repo. Only "done, differences explained" is recorded. M3 isn't marked done until it is.
- Close-out:
  - `SPEC.md`:
    - §1.3: the joint idealization;
    - §2.1: Eqs. 3 and 5 aren't used until verified;
    - §5.1: the result;
    - §7: the jointed check, its API and geometry, and "unless joint locations are given" noted as M5;
    - §12.4: M3 done, with the date.
  - `docs/reference/sources.md`: `bracegirdle1996` gains Table 2, p. 661, Table 4 with Herbert & Leach, p. 663, and Eqs. 5–6 read but not used. Attewell 1986 and Herbert & Leach 1990 are listed as 🔬 not read, cited as quoted.
  - `docs/TODO.md`:
    - #4: joint definitions decided, plus the Eq. 5 comparison;
    - #5: stays open;
    - #6: deleted, moved into SPEC.
  - `CLAUDE.md`: the status and "Next" sentence move to M4. Recurring mistakes go into its conventions.
  - Report each of the 16 ACs as met or not, with evidence.
