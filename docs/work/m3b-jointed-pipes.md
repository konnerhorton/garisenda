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
