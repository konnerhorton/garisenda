# TODO

Items to think through or research. Each item notes who owns it and the SPEC section it affects.

- **Owner key:** **You** = judgment or research the author does. **Claude** = verification or build-time work.
- When an item is resolved, move the decision into SPEC.md and delete it here.
- Every source named here is a 🔬 candidate from the scope discussion, not yet verified against the source itself.

---

## Sources and methods

### 1. Soil–structure interaction literature review · You and Claude · SPEC §1.3, §13 Q1
- **Decided (2026-11-01):** Phase 1 is greenfield only. A single reduction factor is not offered (it depends on pipe size and relative stiffness, so one factor is worse than none). The intended approach is a beam on springs, in a later phase.
- **What depends on it:** §13 Q1, whether closed-form relative-stiffness methods are added before the beam on springs; and the later beam-on-springs phase.
- **Candidates to read:** Bracegirdle et al. (1996), CIRIA Project Report 30, the chart practice uses now; closed-form relative stiffness approaches (Vorster et al. 2005; Klar et al. 2005); soil spring formulas for a beam on springs (ALA 2001).
- **Questions:**
  - Which closed-form methods can be verified, over what range of relative stiffness, and for what imposed profile (a single Gaussian perpendicular to the pipe only, or also skewed and longitudinal)?
  - Which inputs are easy to get wrong: soil modulus and its strain level; HDPE and PVC modulus depending on load duration and temperature; joint stiffness? Each needs a validity limit or a warning.
  - For a beam on springs: soil springs in each direction, joint springs, and verification cases with closed-form solutions.

