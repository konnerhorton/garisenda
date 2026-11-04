# M2 (b): movements below the surface

## Intent

### Goal
A caller can assess an asset below the ground surface, such as a buried utility, against a tunnel's transverse trough at the asset's own depth. The trough width changes with depth by a method the caller names: Mair & Taylor's (1997) method for clay, or a width i = k (z₀ − z) from a k the caller gives, recorded as their choice (decision 1). The subsurface trough is a source like any other (SPEC §3), so the profile, superposition, `gs.sweep` and the figures take it unchanged. Points the method doesn't cover are flagged, not raised (SPEC §2.5).

### Why
- **SPEC §12.4:** M2 (b) is "movements below the surface". Its done-when is golden values from the verified subsurface method, with the depth validity flags tested.
- **Utilities are buried.** Until now every asset below the surface is flagged `outside`, because M1's surface trough is applied at its plan position and the trough at depth is narrower, so settlement and curvature are underestimated there (`BELOW_SURFACE` in `sources/_transverse.py`). M3's utility checks need the movements at the pipe's depth.
- **The method, as the user gave it (2026-11-04)**, from Taylor (1995) and Mair & Taylor (1997), "Theme lecture: Bored tunnelling in the urban environment". SPEC §13 Q2 and TODO #3 name Mair et al. (1993) for the clay method; the spec step updates them to the paper the formula is verified against:
  - K(z) = 0.325 + 0.175 / (1 − z/z₀) (Taylor's form), which equals (0.175 + 0.325 (1 − z/z₀)) / (1 − z/z₀) (Mair's form);
  - i(z) = K(z) (z₀ − z) = 0.175 z₀ + 0.325 (z₀ − z).
  - 🔬 Not yet checked against the papers, which are in `../hangtu/sandbox/sources/inbox/` and may need OCR. Verifying them, with the equation numbers and validity limits, is the spec step's work.
