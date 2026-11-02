# M1 (a): the transverse surface trough over an idealized straight tunnel

## Intent

### Goal
A caller can describe an idealized straight tunnel and evaluate the steady-state transverse Gaussian trough at the ground surface: settlement and horizontal movement at any points (x, y, z), with their exact spatial derivatives, the trough width from a given k, every input recorded with its kind and source, and points outside the method's range flagged, including every point below the surface. This is the first source (SPEC §3) and the numerical core that M1 (b) builds the profile, the result and the figures on.

### Why
- SPEC §12.4: M1 is the first milestone with analysis code. As written it holds nine pieces (units, the input rules, the result shape and verdict, `gs.sweep`, the source interface, the profile, the tunnel and builder, the trough, two figures) plus the docs site from §12.3, which is several sittings of review, not one. So M1 splits in three, as hangtu's large milestones did:
  - **(a) this unit:** units and the input rules, the idealized tunnel, the source interface, the transverse surface trough.
  - **(b)** the station-and-offset builder, the profile along an asset, the result object and its verdict and views, the cross-section and profile figures.
  - **(c)** `gs.sweep`, the docs site (Zensical), and M1's user docs and figures.
- The trough comes first rather than the framework because it is the framework's first real consumer: designing the result object without a calculation to wrap tends to guess wrong. (a) builds only the parts of the framework the trough needs (units, the input kinds, validity as data) and (b) wraps them into the result shape.
- The surface trough settles the geometry, the interface and the math. The subsurface trough (M2) then replaces only how the trough is built at a depth: the width i(z), the maximum settlement at depth and the horizontal movement model, plus the validity rule. That holds only if the interface is 3D from the start (decision 3).
- Everything after it depends on this: the profile (b), utilities (M3), buildings (M4) and several tunnels (M2) all consume this source.

### Constraints
- **SPEC §3:** a closed-form source is a function of points, not a grid; it returns global displacement components (x, y, vertical) and their exact spatial derivatives. No spline, no finite differences inside the source.
- **SPEC §4:** volume loss and the trough width parameter are required keyword-only judgments with no default. Provenance is optional on input and always kept on output.
- **SPEC §2:** golden values come from hand calculations written out in the spec, never from the code. Citations stay 🔬 unverified in this unit (decision 5); nothing is cited as verified until it is checked against the source.
- **SPEC §2.5, §5.2:** outside the method's range is flagged, not raised; only physically impossible inputs raise.
- **SPEC §6, §8.1:** pint first, SI preferred, never guess a unit; settlement positive downward; depth positive downward; offset positive to the right looking up-station.
- **SPEC §8.3:** the idealized tunnel is a reference point (x, y), a plan direction, an axis depth or elevation, and a diameter, with no ends.
- **SPEC §11:** hypothesis properties: trough volume equals volume loss times tunnel area; settlement symmetric about the axis; derivatives match finite differences of the same field.
- **SPEC §12.1:** `pint` and `numpy` are added now, with floors proven by the `lowest` job; `hypothesis` joins the dev group.

### Out of scope
- **The trough below the surface** (width at depth, Taylor 1995's horizontal movements): M2, as SPEC §12.4 has it. In (a) a point below the surface gets the surface trough's values and is flagged (decision 3).
- **Named trough width methods and k presets** (O'Reilly & New 1982, Mair et al. 1993, Selby 1988): later, once you decide how recommendations are offered (decision 4).
- **Several tunnels and superposition:** M2.
- **The builder, the profile, the result object, figures, `gs.sweep`, the docs site:** M1 (b) and (c).
- **Real alignments, tunnel ends, the longitudinal trough:** M5, M6.
- **Utility and building checks:** M3, M4.

### SPEC sections touched
- **SPEC §12.4:** M1's row records the split into (a), (b) and (c).
- **SPEC §1.3:** the tunnel movements row says the trough width comes from a given k for now, named methods later.
- **SPEC §6:** inputs that practice writes as percentages must be pint quantities (decision 2).
- **SPEC §3:** the 🟡 source interface becomes decided, with its exact signature recorded in this unit's spec.
- **SPEC §2.1, §2.2, `docs/TODO.md` #2:** the sources this unit relies on are named as 🔬 candidates, unverified; TODO #2 stays open.

### Decisions (intent review, 2026-11-02)
1. **M1 splits into (a), (b) and (c), in that order.** Agreed as proposed.
2. **An input that practice writes as a percentage must be a pint quantity.** A plain float for volume loss is an error that says how to write it (`0.5 * gs.units.percent` or `0.005 * gs.units.dimensionless`), because `0.5` could mean 0.5 % or 50 %, and SPEC §6 says never guess a unit. It covers volume loss now and strain limits in M3. Inputs never written as percentages (k, lengths) still accept a plain float read as the documented SI unit.
3. **Surface trough only; every point below the surface is flagged.** It gets the surface trough's values and an `outside` flag with the reason (the surface trough applied below the surface, where the real trough is narrower and unconservative to ignore; the subsurface method is M2). A flag on the result, not a Python warning: the tests treat warnings as errors, and a long utility would emit one per point. So that M2 only replaces how the trough is built, the source takes full (x, y, z) points and returns derivatives with respect to z too; for the surface trough they are exactly zero, and a test says so. Validity is computed per point, so M2 changes the rule, not the shape. Briefly considered and dropped: the subsurface trough in M1 with i = k·(z₀ − z).
4. **k is given directly** (`trough_width_parameter=`), a required judgment. Named methods and presets come later, once you've decided how recommendations are offered.
5. **Citations stay 🔬 unverified for now.** The spec names the candidate sources (Peck 1969 for the Gaussian form, O'Reilly & New 1982 for the volume relation and horizontal movement) as unverified, and golden values come from hand calculations. Docstrings mark the citation 🔬 until TODO #2 is done.
6. **Horizontal movement assumes ground moves toward the tunnel axis**, recorded on the result as an assumption, with no alternative method in this unit.
