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