- **What the formula settles (TODO #3):** i(z) is linear in depth, with di/dz = −0.325, so the derivatives with respect to depth stay short (M2 (a) decision 6). At the surface K = 0.5 and i = 0.5 z₀. At axis level i = 0.175 z₀, which is finite although K is not, so i is computed from the linear form, never as K (z₀ − z).

### Constraints
- **SPEC §3:** the subsurface trough is a `Source`. Its derivatives with respect to depth are now nonzero and exact, including the third derivatives. It finds its own critical distances on any segment, including one whose depth changes along it, where i varies along the segment.
- **SPEC §2.3:** where practice uses more than one method, the method is a required argument and garisenda doesn't pick. The width method has no default.
- **SPEC §4:** volume loss and, for the linear method, k remain required judgments. Mair's coefficients (0.175, 0.325) are part of the method, recorded as such, not judgments the caller sets.
- **SPEC §2.1, §2.4:** golden values from a worked example in the papers or a hand calculation from the verified equations, never from the code. The citations are verified against the papers before they go into a docstring.
- **SPEC §2.5, §5:** outside the method's range (the depth limit the papers state, points below the axis level, points beside the bore) the point is flagged with its reason, not raised. A point inside the bore still raises.
- **Test on segments at any angle** (CLAUDE.md), and on segments that change depth.
- **SPEC §9, §12.3:** the cross-section shows the trough at the asset's depth; the user docs and their example are written at close-out.

### Out of scope
- **A granular-specific method:** later (SPEC §13 Q2 stays open). The linear method with a caller's k is what's offered for granular ground, recorded as their choice.
- **New & Bowers (1994)** as a separate method: 🟡 proposed out of scope. It stays a candidate in TODO #3 unless the papers show M2 (b) needs it.
- **Interaction between tunnels, real alignments, the longitudinal trough:** as in M2 (a); M5, M6.
- **Utility and building checks:** M3, M4. This unit gives them the movements at depth.

### SPEC sections touched
- **§12.4:** M2's row marks (b) done at close-out.
- **§3:** the subsurface trough as a source, and nonzero derivatives with respect to depth.
- **§2.1, `docs/reference/sources.md`:** the subsurface sources, verified, with their keys and dates.
- **§13 Q2, TODO #3:** the clay method and the linear method become decided; TODO #3 keeps only the granular method and New & Bowers.
- **§9:** the cross-section with a subsurface trough.
- **§2.5:** the depth validity limits.

### Decisions (intent review, 2026-11-04)
1. **Two named width methods, neither mixed with the other:** (a) Mair & Taylor's (1997) method for clay, whose surface width k = 0.5 is built in and recorded as part of the method; (c) i = k (z₀ − z) from the caller's k, as already decided (M2 (a) decision 3), whose surface width is k z₀, the same as M1's surface trough. Considered and dropped: (b) refusing or flagging Mair's method combined with a surface k other than 0.5. With (a) the method carries its own surface width, so there's nothing to combine.

### 🟡 To settle in the spec
- **The API.** Proposed: one source, `gs.transverse_trough(tunnel, *, volume_loss, trough_width=...)`, where `trough_width` is a required method object (e.g. a Mair clay method, or a linear method that takes k). M1's `transverse_surface_trough` stays, and the linear method at z = 0 matches it exactly (an acceptance criterion). Names follow SPEC §8.5.
- **Settlement at depth.** Whether S_max(z) follows from the same volume loss at every depth, S_max(z) = V_L A / (√(2π) i(z)), as the papers state it. Not assumed until read.
- **Horizontal movement below the surface** (Taylor 1995): whether it's toward the axis, h = (o / (z₀ − z)) S, and what the vertical displacement's depth derivative becomes.
- **Validity limits:** the depth limit from Mair & Taylor (1997) or Mair et al. (1993), and what's flagged between the crown and the axis, beside the bore and below the axis.
- **Citations:** which paper and year each equation is cited to, once the inbox PDFs are read.

## Spec

No topic doc holds this, so the spec is here. Every 🟡 proposal below was accepted as written in review (2026-11-04). It settles the intent's "To settle in the spec" items (decisions 1–6, 9, 12). Read 2026-11-04 from `../hangtu/sandbox/sources/inbox/`, against the page images where the text layer was garbled: Taylor (1995), Mair & Taylor (1997) and Bracegirdle et al. (1996). Mair et al. (1993) isn't in the inbox and hasn't been read.

### What the papers say
- **Taylor (1995)**, pp. 124–125: the surface trough (Eqs. 1–4: V_L = 4V_s/(πD²), the Gaussian S_v = S_max exp(−y²/2i²), V_s = √(2π) i S_max, i = K z₀). Eq. 5, K = 0.325 + 0.175/(1 − z/z₀), "an empirical expression for K for tunnels in clay", from Mair et al. (1993). Eq. 6, S_h = (y/z₀) S_v, for vectors directed at the axis. Then: "In order to achieve a constant volume condition ... the displacement vectors should be directed at a point on the centre-line 0.175z₀/0.325 below tunnel axis level if eqn. 5 is used for K."
- **Mair & Taylor (1997)**, pp. 2361–2362: subsurface profiles "can also be reasonably approximated in the form of a Gaussian distribution in the same way as surface settlement profiles"; Eq. 7, i = K(z₀ − z); Eq. 8, K = (0.175 + 0.325(1 − z/z₀))/(1 − z/z₀), "proposed by Mair et al (1993)"; the point 0.175 z₀/0.325 below the axis (Taylor, 1995b), which "gives horizontal movements of 65% of those that would be obtained by assuming the ground movements to be directed towards the tunnel axis"; and, for sands, that even vectors toward the axis "may lead to significant underestimates of horizontal ground movement at the ground surface near the edge of the settlement trough". Its Fig. 20 (Mair et al., 1993) has data to z/z₀ ≈ 0.9, all in clays.
- **Bracegirdle et al. (1996)**, p. 660, on cast iron pipes: Eq. 1, the settlement with the volume V_s and the width i at the pipe's depth; Eq. 2, i = z₀(0.175 + 0.325(1 − z_p/z₀)), "derived from case studies by Mair et al (1993)"; and **"Equation 2 should only be applied when estimating ground movements above the level of the crown of the tunnel."** "An alternative method of estimating ground movements close to the tunnel is given by New & Bowers (1994)." Its Eq. 3, for horizontal movement, has a smudge before z₀ in its denominator. **Read as S_hf = (y/(z₀ − z_p)) S_v**, toward the axis (2026-11-04, from the 400 dpi scan layer, as a reading, not a verified citation): the fraction bar is centered on y and on "z₀ − z_p" to within 1 px, and the smudge starts about 1 mm left of the bar, where a typeset coefficient would have lengthened it; the smudge has only horizontal strokes, no digit; a coefficient for Taylor's point O would be about 1.54, four glyphs, where the smudge is one glyph wide; and the text says the movements are "towards the tunnel centreline". No cleaner copy is available.
- **Checked by hand:** Taylor's and Mair's forms of K agree (both give K = 0.675 at z/z₀ = 0.5), and K(z)(z₀ − z) = 0.175 z₀ + 0.325(z₀ − z). The 65 % is 0.325/0.5, the ratio at the surface of the field in decision 4 to M1's. Point O is where that field's vectors meet (decision 4).

### Changes
- **SPEC §2.1, §2.2:** the first verified sources; `docs/reference/sources.md` created with them (decision 11); how a review by a method's own authors is cited (decision 10).
- **SPEC §2.5:** the crown limit and what is evaluated below it (decision 7).
- **SPEC §3:** the transverse trough at depth, a source whose derivatives with respect to depth are nonzero and exact (decisions 1–6).
- **SPEC §5.1:** an input record can hold a named method (decision 2).
- **SPEC §9:** the cross-section draws the trough at the utility's depth (decision 9).
- **SPEC §13 Q2, TODO #3:** the clay method and the linear method decided; TODO #3 keeps the granular method, New & Bowers (1994) and reading Mair et al. (1993). **TODO #2** notes that Taylor (1995) and Mair & Taylor (1997) restate the surface trough, for whoever verifies it.
- **New:** `gs.sources.transverse_trough`, `gs.sources.TransverseTrough`, `gs.sources.mair_trough_width`, `gs.sources.linear_trough_width`, `gs.sources.TroughWidth`. A guide page, "Below the surface", with its example.
- **Unchanged:** `transverse_surface_trough` keeps its behavior; its below-surface flag now names `transverse_trough` as the method for depth.

### Decisions

**The source (intent: "The API")**

1. 🟡 **`gs.sources.transverse_trough(tunnel, *, volume_loss, trough_width) -> gs.sources.TransverseTrough`**, beside `transverse_surface_trough` in `gs.sources` (where M1 put sources; the intent's `gs.transverse_trough` would be the only source at the top level). `volume_loss` as in M1. `trough_width` is a required design judgment with no default (SPEC §2.3, §4): a `TroughWidth`, made by one of:
   - **`gs.sources.mair_trough_width()`**: Mair et al. (1993)'s method for clay. No arguments: its coefficients 0.175 and 0.325 are the method (intent decision 1, constraint SPEC §4).
   - **`gs.sources.linear_trough_width(*, trough_width_parameter)`**: i = k (z₀ − z), k a required design judgment, positive, as in M1 and under the same name, so a sweep of `trough_width_parameter` works on either source.

   Anything else, including a plain number for `trough_width`, raises `TypeError` saying how to write each method. Considered and dropped: one source with both troughs and a `depth=None` meaning "at the surface" (a default that picks a method); a `method="mair"` string (k would then be an argument that only one method takes).
2. 🟡 **What it records.** `trough_width` is an input record, kind "design judgment", whose value is the method's name (`"Mair et al. (1993), clay"`, `"linear"`), given-as `"method"`; so an input record's value becomes a pint quantity *or* a string (SPEC §5.1), and `to_dict()`, `to_frame()`, the summary and `gs.sweep`'s unchanged-inputs check take strings. The linear method adds `trough_width_parameter`. Mair's coefficients are not input records: they are in the method record's equations, so they can't be swept or overridden. Constants, "constant or setting": `depth_tolerance` (1e-3 m, decision 7), `critical_distance_sampling` (1/8) and `critical_distance_tolerance` (1e-9 m) (decision 8). Method: `"Transverse Gaussian trough at depth"`, its equations (decision 3) and the method's sources. Assumptions: decision 5's, then the tunnel's.

**The field (intent: "Settlement at depth", "Horizontal movement below the surface")**

3. 🟡 **Equations.** With o the point's offset from the axis in plan, z its depth, z₀ the axis depth, D the diameter and A = πD²/4:
   - **width:** i(z) = c₀ z₀ + c₁ (z₀ − z), with (c₀, c₁) = (0.175, 0.325) for Mair's method (Mair & Taylor 1997, Eqs. 7–8; Taylor 1995, Eq. 5; Bracegirdle et al. 1996, Eq. 2) and (0, k) for the linear method. Always computed in this form, never as K (z₀ − z), so it stays finite as z → z₀ (intent). di/dz = −c₁, a constant.
   - **settlement:** S(o, z) = (Q/i) exp(−r²/2), with r = o/i and Q = V_L A/√(2π). The trough's volume per unit length is √(2π) i S_max = V_L A at every depth (Bracegirdle et al. 1996, Eq. 1, with i at the pipe's depth; Taylor 1995, Eq. 3 at the surface).
   - **horizontal:** u_n = −c₁ r S = −c₁ (o/i) S, toward the axis, along the right-hand normal n as in M1 (SPEC §8.1).
4. 🟡 **Why that horizontal movement.** It is the only one that keeps the volume constant (undrained), as Taylor (1995, p. 125) requires, and is zero over the axis: ∂u_n/∂o + ∂S/∂z = 0 exactly (checked symbolically, and by AC 3). Its vectors meet the centerline at depth z₀ + (c₀/c₁) z₀, since u_n/S = −o/(i/c₁) and i/c₁ = (z₀ − z) + (c₀/c₁) z₀:
   - **Mair:** 0.175 z₀/0.325 below the axis: Taylor's (1995) point O, and Mair & Taylor's (1997) 65 % of M1's horizontal movement at the surface.
   - **Linear:** the axis itself, u_n = −(o/(z₀ − z)) S, which at z = 0 is M1's u_n = −(o/z₀) S exactly.

   So Mair's method at the surface has M1's settlement with k = 0.5 but 0.65 of its horizontal movement; that is the paper's statement, not a mismatch. **The sources disagree** (SPEC §2.3): Bracegirdle et al. (1996), Eq. 3, as read above, pairs Mair's width with vectors toward the axis, (y/(z₀ − z)) S, 1/0.65 ≈ 1.54 times this field's horizontal movement at the surface, rising to 2.08 at z = z₀/2 (the ratio is i/(c₁(z₀ − z))). Point O governs, because it is the only field that keeps constant volume with Mair's width (with vectors to the axis the horizontal and vertical strains disagree), it is what Taylor (1995) derived for that width, and it is the later of the authors' statements (Mair & Taylor 1997, p. 2362, which two of Bracegirdle et al.'s four authors wrote). The vectors-toward-axis pairing isn't offered as a second method: its source can't be read with certainty. 🟡 For M3: Bracegirdle et al. take joint pullout as the maximum horizontal movement, so a pullout check paired with their method would use the larger value; M3's spec revisits this.
