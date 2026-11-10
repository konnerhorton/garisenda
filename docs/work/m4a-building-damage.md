# M4 (a): building damage

## Intent

### Goal
A caller can build a building from station and offset, as a wall perpendicular to the tunnel, and assess it for damage from the greenfield movements of one or more tunnels. The assessment is the staged method of Mair, Taylor & Burland (1996), after Burland & Wroth (1974) and Boscardin & Cording (1989), as practice uses it:

- **Stage 1:** the largest settlement and the largest slope along the wall, each checked against a limit.
- **Stage 2:** the wall is split into hogging and sagging zones at the inflection points of the settlement trough at foundation level. For each zone the assessment gives the deflection ratio Δ/L, the average horizontal strain ε_h, the bending and diagonal strains from a beam model, their combinations with ε_h, the damage category, and the zone that governs.

M4 (b) adds the building figures and user docs. Together they finish M4: "the spreadsheet is replaced for buildings" (SPEC §12.4).

### Why
- **SPEC §12.4:** M4 is the last spreadsheet-replacement milestone before real geometry (M5).
- **SPEC §1.3:** buildings are in Phase 1 as "facade lines", with deflection ratio, horizontal strain and damage category "per facade"; this unit calls them walls (decision 10).
- **SPEC §13 Q4** (where a facade's movement is taken; here, a wall's) is to be decided in M4.

