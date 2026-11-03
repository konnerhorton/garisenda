# M2 (a): several tunnels

## Intent

### Goal
A caller can assess an asset against several tunnels at once, such as twin bores or a tunnel crossing another: each tunnel has its own trough with its own volume loss and k, and the movements add by superposition. The combined field is a source like any other (SPEC §3), so the profile, the result, `gs.sweep` and the figures take it unchanged. The result records superposition as an assumption, and each input says which tunnel it belongs to. A twin bore is built from spreadsheet-style input as an idealized tunnel parallel to another at a given offset (SPEC §8.3).

### Why
- SPEC §12.4: M2 is "movements below the surface, several tunnels". The two halves are independent. Superposition works on any source, including M1's surface trough, and needs no new sources. The subsurface trough needs Mair et al. (1993), Taylor (1995) and New & Bowers (1994) verified first (TODO #3). So M2 splits in two (decision 1), and this half goes first because research doesn't block it.
- Twin bores are the usual case in practice. Until this unit, the user would have to add two results by hand, which loses the record of what was added and the profile's exact derivatives.
- Doing superposition before the subsurface trough tests the source interface (SPEC §3) with a second kind of source before M2 (b) adds a third. It shows whether the interface holds up when a source isn't a single trough.

### Constraints
- **SPEC §3:** sources produce a field and assessments consume it. The combined source satisfies the `Source` protocol: displacements, gradients and Hessians are global components, so they add exactly. Verdicts per point are the worst over the tunnels, and flags are kept with the tunnel they came from. Superposition is recorded on the result as an assumption, 🟡 there now and decided here.
- **SPEC §3, `critical_distances()`:** the profile must not miss a peak between stations. The union of each tunnel's critical distances is *not* where the combined field peaks: two overlapping troughs peak between their axes. So the combined source finds its own peaks (decision 6).
- **SPEC §4:** each tunnel's volume loss and k remain required judgments with no default. Nothing is shared between tunnels silently: the trough parameters of one aren't copied to another.
- **SPEC §5.1, §5.3:** every input is recorded with its kind and source, and `gs.sweep` must be able to vary one tunnel's volume loss without the other's. Two records named `volume_loss` are ambiguous, so inputs need to name their tunnel.
- **SPEC §2.5, §10:** the inputs are inconsistent, and the call raises, if the tunnels don't share a ground surface (two `ground_elevation`s that differ) or if their bores overlap. A point inside any tunnel's bore raises, as it does for one tunnel now.
- **SPEC §9:** the cross-section shows every tunnel and the combined trough. Each milestone ships the figures for what it builds.
- **SPEC §12.3:** the user docs and their examples are written at close-out.

### Out of scope
- **The trough below the surface** (width at depth, subsurface horizontal movement, depth validity): M2 (b). Assets below the surface keep M1's `outside` flag until then.
- **Interaction between tunnels:** a later bore's larger volume loss, eccentric or asymmetric troughs over twin bores, and construction order. Each tunnel's volume loss is the user's judgment. The docs say that this is where those effects go, and the assumptions say they aren't modeled.
- **Real alignments:** M5. Every tunnel here is idealized.
- **The plan figure:** M5. It's the natural place to show crossing tunnels.
- **Utility and building checks:** M3, M4.

