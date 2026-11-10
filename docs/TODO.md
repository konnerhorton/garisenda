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

### 4. Utility check definitions · You (supply) and Claude (verify) · SPEC §2.1, §7
- **Decided and built:** strain (2026-11-06, M3 (a), `gs.check_continuous_pipe`) and joint rotation and pullout (2026-11-06, M3 (b), `gs.check_jointed_pipe`, `docs/work/m3b-jointed-pipes.md`). All are geometry and mechanics derived in the units' specs, not cited (SPEC §7). Pullout is the opening between rigid pipes moving with the ground at their midpoints; the outer opening Δ + rθ is reported, not checked; the maximum horizontal movement isn't reported as a bound.
- **Still open:**
  - 🔬 **Eq. 5 (p. 661).** For one Gaussian trough and a joint at the center of a perpendicular pipe, the geometry gives θ = (S_max/i) · 2(1 − e^(−x²/2))/x with x = L/i, at most 0.9025 S_max/i (x = 1.5852); Eq. 5 is 0.7979 S_max/i to small angles. So the geometry exceeds Eq. 5 for 1.026 i < L < 2.347 i, and Eq. 5 isn't "the worst conceivable configuration of joints" for every pipe length. Claude's reading, unchecked: Eq. 5 is the apex rotation of a triangular trough with the Gaussian's depth and volume. Read Attewell et al. (1986) to check where Eq. 5 comes from before using it as a bound or a golden value.
  - 🔬 **Eq. 3 and the pullout limits.** Whether Table 2's pull-out limits were calibrated with the maximum horizontal movement (Bracegirdle et al.'s conservative shortcut) can't be checked until Attewell et al. (1986) is read; the Table 2 preset carries that caveat. A clean copy of Bracegirdle et al. (1996) (the proceedings volume, later CIRIA guidance, or the authors) is needed to read Eq. 3 with certainty. Only if it confirms Eq. 3, offer movement toward the axis as a named horizontal movement method, required with no default (SPEC §2.3). The M2 (b) comparison (2026-11-04, `docs/work/m2b-subsurface.md`, decision 4): Eq. 3 read as (y/(z₀ − z_p)) S_v is i/(0.325 (z₀ − z)) times garisenda's constant-volume field with Mair's width, 1.54 at the surface, 2.08 at z₀/2, and about 4.6 at the crown for z₀ = 20 m, D = 6 m.
  - To look for: Yeates (1985), "The response of buried pipelines to ground movements caused by tunnelling in soil", for a published joint-by-joint method.

### 5. Pipe length presets · You and Claude · SPEC §4, §7
- Find citable nominal laying lengths by pipe type and diameter (manufacturer catalogs, AWWA or similar standards) for an opt-in preset. Old cast iron mains are the hard case: record what the source says about era and range.