### Evidence (sources read, 2026-11-10)
Local copies are in `../sources/`. None of the originals (Burland & Wroth 1974, Burland et al. 1977, Boscardin & Cording 1989, Burland 1995) is in hand (TODO #7).

- **Mair, Taylor & Burland (1996), pp. 715–717.**
  - **Table 1:** the damage categories 0–5.
  - **Table 2:** the limiting tensile strain per category (0.05 / 0.075 / 0.15 / 0.3 %), after Boscardin & Cording (1989).
  - **§4.1, Fig. 3:**
    - H is measured from foundation level to the eaves.
    - The building is split at the inflection points of the trough at foundation level.
    - The building is "not considered beyond the practical limit of the settlement trough", 2.5i for one tunnel.
  - **§4.2:**
    - The building follows the greenfield trough at foundation level.
    - Δ is the largest departure from the chord across a zone, "search[ed] for numerically".
    - Eq. 7 gives ε_b and Eq. 8 gives ε_d from Δ/L. The neutral axis is at the bottom in hogging (I = H³/3, t = H) and at mid-height in sagging (I = H³/12, t = H/2).
    - E/G is 2.6 for masonry, after Burland & Wroth (1974).
  - **§4.3:**
    - ε_h is the average over a span: the difference in horizontal movement between its ends, divided by its length.
    - Eq. 9: ε_bt = ε_h + ε_b.
    - Eq. 10: ε_dt = 0.35 ε_h + √((0.65 ε_h)² + ε_d²), with ν = 0.3.
  - **§4.5:** E/G is 12.5 for framed buildings.
  - **§5:**
    - The larger of Eqs. 9 and 10 sets the category.
    - Preliminary stage: settlement < 10 mm and slope < 1/500.
    - The line between categories 2 and 3 is the threshold.
  - **What it lacks:** no worked example, and no stated validity range.
- **Jones (2022), *Soft Ground Tunnel Design*, ch. 13, pp. 467–495.** This is a review by someone else, so it is not citable for equations under SPEC §2.1, but it changes the design in these ways:
  - **A corrected beam (Netzel 2009).** It changes Eqs. 7 and 8, as derived in Jones (Eqs. 13.12 and 13.23).
    - Burland & Wroth's shear deflection implies a form factor of 3/2. Timoshenko beam theory gives 6/5 for a rectangle.
    - In Eq. 7, the shear term's coefficient goes from 3/2 to 6/5. In Eq. 8, the constant 1 becomes 4/5.
    - On Jones's hogging zone, ε_b is 0.051 % with the correction and 0.044 % with the 1996 form.
  - **Eq. 10 derived from Mohr's circle** (Eqs. 13.27–13.38): ε_dr = ε_h(1−ν)/2 + √((ε_h(1+ν)/2)² + ε_d²).
  - **Worked Examples 13.1 and 13.2.**
    - The case: an 8 m tunnel with its axis at 18 m, V_L = 1.5 %, K = 0.5, so i = 9 m and S_max = 33.4 mm. The wall is masonry, H = 5.6 m, from y = −25 to +6.5 m.
    - Hogging zone: Δ/L = 3.05×10⁻⁴, ε_br = 0.105 %, category 2.
    - Sagging zone: Δ/L = 6.53×10⁻⁴, ε_dr = 0.039 %, category 1.
    - Stage 1: the 10 mm contour falls at y = 13.977 m and the 1/500 slope at 12.262 m.
    - These values are sampled. Δ is the largest at 1 m spacing, and ε_h is the plain mean of 17 point strains. The exact mean, (u_end − u_start)/L, is 5.72×10⁻⁴ for hogging (Jones 5.45×10⁻⁴) and −1.254×10⁻³ for sagging (Jones −1.183×10⁻³). Claude's hand check, 2026-11-10.
    - So the example checks the strain equations given Jones's Δ/L and ε_h, not the whole calculation.
  - **The 2.5i cut-off.** Cutting there can lower Δ/L. Netzel (2009) shows that counting the building beyond it can raise the tensile strain by up to 75 %. Jones's own example uses the whole wall, out to 2.78i.
  - **Compressive ε_h.** It reduces ε_br in sagging, so ε_dr governs in Jones's example; Mair, Taylor & Burland's Eqs. 9–10 also allow it.
  - **A depth limit.** The surface-trough method is limited to z_f/z₀ < 0.2 (Harris & Franzius 2006, cited by Jones). Two or more basement levels and piled foundations are assessed separately.
  - **Attributions.** Stage 1's limits are from Rankin (1988), and Table 13.1 from Burland et al. (1977), Rankin (1988) and Burland (2001).
- **Mair (2008), Rankine Lecture.** Nothing on building damage. Its tunneling-effects section covers pipelines (Vorster et al. 2005), which belongs to TODO #1.

### Constraints
- **SPEC §3:** the assessment consumes the movement profile along the wall, at foundation level. It evaluates the source only at points on the wall's own line, to find Δ and the zone ends exactly.
- **SPEC §4:** E/G, the category limits, the Stage 1 limits, the beam method, the cut-off, `interaction` and the acceptable category are required, keyword-only judgments. Standard values come as named, cited presets the caller passes.
- **SPEC §1.3:** greenfield. The building follows the ground at foundation level with no stiffness. The result records that this is conservative and that soil–structure interaction would reduce the strains. The wall is built perpendicular, and only the transverse trough is used until M6.
- **SPEC §2.1:** Eqs. 7–8 in Burland & Wroth's form, E/G and Table 2 are cited from Mair, Taylor & Burland (1996), "after" the originals, and marked provisional 🔬 per TODO #7. Eq. 10 and the corrected beam are derived in this unit's spec as garisenda's own mechanics, with Jones as the check, not the citation.
- **SPEC §2.4:** golden values are hand calculations written out in the spec. Jones's worked example checks the strain equations from his Δ/L and ε_h, and Stage 1's contour offsets.
- **SPEC §5:** one `Result`. Its checks are Stage 1's two checks, and Stage 2's category per zone with the governing zone.
- **SPEC §10:** a zone too short to have a Δ, or a wall with no zone, is reported with its reason, never dropped.
- **Test on segments at any angle** (CLAUDE.md): a wall from station and offset is perpendicular, but the assessment works on any straight segment. It is tested oblique too, where the along-wall horizontal movement differs.
- **The repo is public:** a real building is checked locally only.

### Out of scope
- **Figures and user docs:** M4 (b).
- **Footprints and walls as polylines:** M5. **Walls parallel to a tunnel:** M6, with the longitudinal trough.
- **Soil–structure interaction:** the modification factors of Potts & Addenbrooke (1997) and Franzius et al. (2006) are design charts, and SPEC §13 Q1 is undecided.
- **Stage 3 (detailed evaluation), Boscardin & Cording's angular-distortion route, and Burland (1995)'s chart.** The chart is a digitized chart, so it can't ship (SPEC §2.3).
- **Searching for the worst cut-off length** (Jones: usually between 2.5i and 3i): later, if users want it.
- **The generic Stage 2 of Harris & Franzius (2006).**

### SPEC sections touched
- **§1.3:** the building idealization (a beam of height H following the greenfield trough at foundation level) joins the Phase 1 assumptions.
- **§2.1:** citations for building damage, and Eq. 10 and the corrected beam as garisenda's own derivation.
- **§2.5:** the building method's validity (decision 9).
- **§3, §5.1:** the building assessment's inputs and result, at the spec step.
- **§4:** the building presets (E/G, category limits, Stage 1 limits).
- **§8.3:** the building builder from station and offset, and the wall's geometry (height, foundation depth or elevation).
- **§1.3, §8.3:** "facade" becomes "wall" (decision 10).
- **§12.4:** M4 split into two units.
- **§13 Q4:** answered (decision 1).
- **`docs/TODO.md`:** #7 (the sources read, the primaries to find: Burland (2001), Netzel (2009), Rankin (1988), Harris & Franzius (2006)).
- **`docs/reference/sources.md`:** Mair, Taylor & Burland (1996) gains Tables 1–2, Eqs. 7–10 and §§4–5.

### Decisions (intent review, 2026-11-10)
1. **Movement is taken at foundation level** (SPEC §13 Q4), from the source evaluated at the foundation depth. Both sources say so. The foundation depth or elevation is geometry the builder requires, not a judgment. A caller who wants the surface trough gives depth 0, and the result records the depth used. With Mair's width method, the trough at depth is narrower, so the result is more onerous.
2. **The beam method is a required argument, with two named methods.** One is Burland & Wroth's, as restated by Mair, Taylor & Burland (1996), which is what practice uses. The other is the corrected Timoshenko beam (Netzel 2009), derived in our spec. Where practice has two methods, garisenda doesn't choose silently (SPEC §2.3). Shipping only one was considered: the first is practice and the second is right as mechanics, so each user needs the other one sometimes.
3. **The cut-off is a required judgment:** none (the whole wall, which is the building's real length), or a multiple of i. Mair, Taylor & Burland recommend 2.5i, and Netzel shows that cutting there can be unconservative. With several sources, each source's cut-off is found and the outermost on each side is used. A building's ends are real, so TODO #15's end-of-asset flag doesn't apply.
4. **Compressive ε_h is used as the sources use it** in Eqs. 9 and 10, unlike the pipes' rule (SPEC §7). For a building, ε_h is a zone average fed into a beam model, not a strain at a fiber, and both sources apply it with its sign. The result records this as an assumption.
5. **E/G and the category limits are required arguments, with presets the caller passes** (SPEC §4). Examples: an E/G preset with rows `masonry` (2.6) and `framed` (12.5), and Table 2 as a category-limit preset, each cited from Mair, Taylor & Burland (1996) after the originals.
6. **`acceptable_category` is required and may be `None`**, as the pipe checks' limits may (SPEC §7). With `None`, the category per zone and the governing zone are reported with no pass/fail. With a category (practice uses 2), the check passes when the governing category is at or below it. Making it optional with a default was considered and rejected, because SPEC §4 says judgments have no defaults.
7. **Stage 1 is included**, as two checks on the same result: the largest settlement and the largest slope along the wall. Their limits are required, with a preset of 10 mm and 1/500 after Rankin (1988), as stated by Mair, Taylor & Burland (1996), §5.2.
8. **M4 is two units:** (a) this one, the calculation; (b) the building figures (profile with zones, chord and Δ; cross-section with the building) and the user docs.
9. **Validity.** The verdict is `outside` where z_f/z₀ ≥ 0.2 (Harris & Franzius 2006, via Jones; 🔬 until read). Otherwise it is `within`, with a warning that the method states no range, as TODO #16 does.
10. **The assessed line is called a wall, not a facade.** In practice a facade is the street front, which over a tunnel route usually runs parallel to the tunnel: the opposite of what is assessed. The line is a vertical plane across the tunnel, which Burland & Wroth treat as a deep beam, and Mair, Taylor & Burland's Table 1 classifies damage "to walls". A wall also extends to M5: each edge of a footprint is a wall, assessed in its own direction, and walls parallel to a tunnel are flagged until M6. "Building section" was considered and rejected, because a section means a cut, and a footprint's edges aren't cuts. The builder is `perpendicular_building`, matching `perpendicular_utility`.

### 🟡 To settle in the spec
- **The API.** Proposed:
  - the builder `gs.buildings.perpendicular_building(tunnel, *, building_id, station, start_offset, end_offset, height, foundation_depth | foundation_elevation)`, beside `perpendicular_utility`;
  - the check `gs.check_building(profile, *, beam_method, stiffness_ratio, category_limits, cutoff, settlement_limit, slope_limit, acceptable_category, interaction)`.

  Settle the names, including whether "stiffness ratio" or "E/G" goes in the name (SPEC §8.5), and whether the profile or the wall with its source is the input. Δ and the zone ends need the source.
- **Zones.**
  - Inflection points are the zeros of vertical curvature along the wall. They are already among the source's critical distances.
  - A zone is hogging or sagging by the sign of curvature in it.
  - Superposed troughs give several zones.
  - Settle what happens to a zone shorter than some length, and what counts as "no zone".
- **Δ, exactly.** It is the largest departure from the chord, at a zero of (slope − chord slope), found by root-finding. Also settle the sign convention, and whether Δ is reported signed.
- **Category boundaries.** Settle which category a strain exactly on a boundary falls in, and how categories 4 and 5 (both > 0.3 %) are reported.
- **The cut-off for superposed and subsurface troughs:** how "a multiple of i" is defined when i varies with depth and between sources.
- **Golden values:**
  - one Gaussian trough with a wall straddling the tunnel, with Δ, ε_h and the strains by hand for both beam methods;
  - a wall wholly in hogging;
  - twin tunnels, with several zones;
  - Jones's Examples 13.1 and 13.2, as above;
  - an oblique wall.
