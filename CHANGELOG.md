# Changelog

garisenda is pre-alpha: the API can change between releases, and the transverse trough's sources aren't verified yet, so results are for trying the library, not for design.

## Unreleased

### Added
- **Buildings**, `gs.buildings`: a building's wall, `gs.buildings.Building`, or one built square to a tunnel from station and offsets, `gs.buildings.perpendicular_building`, with its height and foundation depth. `gs.movement_profile` runs along a wall at its foundation level.
- **The building damage check**, `gs.check_building`: Mair, Taylor & Burland (1996)'s staged method. Stage 1 checks the largest settlement and slope along the wall. Stage 2 splits the wall into hogging and sagging zones and gives each its deflection ratio, horizontal strain, bending and diagonal strains, and damage category, with the governing zone. Every choice is an argument you give: the beam (`burland_wroth_beam()`, as practice uses it, or `timoshenko_beam()`), E/G, the damage categories, the cut-off (`no_cutoff()` or `trough_width_cutoff(multiple=...)`), the Stage 1 limits and the acceptable category. A foundation at 0.2 of a tunnel's axis depth or deeper is flagged `outside`.
- **Presets for buildings**, in `gs.presets`: `youngs_to_shear_modulus_ratio(structure=...)` (masonry 2.6, framed 12.5), `damage_categories()` (Table 2) and `preliminary_assessment_limits()` (10 mm and 1/500), each with its source and caveats.
- `Result.zones`, a building check's zones, empty for every other result; `Result.checks` has `zone` and `category` columns; and a sweep over a building check has a `<check>_category` column for its zones and damage category.

### Changed
- `gs.movement_profile`'s first argument is named `asset`, since it takes a utility or a building. Passing it by position, as every example does, is unchanged.
- The utility's inputs are named for it in a result: `utility.diameter`, `utility.depth`, `utility.station`. A single tunnel's keep their names (`diameter`, `volume_loss`), so no two inputs share a name. A sweep over a utility input names it so: `vary={"utility.depth": ...}`, with your function taking `utility_depth`.
- A source in `gs.superpose` can't be named `utility`.
- Assumptions, messages and docstrings no longer refer to garisenda's internal planning documents. Where a result's method was derived by garisenda, its source says so and points to the docstring that states it.
- The cross-section's messages and notes no longer mention a plan figure, which doesn't exist yet.

## 0.1.0 (2026-11-05)

The first usable release: greenfield movements from tunneling along a utility, with their figures and sweeps. It covers milestones M1 and M2 (`SPEC.md` §12.4).

### Sources of movement
- **An idealized straight tunnel**, `gs.sources.IdealizedTunnel`, described by station and offset. `IdealizedTunnel.parallel()` builds a second tunnel at a given offset, such as a twin bore.
- **The transverse trough at the ground surface**, `gs.sources.transverse_surface_trough`: a Gaussian settlement trough and horizontal movement toward the tunnel, from a volume loss and a k you give, with exact strains and curvatures (derivatives, not finite differences).
- **The transverse trough below the surface**, `gs.sources.transverse_trough`, at an asset's own depth. The width at depth comes from a method you name: `mair_trough_width` (Mair & Taylor's method for clay) or `linear_trough_width`, i = k (z₀ − z) from your k. Points below the tunnel crown are flagged.
- **Several tunnels by superposition**, `gs.superpose`. Each tunnel keeps its own volume loss and k, the movements add, and the result records each input with its tunnel and superposition as an assumption.

### The movement along a utility
- **A utility built from station and offset**, `gs.utilities.perpendicular_utility`, perpendicular to the tunnel, with a required elevation reference (`"invert"`, `"axis"` or `"crown"`).
- **The movement profile**, `gs.movement_profile`: movements along and across the utility and their exact derivatives, keyed by distance along it. Stations are added at the field's critical distances (where its components peak, found by root-finding), so no peak between stations is missed, including the peaks between two tunnels.
- **One result shape**, `gs.Result`: the table, every input with its kind and source, the methods, assumptions, warnings and a validity verdict, viewable as a dict, a DataFrame or a text summary. Outside a method's range, points are flagged, not raised.
- **Inputs with units and sources.** Inputs take pint quantities (`gs.units`) and can carry their source with `gs.Sourced`. Judgments such as volume loss and k have no defaults.

### Figures and sensitivity
- **The cross-section**, `gs.plot.cross_section`: the trough, the tunnels and the utility to scale, at the utility's depth.
- **The profile**, `gs.plot.profile`: movement, strain and curvature along the utility, with flagged stations marked.
- **Sweeps**, `gs.sweep`: the same calculation over arrays of one to three inputs, as a table of governing values and verdicts.

### Docs
- The docs site at [konnerhorton.github.io/garisenda](https://konnerhorton.github.io/garisenda/): a getting-started walkthrough, conventions, the figures, guides to sweeps, several tunnels and movements below the surface, and the API reference with its sources.

### Not yet
- Utility checks (strain, curvature, joint pullout and rotation), M3, and building damage, M4.
- Real alignments and polylines, M5, and the longitudinal trough, M6.

## 0.0.1 (2026-11-02)

A placeholder that reserves the name on PyPI. No analysis code.
