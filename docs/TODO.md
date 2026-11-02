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

### 3. Subsurface movements · You and Claude · SPEC §13 Q2, M2
- **To verify:** Mair et al. (1993) for trough width below the surface in clay, with its stated validity limit; Taylor (1995) for horizontal movements below the surface; New & Bowers (1994).
- **Open:** which method for granular soil, and what the validity limits are (including the depth limit Mair et al. state for their method).

### 4. Utility check definitions · You (supply) and Claude (verify) · SPEC §7, M3
- **To verify:** how axial strain, bending strain, radius of curvature, joint pullout and joint rotation are defined from movements, in Bracegirdle et al. (1996) or its successor guidance. Verify against the primary source, not a summary of it.
- Write the definitions and hand-calculated golden values into M3's spec.

### 5. Pipe length presets · You and Claude · SPEC §4, §7
- Find citable nominal laying lengths by pipe type and diameter (manufacturer catalogs, AWWA or similar standards) for an opt-in preset. Old cast iron mains are the hard case: record what the source says about era and range.

### 6. Limit presets · You · SPEC §4
- Which published sources give allowable strain, pullout, rotation and radius of curvature by material, that a preset could cite? Limit tables that don't state their source can't be used.

### 7. Building damage · You and Claude · M4
- **To verify:** Burland & Wroth (1974), Boscardin & Cording (1989), Burland (1995, 1997) damage categories, Mair, Taylor & Burland (1996) for the stiffness ratio values of masonry and framed buildings, and how hogging and sagging segments are split.

### 10. The perpendicular assumption and the longitudinal trough · You and Claude · SPEC §1.3, M3, M6
- **Decided:** an asset built from station and offset is perpendicular, and the longitudinal trough isn't considered until M6; both are stated assumptions, recorded on the result. The 3D field (M6) adds the longitudinal trough.
- **What secondary sources say (not citations):** the longitudinal trough is commonly modeled as a cumulative normal curve (attributed to Attewell & Woodman 1982), and the longitudinal and transverse trough width parameters are "typically assumed" equal (attributed to Attewell et al. 1986, in Zhang et al., arXiv 2201.06332). One thesis summary says observed longitudinal troughs are flatter, which would make the equal-width assumption conservative (Bloodworth, Oxford DPhil thesis). None of this is verified against the primary sources.
- **To verify:** Attewell & Woodman (1982) and Attewell et al. (1986) for the longitudinal form and the equal-width assumption; whether Bracegirdle et al. (1996) or its successor guidance states that perpendicular assessment is conservative, or how it treats parallel pipes.
- **To write into M3's spec as a hand calculation:** the argument that the perpendicular case bounds the others: curvature and axial strain scale as sin²θ for a skewed pipe; lateral bending (sin²θ·cos θ, peak near 55°) doesn't govern; and, if the equal width holds, the transverse peak curvature (S_max/i² at the centerline) exceeds the longitudinal peak (about 0.24·S_max/i²). Axial strain during face passage (tensile over the axis ahead of the face) is the case most likely to break the argument, and depends on the horizontal movement model.
- **Outcome:** a short section in the user docs on what the perpendicular assumption covers and what it doesn't. M6 can check the argument numerically: a parallel pipe loaded as a polyline against the same pipe built perpendicular from station and offset.

## Release and infrastructure

### 8. Claim `garisenda` on PyPI · You and Claude · SPEC §1.1
- A 0.0.1 placeholder upload with a release workflow using trusted publishing. Its own small unit after M0.

### 9. GitHub repo · You · SPEC §12.1
- Create the public repo and push, then confirm M0's CI is green on GitHub. M0 closed without it (2026-11-02): every CI job's commands pass locally on Linux with Python 3.12, 3.13 and 3.14 and on the lowest versions, but the Windows and macOS jobs have never run.