5. 🟡 **Assumptions recorded:** steady state and transverse only (as M1); Gaussian at every depth, with the same volume V_L A; constant volume (undrained), which sets the horizontal movement; points below the crown get the trough at the crown (decision 7). Mair's method adds *"Mair et al. (1993)'s fit is to tunnels in clays (London Clay, soft clay, centrifuge tests); garisenda can't check the ground."* The linear method adds *"i = k (z₀ − z) with the caller's k, their choice: no source gives this width at depth. With constant volume, movement is toward the axis; in sands this may underestimate horizontal movement near the edge of the trough (Mair & Taylor 1997, p. 2362)."* No range is checked for k or volume loss (TODO #2), as in M1.
6. 🟡 **Exact derivatives.** u depends on (x, y, z) through o (gradient g = (n_x, n_y, 0)) and z (gradient e_z), and i is linear in z, so every derivative is a polynomial in r times exp(−r²/2):
   - ∂^(a+b) S/∂o^a ∂z^b = (Q c₁^b / i^(1+a+b)) P_ab(r) exp(−r²/2)
   - ∂^(a+b) u_n/∂o^a ∂z^b = (Q c₁^(b+1) / i^(1+a+b)) R_ab(r) exp(−r²/2)

   | a, b | P_ab (settlement) | R_ab (horizontal) |
   |---|---|---|
   | 0, 0 | 1 | −r |
   | 1, 0 | −r | r² − 1 |
   | 0, 1 | 1 − r² | r³ − 2r |
   | 2, 0 | r² − 1 | −r³ + 3r |
   | 1, 1 | r³ − 3r | −r⁴ + 5r² − 2 |
   | 0, 2 | r⁴ − 5r² + 2 | −r⁵ + 7r³ − 6r |
   | 3, 0 | −r³ + 3r | r⁴ − 6r² + 3 |
   | 2, 1 | −r⁴ + 6r² − 3 | r⁵ − 9r³ + 12r |
   | 1, 2 | −r⁵ + 9r³ − 12r | r⁶ − 12r⁴ + 27r² − 6 |
   | 0, 3 | −r⁶ + 12r⁴ − 27r² + 6 | r⁷ − 15r⁵ + 48r³ − 24r |

   Derived with ∂/∂z = −c₁ ∂/∂i and checked with sympy; the a-columns with b = 0 are M1's (with c₁/i = 1/z₀ at the surface for the linear method). Two checks: R_(1,b) = −P_(0,b+1) (constant volume), and fourth-order central differences of S and u_n match to 1e-6 (hand calculation, case C). The gradient, Hessian and third derivative are assembled from these with g and e_z, symmetric by construction as in M1. Below the crown (decision 7) every derivative with respect to depth is exactly zero.

