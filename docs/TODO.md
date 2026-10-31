# TODO

Items to think through or research. Each item notes who owns it and the SPEC section it affects.

- **Owner key:** **You** = judgment or research the author does. **Claude** = verification or build-time work.
- When an item is resolved, move the decision into SPEC.md and delete it here.
- Every source named here is a 🔬 candidate from the scope discussion, not yet verified against the source itself.

---

## Sources and methods

### 1. Soil–pipe interaction literature review · You and Claude · SPEC §4, §12.4 (M4b)
- **Current draft:** a factor given as a number with a reason (M4a); named methods come from this review (M4b).
- **What depends on it:** M4b's spec can't start without it. It decides SPEC §13 Q1 (Winkler beam).
- **Candidates to read:** Bracegirdle et al. (1996), CIRIA Project Report 30, the chart practice uses now; closed-form relative stiffness approaches (Vorster et al. 2005; Klar et al. 2005); soil spring formulas for a beam on springs (ALA 2001).
- **Questions:**
  - Which methods have a closed form that can be verified, and over what range of relative stiffness?
  - Which inputs are easy to get wrong: soil modulus and its strain level; HDPE and PVC modulus depending on load duration and temperature; joint stiffness? Each needs a validity limit or a warning.
  - Is a separate factor needed for each quantity (axial, bending, pullout, rotation)?

### 2. Transverse trough sources · Claude (You to supply the papers) · SPEC §2.1, M1
- **To verify:** O'Reilly & New (1982) for trough width (the cohesive and granular linear fits); Peck (1969) for the Gaussian form; the relation between maximum settlement, volume loss and trough width; horizontal movement at the surface.
- **Golden values:** a worked example from one of these, or a hand calculation written out in M1's spec.

### 3. Subsurface movements · You and Claude · SPEC §13 Q2, M2
- **To verify:** Mair et al. (1993) for trough width below the surface in clay, with its stated validity limit; Taylor (1995) for horizontal movements below the surface; New & Bowers (1994).
- **Open:** which method for granular soil, and what the validity limits are (including the depth limit Mair et al. state for their method).

### 4. Utility check definitions · You (supply) and Claude (verify) · SPEC §7, M4a
- **To verify:** how axial strain, bending strain, radius of curvature, joint pullout and joint rotation are defined from movements, in Bracegirdle et al. (1996) or its successor guidance. Verify against the primary source, not a summary of it.
- Write the definitions and hand-calculated golden values into M4a's spec.

### 5. Pipe length presets · You and Claude · SPEC §4, §7
- Find citable nominal laying lengths by pipe type and diameter (manufacturer catalogs, AWWA or similar standards) for an opt-in preset. Old cast iron mains are the hard case: record what the source says about era and range.

### 6. Limit presets · You · SPEC §4
- Which published sources give allowable strain, pullout, rotation and radius of curvature by material, that a preset could cite? Limit tables that don't state their source can't be used.

### 7. Building damage · You and Claude · M6
- **To verify:** Burland & Wroth (1974), Boscardin & Cording (1989), Burland (1995, 1997) damage categories, Mair, Taylor & Burland (1996) for the stiffness ratio values of masonry and framed buildings, and how hogging and sagging segments are split.

## Release and infrastructure

### 8. Claim `garisenda` on PyPI · You and Claude · SPEC §1.1
- A 0.0.1 placeholder upload with a release workflow using trusted publishing. Its own small unit after M0.

### 9. GitHub repo · You · SPEC §12.1
- Create the public repo and push, then confirm M0's CI is green on GitHub.
