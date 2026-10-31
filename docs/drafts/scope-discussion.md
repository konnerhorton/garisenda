# garisenda scope discussion (2026-10-31)

Condensed from the conversation that produced `SPEC.md`. Input for the SPEC and for later intents; only items marked "decided" are decisions, and those now live in `SPEC.md`. Every source named here is a 🔬 candidate, not a verified citation.

## The starting point

Greenfield assessments of individual utilities and structures follow a well-known pattern: a Gaussian trough, a few strain formulas, a reduction factor read off a chart, and limits from somewhere. Done by hand, these calculations are hard to check: chart readings aren't recorded, and limits rarely say where they came from. garisenda does the same work traceably, and grows from there toward the 3D field, buildings and other sources of movement.

## Methods in common practice

A map of what practice uses, to plan the scope. None of these are verified citations yet (TODO #2–#7).

- **Tunnels:** Gaussian transverse trough and cumulative-normal longitudinal trough; volume loss as the ratio of the trough volume to the tunnel's area; a 3D field (Attewell & Woodman 1982). Surface and subsurface methods: O'Reilly & New (1982), Mair et al. (1993) with Taylor (1995) for horizontal movements below the surface, New & Bowers (1994).
- **Trough width parameter (k):** given directly; from O'Reilly & New's linear fits for cohesive and granular soil; simplified values; layered ground (Selby 1988).
- **Other sources:** embedded walls (CIRIA C580/C760), mining (influence functions).
- **Buildings:** Burland & Wroth (1974), Burland (1995), Boscardin & Cording (1989); deflection ratio and horizontal strain; hogging and sagging segments split where the curvature changes sign; damage categories 0–5 (Burland 1997); stiffness ratios for masonry and framed buildings (Mair, Taylor & Burland 1996).
- **Utilities,** following Bracegirdle et al. (1996):
  - jointed pipes: joint pullout (axial plus a flexural part from joint rotation) and joint rotation (from offsets one pipe length either side of the joint);
  - all pipes: axial and bending strain, with radius of curvature from chord offsets;
  - reduction factors for each quantity, commonly left to the engineer's judgment;
  - criteria for pullout, rotation, strain and radius of curvature;
  - discrete results depend on the sampling interval, and very short spans give extreme results.
- **Rail** (cant and twist) and **staged construction.**

## Pitfalls to design against

Mistakes that are easy to make in this kind of calculation, and the SPEC rule that prevents each:

- **Using the wrong displacement component:** movement along the pipe where movement across it is needed, or a position mixed with a displacement. → SPEC §7 resolves movement into components along and across the pipe at every point.
- **Inconsistent chord length and interval:** an offset measured over several intervals with a radius computed from one. → Discrete strain is defined once, with its interval, and tested against analytical strain on a smooth field (SPEC §2.4).
- **Silent truncation:** a pipe length divided by an interval rounded to an integer. → Error or flag (SPEC §10).
- **Hidden defaults:** soil modulus or trough constants fixed in code. → SPEC §4.
- **Silently clamped charts:** a chart that returns its edge value for an input outside it. → Outside a method's range is flagged (SPEC §2.5); digitized charts aren't shipped (SPEC §2.3).
- **One reduction factor for everything** (strain, pullout and rotation). → SPEC §4 and TODO #1 ask whether each quantity needs its own.
- **Units by convention.** → Pint first; units recorded on every table.

## Decisions reached (now in SPEC)

- **Greenfield utility assessment first, 3D interface from the start.** Starting with the 3D surface was considered: it would get the geometry right first, but gives nothing usable until utilities are assessed. The greenfield assessment gives quick feedback on real work, and designing the movement-field interface for 3D means nothing is thrown away. (SPEC §1.3, §3)
- **Pipe types.** Some utilities are jointed, some continuous (PVC or HDPE, often installed by HDD). Both discrete and analytical strain are computed and compared; every check runs by default. (SPEC §7)
- **Steady-state transverse trough first.** (SPEC §12.4)
- **Limits** are project-specific judgments with literature provenance. (SPEC §4)
- **Figures** are needed for the output in every case. As soon as the transverse trough is done and tested, real geometries are imported and the profile along a utility is plotted. (SPEC §9, M3)
- **Soil–pipe interaction** is a critical part of Phase 1: a factor as a judgment with a reason first, then derived methods from a literature review (TODO #1). Charts are very imperfect, which is why they aren't the answer.
- **Joints:** worst case over every joint position; each pipe type and diameter has a pipe length, from the user or an opt-in cited preset. (SPEC §7)
- **Geometry:** utilities as x, y, z tables; buildings as footprints with facades derived from edges; a single facade line allowed. (SPEC §8.3)
- **Ground surface:** a single elevation, or depths only, in Phase 1; its own geometry later. (SPEC §8.2)
- **No datum or projection recorder** in Phase 1: one flat coordinate system, converted before it reaches garisenda. (SPEC §8.1)
- **A thin `Site` bundle.** (SPEC §8.4)
- **Buildings (M6) are in Phase 1**, with footprints entered by hand. Public GIS building data is a later phase. (SPEC §1.3)

## Soil–pipe interaction: the path forward

Four levels, from simplest:
1. **Greenfield, factor 1.** The baseline, and realistic for flexible HDPE and PVC pipes. It must still be chosen explicitly.
2. **Closed-form relative stiffness.** Published methods relate the pipe's bending stiffness to the soil's stiffness and the trough width, and give the reduction directly. These replace reading a chart.
3. **A beam on springs** along the real geometry, with soil springs from published guidance. Whether this is in scope is SPEC §13 Q1.
4. **Numerical analysis.** Out of scope, flagged.

The inputs that are easiest to get wrong are the soil modulus (and the strain level it belongs to), the modulus of plastic pipes (which depends on load duration and temperature), and joint stiffness. Each method's spec needs a validity range and warnings for these.

## Later phases (not specified yet)

- Ground surface as its own geometry.
- Buildings from public GIS data: footprints, and heights where available. Missing heights are errors or flags, never filled; foundation and material are judgments; short footprint edges need a simplification tolerance, which is a judgment; heights are often given above ground, not as elevations.
- Embedded walls and excavations, staged construction, rail, mining.
