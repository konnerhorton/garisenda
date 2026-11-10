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

## Spec

No topic doc holds this, so the spec is here. It settles the intent's "To settle in the spec" items. Each 🟡 is a proposal for review. Sources were read again on 2026-11-10 from `../sources/`:
- **Mair, Taylor & Burland (1996), pp. 715–717:** checked against the page images, because the text layer is OCR.
- **Jones (2022), pp. 467–490 (book pp.; PDF pp. 490–513):** checked against the page images for Eqs. 13.12 and 13.23 and Tables 13.2–13.3.

### What the sources say (beyond the intent)
- **Mair, Taylor & Burland (1996), p. 716:**
  - Eq. 7: Δ/L = (L/(12t) + 3IE/(2tLHG)) ε_b.
  - Eq. 8: Δ/L = (1 + HL²G/(18IE)) ε_d.
  - "Within each zone the maximum value of Δ can be determined", and "it will be simplest to search for these numerically".
  - L is "limited by any point of inflexion or extent of settlement trough". E/G = 2.6 "is consistent with an isotropic Poisson's ratio of 0.3".
- **p. 717:**
  - Eq. 10 is stated "assuming a value for Poisson's ratio of 0.3", whatever E/G is. §4.5 uses it unchanged with E/G = 12.5 for framed buildings, "(Burland and Wroth, 1974)".
  - §5.2: the preliminary assessment uses "contours of ground surface settlement", 10 mm, and "an additional check ... that no eliminated building experiences a slope exceeding 1/500".
  - §5.3: the larger of Eqs. 9 and 10 gives the category from Table 2. The approach "is usually very conservative" because the building "is assumed to have no stiffness".
- **Table 2 (p. 715):** categories 0, 1, 2, 3 and "4 to 5", with limits 0–0.05, 0.05–0.075, 0.075–0.15, 0.15–0.3 and > 0.3 %. The ranges share their ends, so a strain on a boundary isn't placed (decision 9).
- **Jones (2022):**
  - **p. 469:** Stage 1 uses "the ground surface" too (Rankin 1988).
  - **pp. 476–479:** shear area A = H for a wall of unit width. α = 3/2 is the ratio of peak to mean shear stress (Eq. 13.15). Eqs. 13.12 and 13.23 have 72EI/(5L²AG) and 4/5.
  - **p. 490:** Harris & Franzius's z_f/z₀ < 0.2 is a limit of their *generic* Stage 2, "since it is the surface settlement trough that is used in the analysis"; "two or more basement levels or piled foundations have to be assessed separately". garisenda takes the trough at foundation level (intent decision 1), so the stated reason only partly applies (decision 14).
  - **A slip in Jones's Example 13.2 (p. 490):** the sagging zone's ε_dr = 0.039 % is called category 1. By his own Table 13.1 (p. 468), the same as Mair, Taylor & Burland's Table 2, it is category 0. The intent's "category 1" copies the slip. The golden values use category 0.
- **Burland (1997), ICSMFE 14 theme lecture,** is also in `../sources/`. It is a gaps-in-knowledge lecture by one of the method's authors. It wasn't read for equations; it goes on TODO #7's list.

### Mechanics
Derived here as garisenda's own (intent; SPEC §2.1). The wall is a beam of height H and unit width, so its shear area is H, spanning a zone of length L. Its neutral axis is at depth t below the extreme tensile fiber, with second moment of area I:
- hogging: t = H, I = H³/3;
- sagging: t = H/2, I = H³/12.

Mair, Taylor & Burland, p. 716, give these.

1. **Bending.** The beam is simply supported under a central point load P, so M = PL/4 and ε_b = Mt/(EI) = PLt/(4EI).
   - Bending deflection: PL³/(48EI).
   - Shear deflection: α_s PL/(4GH), with α_s the shear-deflection coefficient.
   - So Δ/L = (L/(12t) + α_s EI/(tLHG)) ε_b.
   - With α_s = 3/2 this is Eq. 7 exactly; that's what Burland & Wroth's form implies.
   - Timoshenko's coefficient for a rectangle is 6/5. That gives Δ/L = (L/(12t) + 6EI/(5tLHG)) ε_b, which is Jones's Eq. 13.12 expanded.