### 7. Building damage · You and Claude · M4
- **To verify:** Burland & Wroth (1974), Boscardin & Cording (1989), Burland (1995, 1997) damage categories, Mair, Taylor & Burland (1996) for the stiffness ratio values of masonry and framed buildings, and how hogging and sagging segments are split.
- **Decided (2026-11-10), provisional:** M4 works from the secondary sources in hand, not the originals, while the author looks for the primaries or better secondaries. SPEC §2.1 stays as it is. Burland & Wroth (1974) and Boscardin & Cording (1989) aren't free (BRE / Pentech; ASCE paywall), and Burland (1995) isn't either (IS-Tokyo '95, later in Ishihara (ed.) 1997, pp. 1189–1201). The originals stay 🔬 here.
- **In hand (2026-11-10, local copies in `../sources/`, see its README):** Mair, Taylor & Burland (1996), IS-London '96: Table 1 (damage categories), Table 2 (limiting tensile strain per category), Fig. 3 (hogging and sagging zones split at the inflection point), restating Burland & Wroth (1974) and Boscardin & Cording (1989). Burland (1997), 14th ICSMFE theme lecture (likely gaps and the Jubilee Line, not the method; check whether it's the "Burland (1997)" meant above). Jones, *Soft Ground Tunnel Design*, and Mair (2008), Rankine Lecture, both reviews by others.
- **Under SPEC §2.1:** Mair, Taylor & Burland (1996) is Burland's own restatement, so it can be cited for Burland & Wroth's equations, and its tables of limits can be cited "after" the original. Boscardin & Cording's equations restated there, and anything only in Jones or Mair (2008), are restatements by others, which §2.1 doesn't allow for equations. M4's spec marks each such use as provisional, 🔬, so it can be replaced when a primary is found.
- **Used in M4 (a) (done 2026-11-10):** Mair, Taylor & Burland (1996) for Tables 1–2 and Eqs. 7–10, with Burland & Wroth (1974), Burland et al. (1977) and Boscardin & Cording (1989) cited "after" it; Jones (2022) as the check of the worked example and the Timoshenko beam, and as the report of Rankin (1988) and Harris & Franzius (2006). Burland (1997), the 14th ICSMFE theme lecture, is in hand and unread.
- **Read for M4 (a) (2026-11-10, `docs/work/m4a-building-damage.md`):** Jones (2022), ch. 13, has a worked example (Examples 13.1–13.2) and the corrected beam of Netzel (2009). Mair (2008) has nothing on buildings. **Primaries to find:** Burland (2001), "Assessment methods used in design", CIRIA SP200 Vol. 1, ch. 3, pp. 23–43 (Burland's own later restatement, likely the best source to get); Netzel (2009), Delft PhD thesis (the shear correction to Burland & Wroth); Rankin (1988), Geol. Soc. Eng. Geol. Spec. Publ. 5, pp. 79–92 (the Stage 1 limits); Harris & Franzius (2006), 5th Int. Symp. Geotech. Aspects of Underground Construction in Soft Ground (the z_f/z₀ < 0.2 limit).

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
- Find published, citable limits for PVC, HDPE, welded steel, concrete and clay pipes: allowable tensile and compressive strain, joint rotation and pullout, and radius of curvature, which no source read so far gives for any material. A limit table that doesn't state its source can't be used. Also the parameters the later soil–structure interaction phase needs (pipe and soil moduli, Bracegirdle et al.'s reduction factor inputs, TODO #1).

### 14. Confirming the utility checks on a real crossing · You · SPEC §12.4, M3
- **Decided (2026-11-06):** M3 closed without the planned comparison with the spreadsheet, which isn't trusted as a reference (it roughly follows Bracegirdle et al. (1996) but is incomplete and implemented poorly).
- **To find:** another way to check `gs.check_continuous_pipe` and `gs.check_jointed_pipe` on a real crossing, such as a published case history with measured or independently computed pipe strains and joint movements, or another engineer's independent calculation. Checked locally on the work machine; no project data in the repo.

## Figures

### 11. Profile figure details, after user feedback · You · SPEC §9
- **Decided at M1 (c)'s figure review (2026-11-03), to revisit with users:** the profile joins stations with straight lines, so it looks jagged at a coarse `spacing` (the figure draws only the result's values; a finer spacing smooths it); the lateral lines stay, though they are zero for a perpendicular utility.
- **Open:** whether to drop the lateral lines for a built perpendicular utility, and whether users want a note or a smoother line for coarse spacings.
- **Decided at M3 (a)'s figure review (2026-11-06), to revisit with users:** in a check's figure, the limit lines set each panel's scale, so a check far below its limit looks flat (the example's bending: 23 µε against 500 µε). It shows the utilization at a glance. The alternative is to scale each panel to its data and mark a limit beyond it at the panel's edge.

## Agent-use review (2026-11-09)

From a whole-package review at M3 (`dc59a48`) for whether an AI agent can use garisenda to produce work an engineer can sign off, with two trial agents working from the published docs only (one run each: a jointed main over twin tunnels, a welded main over a volume loss sweep). Probe scripts are not kept; each item gives enough to reproduce.

### 15. Flag an asset that ends where the trough is still significant · Claude (You to set the margin) · SPEC §8.3, §7
- **What happens:** a utility from −3 m to +3 m over a trough with i = 9 m returns `within` with no warnings; `axial_tension` is `none` with `passes=True`, though the tension peak (about ±√3 i ≈ ±15.6 m) is beyond the pipe's ends. A truncated pipe passes, and nothing says its extent was too short.
- **Record:** SPEC §8.3 (🟡) says such an asset is flagged, with the margin set in M3's spec; `docs/work/m1b-movement-profile.md` defers it to M3. M3's specs don't set it and nothing tracks it.
- **Decided (2026-11-10), provisional:** a margin of 3 m, likely to change, so it's a constant recorded on the result. 🟡 How it's read: the asset is flagged when one of the source's critical distances lies beyond an end, or within 3 m inside it.
- **Open:** whether it applies to the profile or only to the checks. Needs its own unit.

### 16. A `within` verdict where no range was checked · You · SPEC §5.2, TODO #2
- **What happens:** volume loss 50 %, k = 0.01 or k = 5 all give `within` (0.63 m settlement at 50 %). The only trace is one assumption, "No validity range is checked for k or volume loss", among 10–23. One trial agent caught it; nothing makes it hard to miss.
- **Decided (2026-11-10):** warn. The result carries a warning that no validity range was checked for k or volume loss, until TODO #2 sets real limits. The verdict stays `within`.

### 17. Plain-number lengths read as m without a visible trace · You · SPEC §6
- **What happens:** `IdealizedTunnel(diameter=20, axis_depth=60)` from a project in feet is silently 3.28× off. The input record says `given_as="plain number, read as m"`, but the summary doesn't show it.
- **Decided (2026-11-10):** always show units: the summary shows each input with its unit, and how it was given, so a plain number read as m is visible. Plain lengths are still accepted (SPEC §6 unchanged).

### 23. A governing utilization for a check and a sweep · You · SPEC §5.1, §5.3
- `checks` and `gs.sweep` give no overall governing utilization or pass, so trial B took the maximum itself and bisected for the volume loss at which the pipe stops passing. A symmetric peak reports one location only (trial A).
- **Open:** whether to add a governing row or column (with `None` limits and NA passes handled explicitly), and whether to report both locations of a symmetric peak.
- **Deferred (2026-11-10):** to revisit later; no trigger set.