**Validity (intent: "Validity limits")**

7. 🟡 **The crown limit, for both methods.** With crown depth z_c = z₀ − D/2:
   - z ≤ z_c + 1 mm: `within`.
   - **Deeper than the crown, outside the bore** (beside it, or below the axis): `outside`, evaluated as the trough at the crown, S(o, z_c) and u_n(o, z_c), with depth derivatives zero. Flag reason: *"Below the tunnel crown: the subsurface trough applies only above the crown (Bracegirdle et al. 1996, p. 660). Values are the trough at crown level; movements beside and below the bore need another method or numerical analysis."* Limit: `"depth at most z₀ − D/2 = <z_c> m (the crown)"`.
   - **Inside the bore:** raises, as in M1. **Above the surface:** raises, as in M1.

   Why evaluate at the crown: SPEC §2.5 asks for every point's result, flagged. The linear method's i reaches zero at the axis, so the formula itself can't be evaluated there, and Mair's gives a trough below the tunnel, which has no meaning. The crown values are continuous with the valid ones, and the flag says what they are. Considered and dropped: NaN (would break governing values and root-finding, SPEC §5.1, §10); evaluating the formula down to the axis (undefined for the linear method).
   - **Mair's method** has its limit from Bracegirdle et al. (1996), whose authors include two of Mair et al. (1993)'s. **The linear method** has no source for one, so the same crown limit is garisenda's choice, recorded in the flag's reason as such: *"(applied to the linear method by garisenda)"*.
   - **No `marginal` band:** no source gives one. Fig. 20's data reach z/z₀ ≈ 0.9; for a tunnel with z₀ < 5D the crown is deeper than that, so near the crown the fit is extrapolated. The docstring says so; it isn't a limit, since no paper states it as one.
   - 🔬 If Mair et al. (1993) is read later and states a different limit, it governs and this decision changes.

**Along a segment (intent constraint: segments that change depth)**

8. 🟡 **Critical distances by root-finding**, with `find_critical_distances` (M2 (a)) and the same constants as a superposition (sampling 1/8 of the feature length, tolerance 1e-9 m). On a level segment the analytic set is known, and is M1's with i(z): o = 0, ±i, ±√3 i, and on an oblique segment ±0.74196378 i and ±2.3344142 i (the polynomials in o at fixed z are M1's). On a segment that changes depth, i varies along it and there is no closed form. One path for both, tested against the analytic set on level segments (AC 6) and against dense sampling on sloped ones (AC 7). **`feature_length`** is the least i along the segment: i at its deeper end, with depth capped at the crown (decision 7), since i decreases with depth.

**Figures (intent: SPEC §9)**

9. 🟡 **The cross-section draws the trough at the utility's depth.** Its two movement panels evaluate the source at the built utility's axis depth (it is level: the builder makes it so), not at z = 0, and their titles say so: "Settlement at depth 10 m" (at the surface, as now, "Settlement at the surface"). The ±i marks are at i at that depth, from `TroughWidth.at(depth=..., axis_depth=...)`; reach is the utility's offsets and each tunnel's offset ± 3 i at that depth. For M1's surface trough this changes nothing it draws, since it returns the surface values at depth. Stations below the crown are already marked as flagged. Considered and dropped: drawing the surface trough beside it for comparison (one more line in a panel that, with twin tunnels, already has three).

**`TroughWidth`**

10. 🟡 **A frozen dataclass** with `name`, `surface_coefficient` (c₀), `rate` (c₁), `inputs` (its records), `equations`, `source` (the citation) and `assumptions`, and `at(*, depth, axis_depth) -> i` (plain SI floats or arrays). Not meant to be built directly; the two functions build it.

**Citations (intent: "Citations")**