### 2. Transverse trough sources · Claude (You to supply the papers) · SPEC §2.1, M1
- **To verify:** O'Reilly & New (1982) for trough width (the cohesive and granular linear fits); Peck (1969) for the Gaussian form; the relation between maximum settlement, volume loss and trough width; horizontal movement at the surface.
- **Golden values:** a worked example from one of these, or a hand calculation written out in M1's spec.
- **In hand since M2 (b)** (2026-11-04): Taylor (1995), Eqs. 1–4 and 6, pp. 124–125, and Mair & Taylor (1997), Eqs. 9–10, p. 2362, restate the surface trough and horizontal movement toward the axis (see `docs/reference/sources.md`). They are reviews, so the originals (Peck 1969, O'Reilly & New 1982) still need reading unless the authors' own restatement applies (SPEC §2.1).
- **Used unverified in M1 (a)** (decided 2026-11-02): the Gaussian form, the volume relation and horizontal movement toward the axis, cited with 🔬 and no equation numbers; golden values are hand calculations. Verifying them adds the equation numbers, the validity ranges for k, volume loss and cover, and replaces M1 (a)'s "no range checked" assumption.

### 3. Subsurface movements · You and Claude · SPEC §13 Q2, M2
- **Decided in M2 (b)** (2026-11-04): Mair et al. (1993)'s clay method, cited from Mair & Taylor (1997), Taylor (1995) and Bracegirdle et al. (1996), and i = k (z₀ − z) from a given k; the crown limit (SPEC §2.5). See `docs/work/m2b-subsurface.md`.
- **To read:** Mair, Taylor & Bracegirdle (1993), *Géotechnique* 43(2), 315–320, the original of the clay method; check its equation and whether it states a validity limit other than the crown. If it does, it governs.
- **Open:** a granular-specific method (SPEC §13 Q2); New & Bowers (1994) for movements close to the tunnel, below the crown, where M2 (b) flags points.

### 4. Utility check definitions · You (supply) and Claude (verify) · SPEC §7, M3
- **Decided for strain, and built (2026-11-06, M3 (a), `docs/work/m3a-continuous-pipes.md`, `gs.check_continuous_pipe`):** the definitions are mechanics, derived in the spec, not cited (SPEC §7). Bracegirdle et al. (1996) (read in full 2026-11-06) give the approach, the pipe following the ground and strains from differentiating the displacements (pp. 660, 663), and closed forms for one trough (Eqs. 7–11) used as golden values.
- **Joint rotation and pullout, for M3 (b):** Bracegirdle et al. give only conservative bounds for one Gaussian trough: θ = 2 tan⁻¹(S_max/(√(2π) i)) for transverse pipes and tan⁻¹(0.4 S_max/i) for parallel ones (Eqs. 5–6, p. 661), and pullout equal to the maximum horizontal movement (p. 661). Joint-by-joint definitions (rigid pipes, a joint's offset from the chord between its pipes' far ends) are geometry, derived in M3 (b)'s spec as garisenda's own.
  - 🔬 Eq. 5 doesn't match the steepest slope of a Gaussian trough (S_max/(i√e) ≈ 0.607 S_max/i, against 0.399 S_max/i in Eq. 5); Eq. 6 matches the steepest slope of the longitudinal cumulative-normal trough. Check against Attewell et al. (1986) before using Eq. 5 as a golden value.
  - To look for: Yeates (1985), "The response of buried pipelines to ground movements caused by tunnelling in soil", and Attewell et al. (1986), for a published joint-by-joint method.
  - The spreadsheet being replaced roughly follows these methods, but is incomplete and implemented poorly, so it's compared against, not matched (SPEC §12.4).
- **Joint pullout, from M2 (b)** (2026-11-04, `docs/work/m2b-subsurface.md`, decision 4). Bracegirdle et al. (1996) take joint pullout as the maximum horizontal movement, with movement toward the axis (their Eq. 3, smudged, read as (y/(z₀ − z_p)) S_v). That is i/(0.325 (z₀ − z)) times garisenda's constant-volume field with Mair's width: 1.54 at the surface, 2.08 at z₀/2, and 1 + 1.08 z₀/D at the crown (about 4.6 for z₀ = 20 m, D = 6 m).
  - **Preferred direction, not yet decided** (discussed 2026-11-04): pullout from the pipe's own movement, as the difference in along-pipe displacement between neighboring joints, from garisenda's exact field and a pipe length the user gives. It isn't tied to either horizontal field. Taking the maximum horizontal movement as pullout is an upper bound (all the stretch in the tension zone beyond ±i in one joint, u(i) − u(∞) = u_max). That reading is Claude's, not checked against Bracegirdle et al.'s text.
  - **To resolve in M3 (b)'s spec:**
    - Pullout from rigid pipes moving with the average along-pipe movement over their length, or from the difference in along-pipe movement between joint ends; and whether the joint opening from rotation (flexural pullout) is added.
    - Whether Bracegirdle et al.'s pullout limits were calibrated with movement toward the axis. If so, using them with garisenda's smaller field is unconservative against their method as published, and the spec says how that's handled.
    - The pipe length, a required judgment (TODO #5).
    - A clean copy of Bracegirdle et al. (1996) (the proceedings volume, later CIRIA guidance, or the authors) to read Eq. 3 with certainty. Only if it confirms Eq. 3, offer movement toward the axis as a named horizontal movement method, required with no default (SPEC §2.3). Until then it isn't offered.
    - Whether max horizontal movement is also reported as Bracegirdle's bound, beside the joint-to-joint value.

### 5. Pipe length presets · You and Claude · SPEC §4, §7
- Find citable nominal laying lengths by pipe type and diameter (manufacturer catalogs, AWWA or similar standards) for an opt-in preset. Old cast iron mains are the hard case: record what the source says about era and range.

### 6. Limit presets · You · SPEC §4
- **Decided (2026-11-06, M3 (a) intent):** opt-in presets (SPEC §4) from Bracegirdle et al. (1996), shipped in M3 (b): Table 2, allowable joint rotation and pullout for lead-yarn and rubber-gasket joints in gas and water mains, after Attewell et al. (1986) (p. 661); Table 4, allowable increase in strain for grey and ductile iron (p. 662); and Herbert & Leach (1990)'s grey iron values as quoted there (p. 662). Cited as SPEC §2.1 allows for a quoted table.
- Other materials and radius of curvature: TODO #13. Limit tables that don't state their source can't be used.

### 7. Building damage · You and Claude · M4
- **To verify:** Burland & Wroth (1974), Boscardin & Cording (1989), Burland (1995, 1997) damage categories, Mair, Taylor & Burland (1996) for the stiffness ratio values of masonry and framed buildings, and how hogging and sagging segments are split.

### 10. The perpendicular assumption and the longitudinal trough · You and Claude · SPEC §1.3, M3, M6
- **Decided:** an asset built from station and offset is perpendicular, and the longitudinal trough isn't considered until M6; both are stated assumptions, recorded on the result. The 3D field (M6) adds the longitudinal trough.
- **What secondary sources say (not citations):** the longitudinal trough is commonly modeled as a cumulative normal curve (attributed to Attewell & Woodman 1982), and the longitudinal and transverse trough width parameters are "typically assumed" equal (attributed to Attewell et al. 1986, in Zhang et al., arXiv 2201.06332). One thesis summary says observed longitudinal troughs are flatter, which would make the equal-width assumption conservative (Bloodworth, Oxford DPhil thesis). None of this is verified against the primary sources.
- **To verify:** Attewell & Woodman (1982) and Attewell et al. (1986) for the longitudinal form and the equal-width assumption; whether Bracegirdle et al. (1996) or its successor guidance states that perpendicular assessment is conservative, or how it treats parallel pipes.
- **Written in M3 (a)'s spec** (2026-11-06, `docs/work/m3a-continuous-pipes.md`, "The perpendicular bound"): for one transverse trough, at any depth above the crown and with either width method, the perpendicular pipe bounds every crossing angle for resultant curvature and combined strain. Not covered: superposed troughs, a pipe that changes depth, the longitudinal trough and face passage. Bracegirdle et al. (1996, p. 663) note that "bending strains in pipes transverse to tunnels tend to be more severe than for pipes running parallel to tunnels".
- **The original note, for M6:** the argument that the perpendicular case bounds the others: curvature and axial strain scale as sin²θ for a skewed pipe; lateral bending (sin²θ·cos θ, peak near 55°) doesn't govern; and, if the equal width holds, the transverse peak curvature (S_max/i² at the centerline) exceeds the longitudinal peak (about 0.24·S_max/i²). Axial strain during face passage (tensile over the axis ahead of the face) is the case most likely to break the argument, and depends on the horizontal movement model.
- **User docs written in M3 (a):** the "Continuous pipes" guide, "A perpendicular pipe bounds an oblique one", says what the bound covers and what it doesn't, for one trough.
- **Still open, for M6:** check the argument numerically, a parallel pipe loaded as a polyline against the same pipe built perpendicular from station and offset, and extend the docs section to the longitudinal trough and face passage.

### 12. The slope criterion for pipes · You · SPEC §7
- Bracegirdle et al. (1996)'s step (a): compare S_max/i with empirical limits, 0.012 for relatively rigid pipes over 200 mm and 0.012–0.040 for flexible pipes under 200 mm (Table 1, p. 661, after O'Rourke & Trautman 1982). Left out of M3 (decided 2026-11-06): garisenda computes the strains it screens for. Some users may want it as a check; it's defined only for one Gaussian trough, so adding it needs a definition for superposed and subsurface troughs, or a flag where it doesn't apply.

### 13. Cited limits and parameters for other materials · You · SPEC §4, §7
- Find published, citable limits for PVC, HDPE, welded steel, concrete and clay pipes: allowable tensile and compressive strain, joint rotation and pullout, and radius of curvature, which no source read so far gives for any material. Also the parameters the later soil–structure interaction phase needs (pipe and soil moduli, Bracegirdle et al.'s reduction factor inputs, TODO #1).

## Figures

### 11. Profile figure details, after user feedback · You · SPEC §9
- **Decided at M1 (c)'s figure review (2026-11-03), to revisit with users:** the profile joins stations with straight lines, so it looks jagged at a coarse `spacing` (the figure draws only the result's values; a finer spacing smooths it); the lateral lines stay, though they are zero for a perpendicular utility.
- **Open:** whether to drop the lateral lines for a built perpendicular utility, and whether users want a note or a smoother line for coarse spacings.
- **Decided at M3 (a)'s figure review (2026-11-06), to revisit with users:** in a check's figure, the limit lines set each panel's scale, so a check far below its limit looks flat (the example's bending: 23 µε against 500 µε). It shows the utilization at a glance. The alternative is to scale each panel to its data and mark a limit beyond it at the panel's edge.
