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