11. 🟡 **Each equation is cited to the paper it was read in, naming the original:**
    - i(z) for clay: *Mair & Taylor (1997), Theme lecture: Bored tunnelling in the urban environment, Eqs. 7–8, pp. 2361–2362, after Mair et al. (1993)*, with Taylor (1995), Eq. 5, p. 125 and Bracegirdle et al. (1996), Eq. 2, p. 660 as the same equation in other forms.
    - The point O and constant volume: *Taylor (1995), Tunnelling in soft ground in the UK, p. 125*; Mair & Taylor (1997), p. 2362.
    - Settlement at depth with the volume V_L A: *Bracegirdle et al. (1996), Eq. 1, p. 660*.
    - The crown limit: *Bracegirdle et al. (1996), p. 660*.

    **SPEC §2.1 changes (accepted 2026-11-04).** It says secondary sources, "reviews" among them, are never cited for equations, and Mair & Taylor (1997) and Taylor (1995) are reviews; the original, Mair et al. (1993), *Géotechnique* 43(2), 315–320, isn't in hand. Decided: a review **by the method's own authors** that states the equation in full may be cited for it, naming the original ("after Mair et al. (1993)"), and the original stays 🔬 in TODO #3 until read. Mair and Taylor are two of Mair et al. (1993)'s three authors.
12. 🟡 **`docs/reference/sources.md`**, created (SPEC §2.2), one entry each, key and date verified 2026-11-04:
    - `taylor1995`: Taylor, R. N. (1995). Tunnelling in soft ground in the UK. In *Underground Construction in Soft Ground*, eds K. Fujita & O. Kusakabe, pp. 123–126. Balkema, Rotterdam.
    - `mair_taylor1997`: Mair, R. J. & Taylor, R. N. (1997). Theme lecture: Bored tunnelling in the urban environment. *Proc. 14th Int. Conf. on Soil Mechanics and Foundation Engineering*, Hamburg, pp. 2353–2385. Balkema. 🔬 The volume number isn't on the pages read.
    - `bracegirdle1996`: Bracegirdle, A., Mair, R. J., Nyren, R. J. & Taylor, R. N. (1996). A methodology for evaluating potential damage to cast iron pipes induced by tunnelling. In *Geotechnical Aspects of Underground Construction in Soft Ground*, eds R. J. Mair & R. N. Taylor, pp. 659–664. Balkema, Rotterdam.
    - `mair1993`: Mair, R. J., Taylor, R. N. & Bracegirdle, A. (1993). Subsurface settlement profiles above tunnels in clays. *Géotechnique* 43(2), 315–320. 🔬 Not read: as cited in Taylor (1995) and Mair & Taylor (1997).

**Scope (intent: New & Bowers)**

13. **New & Bowers (1994) stays out**, as the intent proposed. The papers name it as an alternative "close to the tunnel" (Bracegirdle et al. 1996, p. 660), which is where decision 7 flags points for another method. It stays in TODO #3 as the candidate for that zone.

**Docs**

14. 🟡 **A guide page, "Below the surface"**, with an example script in `docs/site/examples/`: a utility built at depth over M1's tunnel, the profile and cross-section with Mair's method; the same with the linear method; what the crown flag means; a sweep of `trough_width_parameter`. API reference entries for the new names.

### Hand calculation (golden values)
M1's tunnel: reference point (0, 0), azimuth 0°, D = 6.0 m, z₀ = 20.0 m, V_L = 1.0 %. A = 9π = 28.274334 m², Q = V_L A/√(2π) = 0.11279827 m², crown z_c = 17.0 m. Mair: i(z) = 3.5 + 0.325 (20 − z). Linear, k = 0.5: i(z) = 0.5 (20 − z). Calculated by hand from decision 3 (with a calculator, not the library).

**A. Mair's method** (K from Taylor's Eq. 5 and Mair's Eq. 8 agree at each depth):

| z (m) | K | i (m) | o (m) | S (m) | u_n (m) |
|---|---|---|---|---|---|
| 0 | 0.5 | 10.0 | 0 | 1.12798272e-2 | 0 |
| 0 | | | 10 | 6.84156105e-3 | −2.22350734e-3 |
| 10 | 0.675 | 6.75 | 0 | 1.67108552e-2 | 0 |
| 10 | | | 6.75 | 1.01356460e-2 | −3.29408495e-3 |
| 10 | | | 10 | 5.57707713e-3 | −2.68525936e-3 |
| 15 | 1.025 | 5.125 | 5.125 | 1.33493874e-2 | −4.33855091e-3 |
| 15 | | | 10 | 3.27999437e-3 | −2.07999643e-3 |
| 17 (crown) | 1.4916667 | 4.475 | 4.475 | 1.52884046e-2 | −4.96873149e-3 |

At z = 0, o = 10, u_n is 0.65 of M1's −(o/z₀) S = −3.42078053e-3 m.

**B. Linear method, k = 0.5:**

| z (m) | i (m) | o (m) | S (m) | u_n (m) |
|---|---|---|---|---|
| 0 | 10.0 | 10 | 6.84156105e-3 | −3.42078053e-3 |
| 10 | 5.0 | 0 | 2.25596545e-2 | 0 |
| 10 | | 5 | 1.36831221e-2 | −6.84156105e-3 |
| 10 | | 10 | 3.05311723e-3 | −3.05311723e-3 |
| 15 | 2.5 | 2.5 | 2.73662442e-2 | −1.36831221e-2 |

At z = 0 and o = 7: S = 8.82877197e-3 m and u_n = −3.09007019e-3 m, M1's values.

**C. Derivatives, Mair's method at o = 5 m, z = 10 m** (i = 6.75 m, r = 0.74074074), from decision 6's table:

| ∂o^a ∂z^b | S | u_n |
|---|---|---|
| 0, 0 | 1.27013730e-2 | −3.05773794e-3 |
| 1, 0 | −1.39384066e-3 | −2.75993356e-4 |
| 0, 1 | 2.75993356e-4 | −2.13667264e-4 |
| 2, 0 | −1.25808937e-4 | 1.64509029e-4 |
| 1, 1 | −1.64509029e-4 | 1.30268876e-5 |
| 0, 2 | −1.30268876e-5 | −1.74392636e-5 |
| 3, 0 | 7.49898710e-5 | 1.19284936e-7 |
| 2, 1 | −1.19284936e-7 | 2.37911321e-5 |
| 1, 2 | −2.37911321e-5 | 7.60915632e-6 |
| 0, 3 | −7.60915632e-6 | −6.87170813e-7 |

(units m^(1−a−b)). ∂u_n/∂o = −∂S/∂z, as constant volume requires; a central difference of S in z (h = 1 mm) gives 2.7599335e-4.

**D. Below the crown.** At o = 5 m, z = 19 m (√(5² + 1²) = 5.10 m from the axis, outside the 3 m bore): `outside`, with the values at z = 17 m. Mair: i = 4.475 m, S = 1.35027643e-2 m, u_n = −4.90323843e-3 m. Linear: i = 1.5 m, S = 2.90712742e-4 m, u_n = −4.84521236e-4 m. At o = 0, z = 18 m: inside the bore, raises.

**E. Feature length** on a segment from depth 2 m to depth 12 m: Mair 6.1 m, linear 4.0 m (i at 12 m). From depth 2 m to depth 19 m: i at the crown, 4.475 m and 1.5 m.

### Acceptance criteria
Tolerance 1e-6 relative for values carried to 8 figures, as in M1 and M2 (a); critical distances to 1e-8 m.

1. **Golden values:** cases A, B and D through `evaluate`, at points with the tunnel's normal along +x and at a rotated tunnel (azimuth 30°); and cases A (z = 10 m) and B (z = 10 m) through `movement_profile` on a utility built perpendicular at station 50, depth 10 m (axis), offsets −30 to 30 m, spacing 2.5 m, for `vertical` and `along`.
2. **Derivatives:** case C's values for both settlement and horizontal, read from the gradient, Hessian and third derivative with g and e_z; and (hypothesis, as M1's tests: random points above the crown, both methods, any azimuth) the gradient, Hessian and third derivative match central differences of the next lower order, and are symmetric.
3. **Constant volume:** (hypothesis) the trace of the gradient, ∂u_x/∂x + ∂u_y/∂y + ∂S/∂z, is zero to 1e-12 of its terms' scale, for both methods.
4. **Against M1:** the linear method at z = 0 gives M1's displacement and its derivatives with respect to x and y at every point (to 1e-12 relative), for any k (hypothesis); Mair's at z = 0 gives M1's with k = 0.5 for settlement, and 0.65 of its horizontal movement.
5. **Validity:** case D's verdicts, values and flag (reason, limit, points); a point 0.5 mm below the crown is `within`; depth derivatives below the crown are exactly zero; inside the bore and above the surface raise as in M1; the linear method's flag says the limit is garisenda's.
6. **Critical distances, level segments:** on level segments at any angle, position and depth above the crown (hypothesis), the root-finding returns the analytic set of decision 8 with i(z), to 1e-8 m.
7. **Critical distances, sloped segments:** for segments changing depth (including one crossing the crown, and one at 45° in plan and descending), sampling each of the eight functions at h/20 finds no sign change without a returned distance between the samples, and each returned distance is a zero of one of them (M2 (a)'s AC 7 test, reused); `feature_length` is case E's.
8. **Inputs and records:** `trough_width` missing raises the judgment error; a plain number or string raises `TypeError` naming both methods; `linear_trough_width` without k raises the judgment error, and with k ≤ 0 or not finite raises `ValueError`. Records: `trough_width` with value `"Mair et al. (1993), clay"` or `"linear"`, `trough_width_parameter` for the linear method only, the three constants; `to_dict()`, `to_frame()` and the summary show the method's name.
9. **Superposition and sweep:** two subsurface troughs (one each method) superpose and their sum and records are as M2 (a)'s AC 2 and 8; `gs.sweep` varying `trough_width_parameter` over [0.4, 0.5, 0.6] runs; changing the method between runs raises the unchanged-inputs error.
10. **Cross-section:** a utility at depth 10 m over Mair's trough draws the settlement panel at that depth (its value at o = 0 is case A's), titled with the depth, with ±i marks at ±6.75 m; M1's figure tests pass unchanged. Checked by eye at close-out.
11. **Citations and docs:** every new public calculation's docstring has its equations, inputs and outputs with units, validity limits and the citations of decision 11; `docs/reference/sources.md` has decision 12's entries; the guide page and its example build with `--strict`; mypy strict and the `lowest` job pass.

## Plan

Nine build commits, each with lint, format, mypy strict and pytest green. Opus does 1–6, Sonnet does 7–8, and Opus does 9 (figures by eye, then close-out), so a new session starts before 7 and before 9. The golden values and citations come from the spec, never from running the code; docstrings copy the citations from decision 11 as written there.

### 1. `M2 (b): let an input record hold a named method` (Opus)
- `src/garisenda/_inputs.py`:
  - `InputRecord.value` becomes `pint.Quantity | str` (SPEC §5.1, decision 2), its docstring saying when it's a string.
  - 🟡 **Not in the spec, proposed here:** a new `record_method(name, value, *, kind, expected, how) -> (method, InputRecord)`, the counterpart of `record()` for a method object: it unwraps `Sourced`, raises `TypeError` with `how` (how to write each method) if `value` isn't an `expected`, and records the method's `name` with given-as `"method"`. `record()` stays for quantities, so "every input goes through `record()`" becomes "through `record()` or `record_method()`" (CLAUDE.md, at close-out).