### SPEC sections touched
- **§12.4:** M2's row records the split into (a) and (b), and the done-when moves with each half.
- **§3:** superposition becomes decided, with how the combined source finds its critical distances; the source interface adds third derivatives (decision 6).
- **§8.3:** the parallel-tunnel builder becomes decided, and what "several tunnels" means for station and offset (they stay relative to the asset's reference tunnel).
- **§5.1, §5.3:** how an input names its tunnel, and how `gs.sweep` refers to it.
- **§9:** the cross-section with several tunnels.
- **§13 Q2, TODO #3:** carried to M2 (b), with the granular answer from this review (decision 3).

### Decisions (intent review, 2026-11-03)
1. **M2 splits into (a) several tunnels and (b) the subsurface trough, in that order.** (a) needs no new sources; (b) waits on the papers.
2. **The subsurface papers will be supplied for M2 (b)**, so its done-when stays as written: golden values from the verified subsurface method.
3. **Granular soil in M2 (b):** Mair et al. (1993) for clay, plus a width at depth from a given k, i = k (z₀ − z), offered as the user's own choice and recorded as such. A granular-specific method comes later; §13 Q2 stays open for it.

4. **The API is a function that combines sources:** `gs.superpose(...)` returns a source, so `movement_profile(utility, gs.superpose(...), spacing=...)` works unchanged. It takes any sources, not only troughs, so M2 (b)'s subsurface trough and later sources combine the same way.
5. **Each tunnel has a name, and inputs are recorded under it:** `gs.superpose(north=trough_n, south=trough_s)`, so records read `north.volume_loss`, and `gs.sweep` varies `"north.volume_loss"`. A `name=` on `IdealizedTunnel` was considered and dropped: it puts a label on geometry that one tunnel doesn't need.
6. **Sources return third derivatives too, and the combined source finds its critical distances by root-finding on exact derivatives.** Of the profile's quantities, the peaks of movement (zero slope), of slope (zero curvature) and of along strain (zero `along_strain_gradient`) are all zeros of the gradient or Hessian. Only the curvature peaks, vertical and lateral, need a third derivative, and they're the ones M3 and M4 check. So `Movement` gains a third-derivative array, shape (N, 3, 3, 3, 3), and SPEC §3's interface changes with it.
   - **Cost:** small for the Gaussian, whose third derivative is one scalar times g⊗g⊗g, tested against finite differences of the Hessian as the lower orders are.
   - **Considered and dropped:** locating curvature peaks by finite differences of the exact curvature. Its error is second order in the location error, so it's accurate, but it puts finite differences inside a source (SPEC §3) and leaves new sources without a third-order check.
   - **Carried forward:** M2 (b)'s width at depth lengthens the derivatives with respect to depth; they stay short if i(z) is linear in depth (to confirm for Mair et al. against the paper). Movements given as data (later) need a spline with a continuous third derivative, which a cubic spline isn't.
   - **To settle in the spec:** how roots are bracketed along a segment (a sampling interval tied to the narrowest trough) and the tolerance they're found to, with numpy only (no scipy, SPEC §12.1).
7. **Twin tunnels:** `tunnel.parallel(offset=..., ...)` returns an idealized tunnel parallel to `tunnel` at a plan offset (positive to the right, SPEC §8.1), with stationing aligned to it. The depth and diameter are required again, not copied, because stacked and unequal bores are common and copying would be a silent default.
8. **Any idealized tunnels can be combined, parallel or not.** The cross-section draws the tunnels parallel to the asset's reference tunnel. If any aren't parallel, it says so in a note on the figure and doesn't draw them, rather than drawing a misleading section. The plan figure (M5) shows them.

## Spec

No topic doc holds this, so the spec is here. Every 🟡 proposal below was accepted as written in review (2026-11-03).

### Changes
- **SPEC §3:** superposition decided (decisions 1–5); the source interface gains a third derivative and `feature_length()` (decisions 6–7); how a superposition finds its critical distances (decisions 8–10).
- **SPEC §5.1, §5.3:** input records named per source; `gs.sweep` with dotted names (decisions 3, 12).
- **SPEC §8.3:** the parallel-tunnel builder decided (decision 11).
- **SPEC §9:** the cross-section with several tunnels (decision 14).
- **SPEC §12.4:** M2 split into (a) and (b), each with its done-when. **§13 Q2** and **TODO #3:** carried to M2 (b) with intent decision 3.
- **New:** `gs.superpose`, `gs.sources.Superposition`, `IdealizedTunnel.parallel`, `Movement.third_derivative`, `Source.feature_length`, `Flag.source`. A guide page, "Several tunnels", with its example.

### Decisions

**The superposition (intent decisions 4 and 5)**

1. 🟡 **`gs.superpose(**sources) -> gs.sources.Superposition`.** Keyword arguments only, at least two; each name a Python identifier (so no dots), each value a source (it has `evaluate`, `critical_distances`, `feature_length`, `inputs`, `method` and `assumptions`), or `TypeError` naming the argument. Order is kept as given. A superposition is a source, so superpositions nest, and their names nest with them (`twins.north.volume_loss`). With one source there is nothing to add, and recording superposition would be false, so one raises.
2. 🟡 **`evaluate`** evaluates every source at the same points and sums the displacement, gradient, Hessian and third derivative, which are global components (SPEC §8.1), so the sum is exact. The verdict at a point is the worst over the sources. Each source's flags are kept, one for one, with `source` set to its name (decision 13); two tunnels flagging the same points give two flags. An error from a source is raised again as the same type, its message prefixed `"<name>: "`, so the profile still names the stations (it reads the last index list). A point inside any tunnel's bore raises, through that source.
3. 🟡 **What it records.** Each source's input records are renamed `<name>.<record name>`, with value, kind, given-as and source unchanged; the superposition adds two constants of its own, unprefixed: `critical_distance_sampling` (1/8, dimensionless) and `critical_distance_tolerance` (1e-9 m), both "constant or setting" (decision 9). Methods: each source's, in order, an identical record kept once, then `Superposition` (equations `u = sum over sources of u_s`, the same for each derivative, and `verdict = worst over sources`; source: "Linear superposition of the sources' fields; no external source"). Assumptions: each source's, an identical one kept once, then: *"Superposition: each tunnel's movement is calculated as if the others weren't there, and the movements add. Interaction between tunnels (a later bore's larger volume loss, an eccentric trough over twin bores, the order of construction) isn't modeled; set each tunnel's volume loss for it (SPEC §3)."*
4. 🟡 **Inconsistent inputs raise** `ValueError` in `superpose`, naming the sources and values (SPEC §2.5, §10):
   - **Ground surface:** any two input records named `ground_elevation`, at any depth of nesting, that differ by more than 1 µm. A tunnel given by `axis_depth` has no such record and isn't compared: its depth is already from the one ground surface (SPEC §8.2).
   - **Overlapping bores:** for any two tunnels (a source's `tunnel` attribute, found through nested superpositions), the shortest distance between the axes is less than (D₁ + D₂)/2. Both axes are horizontal lines, so for parallel tunnels (|sin Δθ| ≤ 1e-9) it is √(Δo² + Δz₀²) in the section, Δo the plan offset between axes; otherwise their plans cross and it is |Δz₀|. Touching bores (equal) are allowed. The same tunnel in two sources overlaps itself, which catches passing one trough twice.
   - Sources with no `tunnel` attribute (later kinds) are skipped by the overlap check.
5. 🟡 **`superpose` is in `gs`; `Superposition` is in `gs.sources`**, beside `TransverseSurfaceTrough`. Its attributes: `sources` (a mapping of name to source, read-only), `inputs`, `method`, `assumptions`.

**The source interface (intent decision 6)**

6. 🟡 **`Movement.third_derivative`**, shape (N, 3, 3, 3, 3): `third_derivative[n, i, j, k, l]` is ∂³u_i/∂x_j∂x_k∂x_l in 1/m², symmetric in j, k, l, checked in `__post_init__` like the others. For the surface trough it is (d³u/do³) g⊗g⊗g, with g = (n_x, n_y, 0) and, writing r = o/i:
   - d³S/do³ = (o/i⁴) S (3 − r²)
   - d³u_n/do³ = S/(z₀ i²) (r⁴ − 6r² + 3)

   Derived in the hand calculation below. Every derivative with respect to depth stays exactly zero.
7. 🟡 **`Source.feature_length(*, start, end) -> float`**, in m: the shortest length over which the source's field changes along that straight segment, so a sampling interval can be tied to it. The surface trough returns i whatever the segment; a superposition the least of its sources'. It is on the segment so M2 (b)'s narrower trough at depth can return the least i(z) along it.

**Critical distances of a superposition (intent decision 6, settled here)**

8. 🟡 **What is a critical distance.** Along the segment, with a, v and l the profile's along, vertical and lateral directions (SPEC §3; the profile's helper moves to `sources` so both use the same), the zeros of eight functions of distance s:
   - d/ds and d²/ds² of along, vertical and lateral (peaks of movement; peaks of strain and slope);
   - d³/ds³ of vertical and lateral (peaks of curvature, which M3 and M4 check).

   d³/ds³ of along (peaks of `along_strain_gradient`) is left out: nothing checks it. For a lone trough on a level segment at any angle, these zeros are exactly its analytic critical distances, which acceptance criterion 6 tests: 0, ±i and ±√3 i in offset, and, on a segment not perpendicular to the tunnel, ±0.74196378 i and ±2.3344142 i. The sources' own critical distances aren't used: two overlapping troughs peak between their axes (case B).
   - **Corrected in build (2026-11-03):** the review wrote only 0, ±i, ±√3 i. On an oblique segment the lateral displacement is u_n (n·l), not zero, so lateral curvature peaks where d³u_n/do³ = 0 (case D's He₄ roots). M1's trough missed these, and its `critical_distances` now includes them when |n·l| > 1e-10 (build step 3a). M1's 45° case gains s = 17.791319 and 38.777224 m (o = ∓7.4196378 m, s = √2 (o + 20)).
9. 🟡 **How they're found, with numpy only** (SPEC §12.1):
   - **Sampling:** the segment at an interval h ≤ `feature_length` / 8 (the largest such interval that divides L evenly), with the ends.
   - **Bracketing:** a function brackets a zero between consecutive samples whose signs differ (an exact zero counts as a sign of its own), unless both values are below 1e-10 times the order's scale: the largest value of that order over the segment and its three components, or the largest displacement over the segment divided by `feature_length`ⁿ for order n, whichever is larger. That leaves out rounding noise (lateral on a perpendicular utility is zero to rounding) and the far tails, where the troughs have underflowed to zero.
     - **The floor, added in build (2026-11-03):** on a segment parallel to a tunnel every derivative along it is rounding noise, so the largest value over the segment is noise too, and a band relative to it brackets the noise (at offsets 0 and i, where a component changes sign). The cost: on a segment within a small angle of parallel, an order below 1e-10 of the trough's own isn't searched, which the docstring says.
   - **Refining:** bisection, all brackets at once, until each is shorter than 1e-9 m (about 30 steps from h = 1.25 m). Bisection, not Brent's method: it is a few lines of numpy, it can't leave the bracket, and the cost is a few dozen evaluations of the bracketed points.
   - **Returned:** the midpoints, sorted, within [0, L], with any two within 1e-9 m merged.
10. 🟡 **What this can miss, stated in the docstring:** two zeros of the same function closer together than h, which bound a peak narrower than i/8. A Gaussian's own zeros are at least (√3 − 1) i ≈ 0.73 i apart, so this needs two troughs placed to nearly cancel. The profile still has its `spacing` stations, so such a peak is under-resolved, not lost.

**Twin tunnels (intent decision 7)**

11. 🟡 **`IdealizedTunnel.parallel(*, offset, diameter, axis_depth=None, axis_elevation=None, ground_elevation=None) -> IdealizedTunnel`.** The new tunnel has the same azimuth and reference station, and reference point p₀ + offset·n, so its stationing lines up with the first. `offset` (a length, in m if a plain number, positive to the right, SPEC §8.1) and `diameter` are required, and the axis follows the same rule as the constructor: none is copied (intent decision 7). Offset 0 is allowed: stacked bores. Its input records: `offset`, `diameter` and the axis as given, and `reference_point`, `azimuth` and `reference_station` as derived, given-as `"parallel to a tunnel at offset <o> m"`. It doesn't check for overlap; `superpose` does, in one place.

**Inputs and the sweep (intent decision 5)**

12. 🟡 **`gs.sweep` takes dotted names.** A `vary` key is a record name, such as `"south.volume_loss"`; it is passed to `run` as a keyword argument with its dots replaced by underscores (`south_volume_loss`), since a keyword can't hold a dot. The table's column keeps the record name. A key that doesn't become an identifier, or two keys that become the same one, raise `TypeError`. Undotted keys behave as now. Considered and dropped: `run(**inputs)` with dotted keys (every `run` written for several tunnels would have to unpack a dict); keys as `run`'s argument names matched to records by underscore (the table would show a name no record has).
13. 🟡 **`Flag.source: str = ""`**, the name path of the source a flag came from (`"north"`, `"twins.north"`), empty for a lone source. `to_dict()` adds it to each warning; the summary and the figures' flag notes print `"<source>: <reason>"` when it is set.

**The cross-section (intent decision 8)**

14. 🟡 **With a superposition**, `gs.plot.cross_section` finds its tunnels through `source.sources`, nested ones included; offsets are from the utility's reference tunnel (`built.tunnel`), which needn't be one of them.
   - **Each tunnel parallel to the reference tunnel** is drawn in the section at its offset and depth, labeled with its name, with its axis depth and cover dimensioned and its axis as a dash-dot line on every panel (gids `tunnel:<name>`, `axis:<name>`).
   - **The troughs:** the superposition as the solid line (gid `vertical` and `horizontal`, as now, label "Combined"), and each source's own trough thin and dashed (gid `trough:<name>:vertical`, `trough:<name>:horizontal`), so the user sees what was added. The ±i marks are drawn only with one tunnel.
   - **Reach:** the utility's offsets and each drawn tunnel's offset ± 3i.
   - **A tunnel not parallel** to the reference tunnel isn't drawn; a note under the figure (gid `note`) names it and says the troughs include it and the plan figure (M5) shows it. Its dashed trough is still drawn, being the field along the section.
   - The x label becomes "Offset from reference tunnel axis" with several tunnels. One tunnel, or a lone trough, draws as now.
   - The profile figure is unchanged: it draws the result's values.

**Docs**

15. 🟡 **A guide page, "Several tunnels"**, with an example script in `docs/site/examples/`: twin bores built with `parallel`, each with its own trough, superposed; the profile and the cross-section; a sweep of `south.volume_loss`; what superposition assumes and that a later bore's larger volume loss is set through its own `volume_loss`. API reference entries for the new names.

### Hand calculation (golden values)
The reference tunnel is M1's: reference point (0, 0), azimuth 0° (along +y, so n = +x), D = 6.0 m, z₀ = 20.0 m, V_L = 1.0 %, k = 0.5, so i = 10.0 m, A = π·3² = 28.274334 m², S_max = V_L A/(√(2π) i) = 1.1279827e-2 m. Offsets o are from its axis. For a trough with axis at offset c, S(o) = S_max exp(−(o − c)²/2i²) and u_n(o) = −((o − c)/z₀) S(o); the superposition adds them. Utilities are built perpendicular to the reference tunnel at station 50, at the surface, so along = u_n and vertical = S.

**A. Equal twins, 15 m apart** (2a = 15 m < 2i, so one peak). `south = north.parallel(offset=15 m, diameter=6 m, axis_depth=20 m)`, the same V_L and k. By symmetry the peak is midway, at o = 7.5:
- o = 7.5: S = 2 S_max exp(−7.5²/200) = 2 × 1.1279827e-2 × 0.75483960 = 1.7028921e-2 m; u_n = 0.
- o = 0 (north's axis): S = S_max (1 + exp(−225/200)) = 1.4941851e-2 m; u_n = −(−15/20) S_max exp(−1.125) = +2.7465178e-3 m (toward south, to the right).
- o = 15: S = 1.4941851e-2 m; u_n = −2.7465178e-3 m.
- o = 22.5: S = S_max (exp(−0.28125) + exp(−2.53125)) = 9.4118778e-3 m; u_n = −4.2025173e-3 m.

**B. Equal twins, 30 m apart** (2a = 30 m > 2i, so two peaks, and neither is over an axis). South at offset 30 m, as A otherwise.
- o = 15 (midway): S = 2 S_max exp(−1.125) = 7.3240475e-3 m, a local minimum; u_n = 0.
- o = 0 and 30 (the axes): S = S_max (1 + exp(−4.5)) = 1.1405135e-2 m; u_n = ±1.8796134e-4 m (+ at 0).
- **The peaks.** With x = o − 15 from the midpoint, dS/do = 0 where (x − a) e^{−(x−a)²/2i²} + (x + a) e^{−(x+a)²/2i²} = 0, which rearranges to (a − x)/(a + x) = exp(−2ax/i²), a = 15 m. The root in (0, a), by bisection to machine precision, is x = 14.632437 m (residual 3e-17), so the peaks are at o = 0.36756261 and 29.632437 m, with S = 1.1412031e-2 m. A union of the two troughs' critical distances would put them at 0 and 30.

**C. Unequal twins.** South at offset 15 m, z₀ = 30 m, D = 6 m, V_L = 1.5 %, k = 0.4: i = 12.0 m, S_max = 0.015 × 28.274334/(√(2π) × 12) = 1.4099784e-2 m. The axes are √(15² + 10²) = 18.0 m apart, more than D, so the bores don't overlap.

| o (m) | north S | north u_n | south S | south u_n | S | u_n |
|---|---|---|---|---|---|---|
| 0 | 1.1279827e-2 | 0 | 6.4553515e-3 | 3.2276758e-3 | 1.7735179e-2 | 3.2276758e-3 |
| 7.5 | 8.5144603e-3 | −3.1929226e-3 | 1.1598166e-2 | 2.8995415e-3 | 2.0112626e-2 | −2.9338112e-4 |
| 15 | 3.6620237e-3 | −2.7465178e-3 | 1.4099784e-2 | 0 | 1.7761808e-2 | −2.7465178e-3 |

**D. The third derivative of one trough.** With r = o/i and dS/do = −(o/i²) S, d²S/do² = (r² − 1) S/i² (M1 (a)):
- d³S/do³ = d/do[(r² − 1) S/i²] = (2o/i⁴) S + (r² − 1)(−o/i⁴) S = (o/i⁴) S (3 − r²).
- u_n = −(i S_max/z₀) r e^{−r²/2} and r e^{−r²/2} = −(d/dr) e^{−r²/2}, so with the Hermite polynomials (dⁿ/drⁿ) e^{−r²/2} = (−1)ⁿ Heₙ(r) e^{−r²/2}, d³(r e^{−r²/2})/dr³ = −He₄(r) e^{−r²/2} = −(r⁴ − 6r² + 3) e^{−r²/2}, and d³u_n/do³ = (S/(z₀ i²))(r⁴ − 6r² + 3). (The same route gives M1 (a)'s d²u_n/do², a check.)
- Values: o = 0: 0 and 1.6919741e-5 1/m²; o = 10: 1.3683122e-5 and −6.8415611e-6; o = 20: −3.0531172e-6 and −3.8163965e-6. Fourth-order central differences of the hand formulas for S and u_n agree to 1e-6 relative.
- The zeros of d³u_n/do³, r² = 3 ± √6, are r = 0.74196378 and 2.3344142: the peaks of `along_strain_gradient`, which decision 8 leaves out, and, on a segment not perpendicular to the tunnel, of `lateral_curvature`, which it keeps.

**E. Inconsistent inputs.**
- North at z₀ 20 m, D 6 m; south parallel at offset 5 m, z₀ 20 m: the axes are 5 m apart, less than 6 m, so it raises. At offset 6 m they touch, and it doesn't.
- Crossing: east at reference point (0, 50), azimuth 90°, D 6 m. At z₀ 24 m, |Δz₀| = 4 m < 6 m, so it raises; at 26 m (6 m) it doesn't.
- North given by `axis_elevation=80 m, ground_elevation=100 m`, south by `axis_elevation=80 m, ground_elevation=100.5 m`: raises. With 100 m for both, or south by `axis_depth=20 m`, it doesn't.

### Acceptance criteria
Tolerance 1e-6 relative for values carried to 8 figures, as in M1; sums checked to 1e-12 relative, since they are exact; critical distances to 1e-8 m.

1. **Golden values:** cases A, B and C through `movement_profile` (spacing 2.5 m, utility from offset −30 to 60 m), at the offsets given, for `vertical` and `along`.
2. **Exact sums** (hypothesis, over two or three troughs on parallel and crossing tunnels and points at the surface): displacement, gradient, Hessian and third derivative equal the sum of the sources'; the verdict is the worst of theirs.
3. **Third derivative:** case D's values; and (hypothesis, as M1 (a)'s gradient and Hessian tests) the third derivative matches central differences of the Hessian, and is symmetric in its last three indices. `Movement` raises on a wrongly shaped `third_derivative`.
4. **Feature length:** a trough returns i; a superposition the least of its sources', nested ones included.
5. **Critical distances, case B:** they include 0.36756261, 15 and 29.632437 m from the axis (vertical slope zero, to 1e-9 of its scale over the segment, at each), and the profile marks those stations critical. (Corrected in build, 2026-11-03: the review wrote 1e-12, but a zero found to 1e-9 m leaves a slope of about curvature × 1e-9 m, some 1e-10 of its scale; AC 7 already uses 1e-9.)
6. **Critical distances, one trough:** the root-finding helper applied to a lone trough, on level segments at any angle and position (hypothesis), returns its analytic `critical_distances` to 1e-8 m, the lateral-curvature peaks of decision 8 included on oblique segments; M1's 45° case gives its two new distances.
7. **Nothing missed:** for cases A, B, C and a crossing at 45°, sampling each of the eight functions at h/20 finds no sign change (outside the negligible band of decision 9) without a returned critical distance between the two samples; and each returned distance is a zero of one of them (below 1e-9 of its scale).
8. **Records:** case C's inputs include `north.volume_loss` (0.01) and `south.volume_loss` (0.015), `south.offset` (15 m), `south.axis_depth` (30 m), and the two critical-distance constants; method and assumptions hold one trough record, the superposition method and the superposition assumption, each once.
9. **Flags:** a utility below the surface over twin troughs is `outside` at every station, with two flags, `source` `"north"` and `"south"`; `to_dict()`, the summary and the figure notes show the names. A point inside south's bore raises a `ValueError` starting `"south: "`, and the profile's message names the stations' distances.
10. **Inconsistent inputs:** each raise and non-raise of case E.
11. **Arguments:** one source raises; a positional argument, a non-source, and a name with a dot (through `**{}`) raise `TypeError`; nested superpositions name records `outer.north.volume_loss`.
12. **Parallel builder:** the new tunnel's reference point is p₀ + offset·n on a rotated tunnel (azimuth 30°, reference station 1000); a point's station is the same from either tunnel and its offsets differ by `offset`; missing diameter or axis raises; the records of decision 11.
13. **Sweep:** varying `"south.volume_loss"` over [1.0, 1.5, 2.0] % calls `run(south_volume_loss=...)`, and the table's column is `"south.volume_loss"` with 0.01, 0.015, 0.02; a run that changes north's volume loss instead raises the existing error; `"a.b-c"` and `{"a.b", "a_b"}` raise `TypeError`; M1's sweep tests pass unchanged.
14. **Cross-section:** case A draws `tunnel:north`, `tunnel:south`, both axes and both dashed troughs, and the combined trough's settlement at o = 7.5 is case A's; the crossing case draws one bore and the note naming the other; a lone trough's figure is unchanged (M1's figure tests pass). Checked by eye at close-out.
15. **Docs:** the guide page and its example build with `--strict`; every new public name has a reference docstring (equations, inputs and outputs with units, assumptions); mypy strict and the `lowest` job pass.

## Plan

Eleven build commits, each with lint, format, mypy strict and pytest green. Opus does 1–6, Sonnet does 7–10, and Opus does 11 (figures by eye, then close-out), so a new session starts before 7 and before 11.

### 1. `M2 (a): add the third derivative and feature_length to sources` (Opus)
- `src/garisenda/sources/_movement.py`: `Movement.third_derivative`, shape (N, 3, 3, 3, 3), with its shape checked in `__post_init__` like the other arrays. `Source.feature_length(*, start, end) -> float` added to the protocol.
- `src/garisenda/sources/_transverse.py`: the third derivative (d³/do³)·g⊗g⊗g, using spec decision 6's formulas for S and u_n, written into the `evaluate` docstring. `feature_length` returns i.
- Tests in `tests/sources/test_transverse.py` and `test_transverse_properties.py`:
  - case D's values at o = 0, 10, 20;
  - hypothesis: the third derivative matches central differences of the Hessian, is symmetric in its last three indices, and has every depth component exactly zero;
  - `Movement` raises on a `third_derivative` of the wrong shape;
  - `feature_length` returns i (AC 3, the trough half of AC 4).

### 2. `M2 (a): move segment reading and directions into sources` (Opus)
A refactor with no change in behavior.
- New `src/garisenda/sources/_segment.py`:
  - `read_segment(start, end) -> (start, end, length)`, which records, checks finiteness and refuses zero length; taken from the trough's `critical_distances`;
  - `directions(start, end) -> (a, v, l)`, which raises for a vertical segment; taken from `movement_profile`.
- `_transverse.py` and `profile/_movement_profile.py` use them. The profile keeps its utility-specific error message by catching and re-wording.
- Tests: the existing suite passes unchanged.

### 3a. `M2 (a): mark lateral curvature peaks on oblique segments` (Opus)
Added in build: AC 6's hypothesis test found the gap (decision 8, corrected).
- `src/garisenda/sources/_transverse.py`: `critical_distances` adds the offsets ±√(3 ∓ √6) i when |n·l| > 1e-10, and says why in its docstring.
- Tests: M1's 45° case in `tests/sources/test_transverse.py` and `tests/profile/test_movement_profile.py` gains s = 17.791319 and 38.777224 m; the perpendicular cases are unchanged.

### 3. `M2 (a): find critical distances by root-finding` (Opus)
- New `src/garisenda/sources/_critical.py`: `find_critical_distances(source, *, start, end, sampling, tolerance) -> ndarray`, a private helper implementing spec decisions 8–10:
  - **Functions:** the eight functions of s, built from the gradient, Hessian and third derivative contracted with a, v, l.
  - **Sampling:** h = L / ceil(L / (sampling · feature_length)).
  - **Bracketing:** sign changes, with an exact zero counted as a sign of its own, outside the 1e-10 negligible band (per order, over the segment and all three components).
  - **Refining:** vectorized bisection, with every bracket's midpoints evaluated in one `evaluate` call per iteration, until each bracket is shorter than `tolerance`.
  - **Returned:** the midpoints, sorted, clipped to [0, L], with any within `tolerance` of each other merged.
  - The docstring states what it can miss (decision 10).
- 🟡 **Not in the spec, proposed here:** if `evaluate` raises at a sample (the utility passes through a bore), the helper re-raises the same type with the sample indices replaced by their distances along the segment ("at distances 12.5, 13.75 m along the segment"), and leaves no bracketed index list in the message. The profile then prefixes the utility's name. So AC 9's "the profile's message names the distances" holds through the samples, which come before any station is evaluated.
- Tests in new `tests/sources/test_critical.py`:
  - AC 6: hypothesis over lone troughs on level segments at any angle and position; the helper's distances equal `trough.critical_distances` to 1e-8 m;
  - a segment parallel to the tunnel returns none;
  - the bore message gives distances.

### 4. `M2 (a): build a tunnel parallel to another` (Opus)
- `src/garisenda/sources/_tunnel.py`: `IdealizedTunnel.parallel(*, offset, diameter, axis_depth=None, axis_elevation=None, ground_elevation=None)`, following spec decision 11:
  - It reuses the constructor with `reference_point = p₀ + offset·n`, then replaces the records of `reference_point`, `azimuth` and `reference_station` with given-as `"parallel to a tunnel at offset <o> m"`.
  - It adds an `offset` record (geometry).
- Tests in `tests/sources/test_tunnel.py` (AC 12):
  - azimuth 30°, reference station 1000: the new reference point is p₀ + offset·n;
  - a point's station is the same from both tunnels, and its offsets differ by `offset`;
  - missing diameter or axis raises;
  - the records match decision 11;
  - offset 0 is allowed.

### 5. `M2 (a): add gs.superpose` (Opus)
- `src/garisenda/sources/_movement.py`: `Flag.source: str = ""`.
- New `src/garisenda/sources/_superposition.py`:
  - `superpose(**sources)` checks its arguments as decision 1 says:
    - at least two sources;
    - each name an identifier;
    - each value has the six source attributes, or `TypeError`.
  - It checks inputs for consistency as decision 4 says:
    - `ground_elevation` records at any depth of nesting differ by no more than 1 µm;
    - no two bores overlap. Tunnels are found through `.tunnel` and through nested `.sources`; the parallel test is |sin Δθ| ≤ 1e-9; touching bores are allowed.
  - `Superposition`, a frozen dataclass with `sources` held as a `MappingProxyType`:
    - `evaluate` sums the four arrays, takes the worst verdict, re-tags flags with `source`, prefixing names for nesting, and re-raises errors as `"<name>: …"`;
    - `critical_distances` calls `find_critical_distances` with the two constants;
    - `feature_length` returns the least of its sources';
    - `inputs`, `method` and `assumptions` follow decision 3, with identical records kept once.
- `src/garisenda/sources/__init__.py` exports `Superposition`. `src/garisenda/__init__.py` exports `superpose`.
- Tests in new `tests/sources/test_superposition.py`:
  - AC 1: cases A, B and C through `movement_profile` (spacing 2.5 m, offsets −30 to 60 m), `vertical` and `along` at the offsets given, to 1e-6. South is built with `parallel`.
  - AC 2 (hypothesis, in `test_superposition_properties.py`): two or three troughs on parallel and crossing tunnels; all four arrays equal the sum to 1e-12 relative; the verdict is the worst.
  - AC 4, the superposition half: nested superpositions included.
  - AC 8: case C's records.
  - AC 9, the source part: two `outside` flags with `source` "north" and "south"; a point in south's bore raises `"south: …"`; through the profile, the message names the distances.
  - AC 10: every raise and non-raise of case E.
  - AC 11: one source, a positional argument, a non-source and a dotted name raise; nested names read `outer.north.volume_loss`.

### 6. `M2 (a): test critical distances against dense sampling` (Opus)
Tests only. If a test fails, the fix goes in this commit with the cause stated.
- AC 5: case B's distances include 0.36756261, 15 and 29.632437 m, each a zero of vertical slope to 1e-12 of its scale, and the profile marks those stations critical.
- AC 7: cases A, B, C and a 45° crossing:
  - at h/20, every sign change outside the negligible band has a returned distance between its two samples;
  - every returned distance is a zero of one of the eight functions, below 1e-9 of that function's scale.

### 7. `M2 (a): take dotted names in gs.sweep` (Sonnet)
- `src/garisenda/_sweep.py`:
  - `_check_vary` maps each record name to a keyword with dots replaced by underscores, and raises `TypeError` if the result isn't an identifier or two keys collide;
  - `run` is called with the keywords;
  - `_check_varied`, `_check_fixed` and `_table` keep the record names;
  - the docstring gets a several-tunnels example.
- Tests in `tests/test_sweep.py` (AC 13):
  - `"south.volume_loss"` over 1.0, 1.5 and 2.0 % calls `run(south_volume_loss=…)`, and the column holds 0.01, 0.015, 0.02;
  - a run that changes north's volume loss instead raises the existing error;
  - `"a.b-c"` and `{"a.b", "a_b"}` raise;
  - M1's sweep tests pass unchanged.

### 8. `M2 (a): show each flag's source` (Sonnet)
- `src/garisenda/_result.py`: `to_dict()` adds `"source"` to each warning, and the summary prints `"<source>: <reason>"` when it is set.
- `src/garisenda/plot/_profile.py`: `flag_notes` does the same.
- Tests in `tests/test_result.py` and `tests/plot/test_profile.py` (AC 9, the display part): a lone source's output is unchanged.

### 9. `M2 (a): draw several tunnels in the cross-section` (Sonnet)
- `src/garisenda/plot/_cross_section.py`:
  - With a `Superposition`, tunnels are collected through `sources`, nested ones included, with offsets from `built.tunnel`.
  - Each parallel tunnel is drawn in `_section` at its offset, labeled, with z0 and C dimensioned, and its axis dash-dot on every panel (`tunnel:<name>`, `axis:<name>`).
  - Each source's trough is drawn thin and dashed (`trough:<name>:vertical|horizontal`), with the combined trough labeled "Combined".
  - ±i marks appear only with one tunnel.
  - Reach: each drawn tunnel's offset ± 3i, and the utility's offsets.
  - A tunnel that isn't parallel gets a `note` naming it.
  - The x label becomes "Offset from reference tunnel axis".
  - A lone trough draws exactly as now. The docstring is updated.
- Tests in `tests/plot/test_cross_section.py` (AC 14):
  - case A's gids, and the combined settlement at o = 7.5;
  - a crossing draws one bore and the note;
  - M1's figure tests pass unchanged; `rcParams` are unchanged.

### 10. `M2 (a): write the several-tunnels guide` (Sonnet)
- New `docs/site/guides/several-tunnels.md` and `docs/site/examples/several-tunnels.py`: twins built with `parallel`, the profile, the cross-section, a sweep of `south.volume_loss`, and what superposition assumes.
- `zensical.toml` nav.
- `docs/site/reference/garisenda.md` and `sources.md`: entries for `superpose`, `Superposition`, `IdealizedTunnel.parallel`, `Movement.third_derivative`, `Source.feature_length` and `Flag.source`.
- Tests: `tests/docs/test_site.py` picks up the example. The docs build passes with `--strict` and no `griffe:` warnings (AC 15).

### 11. `M2 (a): check figures and close out` (Opus)
- Check the figures in `docs/site/img/generated/` by eye against spec decision 14 (the rest of AC 14), and fix anything found.
- Run every check:
  - the CI line;
  - Python 3.13 and 3.14;
  - the `lowest-direct` floors (numpy 1.26: no numpy 2-only functions), then `git checkout uv.lock`.
- Close-out:
  - SPEC §12.4 marks M2 (a) done with its date;
  - `CLAUDE.md`'s status and "Next" sentence point to M2 (b);
  - any recurring mistake goes into the `CLAUDE.md` conventions;
  - every new public calculation has a complete docstring;
  - report each of the 15 ACs as met or not, with its evidence.