2. **Diagonal strain.** The shear force is P/2. The peak shear strain, at the neutral axis, is γ = (3/2)(P/2)/(GH), where 3/2 is the rectangle's ratio of peak to mean shear stress. The largest principal strain of pure shear is ε_d = γ/2 = 3P/(8GH). Substituting P:
   - Δ/L = (2α_s/3 + HL²G/(18IE)) ε_d.
   - With α_s = 3/2 the constant is 1 (Eq. 8). With 6/5 it is 4/5 (Jones's Eq. 13.23).
   - The 3/2 of the peak stress stays in both. Only the deflection's coefficient changes.
3. **Combined with ε_h.**
   - **Bending (Eq. 9):** ε_h is uniform over the section, so ε_bt = ε_h + ε_b.
   - **Diagonal:** the wall is free to strain vertically, so a horizontal strain ε_h comes with −ν ε_h vertically. The shear adds a half shear strain ε_d. By Mohr's circle, the largest principal strain is ε_dt = ε_h(1 − ν)/2 + √((ε_h(1 + ν)/2)² + ε_d²). With ν = 0.3 this is Eq. 10: 0.35 ε_h + √((0.65 ε_h)² + ε_d²). ε_dt ≥ 0.35 ε_h + 0.65|ε_h| ≥ 0, so the zone's tensile strain max(ε_bt, ε_dt) is never negative.
4. **Zones.**
   - Along the wall, w(s) is the settlement at foundation level (the profile's `vertical`), and w″ is `vertical_curvature`.
   - The assessed range (decision 6) is split at the zeros of w″, so w″ has one sign in each zone.
   - Positive w″ is hogging (SPEC §3): the settlement is convex, so it lies on or below its chord.
5. **Δ.**
   - On a zone [s₁, s₂], the chord is c(s) = w(s₁) + (w(s₂) − w(s₁))(s − s₁)/L.
   - The departure is d(s) = w(s) − c(s), signed as Jones's Δ = S − T: negative in hogging.
   - w″ has one sign in the zone, so d does too. w′ − (chord slope) is monotone, and its one zero is where |d| is largest.
   - Δ = |d| there. It is found by bisection on the source's exact slope, to 1e-9 m.
6. **ε_h** = (u_a(s₂) − u_a(s₁))/L, the mean of `along_strain` over the zone (Mair, Taylor & Burland, §4.3). u_a is the movement along the wall.
7. **Oblique wall, one trough.** The wall crosses the tunnel at angle θ in plan, with offset o = s sin θ. Then:
   - zone ends and Δ are those of the perpendicular wall, at the same offsets;
   - L is longer by 1/sin θ, so Δ/L is sin θ times the perpendicular value;
   - u_a = u_n sin θ, so ε_h is sin²θ times the perpendicular value;
   - the slope is sin θ times the perpendicular value.

   The strains don't scale simply, because L enters Eqs. 7–8 on its own.

### Hand calculations (golden values)
These are Claude's calculations (2026-11-10), in a script independent of garisenda, from Mechanics 1–7.
- **The trough:** S = S_max e^(−ρ²/2) with ρ = o/i, and u_n = −c₁ (o/i) S. The linear width method gives c₁ = k and i = k(z₀ − z_f).
- **The wall:** E/G = 2.6.
- **Notation:** "BW" is α_s = 3/2 and "T" is 6/5. Strains are dimensionless.
- **Tolerance:** 1e-6 relative, since every value is exact up to the root-finding (1e-9 m). Jones's printed values (case J) are checked to half a unit in their last printed digit.

**Case A: one tunnel, foundation below the surface, wall straddling it.**
- **Inputs:** z₀ = 20 m, D = 6 m, V_L = 1 %, linear width with k = 0.5. The wall is perpendicular at foundation depth 2 m, from offset −30 to +30 m (distance 0–60 m), H = 8 m.
- **Trough at 2 m:** i = 9 m; S_max = 0.282743/(√(2π) · 9) = 12.5331 mm (M3 (a)'s case A); z_f/z₀ = 0.1.
- **Zones:** at offsets ±9 m.
  - Zone 1 is hogging, offsets −30 to −9.
  - Zone 2 is sagging, −9 to 9.
  - Zone 3 is hogging, 9 to 30, the mirror of zone 1.

| zone | L (m) | Δ (mm) at offset | Δ/L | ε_h | BW ε_b, ε_d | BW ε_bt, ε_dt | T ε_b, ε_d | T ε_bt, ε_dt |
|---|---|---|---|---|---|---|---|---|
| 1 hog | 21 | 2.67082 at −18.2775 | 1.27182e-4 | 1.77148e-4 | 1.78129e-4, 8.82163e-5 | **3.55277e-4**, 2.07056e-4 | 2.06820e-4, 1.02425e-4 | **3.83968e-4**, 2.16111e-4 |
| 2 sag | 18 | 4.93141 at 0 | 2.73967e-4 | −4.22319e-4 | 4.12670e-4, 1.19216e-4 | −9.64855e-6, **1.51465e-4** | 4.52008e-4, 1.30580e-4 | 2.96894e-5, **1.56171e-4** |

- **Zone 2 in closed form:** Δ = S_max(1 − e^(−1/2)) = 4.93141 mm, with a level chord. ε_h = 2u(9)/18 = −c₁ S_max e^(−1/2)/9 = −4.22319e-4.
- **Governing:** zone 1, by distance on a tie with zone 3. Category 0 for both methods.
- **Stage 1:**
  - The largest settlement is 12.5331 mm at distance 30 m. Against 10 mm: utilization 1.25331, fails.
  - The largest |slope| is S_max e^(−1/2)/i = 8.44637e-4 (1/1184) at distances 21 and 39 m. The governing distance is 21 m. Against 1/500: utilization 0.422319, passes.
- **With a 2.5i cut-off:** the assessed range is offsets −22.5 to 22.5 (distance 7.5–52.5 m). Zone 2 is unchanged. Zone 1 has:
  - L = 13.5 m, Δ = 1.36588 mm at −15.8187, Δ/L = 1.01176e-4, ε_h = 2.30558e-4;
  - BW: ε_b = 1.11061e-4, ε_bt = 3.41619e-4;
  - T: ε_b = 1.33668e-4, ε_bt = 3.64226e-4.

  So in this case the cut-off lowers the governing strain, as Netzel warns, by 3.8 % (BW) and 5.1 % (T).

**Case B: a wall wholly in hogging.** Case A's trough, the wall from offset 12 to 30 m. One zone, hogging:
- L = 18 m; Δ = 1.82746 mm at 19.5918; Δ/L = 1.01526e-4; ε_h = 1.86348e-4.
- BW: ε_b = 1.32665e-4, ε_d = 7.66508e-5, ε_bt = 3.19013e-4, ε_dt = 2.08564e-4.
- T: ε_b = 1.56260e-4, ε_d = 9.02835e-5, ε_bt = 3.42608e-4, ε_dt = 2.16294e-4.
- Stage 1: 5.15253 mm and |slope| 7.63338e-4, both at the wall's start.

**Case C: twin tunnels 15 m apart** (`twins_below_the_surface`'s tunnels), foundation at the surface.
- **Trough:** i = 10 m each, S_max = 11.2798 mm each.
- **Wall:** offsets −30 to 45 m relative to the north tunnel, H = 8 m.
- **Zones:** inflections at −7.56962 and 22.5696.
  - Zone 1, hogging: L = 22.4304; Δ = 2.78184 mm at −18.1187; Δ/L = 1.24021e-4; ε_h = 1.78939e-4; ε_bt is 3.56797e-4 (BW) and 3.84077e-4 (T).
  - Zone 2, sagging: L = 30.1392; Δ = 7.67556 mm at 7.5; Δ/L = 2.54670e-4; ε_h = −2.78883e-4; ε_dt is 9.17941e-5 (BW) and 9.25256e-5 (T).
  - Zone 3 mirrors zone 1.
- **Stage 1:** 17.0289 mm at offset 7.5, and |slope| 8.40531e-4.
- **With a 2.5i cut-off:** each tunnel's range is ±25 m about its axis, and the outermost on each side gives offsets −25 to 40. Zone 1 has:
  - L = 17.4304 m, Δ = 1.84690 mm, Δ/L = 1.05959e-4, ε_h = 2.05135e-4;
  - ε_bt is 3.41290e-4 (BW) and 3.65948e-4 (T).

**Case D: twin tunnels 30 m apart, five zones.** As case C with the south tunnel at offset 30, and the wall from −30 to 60.
- **Zone ends:** −9.95800, 7.54021, 22.4598, 39.9580.
- **Governing:** zone 3, the hogging zone between the tunnels.
  - L = 14.9196 m; Δ = 2.07027 mm at 15; Δ/L = 1.38762e-4; ε_h = 2.92690e-4.
  - BW: ε_b = 1.62774e-4, ε_bt = 4.55464e-4.
  - T: ε_b = 1.94598e-4, ε_bt = 4.87289e-4.
- **The other zones:** the outer hogging zones (1, 5) have ε_bt of 2.97218e-4 (BW) and 3.19763e-4 (T). The sagging zones (2, 4) have ε_dt of 1.11356e-4 (BW) and 1.14365e-4 (T).

**Case E: an oblique wall at 45°.**
- **Inputs:** case A's trough (foundation depth 2 m), with the tunnel at azimuth 0 through the origin, so offset = x. The wall is a `Building` from (−30, −30) to (30, 30), 84.8528 m long, H = 8 m.
- **Zones:** the zone ends are at offsets ±9, at distances 29.6985 and 55.1543 m.
- **Zone 1, hogging:**
  - L = 29.6985 m; Δ = 2.67082 mm; Δ/L = 8.99312e-5 (= sin 45° × case A); ε_h = 8.85741e-5 (= sin²45° × case A).
  - BW: ε_b = 1.36353e-4, ε_bt = 2.24928e-4.
  - T: ε_b = 1.52553e-4, ε_bt = 2.41127e-4.
- **Zone 2, sagging:**
  - L = 25.4558 m; Δ/L = 1.93724e-4; ε_h = −2.11159e-4.
  - BW: ε_bt = 5.25523e-5, ε_dt = **7.35408e-5**.
  - T: ε_bt = 6.80823e-5, ε_dt = **7.47292e-5**.
- **Stage 1:** the largest |slope| along the wall is 5.97249e-4 (= sin 45° × 8.44637e-4).

**Case J: Jones's Examples 13.1 and 13.2.**
- **Inputs:** z₀ = 18 m, D = 8 m, V_L = 1.5 %, k = 0.5, at the surface. i = 9 m; S_max = 0.753982/(√(2π) · 9) = 33.4217 mm. The wall is masonry, from offset −25 to 6.5 m, H = 5.6 m.

| zone | L | Δ (mm) at offset | Δ/L | ε_h | BW ε_bt, ε_dt | T ε_bt, ε_dt | category |
|---|---|---|---|---|---|---|---|
| 1 hog | 16 | 4.88003 at −16.7506 | 3.05002e-4 | 5.72235e-4 | **1.01229e-3**, 6.22703e-4 | **1.07880e-3**, 6.37859e-4 | 2 |
| 2 sag | 15.5 | 10.1214 at −0.860446 | 6.52994e-4 | −1.25380e-3 | −3.15795e-4, **4.05387e-4** | −2.47931e-4, **4.09685e-4** | 0 |

- **Jones's own values,** sampled at 1 m: Δ/L = 3.04653e-4 and 6.52738e-4; ε_h = 5.448e-4 and −1.1829e-3, plain means. Given these, the strain equations must reproduce:
  - **T, hogging:** ε_b = 0.0005060, ε_d = 0.0002302, ε_bt = 0.0010508, ε_dt = 0.0006130.
  - **T, sagging:** ε_b = 0.0010055, ε_d = 0.0002361, ε_bt = −0.0001774, ε_dt = 0.0003903.
  - **BW:** hogging ε_b = 0.0004396 (the intent's 0.044 %). This is Claude's value, not Jones's.
- **Stage 1 (Example 13.1):**
  - **The 10 mm contour:** settlement 10 mm falls at offset √(2i² ln(S_max/0.01)) = 13.9811 m. Jones's 13.977 m uses S_max rounded to 33.4 mm; S(13.977) = 10.0072 mm.
  - **The 1/500 slope:** it falls at 12.2618 m (Jones: 12.262).
  - **On this case's wall:** 33.4217 mm at offset 0, and |slope| 2.25237e-3 at −9.

### Changes
- **SPEC §1.3:**
  - "facade" becomes "wall" in the Buildings row and the station-and-offset bullet.
  - Assumptions are added for buildings: greenfield at foundation level, and the wall as a beam of height H and unit width.
- **SPEC §2.1:** buildings cite Mair, Taylor & Burland (1996) after the originals. The beam and Eq. 10 are garisenda's own mechanics (Mechanics 1–3).
- **SPEC §2.5:** the building method's validity (decision 14).
- **SPEC §3:**
  - `gs.movement_profile` takes a `Building` too.
  - The source gains the extent of its trough on a segment (decision 6).
- **SPEC §4:** the building presets (decision 4).
- **SPEC §5.1:**
  - `Result` gains `zones`.
  - `CHECK_COLUMNS` gains `zone` and `category` (decision 11).
  - `asset` may be a `Building`.
- **SPEC §8.3:** the `Building` and `perpendicular_building` (decisions 1–2). "Facade" becomes "wall" in the polyline bullet: each edge of a footprint is a wall.
- **SPEC §12.4:** M4 splits into (a) and (b).
- **SPEC §13 Q4:** answered (intent decision 1).
- **`docs/reference/sources.md`:**
  - `mair1996` is new: Tables 1–2, Eqs. 7–10, §§4.1–4.3, 4.5, 5.1–5.3, verified 2026-11-10.
  - `jones2022` is new: as the check of the worked examples and of Eqs. 13.12 and 13.23, not cited for equations.
- **`docs/TODO.md` #7:**
  - Sources read: Mair, Taylor & Burland (1996) and Jones (2022).
  - Primaries still to find: Burland & Wroth (1974), Burland et al. (1977), Boscardin & Cording (1989), Rankin (1988), Burland (2001), Netzel (2009), Harris & Franzius (2006).
  - Burland (1997) is in hand and unread.
- **New:**
  - `gs.buildings` with `Building` and `perpendicular_building`;
  - `gs.check_building`;
  - the beam methods and cut-offs (decisions 3, 6);
  - presets in `gs.presets` (decision 4).
- **M4 (b):** figures and user docs. Until then, `gs.plot.profile` draws a building's movement profile and its check as the four ground panels, since the columns are the same. `gs.plot.cross_section` draws a building as its wall line at foundation depth. Whichever needs less code; M4 (b) designs both.

### Decisions

**Geometry (intent: "The API")**

1. 🟡 **`gs.buildings.Building(*, building_id, vertices, foundation_depth, height)`.**
   - `vertices` are two plan points (x, y), in m if plain numbers.
   - The wall is level, at `foundation_depth` (≥ 0). Stepped foundations come with polylines (M5).
   - `height` is H, from foundation level to the eaves (Mair, Taylor & Burland, §4.1). It must be positive.
   - All three are geometry (SPEC §4), recorded on the result as `building.<name>`.
   - Like `Utility`, it carries `vertices` as (x, y, depth) at the foundation, so the profile and the source's segment functions take it unchanged.
   - Only two vertices are accepted, as for utilities.
2. 🟡 **`gs.buildings.perpendicular_building(tunnel, *, building_id, station, start_offset, end_offset, height, foundation_depth=None, foundation_elevation=None, ground_elevation=None)`.**
   - It mirrors `perpendicular_utility`. The level is given by exactly one of `foundation_depth`, or `foundation_elevation` with `ground_elevation`.
   - There is no `elevation_reference`, since a wall has no section.
   - It records the `BuildRecord` and the assumption that it is built perpendicular.
   - It has the same errors as the utility builder: equal offsets, a level above the ground, a missing or doubled level.

**The check (intent: "The API")**

3. 🟡 **`gs.check_building(profile, *, beam_method, youngs_to_shear_modulus_ratio, category_limits, cutoff, settlement_limit, slope_limit, acceptable_category, interaction) -> Result`**, at the top level beside the pipe checks.
   - **`profile`:** a movement profile whose asset is a `Building`. Otherwise it raises `TypeError`. The profile carries the source and the wall, which Δ and the zone ends need (Mechanics 4–5), and the caller's `spacing`, as for the pipes.
   - **`beam_method`:** `gs.buildings.burland_wroth_beam()` (α_s = 3/2, Eqs. 7–8 as Mair, Taylor & Burland give them) or `gs.buildings.timoshenko_beam()` (α_s = 6/5, Mechanics 1–2). Each is a named method object, recorded with `record_method`.
   - **`youngs_to_shear_modulus_ratio`:** E/G, a positive plain number or a `Sourced` one. "Stiffness ratio" was rejected, because it is the name of Potts & Addenbrooke's relative stiffness, which comes with soil–structure interaction.
   - **`category_limits`:** a `gs.buildings.DamageCategories` (decision 9), or a preset of one.
   - **`cutoff`:** decision 6.
   - **`settlement_limit`:** a length.
   - **`slope_limit`:** a slope, which refuses a plain number, as strains do (SPEC §6). 1/500, 0.2 % and 2 mm/m are all in use.
   - **`acceptable_category`:** decision 10.
   - **`interaction`:** only `"greenfield"`.
   - **`None`:** the Stage 1 limits and `acceptable_category` may each be given as `None`, which reports the value with no utilization (as M3's limits do).
   - **Errors:** each missing judgment raises `TypeError` naming it, what it depends on and how to set it. A limit below zero, or E/G ≤ 0, raises `ValueError`. A limit of zero is allowed, as in M3 (b).
4. 🟡 **Presets in `gs.presets`.** Each value is a `Preset`, with caveats naming whom the paper quotes:
   - `youngs_to_shear_modulus_ratio(*, structure)`, with rows `"masonry"` (2.6, p. 716) and `"framed"` (12.5, §4.5, p. 717). Caveat: Burland & Wroth (1974) haven't been read. For `"framed"`, also that Eq. 10 still assumes ν = 0.3 (decision 8).
   - `damage_categories()`: Table 2 (p. 715), after Boscardin & Cording (1989), with Table 1's degrees of severity. Caveat: the originals haven't been read. Table 1's note on slopes of 1/100 and 1/150 isn't used. Mair, Taylor & Burland's footnote says no case showed severe damage below 0.3 %.
   - `preliminary_assessment_limits()`, a `PreliminaryLimits(settlement, slope)`: 10 mm and 1/500, from §5.2, p. 717. Caveat: Jones (2022) attributes them to Rankin (1988), which hasn't been read. They are set for the ground surface (decision 7).

**Zones, Δ and the cut-off (intent: "Zones", "Δ, exactly", "The cut-off")**

5. 🟡 **Zones.**
   - **Ends:** the assessed range is split at the zeros of `vertical_curvature`. They are found by root-finding on the source's exact third derivative, with the sampling and noise threshold of `find_critical_distances`, so a far-field wall with no curvature above noise is one zone.
   - **Mode:** a zone is hogging where d < 0 at Δ and sagging where d > 0 (Mechanics 5).
   - **A flat zone:** where Δ is 0 to rounding (below 1e-10 of the zone's largest |w|), the zone is `"flat"`, ε_b = ε_d = 0, and it is assessed on ε_h alone through Eqs. 9–10.
   - **No minimum length.** A short zone's ε_b goes to zero with L (Eq. 7's shear term), and its ε_h is the local ground strain, which is what it should be. Zero-length zones (ends within 1 µm) are merged.
   - **No zone at all:** a wall wholly beyond the cut-off. It is reported with the reason (decision 12), never dropped (SPEC §10).
6. 🟡 **The cut-off is a named object, recorded with `record_method`:** `gs.buildings.no_cutoff()` (the whole wall) or `gs.buildings.trough_width_cutoff(multiple=2.5)`.
   - A plain number was rejected: `cutoff=22.5` meant as meters would be read as 22.5i with no way to catch it. A named object also leaves room for the worst-cut-off search (out of scope).
   - **The range:** for each transverse trough, the points on the wall's line within multiple × i of its axis in plan, with i at the foundation depth (the trough the wall follows). Over several sources, the range is from the first such point to the last, so the ground between two tunnels is kept (intent decision 3).
   - **The source gains `trough_extent(*, start, end, multiple)`,** returning that range along a segment, or none. A superposition takes the hull of its sources' ranges.
   - **Stations and Stage 1:** stations outside the range have no zone. Stage 1 runs on the whole wall.
   - **Rows:** the cut-off points are added as rows (decision 11).

**Stage 1**

7. 🟡 **Stage 1 runs on the same profile, at foundation level,** with the largest settlement and the largest |`vertical_slope`| along the wall. The profile has every peak of both among its critical distances, so the largest row is exact.
   - Both sources state Stage 1 for the ground surface. At depth the trough is narrower and deeper, so this is the more onerous reading. The result records it as an assumption, and that depth 0 gives the published check.
   - Evaluating the surface separately was considered and rejected. Stage 1 and Stage 2 would then see two different troughs on one result.
   - The slope is along the wall, which is the wall's tilt. For an oblique wall it is sin θ times the ground's steepest slope (case E). The assumptions say so.

**Strains and categories (intent: "Category boundaries")**

8. 🟡 **Eq. 10 with ν = 0.3,** as Mair, Taylor & Burland state it whatever E/G is (p. 717), recorded as a constant (SPEC §4), not an argument. The docstring gives the general form (Mechanics 3), and the assumptions record ν = 0.3. Making ν a judgment was considered and rejected: the method fixes it, and with E/G = 12.5 the "ν" implied by E/G (5.25) isn't a Poisson's ratio.
9. 🟡 **`DamageCategories`:** an ordered table of bands, each with a `number` (int), a `label` (`"0"`, …, `"4 to 5"`), a `severity` (`"negligible"`, …) and an upper limit, the last unbounded.
   - The limits must increase. A user may build their own.
   - **A strain on a boundary falls in the lower band:** band n holds limit(n−1) < ε ≤ limit(n). So a check passes at utilization exactly 1, as every other check does. Putting it in the higher band was considered: the "limiting" strain marks the onset of the next category. The difference is measure zero, and consistency wins.
   - Categories 4 and 5 are one band, number 4 with label `"4 to 5"`, as Table 2 gives them.
10. 🟡 **`acceptable_category`** is a band number in the table, or `None`. An unknown number raises `ValueError` listing them.
    - The `damage_category` check's limit is that band's upper limit: 0.15 % for category 2, and ∞ for the last band, which always passes.
    - Its utilization is the governing strain over that limit.
    - With `None`, the limit, utilization and `passes` are NaN and NA, and the category is still reported.

**The result**

11. 🟡 **Its parts.** `analysis` is `"building_check"` and `subject` the building's id.
    - **`values`:** the profile's columns and rows, plus rows at the cut-off points and at each zone's Δ (marked `critical`), and:
      - `zone` (nullable int, NA outside the assessed range; a zone end belongs to the zone after it, and the last end to the last zone);
      - `chord` (m, the zone's chord settlement);
      - `deflection` (m, d = w − c, Jones's sign).
    - **`zones`** (new on `Result`, empty with its columns for every other analysis): one row per zone, in order, with columns:
      - `zone`, `mode`, `start`, `end`, `length`;
      - `deflection` (Δ, m), `deflection_distance`, `deflection_ratio`;
      - `horizontal_strain`, `bending_strain`, `diagonal_strain`, `total_bending_strain`, `total_diagonal_strain`;
      - `tensile_strain` (the larger of the two), `governed_by` (`"bending"` or `"diagonal"`);
      - `category`, `label`, `severity`.

      Units are in `attrs`.
    - **`checks`:** rows in this order:
      - `settlement` and `slope`: value, distance, limit, utilization, passes;
      - `zone_1` … `zone_n`: the zone's tensile strain against the acceptable band's limit;
      - `damage_category`: the governing zone's, the first by distance on a tie.

      `CHECK_COLUMNS` gains `zone` (the zone's number on zone rows, the governing zone's on `damage_category`) and `category` (nullable int). Zone rows have NaN `governing_distance`, because a zone's strain comes from a beam model and isn't at a point; the zone's Δ distance is in `zones`. The analytical and discrete columns are NaN and NA.
    - **`method`:** the profile's methods, plus "Building damage, staged method" with Eqs. 7–10 in the chosen beam's form and Mechanics 4–6, citing Mair, Taylor & Burland (1996), pp. 715–717, after Burland & Wroth (1974) and Boscardin & Cording (1989). The derivation of the Timoshenko form and Eq. 10 is stated as garisenda's own.
    - **`inputs`:** the judgments, ν and the merge tolerance.
    - **`governing()`:** unchanged.
    - **The summary:** one line each for Stage 1, one line per zone (mode, L, Δ/L, ε_h, the governing strain, the category), and the governing zone.
    - **`to_dict()`:** includes `zones`.
12. 🟡 **Assumptions recorded,** after the profile's:
    - the wall follows the greenfield trough at foundation level, with no stiffness. This is usually very conservative, and soil–structure interaction would reduce Δ/L and ε_h (Mair, Taylor & Burland, §5.3);
    - the wall is a beam of height H and unit width, with the neutral axis at the bottom in hogging and at mid-height in sagging;
    - Eq. 10 takes ν = 0.3;
    - compressive ε_h is used with its sign in Eqs. 9 and 10, as the sources do (intent decision 4);
    - the movement across the wall in plan isn't assessed. It is zero for a perpendicular wall;
    - Stage 1 is taken at foundation level, and the slope along the wall (decision 7);
    - the cut-off used;
    - the presets' caveats, as in M3 (b);
    - any check with no limit.

    **Flags:** "no zone" (the wall is wholly beyond the cut-off; the zone checks and `damage_category` are NaN and NA, verdict `within`) and decision 14's flags.
13. 🟡 **Sweep:** a `gs.sweep` row gains each check's value, utilization and pass/fail as now. `damage_category`'s `category` joins as a column. If `_sweep.py` reads `CHECK_COLUMNS` by name, the plan says what changes.

**Validity**

14. 🟡 **The depth limit stays, with its reason stated as the source gives it.**
    - **The flag:** z_f/z₀ ≥ 0.2 for any tunnel (the smallest z₀ governs) is `outside`. The message says that Harris & Franzius (2006), as reported by Jones (2022, p. 490), limit the surface-trough method to z_f/z₀ < 0.2, and that two or more basement levels or piled foundations should be assessed separately. Harris & Franzius is 🔬 until read.
    - **Why keep it:** garisenda's trough at foundation level removes the source's stated reason. But a deep basement or piles also change what "following the trough at foundation level" means, and it is the only limit stated anywhere.
    - **Otherwise:** `within`, with a `within` flag saying the method states no range of validity.
    - Dropping the flag was considered. It is a judgment for review.
    - The source's own verdicts (above the crown, M2 (b)) carry through the profile.

### Sources
- **mair1996:** Mair, Taylor & Burland (1996), Tables 1–2 (p. 715), Eqs. 7–9 and §§4.1–4.3 (p. 716), Eq. 10, §4.5 and §§5.1–5.3 (p. 717). Verified against the page images on 2026-11-10. It is cited "after" Burland & Wroth (1974), Burland et al. (1977) and Boscardin & Cording (1989), each 🔬 (TODO #7).
- **jones2022:** Jones (2022), *Soft Ground Tunnel Design*, Eqs. 13.12, 13.23 (pp. 476, 479), Examples 13.1–13.2 (pp. 470–490) and §13.2.1 (p. 490). Verified 2026-11-10. It is a check and a pointer, not cited for an equation (SPEC §2.1).
- The beam's shear coefficient and Eq. 10's general form are derived above (Mechanics 1–3).

### Acceptance criteria
1. **Case A:** every value in case A's table for both beam methods, the zone ends and the Δ distances; the governing zone; Stage 1's values, distances and utilizations. All within 1e-6 relative. Zone 3 equals zone 1.
2. **Cut-off:** case A and case C with `trough_width_cutoff(multiple=2.5)` give their cut-off ranges and zone 1 values, within 1e-6. Stations outside the range have `zone` NA. Stage 1 is unchanged by the cut-off.
3. **Case B:** one hogging zone, with its values.
4. **Twins:** case C's three zones and case D's five, with their ends and values. Case D's governing zone is zone 3.
5. **Oblique:** case E's values, Δ/L = sin θ and ε_h = sin²θ times case A's, and the slope = sin θ times case A's.
6. **Jones:**
   - Case J's full calculation within 1e-6, and categories 2 and 0.
   - Jones's printed ε_b, ε_d, ε_bt and ε_dt, from his own Δ/L and ε_h with the Timoshenko beam, to half a unit in his last digit. The same for the Burland & Wroth beam's 0.0004396.
   - A wall ending at offset 13.9811 m has largest settlement 10 mm (utilization 1 ± 1e-6). One ending at 12.2618 m, outside i, has largest slope 1/500.
7. **Δ is exact:** for cases A, C and E, each zone's Δ is at least the largest |d| from evaluating the source every 1 mm along the zone, then every 1 µm within 1 mm of the maximum. It exceeds that by no more than 1e-9 relative.
8. **Categories:**
   - Table 2's bands, including a strain exactly on each boundary (lower band) and above 0.3 % (band 4, `"4 to 5"`).
   - A custom `DamageCategories` with limits that don't increase raises `ValueError`.
   - `acceptable_category` 2 passes at 0.15 % and fails just above it. With `None`, the category is reported and `passes` is NA.
9. **Flat and no zone:**
   - A wall 500 m from the tunnel gives one flat zone, category 0, with ε_b = ε_d = 0.
   - A wall wholly beyond a 2.5i cut-off gives no zone, a flag naming why, and NaN/NA zone checks.
   - Neither raises.
10. **Validity:** foundation depth 2 m on z₀ = 20 m is `within`, with the no-range flag. 4 m (0.2) and 5 m are `outside`, naming the ratio, the tunnel and the limit. In a superposition the shallower tunnel's ratio governs.
11. **Judgments:**
    - Each of the eight, missing, raises `TypeError` naming it.
    - A plain number for `slope_limit` is refused, and a plain number for E/G is accepted.
    - `interaction` other than `"greenfield"` raises `ValueError`, and so do a negative limit and an unknown category.
    - Every judgment appears in `inputs` with its kind, how it was given and its preset's source. The presets' caveats appear once each.
12. **Not a building's profile:** a utility's profile, or anything else, raises `TypeError`.
13. **Builders:** `perpendicular_building` puts the wall at the right x, y and depth for depth and for elevation, records the build and the perpendicular assumption, and raises for each bad input. A `Building` given by vertices matches the built one. The building's inputs are named `building.<name>` on the profile.
14. **Reversal:** reversing the wall leaves every zone's values, the categories and Stage 1 unchanged, and maps distances to L − d.
15. **Beam methods:** at the same Δ/L, the Timoshenko beam's ε_b and ε_d are the larger. Eqs. 7 and 8 follow from Mechanics 1–2 with α_s = 3/2.
16. **Result shape:**
    - `zones` is empty with its columns on a movement profile and a pipe check.
    - `to_dict()` is JSON-serializable, with ∞ as `None`.
    - The summary lists Stage 1, each zone and the governing zone.
    - `CHECK_COLUMNS`' new columns are on every checks table.
17. **Sweep:** a sweep row over volume loss equals a direct call, including `damage_category`'s category.
18. **Published text:** no internal references in the new strings (`tests/test_published_text.py`).

## Plan

Seven build commits, each green on lint, format, mypy strict and pytest. All seven run on Opus. Most of the work is a calculation, its validity limits or its citations. The plumbing steps (2, and the plotting in 1) are too small to justify a session boundary for Sonnet. A new session starts before 5 and before 7. Items not in the spec are marked 🟡. Following the workflow rule, each SPEC change goes in the commit that makes it true.

### 1. `M4 (a): add the building and let a profile run along it` (Opus)
Spec decisions 1–2, and the profile half of SPEC §3's change.
- New `src/garisenda/_asset.py`:
  - `BuildRecord` moves here from `utilities/_utility.py`. `elevation_reference` becomes `ElevationReference | None`, and is `None` for a building 🟡. `gs.utilities.BuildRecord` still re-exports it.
  - `Asset = Utility | Building`, with `asset_name(asset) -> (label, id, prefix)`: `("Utility", id, "utility")` or `("Building", id, "building")`.
- New package `src/garisenda/buildings/` (exported as `gs.buildings`). `_building.py` holds:
  - `Building(*, building_id, vertices, foundation_depth, height)`. `vertices` are two plan points; the class stores (x, y, foundation_depth) like `Utility`. It validates as `Utility` does, plus height > 0 and foundation_depth ≥ 0 and finite. Inputs `vertices`, `foundation_depth`, `height` are each `"geometry"`.
  - `perpendicular_building(tunnel, *, building_id, station, start_offset, end_offset, height, foundation_depth=None, foundation_elevation=None, ground_elevation=None)`. It mirrors `perpendicular_utility`, with no section shift. It shares `_scalar` and the vertex placement through a helper extracted from `perpendicular_utility` 🟡, which is a refactor inside this commit with no change in behavior.
  - Each docstring is the reference entry.
- `src/garisenda/profile/_movement_profile.py`:
  - `movement_profile(asset, source, *, spacing)`: the first parameter is renamed `utility` → `asset` 🟡. No example or test passes it by keyword.
  - `profile_rows` and `_bore_remedy` take an `Asset`. Messages, and the input prefix (`utility.<name>` / `building.<name>`), come from `asset_name`. `_bore_remedy` names the elevation reference only for a utility.
  - The docstring says a building's profile is at its foundation level.
- `src/garisenda/_result.py`: `asset: "Asset | None"`.
- `src/garisenda/plot/_cross_section.py` (the interim drawing from the spec's Changes): a building is drawn as its wall, a line at foundation depth with `gid="building"`, labeled with its height, in place of the utility band. `gs.plot.profile` already draws any unknown analysis as the four ground panels, so it needs no change.
- `src/garisenda/__init__.py` exports `buildings`. New `docs/site/reference/buildings.md` goes in the `zensical.toml` nav (the reference-entry test needs it).
- `SPEC.md`:
  - §1.3: "facade" becomes "wall" in the Buildings row and the station-and-offset bullet;
  - §3: `gs.movement_profile` takes a `Building`;
  - §8.3: `Building`, `perpendicular_building`, and "wall" in the polyline bullet.
- Tests:
  - new `tests/buildings/test_building.py` covers AC 13: placement for depth and for elevation; the `BuildRecord` and the perpendicular assumption; each bad input (equal offsets, a level above the ground, a missing or doubled level, height ≤ 0, an empty id, three vertices); and a `Building` given by vertices equal to the built one;
  - `tests/profile/test_movement_profile.py`: a building's profile equals a utility's on the same line, column for column; its inputs are named `building.height` and so on.
  - `tests/plot/test_cross_section.py`: a building's profile draws the `building` line at foundation depth, and `rcParams` are unchanged.

### 2. `M4 (a): add zones to Result and zone and category to the checks` (Opus)
Spec decision 11's shape, with no building check yet.
- `src/garisenda/_result.py`:
  - `ZONE_COLUMNS` and `ZONE_TYPES` (decision 11's list; `zone` and `category` are `Int64`, `mode`, `governed_by`, `label` and `severity` are `object`), and `empty_zones()`.
  - `Result.zones: pd.DataFrame = field(default_factory=empty_zones)`, placed after `warnings`. It is compared in `__eq__` like the other tables, and `to_dict()` gains `"zones"` (rows, ∞ as `None`).
  - `CHECK_COLUMNS` gains `zone` and `category` (`Int64`) after `governed_by` 🟡.
  - New `checks_frame(rows)`, which builds a checks table from row dicts, filling absent columns with NaN or NA and applying `CHECK_TYPES`. `_continuous_pipe._checks` and `_jointed_pipe._joint_checks` use it.
- `src/garisenda/_sweep.py`: for a check whose `category` is non-NA in any run, the row gains `<check>_category` (`Int64`) 🟡. That covers `damage_category` and the zone rows.
- `SPEC.md` §5.1: `zones`, the two new check columns, and `asset` may be a `Building`.
- Tests:
  - `tests/test_result.py`: `zones` is empty with its columns and types on a profile and on both pipe checks; both new check columns are on every checks table (AC 16, first and fourth bullets); `to_dict` with a non-empty `zones` goes through `json.dumps`;
  - `tests/test_sweep.py`: a pipe-check sweep has no `_category` columns.

### 3. `M4 (a): find a trough's extent along a segment` (Opus)
Spec decision 6's source method, and the rest of SPEC §3's change.
- `src/garisenda/sources/_movement.py`: `Source` gains `trough_extent(*, start, end, multiple) -> tuple[float, float] | None`. It returns the distances along the segment where the offset from each transverse trough's axis is within multiple × i, or `None` if there are none.
- `_transverse.py`: offset is linear along the segment, so the range is the interval where |o(s)| ≤ m·i, clipped to [0, L]. A segment parallel to the tunnel gives all of it or none.
- `_transverse_trough.py`: the same, with i from `width_at` at the segment's depth. A segment whose depth changes raises `ValueError`: a wall is level, and on a sloping segment i would vary along it 🟡.
- `_superposition.py`: the hull of the sources' ranges, or `None` if every source gives none.
- `multiple` must be positive and finite, or `ValueError`.
- `SPEC.md` §3: the source's trough extent.
- Tests in `tests/sources/`:
  - the surface trough, perpendicular (±m·i about the axis) and at 45° (√2·m·i on each side of the crossing);
  - the trough at depth: i at 2 m on case A's tunnel, so 2.5i = 22.5 m;
  - a segment wholly beyond the extent gives `None`, and a sloping segment raises;
  - the superposition is case C's hull, offsets −25 to 40;
  - parallel segments both inside and outside the extent.

### 4. `M4 (a): add the beam methods, damage categories and presets` (Opus)
Mechanics 1–3 as pure functions, and spec decisions 4, 6 (the objects), 8 and 9.
- New `src/garisenda/buildings/_beam.py`:
  - `BeamMethod(name, shear_deflection_coefficient)`, frozen, with `burland_wroth_beam()` (3/2) and `timoshenko_beam()` (6/5);
  - `section(mode, height) -> (t, I)`;
  - `bending_strain(deflection_ratio, *, length, height, mode, youngs_to_shear_modulus_ratio, beam)` (Mechanics 1);
  - `diagonal_strain(...)` (Mechanics 2);
  - `total_bending_strain(ε_b, ε_h)` and `total_diagonal_strain(ε_d, ε_h, poisson_ratio=POISSON_RATIO)` (Mechanics 3);
  - `POISSON_RATIO = 0.3`.

  The docstrings give each equation in both forms, cite Mair, Taylor & Burland (1996), p. 716–717 for Eqs. 7–10, and state that the derivation of the Timoshenko form and the general Eq. 10 is garisenda's own.
- New `src/garisenda/buildings/_categories.py`: `Band(number, label, severity, upper_limit)` and `DamageCategories(bands)`. The limits must increase and the last band is unbounded, or `ValueError`. `category(strain)` puts a boundary strain in the lower band. `band(number)` raises `ValueError` listing the numbers.
- New `src/garisenda/buildings/_cutoff.py`: `NoCutoff` / `no_cutoff()` and `TroughWidthCutoff(multiple)` / `trough_width_cutoff(*, multiple)`, each with a `name` for `record_method`. `multiple` is positive, or `ValueError`.
- `src/garisenda/presets.py`:
  - `youngs_to_shear_modulus_ratio(*, structure)`, with rows `masonry` (2.6) and `framed` (12.5);
  - `damage_categories()`;
  - `preliminary_assessment_limits()`, returning a frozen `PreliminaryLimits(settlement, slope)`. The settlement is `10 mm`. The slope is `2 mm/m` 🟡, which is 1/500 as a quantity, since a slope refuses a plain number.
  - Each has the sources and caveats of decision 4. The docstrings are the reference entries.
- `gs.buildings` exports the beam methods, `DamageCategories`, `Band` and the cut-offs. `docs/site/reference/buildings.md` lists them.
- `SPEC.md`:
  - §2.1: buildings cite Mair, Taylor & Burland (1996) after the originals, 🔬; the beam and Eq. 10 are garisenda's own mechanics;
  - §4: the building presets.
- Tests:
  - new `tests/buildings/test_beam.py`:
    - AC 6, second bullet: Jones's printed ε_b and ε_d from his Δ/L and ε_h with the Timoshenko beam, to half a unit in his last digit, and 0.0004396 with Burland & Wroth's. His ε_bt and ε_dt are checked from his printed (rounded) ε_b and ε_d, as he chains them: from the unrounded ε_d, hogging ε_dt is 0.00061306, outside half a unit of his 0.0006130;
    - AC 15: the Timoshenko beam gives the larger strains, and with α_s = 3/2 the functions reproduce Eqs. 7–8 as printed, written out separately in the test;
    - Mechanics 3's ε_dt ≥ 0 over a grid of ε_h;
  - new `tests/buildings/test_categories.py` covers AC 8, first two bullets;
  - `tests/test_presets.py`: each row's value, source and caveats, plus a missing or unknown row.

### 5. `M4 (a): add gs.check_building` (Opus)
The check on the whole wall (`no_cutoff`). New session.
- New `src/garisenda/buildings/_check.py`, `check_building(profile, *, beam_method, youngs_to_shear_modulus_ratio, category_limits, cutoff, settlement_limit, slope_limit, acceptable_category, interaction)`, with `@judgments` for all eight. It is exported at the top level, and `docs/site/reference/garisenda.md` gains it. The docstring is the reference entry: Mechanics 1–7, inputs and outputs with units, assumptions, sources.
  - **Reading:**
    - `_read_profile` is generalized with a required `asset_type` argument (the pipe checks pass `Utility`) and raises `TypeError` for anything but a profile along that asset (AC 12). `_read_interaction` is reused, naming the asset in its message, and `along_line` takes any asset;
    - E/G goes through `record` (dimensionless, `"read as SI"`) and must be > 0;
    - `settlement_limit` goes through `_read_limit` in m, and `slope_limit` through `_read_limit` (dimensionless, `plain_number="refuse"`);
    - `category_limits` goes through `record_method`-style unwrapping of a `Sourced`, and is recorded by name with its bands' limits 🟡;
    - `acceptable_category` is a band number or `None`, recorded as a design judgment;
    - `beam_method` and `cutoff` go through `record_method`. Until step 6, `trough_width_cutoff` raises `NotImplementedError`.
  - **Zones** (decision 5), in `_zones(asset, source, low, high)`:
    - `along_line` gives w″ along the wall, and `find_zeros` runs on it over [low, high], with the step, tolerance and scale rule of `_peaks`;
    - ends within `MERGE_TOLERANCE` are merged;
    - for each zone, the zero of w′ − chord slope is found by `find_zeros` on the zone, to 1e-9 m. With no sign change, or Δ below 1e-10 of the zone's largest |w|, the zone is `"flat"`;
    - the mode comes from the sign of d at Δ;
    - ε_h = (u_a(s₂) − u_a(s₁))/L, from the exact displacements at the ends.
  - **Values:** the profile's rows plus rows at the zone ends and each Δ, through `_add_stations` and `profile_rows`, marked `critical`. Then the `zone`, `chord` and `deflection` columns (decision 11).
  - **Zones table** from step 4's functions, with the category from `category_limits`.
  - **Checks** through `checks_frame`:
    - `settlement` is the largest positive `vertical`, by `extreme`;
    - `slope` is the largest |`vertical_slope`|;
    - each `zone_<n>` is its tensile strain against the acceptable band's upper limit;
    - `damage_category` is the governing zone (the largest tensile strain, first by distance on a tie at `TIE`).
    - The zone rows have NaN `governing_distance`. Utilizations come from `_utilization`, and ∞ for the last band passes.
    - `governed_by` is `"analytical"` for Stage 1 (the exact extreme, as the pipe checks say) and the zone's `"bending"` or `"diagonal"` on the zone and `damage_category` rows.
  - **Method, assumptions, inputs** as decisions 11–12, with each preset's caveats through `preset_caveats`, and ν as a `"constant or setting"`.
- Tests in new `tests/buildings/test_check_building.py`, with cases A–E and J built as fixtures from the spec's inputs (C and D from a helper with `twins_below_the_surface`'s tunnels, checked against it). The hand values are good to 1e-6 relative and printed to six figures, so each is compared to 1e-6 relative plus half a unit in its last digit; closed forms (case A's zone 2, case E's sin θ relations) to 1e-9:
  - AC 1: case A, both beams, every table value, the ends, the Δ distances, the governing zone and Stage 1, to 1e-6 relative;
  - AC 3: case B;
  - AC 4: cases C and D, with D governed by zone 3;
  - AC 5: case E, and the sin θ / sin²θ relations against case A;
  - AC 6, first and third bullets: case J, categories 2 and 0, and the Stage 1 contour walls;
  - AC 7: Δ against a 1 mm then 1 µm independent search, for A, C and E;
  - AC 8, third bullet: `acceptable_category` 2 at 0.15 % and just above (on a case scaled by volume loss to land there 🟡), and `None`;
  - AC 11: the eight missing judgments; plain-number slope refused and E/G accepted; bad `interaction`, a negative limit, an unknown category; the inputs and caveats;
  - AC 12;
  - AC 14: reversal, on cases A and D, in a hypothesis property test (`tests/buildings/test_check_building_properties.py`) over offsets and angle, as M3 (a)'s.

### 6. `M4 (a): add the cut-off, flat walls and the depth limit` (Opus)
Spec decisions 5 (flat, no zone), 6, 12's flags and 14.
- `src/garisenda/buildings/_check.py`:
  - with `trough_width_cutoff`, the assessed range is `source.trough_extent(..., multiple=...)`, and rows are added at its ends. Stations outside it have `zone` NA. Stage 1 still runs over the whole wall;
  - `None` from the extent means no zone: the zones table is empty, the zone checks are absent 🟡 (no zones, so no rows), `damage_category` is NaN and NA, and the result carries a `within` flag naming the cut-off and the range;
  - the depth flag: for each tunnel (via `tunnels()`, or the lone source's `tunnel`), z_f/z₀ ≥ 0.2 gives an `outside` flag naming the ratio, the tunnel, the limit and the source as decision 14 states it. Otherwise a `within` flag says the method states no range of validity. Both cover every row;
  - the summary in `Result.__repr__`: for a `building_check`, Stage 1's two lines, a line per zone (mode, L, Δ/L, ε_h, governing strain and kind, category label), then `damage_category`.
- `SPEC.md`:
  - §1.3: the building idealization (greenfield at foundation level, beam of height H and unit width);
  - §2.5: the building method's validity;
  - §13 Q4: answered.
- Tests in `tests/buildings/test_check_building.py`:
  - AC 2: cases A and C with 2.5i, their ranges and zone 1 values; NA zones outside; Stage 1 unchanged;
  - AC 9: the wall 500 m away (one flat zone, category 0) and the wall beyond the cut-off (no zone, flag, NaN/NA), neither raising;
  - AC 10: depths 2, 4 and 5 m on z₀ = 20 m, and a superposition where the shallower tunnel governs;
  - AC 16, third bullet: the summary lines.

### 7. `M4 (a): sweep a building check and close out` (Opus)
New session.
- Tests:
  - AC 17 in `tests/test_sweep.py`: a sweep over volume loss equals direct calls, including `damage_category_category`;
  - AC 16, second bullet: `to_dict()` of cases A and J goes through `json.dumps`, with ∞ as `None`;
  - AC 18: `tests/test_published_text.py` passes over the new strings.
- Run every check:
  - the CI line;
  - Python 3.13 and 3.14;
  - `lowest-direct`, then `git checkout uv.lock`;
  - the docs build, `--strict`, with no `griffe:` warnings.
- Look at the interim building cross-section and profile figures once. Their design is M4 (b), so this only checks that they draw sensibly.
- Close-out:
  - `SPEC.md` §12.4: M4 split into (a), done with the date, and (b) next;
  - `docs/reference/sources.md`: `mair1996` and `jones2022` as the spec's Sources say;
  - `docs/TODO.md` #7: the sources read, the primaries still to find, and Burland (1997) in hand and unread;
  - `CHANGELOG.md` Unreleased: `gs.buildings`, `gs.check_building`, the new presets, `movement_profile`'s first argument renamed to `asset`, and the new `zones` and check columns;
  - `CLAUDE.md`: the status sentence and "Next" (M4 (b): the building figures and guide), plus any recurring mistake as a convention;
  - report each of the 18 ACs as met or not, with evidence.