- `src/garisenda/_result.py`: `input_dict` gives a string's `magnitude` as the string, and `unit_text` gives `""` for it (🟡 proposed: no unit, rather than `"dimensionless"`, which would read as a number); a new `value_text(entry)` for messages and the summary.
- `src/garisenda/_sweep.py`: `_as_used` returns None for a string record (a method can't be varied); `_same` and `_check_fixed` compare strings by equality; every `f"{entry.value:~}"` uses `value_text`.
- Tests in `tests/test_inputs.py`, `tests/test_result.py`, `tests/test_sweep.py`, with a stand-in method class:
  - the record's value, kind, given-as and source (through `Sourced`); a wrong type raises `TypeError` with the `how` text;
  - `to_dict()`, `to_frame()` and the summary show the name (AC 8, the views part);
  - a sweep whose runs record different method names raises the unchanged-inputs error, naming both (AC 9, the sweep part, with stand-ins);
  - M1's and M2 (a)'s tests pass unchanged.

### 2. `M2 (b): add the trough width methods` (Opus)
- New `src/garisenda/sources/_trough_width.py`, decision 10:
  - `TroughWidth`, a frozen dataclass: `name`, `surface_coefficient` (c₀), `rate` (c₁), `inputs`, `equations`, `source`, `assumptions`, and `at(*, depth, axis_depth)`, computing i = c₀ z₀ + c₁ (z₀ − z), never K (z₀ − z).
  - `mair_trough_width()`: (0.175, 0.325), name `"Mair et al. (1993), clay"`, no input records, decision 5's clay assumption, decision 11's citations.
  - `linear_trough_width(*, trough_width_parameter)`: `@judgments` with M1's explanation of k; `record()` as M1 does; `ValueError` for k ≤ 0 or not finite; (0, k), name `"linear"`, the `trough_width_parameter` record, decision 5's linear assumption.
  - Docstrings: the equations, inputs and outputs with units, the crown limit (decision 7), the extrapolation note (decision 7, no `marginal` band), citations.
- `src/garisenda/sources/__init__.py`: export `TroughWidth`, `mair_trough_width`, `linear_trough_width`.
- Tests in new `tests/sources/test_trough_width.py`:
  - i from cases A and B at each depth, and i = K (z₀ − z) with K from Taylor's and Mair's forms at z = 0, 10, 15, 17 (case A's K column), to 1e-12;
  - case E's widths at 2, 12 and 17 m;
  - AC 8's linear part: missing k raises the judgment error; k = 0, −0.5, NaN, inf raise `ValueError`.

### 3. `M2 (b): share point reading between the troughs` (Opus)
A refactor with no change in behavior.
- `src/garisenda/sources/_segment.py`: `read_points(x, y, depth, *, surface_tolerance) -> (x, y, depth)`, taken from `TransverseSurfaceTrough.evaluate` (records the coordinates, checks shapes and finiteness, raises above the surface), and `check_outside_bore(tunnel, offset, depth)`, which raises for points inside the bore.
- `src/garisenda/sources/_transverse.py` uses them.
- Tests: the existing suite passes unchanged.

### 4. `M2 (b): add the transverse trough at depth` (Opus)
- New `src/garisenda/sources/_transverse_trough.py`:
  - `transverse_trough(tunnel, *, volume_loss, trough_width)`, `@judgments` for both (decision 1). `volume_loss` as in M1. `trough_width` through `record_method` with `expected=TroughWidth` and a `how` that writes both methods, so a number or string raises `TypeError` naming them.
  - Records (decision 2): the tunnel's, `volume_loss`, `trough_width`, the method's own inputs (`trough_width_parameter` for the linear method), then `depth_tolerance`, `critical_distance_sampling` and `critical_distance_tolerance`. Method `"Transverse Gaussian trough at depth"` with decision 3's equations and the width's source. Assumptions per decision 5, then the width's, then the tunnel's.
  - `TransverseTrough`, a frozen dataclass, with `evaluate`:
    - `read_points` and `check_outside_bore`; depth capped at z_c for points deeper than z_c + 1 mm, which are `outside` with decision 7's reason and limit (the linear method's reason adds "(applied to the linear method by garisenda)");
    - S and u_n and their derivatives from decision 6's P_ab and R_ab tables, held as polynomial coefficients and evaluated in r = o/i, with the factor Q c₁^b / i^(1+a+b) (and c₁^(b+1) for u_n); at capped points every b ≥ 1 term is exactly zero;
    - assembled with g = (n_x, n_y, 0) and e_z: a tensor component whose indices include b twos takes the (a, b) derivative times the product of g over its other indices. That is symmetric by construction, and at z = 0 with the linear method reduces to M1's.
  - `critical_distances` and `feature_length` are added in step 5; this commit has them raise `NotImplementedError`, so the protocol is met. 🟡 Proposed so step 4 stays under 300 lines; step 5 follows straight after.
- `src/garisenda/sources/_transverse.py`: `BELOW_SURFACE` names `gs.sources.transverse_trough` as the method for depth.
- `src/garisenda/sources/__init__.py`: export `transverse_trough`, `TransverseTrough`.
- Tests in new `tests/sources/test_transverse_trough.py`:
  - AC 1, the `evaluate` part: cases A, B and D, with the normal along +x and at azimuth 30°;
  - AC 2: case C's 20 values read from the gradient, Hessian and third derivative;
  - AC 4, the fixed cases: linear at z = 0 equals M1 at k = 0.5 (o = 7: B's last line); Mair at z = 0 is M1's settlement and 0.65 of its horizontal movement;
  - AC 5: case D's verdicts, values and flag; 0.5 mm below the crown is `within`; depth derivatives below the crown are exactly zero; inside the bore (o = 0, z = 18) and above the surface raise; the linear method's reason;
  - AC 8, the trough part: `trough_width` missing, a number, a string; the records and their values.
- Tests in new `tests/sources/test_transverse_trough_properties.py` (hypothesis, both methods, any azimuth, points above the crown):
  - AC 2: the gradient, Hessian and third derivative match central differences of the next lower order, and are symmetric;
  - AC 3: the trace of the gradient is zero to 1e-12 of its terms' scale;
  - AC 4: the linear method at z = 0 equals M1's displacement and x, y derivatives to 1e-12 relative, for any k.

### 5. `M2 (b): find the trough's critical distances at depth` (Opus)
- `src/garisenda/sources/_transverse_trough.py`: `critical_distances` calls `find_critical_distances` with the two constants (decision 8); `feature_length` is i at the segment's deeper end, depth capped at the crown. Docstrings say what root-finding can miss, as M2 (a)'s superposition does.
- Tests:
  - AC 6 (hypothesis, in the properties file): level segments at any angle, position and depth above the crown return 0, ±i, ±√3 i, and on oblique segments ±0.74196378 i and ±2.3344142 i, with i = i(z), to 1e-8 m;
  - AC 7: sloped segments (2 m to 12 m deep; one crossing the crown; one at 45° in plan, descending), both methods, added as cases to `test_nothing_missed_against_dense_sampling` in `tests/sources/test_critical.py`, so M2 (a)'s check (`eight_functions`, h/20) is reused as it stands;
  - case E's feature lengths.
- If a test fails, the fix goes in this commit with the cause stated.

### 6. `M2 (b): profile, superpose and sweep the trough at depth` (Opus)
Tests only, unless a gap shows; then the fix goes here, with its cause.
- `tests/profile/test_movement_profile.py`: AC 1's profile part, cases A and B at z = 10 m on a utility built perpendicular at station 50, depth 10 m, offsets −30 to 30 m, spacing 2.5 m, for `vertical` and `along` at the tabulated offsets.
- `tests/sources/test_superposition.py`: AC 9, a Mair trough and a linear trough superposed: the sum, the records (`north.trough_width` holding the name), the flags tagged with their source.
- `tests/test_sweep.py`: AC 9, `trough_width_parameter` over [0.4, 0.5, 0.6] with the linear method runs; a run that switches to Mair's raises the unchanged-inputs error.

### 7. `M2 (b): draw the cross-section at the utility's depth` (Sonnet)
- `src/garisenda/plot/_cross_section.py`, decision 9:
  - `surface_of` becomes the movement at the built utility's axis depth (the mean of its vertices' depth, as `_section` already reads it), and the panels' titles say "Settlement at depth 10 m" or "Settlement at the surface" (and the same for horizontal) when the depth is within 1 mm of zero;
  - a private `_width(source, depth)` replaces `getattr(..., "trough_width")`: `TroughWidth.at` at the utility's depth, capped at the crown (🟡 proposed, so the marks match the values drawn below the crown), or M1's float;
  - 🟡 **Not in the spec, proposed here:** at a depth that crosses a bore, grid points inside it aren't evaluated, and the line breaks there (NaN in the drawing arrays only, not in any result: SPEC §10 is about data). Otherwise a utility beside the bore, which is a valid input, couldn't be drawn.
  - The docstring says what depth is drawn.
- Tests in `tests/plot/test_cross_section.py` (AC 10): a utility at depth 10 m over Mair's trough: the settlement panel's value at o = 0 is case A's 1.67108552e-2 m, its title names the depth, ±i marks at ±6.75 m; a utility at 18 m beside the bore draws with a break; M1's and M2 (a)'s figure tests pass unchanged; `rcParams` unchanged.

### 8. `M2 (b): write the below-the-surface guide` (Sonnet)
- New `docs/site/guides/below-the-surface.md` and `docs/site/examples/below-the-surface.py` (decision 14): a utility at depth over M1's tunnel; the profile and cross-section with Mair's method; the same with the linear method; what the crown flag means and when another method is needed; a sweep of `trough_width_parameter`.
- `zensical.toml` nav, after "Several tunnels".
- `docs/site/reference/sources.md`: entries for `transverse_trough`, `TransverseTrough`, `TroughWidth`, `mair_trough_width`, `linear_trough_width`. *Changed in build:* added in steps 2 and 4 instead, since `tests/docs/test_site.py` requires an entry for every public name.
- Tests: `tests/docs/test_site.py` picks up the example. The docs build passes with `--strict` and no `griffe:` warnings (AC 11, the docs part).

### 9. `M2 (b): check figures and close out` (Opus)
- Check the figures in `docs/site/img/generated/` by eye against decision 9 (the rest of AC 10), and fix anything found.
- Check every new public docstring against decision 11's citations and `docs/reference/sources.md` against decision 12 (AC 11).
- Run every check: the CI line; Python 3.13 and 3.14; the `lowest-direct` floors, then `git checkout uv.lock`.
- Close-out:
  - SPEC §12.4 marks M2 (b), and so M2, done with its date; check §2.1, §2.5, §3, §5.1, §9 and §13 Q2 say what was built (they were written at the spec step);
  - `docs/TODO.md` #3 keeps only reading Mair et al. (1993), the granular method and New & Bowers (1994);
  - `CLAUDE.md`: status and "Next" point to M3; the `record()` convention names `record_method()`; any recurring mistake goes into the conventions;
  - report each of the 11 ACs as met or not, with its evidence.
