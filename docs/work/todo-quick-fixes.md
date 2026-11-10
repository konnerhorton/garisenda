# TODO quick fixes: #18 (label), #20, #21, #24

A plan only, without the full development cycle (agreed 2026-11-10). Branch `todo-quick-fixes` off `main`, one commit per item. At close, delete #20, #21 and #24 from `docs/TODO.md`, and cut #18 down to its open question (a reference line that isn't a bore, such as a centerline).

## 1. #20: stale README and getting-started (docs only)
- `README.md:7`: replace "utility and building checks come next" with what exists now, and keep the "not for design" caveat: checks of continuous and jointed pipes (`gs.check_continuous_pipe`, `gs.check_jointed_pipe`) work; building checks come next.
- `docs/site/getting-started.md:73`: replace "not yet in garisenda" with a pointer to `gs.check_continuous_pipe` and `gs.check_jointed_pipe` and their guides (Continuous pipes, Jointed pipes).
- **Check:** a strict docs build.

## 2. #21: the surface trough vs the trough at depth (docstrings and a guide)
- `src/garisenda/sources/_transverse.py`, the `transverse_surface_trough` docstring: say this is the movement at the ground surface (z = 0) only. For a buried utility, use `gs.sources.transverse_trough`, which at z = 0 gives this same trough with the linear width method.
- `src/garisenda/sources/_transverse_trough.py`, the `transverse_trough` docstring: add the reverse pointer in one line.
- `docs/site/guides/sweep.md`: after the line about the depth-2 m runs being *outside* because the trough is a surface method, add a pointer to `transverse_trough` and the Below the surface guide for a buried utility.
- **Before writing:** check that "the linear method at z = 0 is the surface trough" holds. Find an existing test in `tests/sources/` that asserts it, or add one. Don't state it unverified.
- **Check:** the tests, and a docs build (griffe warnings).

## 3. #18: name the reference tunnel in the profile's offset label (code)
- `src/garisenda/plot/_profile.py`, `_offset_axis` (called from `profile`): it has no access to the source today, so pass in `result`, or the label. Copy the cross-section's rule (`src/garisenda/plot/_cross_section.py`, `several = isinstance(source, Superposition)`, label near line 325):
  - one tunnel: "Offset from tunnel axis" (unchanged);
  - superposition: "Offset from reference tunnel axis". If the built tunnel (`asset.built.tunnel`) matches a named part of the superposition, name it instead, e.g. "Offset from axis of tunnel 'north'". Use the same matching as the cross-section's `_parts`/`_bores`, so the two figures agree. If the cross-section adopts the name too, update `tests/plot/test_cross_section.py:217`.
- **Tests** in `tests/plot/test_profile.py`: the top-axis label for a single tunnel and for a twin-tunnel result.
- **Check:** regenerate the docs figures and look once at the twin-tunnel profile in `docs/site/img/generated/`.

## 4. #24: the inside-the-bore error (code)
Today the message reads "Utility 'W-1': Points inside the bore can't be evaluated at distances 38.4075, 38.5948, … m along the segment." It is raised by `check_outside_bore` (`src/garisenda/sources/_segment.py`). It is rewritten by `_with_distances` (`src/garisenda/sources/_critical.py`), which replaces the trailing `[indices]` list with distances, and re-raised with the utility's name in `src/garisenda/profile/_movement_profile.py` (`profile_rows`, and the `critical_distances` wrap in `movement_profile`).

- `check_outside_bore`: add the bore's extent, e.g. "inside the bore (axis at depth 20 m, diameter 6 m: depths 17 to 23 m)". Keep the trailing `[indices]` list, so `_with_distances` still finds it.
- `_with_distances`: **decided, more than 5 points** collapse to a count and a range, "at 21 points from 38.4 to 41.6 m along the segment". 5 or fewer keep the full list, so the exact-message test in `tests/sources/test_critical.py` (`test_bore_message_gives_distances`, 5 points) still holds.
- `movement_profile` / `profile_rows`: for the bore error, add the utility's depth (the range of its vertices' depths) and a remedy:
  - a built utility (`utility.built` is not None): check its depth, or its `elevation_reference`, which is converted to the axis with the given diameter;
  - a utility given by its vertices: check its vertices' depths.

  Prefer a private `InsideBoreError(ValueError)` raised by `check_outside_bore` over matching the message text. Superposition prefixes the source name (`south: …`), so the subclass must survive that re-raise, or the profile must look at `__cause__`.
- **Tests:** update `tests/profile/test_movement_profile.py` (`test_utility_through_the_bore_raises_naming_it`) to assert the utility's depth, the bore's extent, the remedy and the range form. Check that `tests/test_sweep.py` (`test_a_run_through_the_bore_is_recorded`) and `tests/sources/test_superposition.py` (`^south: .*inside the bore`) still pass.

## Close
- What CI runs: `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest`, and the strict docs build.
- Update `docs/TODO.md` as above. Merge with `--no-ff` after approval.
