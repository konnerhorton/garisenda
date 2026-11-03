# M1 (c): the cross-section and profile figures, `gs.sweep` and the docs site

## Intent

### Goal
A caller who has run `gs.movement_profile` can draw the two figures of a traditional assessment from its result: the **cross-section** at the utility's station (tunnel, trough and utility in place) and the **profile** along the utility (movement, strain and curvature against distance, flagged stations marked). They can run the same calculation over arrays of one to three inputs with **`gs.sweep`** and get a tidy table of governing values and verdicts. And a **docs site** shows them how, with M1's user docs and figures. This closes M1: the spreadsheet's movement calculation, its figures and its sensitivity runs, end to end (SPEC §12.4).

### Why
- SPEC §9: every assessment has a figure, and figures are the fastest check that a result is sensible. M1 (b)'s result has none yet.
- SPEC §5.3: sensitivity runs over volume loss and k are what an engineer does next with a trough, and the result shape (M1 (b)) exists to be tabulated.
- SPEC §12.3: docs are written as we go, and M1 is where the site is set up; M1 (a) and (b) shipped no user docs (M1 (b) intent, decision 1).

### Constraints
- **SPEC §9:** one plot contract, `gs.plot.<name>(result, *, ax=None, display_units=None) -> (fig, ax)`, matplotlib; a figure draws from the result and never recalculates; checked by eye at close-out.
- **SPEC §3:** a grid is evaluated only to draw a figure, never for a calculation.
- **SPEC §5.3:** one function over one to three inputs, `"grid"` or `"paired"`, one row per run with the varied inputs, governing values, utilizations, pass/fail and verdict; fixed inputs once in `df.attrs`; a run that raises records the error in its row. §11: a test that a sweep row equals a direct call.
- **SPEC §10:** flagged stations are drawn and marked, never dropped.
- **SPEC §12.1:** `matplotlib` added with a floor proven in CI (hangtu: `>=3.8`); tooling follows hangtu (Zensical, `mkdocstrings-python`, a `docs` dependency group, a `docs.yml` workflow to GitHub Pages, `--strict` builds in CI).
- **No project data** (CLAUDE.md): docs and figures use invented geometry. The trough's sources are unverified (TODO #2), and the docs say so where the method is described.

### Out of scope
- **The plan figure** (tunnels and assets in plan): M5, with real geometry (SPEC §9, §12.4).
- **Checks drawn against limits** on the profile figure: M3, when checks exist; the figure leaves room for them.
- **Subsurface troughs and several tunnels** in the cross-section: M2.
- **A docs page on the perpendicular assumption:** TODO #10's outcome, in M3.
- **Verifying the trough's sources:** TODO #2, separate.

### SPEC sections touched
- **SPEC §9:** the plot contract settled, including multi-panel figures and how the cross-section draws the trough (decisions 2 and 3).
- **SPEC §5.3:** `gs.sweep(run, *, vary, mode)` replaces `sweep(analysis, inputs, ...)` (decision 4).
- **SPEC §5.1:** governing values on the result, added by decision 5.
- **SPEC §12.1, §12.2, §12.3:** `matplotlib`, the `docs` group, `garisenda.plot`; the docs site decided.
- **SPEC §12.4:** M1 marked done at close-out.

### Decisions (intent review, 2026-11-03)
1. **One unit.** The user docs need the figures and `gs.sweep` together, and the site setup is mostly hangtu's. Rejected: (c) code, then (d) site and docs.
2. **The profile figure is multi-panel and follows matplotlib's convention**: it returns `(fig, axs)`, as `plt.subplots` does, and takes `axs=` (one axes per panel) in place of `ax=`. Movement; strain along; slope and curvature. The cross-section is one axes and keeps `(fig, ax)` and `ax=`. Rejected: three single-axes functions the user lines up by hand.
3. **The cross-section evaluates the source to draw the trough.** The trough runs past the utility's ends, and its curve between stations isn't in the result. So the result keeps a reference to its source and utility (`result.source`, `result.asset`, not shown in the views), and the figure evaluates the source on a grid across the section, which SPEC §3 allows for drawing. The utility's own values come from the result. SPEC §9's "never recalculates" becomes "never recalculates the result's values". Rejected: `gs.plot.cross_section(source, utility)`, which breaks the one contract; a section grid stored on every result, calculated whether or not a figure is drawn.
4. **`gs.sweep(run, *, vary, mode)` takes a function** the user writes, which builds the chain (tunnel, trough, utility, profile) from keyword arguments and returns a `Result`. The inputs worth varying (volume loss, k) belong to the source, two calls above `movement_profile`, so SPEC §5.3's `sweep(analysis, inputs, ...)` can't reach them. The table has one row per run: the varied inputs, `Result.governing()` (decision 5), the verdict, and an `error` column for a run that raised (SPEC §10). Fixed inputs are read from the first run's input records into `df.attrs`, with the function's name. Safeguards: each varied value must appear in that run's input records, or `sweep` raises (a function that ignores or misroutes an argument can't vary nothing silently); `mode` (`"grid"` or `"paired"`) is required with two or more varied inputs, since the run counts differ, and refused with one. This changes §5.3's signature. Rejected: dotted paths into objects (`"source.volume_loss"`), which need every object to rebuild itself and hide how a change propagates (a diameter changes both the trough and the utility); a pipeline description, a small language for what four lines of Python say.
5. **Governing values come from the result**: `Result.governing()`, a small table of the extremes the `repr()` reports (largest settlement, tension and compression along, sagging and hogging curvature) with their distances. The `repr()`, `gs.sweep` and the figures read it, so they agree. Checks add rows in M3.
6. **Display units:** figures in mm for displacement, microstrain for strain and 1/km for curvature, with `display_units=` to change any of them. A display setting, not a judgment (SPEC §4); axis labels always state the unit.
7. **User docs for M1:** a getting-started page (tunnel → trough → utility → profile → figures → sweep, on invented geometry), a conventions page (station and offset, signs, depth), a page per figure, and the API reference from docstrings. Figures saved as PNGs and committed for review, as hangtu does.

## Spec

No topic doc holds this, so the spec is here. 🟡 marks a proposal for this review; two of them (decisions 9 and 13) change intent decision 2 and are called out there.

### Changes
- **SPEC §5.1:** a `Result` keeps its `source` and `asset` for drawing, outside the views; `Result.governing()` (decisions 1–3).
- **SPEC §5.3:** `gs.sweep(run, *, vary, mode=None)` and its table (decisions 4–8).
- **SPEC §9:** the contract for single- and multi-panel figures; a figure may evaluate the result's source on a grid to draw the field, and never recalculates the result's values (decisions 9–16).
- **SPEC §12.1:** `matplotlib>=3.8`, hangtu's floor; a `docs` dependency group. **§12.2:** `garisenda.plot`. **§12.3:** the docs site decided (decisions 17–19).
- **`gs.units`** gains `microstrain` (decision 15).
- **New modules:** `garisenda._sweep` (`sweep`), `garisenda.plot` (`cross_section`, `profile`). Public names in `gs`: `sweep`, `plot`.

### Decisions

**The result (intent decisions 3 and 5)**

1. 🟡 **`Result.source` and `Result.asset`**, set by the analysis (the `Source` and the `Utility`), are left out of `repr()`, `to_dict()`, `to_frame()` and equality. They are there so a figure can draw what the result's table doesn't hold (the trough beyond the utility's ends). Both are frozen, so the result can't drift from them.
2. 🟡 **`Result.governing() -> DataFrame`**, one row per extreme, read from `values` and never recalculated:

   | `name` | column | extreme |
   |---|---|---|
   | `largest_settlement` | `vertical` | largest positive |
   | `largest_tension` | `along_strain` | largest positive |
   | `largest_compression` | `along_strain` | most negative |
   | `largest_hogging` | `vertical_curvature` | largest positive |
   | `largest_sagging` | `vertical_curvature` | most negative |

   Columns `name`, `column`, `value` (signed, as in `values`), `unit`, `distance` and `verdict` (the station's). Rows whose column the result doesn't have are left out, so later analyses reuse it.
3. 🟡 **No extreme of a sign is NaN, not zero:** if no station is in tension, `largest_tension` has `value` and `distance` NaN and `verdict` None, because nothing was there to report (SPEC §10: never filled). **Ties go to the smallest distance** (a symmetric trough has equal tension peaks either side; the first is reported); values within 1e-9 relative of the extreme count as tied, so rounding can't pick the far peak. The `repr()` reads `governing()` and prints "none" for a NaN row.

**`gs.sweep` (intent decision 4)**

4. **`gs.sweep(run, *, vary, mode=None) -> DataFrame`.** `run` is any callable taking the varied inputs as keyword arguments and returning a `Result`. `vary` maps one to three argument names to one-dimensional sequences (lists, arrays or pint arrays), each element passed to `run` as it is (a pint array's element is a quantity). 🟡 `mode` is `"grid"` (every combination, the first input varying slowest, as `itertools.product`) or `"paired"` (element by element; sequences of equal length). It is required with two or three inputs and refused with one, with an error that says why.
5. 🟡 **The table:** one row per run, in run order, with the columns
   - `run` (0, 1, …);
   - each varied input, **as used**: the magnitude in SI from that run's input record, units in `attrs["units"]` (so 1 % appears as 0.01, dimensionless, SPEC §6);
   - for each row of `governing()`, `<name>` and `<name>_distance`, with units;
   - `validity` (the result's verdict) and `warnings` (how many flags);
   - `error`: None, or `"<ExceptionType>: <message>"` for a run that raised.

   `attrs` also holds `run` (the callable's qualified name), `mode`, `vary` (the names) and `fixed_inputs`, every input record of the first successful run that isn't varied, in `to_dict()`'s form.
6. 🟡 **Each varied input is checked against the run's records:** for each name, at least one input record of that name must hold the value given (converted to the record's SI unit, to 1e-12 relative). Otherwise `sweep` raises, naming the input and the run, because `run` didn't pass it on. So `run`'s arguments are named as the inputs they set (`volume_loss`, not `vl`), as SPEC §8.5 names them anyway. Where two records share a name (the tunnel's and the utility's `diameter`), any match passes; the docs say to vary one of them through its own builder only.
7. 🟡 **Inputs that aren't varied must not change between runs:** a record outside `vary` whose value differs from the first run's raises, naming it, because `fixed_inputs` would be wrong. A function that varies something it wasn't asked to is a mistake, not a sweep.
8. 🟡 **Errors:** a run that raises an `Exception` is recorded in its row, with NaN governing values and validity None, and the sweep goes on (SPEC §5.3, §10). If every run raises, `sweep` raises the first error, since that is a mistake in `run`, not a result. The checks of decisions 6–7 raise at once, never recorded. More than three inputs, an empty sequence, or unequal lengths for `"paired"` raise before any run.

**Figures (SPEC §9)**

9. 🟡 **Contract:** a single-axes figure is `gs.plot.<name>(result, *, ax=None, display_units=None) -> (fig, ax)`; a multi-panel one is `gs.plot.<name>(result, *, axs=None, display_units=None) -> (fig, axs)`, with `axs` a sequence of one Axes per panel, as `plt.subplots` returns. With `ax`/`axs` given, the figure draws into them and creates none; otherwise it creates one sized for the page. Styling is applied inside `matplotlib.rc_context`, never by changing global state. A figure reads the result's `values` and `governing()`, and may evaluate `result.source` on a grid to draw the field (decision 12), never to recalculate a value in the table. **Both M1 figures are multi-panel** (decisions 10 and 13), which changes intent decision 2 for the cross-section.
10. 🟡 **The profile figure, `gs.plot.profile`:** four panels stacked on a shared x axis, distance along the utility (m):
    1. settlement (`vertical`), y axis pointing down, so the trough hangs as it does in the ground;
    2. horizontal movement, `along` and `lateral`;
    3. strain along (`along_strain`), labeled "tension +";
    4. curvature, `vertical_curvature` and `lateral_curvature`, labeled "hogging +, sagging −".

    Slope isn't drawn: it is in the table, and M3 adds it to the figure with joint rotation, where it is first checked. This changes intent decision 2 ("slope and curvature") to one quantity per panel without twin axes, and horizontal movement gets its own panel instead of sharing the settlement axis, whose sign convention differs. 🟡 For a built utility, a top x axis gives the offset from the tunnel axis.
11. 🟡 **Marks on the profile:** each governing value is marked with a point and its value, on its panel; critical stations are ticked on the x axis; stations that aren't `within` are shaded on every panel, by verdict, and each flag's reason is printed under the figure with its distance range (as the `repr()` does). Nothing flagged is left unmarked (SPEC §10).
12. 🟡 **The cross-section, `gs.plot.cross_section`:** two panels sharing the x axis, offset from the tunnel axis (m), at the utility's station:
    1. the trough: settlement (y pointing down) and horizontal movement toward the axis (positive toward the centerline, the transverse-section convention of SPEC §8.1), evaluated from `result.source` at the surface on 401 points over the wider of the utility's offsets and ±3i; the utility's stations from `values` are marked on the curves, and those that aren't `within` ringed by verdict, with each flag's reason under the figure as on the profile (SPEC §10); ±i marked as the inflection points;
    2. the section, to scale (equal aspect), depth pointing down from the ground surface at 0: the tunnel's bore and axis, the utility as a band of its diameter at its axis depth between its offsets, and the axis depth and cover dimensioned.

    It needs a utility built from station and offset and a source with a `tunnel`; otherwise it raises, saying the cross-section is for a built utility and the plan figure (M5) is for the rest.
13. **The cross-section has two panels, not one** (intent decision 2 said one axes): the trough in mm and the section in m to scale can't share a y axis without exaggerating one or hiding the other.
14. 🟡 **Display units** (intent decision 6) are given per kind of quantity: `display_units={"length": "m", "displacement": "mm", "strain": "microstrain", "curvature": "1/km"}`, the defaults, any subset overridable. An unknown kind raises, listing the four; a unit of the wrong dimension raises (SPEC §6). Every axis label gives its unit, as `Quantity (unit)`.
15. 🟡 **`gs.units.microstrain`** (µε, 1e-6) is defined on garisenda's registry, so strain can be displayed and given in it.
16. **Figures are checked by eye** at close-out (SPEC §9): PNGs of both figures for cases A, C and D (where they apply) at 100 dpi, looked at and committed with the docs.

**The docs site (SPEC §12.3, intent decision 7)**

17. 🟡 **As hangtu's:** Zensical with `mkdocstrings-python` for the API reference, pinned in a `docs` dependency group (`zensical==0.0.70`, `mkdocstrings-python>=2.0.9`, hangtu's); `zensical.toml` at the root; pages in `docs/site/`, published; the rest of `docs/` stays internal. Each page's example is a script in `docs/site/examples/`, run by `docs/prepare_site.py` to write its figures, so every figure on the site comes from code that runs. No logo yet.
18. 🟡 **Pages:** home; install; getting started (one invented crossing: tunnel, trough, perpendicular utility, profile, `repr()`, both figures, a sweep over volume loss and k); conventions (station and offset, signs, depth, elevation reference); one page per figure; a sweep guide; the API reference for `gs`, `gs.sources`, `gs.utilities`, `gs.plot`. The getting-started page states that the trough's sources are unverified (TODO #2) and what each Phase 1 assumption on the result means.
19. 🟡 **CI and publishing:** `ci.yml` gains a job building the site with `--strict`; `docs.yml` publishes it to GitHub Pages from `main`, as hangtu's does. Pages has to be enabled in the repository settings (yours to do). A test fails if a public name has no reference entry, as in hangtu.

### Hand calculation (golden values)
The tunnel and trough of M1 (a) and case A of M1 (b) (utility at station 50, offsets −20 to 20, surface, spacing 5 m): D = 6.0 m, z₀ = 20.0 m, A = π D²/4 = 28.274334 m². With i = k z₀ and S_max = V_L A / (√(2π) i), the extremes on a utility that reaches ±√3 i are, from M1 (a)'s derivatives:
- settlement S_max at o = 0;
- compression −S_max / z₀ at o = 0 (du_n/do at the axis);
- tension 2 S_max e^(−3/2) / z₀ at o = ±√3 i, the first at distance 20 − √3 i;
- sagging −S_max / i² at o = 0; hogging 2 S_max e^(−3/2) / i² at o = ±√3 i.

| V_L | k | i (m) | S_max (m) | tension (at m) | compression | hogging (1/m) | sagging (1/m) |
|---|---|---|---|---|---|---|---|
| 1 % | 0.5 | 10 | 1.1279827e-2 | 2.5168697e-4 (2.6794919) | −5.6399136e-4 | 5.0337393e-5 | −1.1279827e-4 |
| 2 % | 0.5 | 10 | 2.2559654e-2 | 5.0337393e-4 (2.6794919) | −1.1279827e-3 | 1.0067479e-4 | −2.2559654e-4 |
| 1 % | 0.4 | 8 | 1.4099784e-2 | 3.1460871e-4 (6.1435935) | −7.0498920e-4 | 9.8315221e-5 | −2.2030913e-4 |
| 2 % | 0.4 | 8 | 2.8199568e-2 | 6.2921741e-4 (6.1435935) | −1.4099784e-3 | 1.9663044e-4 | −4.4061825e-4 |

Settlement, compression and sagging are at distance 20 m in every row. The first row is case A's `governing()`.

### Acceptance criteria
Tolerance 1e-6 relative for the hand values, as in M1 (a) and (b).

1. **`governing()`:** case A's five rows as the table's first row, with units, distances and verdicts; a result with no tension gives NaN and verdict None for `largest_tension`; a tie goes to the smaller distance; a result without curvature columns has no curvature rows; `repr()` reads it and prints "none".
2. **`source` and `asset`:** set by `movement_profile`; absent from `repr()`, `to_dict()` and `to_frame()`; two results differing only in them compare equal.
3. **Sweep, grid:** V_L {1 %, 2 %} × k {0.4, 0.5} gives four rows in product order, with the table's values; varied inputs as used (0.01, 0.02); units in attrs; `fixed_inputs` holds the tunnel's, the utility's and `spacing`, and not `volume_loss` or `trough_width_parameter`.
4. **Sweep, paired:** V_L [1 %, 2 %] with k [0.5, 0.4] gives two rows, the table's rows 1 and 4.
5. **A sweep row equals a direct call** (SPEC §11): every governing value and the validity of each row equal those of `run(**inputs)` called directly.
6. **Sweep errors:** a run through the bore records its error and NaN values while the others complete; every run raising raises the first error; a varied input `run` ignores raises naming it; an input outside `vary` that changes between runs raises naming it; `mode` missing with two inputs, given with one, or unknown raises; four inputs, an empty sequence, or unequal paired lengths raise before any run.
7. **Profile figure:** returns a figure and four axes; the plotted lines equal the result's columns in display units (settlement in mm, strain in µε, curvature in 1/km); with `display_units={"displacement": "m"}` they equal the columns in m; governing values marked at their distances; case C shaded over 0–40 m with the flag's reason under the figure; for case D, no offset axis; with `axs=` given, no new figure is created.
8. **Cross-section figure:** returns a figure and two axes; the trough curve matches the source's settlement at the surface at sampled offsets; the utility's stations marked from `values`; the tunnel circle at offset 0 and depth 20 m with radius 3 m; the utility band at its depth and offsets; a direct (unbuilt) utility raises, naming the plan figure.
9. **No global state:** `matplotlib.rcParams` are unchanged after drawing either figure.
10. **Display units:** an unknown kind raises listing the four; `{"strain": "m"}` raises a dimensionality error; `gs.units.microstrain` converts as 1e-6.
11. **Figures by eye:** the PNGs of decision 16, committed and looked at.
12. **Docs site:** `prepare_site.py` runs every example; `zensical build --clean --strict` passes locally and in CI; every public name has a reference entry (test).
13. **Docstrings** of every new public name state inputs, outputs with units and conventions; ruff's numpy docstring rules pass.
14. **Dependencies:** `matplotlib` with its floor passing the `lowest` job; mypy strict passes.

## Plan

Eight build commits, each with ruff check, ruff format check, mypy and pytest green, and each near 300 changed lines: source, docstrings and tests for one piece. The result changes and `gs.sweep` come first, since the figures and docs need them; then the figures; then a pause for the user to look at them, since the plots may change; then the docs site and pages, built around the settled figures.


### 1. `M1 (c): add governing values and the result's source and asset`
- `src/garisenda/_result.py`: `source` and `asset` fields (`field(default=None, repr=False, compare=False)`), left out of `to_dict()`/`to_frame()`; `governing()` (decisions 2–3) replacing the `EXTREMES` loop, with the NaN rule and ties to the smaller distance; `__repr__` reads `governing()` and prints "none".
- `src/garisenda/profile/_movement_profile.py`: pass `source=source, asset=utility`.
- Tests: `tests/test_result.py` (no tension → NaN/None, tie, absent columns, "none"); `tests/profile/test_movement_profile.py` (case A's `governing()` = hand table row 1; AC 2 equality and views). AC 1, 2.

### 2. `M1 (c): add gs.sweep`
- `src/garisenda/_sweep.py`: `sweep(run, *, vary, mode=None)` (decisions 4–8): argument checks before any run; `itertools.product` / `zip`; per run, the varied-input check against `result.inputs` (convert the given value with `garisenda._units.to_si` into the record's unit, 1e-12 relative) and the fixed-input check against the first successful run; error rows; all-failed raises the first; table columns and `attrs` (`units`, `run`, `mode`, `vary`, `fixed_inputs` in `to_dict()`'s input form; reuse that conversion from `_result.py` as a helper rather than duplicating it).
- `src/garisenda/__init__.py`: export `sweep`.
- Tests: `tests/test_sweep.py`: grid and paired against the hand table (AC 3, 4); each row equals a direct call (AC 5); errors (AC 6), including a utility-depth sweep through the bore.

### 3. `M1 (c): add the plot framework and microstrain`
- `pyproject.toml`, `uv.lock`: `matplotlib>=3.8` (hangtu's floor); the pyparsing deprecation filters hangtu needs on that floor, only if the `lowest` run shows them.
- `src/garisenda/_units.py`: define `microstrain = 1e-6 = µε` (decision 15).
- `src/garisenda/plot/__init__.py`, `plot/_style.py` (house style as an `rc_context`, no global state), `plot/_display.py` (resolve `display_units` per kind with defaults m, mm, microstrain, 1/km; unknown kind or wrong dimension raises; `Quantity (unit)` labels; a conversion factor from the SI column unit).
- `tests/conftest.py`: Agg backend. Tests `tests/plot/test_display.py`: AC 10.

### 4. `M1 (c): add the profile figure`
- `src/garisenda/plot/_profile.py`: `profile(result, *, axs=None, display_units=None) -> (fig, axs)` (decisions 9–11): four panels on shared x (settlement y down; along and lateral; strain along; vertical and lateral curvature), governing marks from `governing()`, critical ticks, verdict shading with the flag reasons under the figure, top offset axis for a built utility.
- Tests `tests/plot/test_profile.py`: AC 7, AC 9 (rcParams unchanged), `axs=` creates no figure.

### 5. `M1 (c): add the cross-section figure`
- `src/garisenda/plot/_cross_section.py`: `cross_section(result, *, axs=None, display_units=None) -> (fig, axs)` (decisions 12–13): trough panel from `result.source.evaluate` at the surface on 401 offsets over the wider of the utility's offsets and ±3i, horizontal movement toward the axis, stations from `values`, ±i marked; section panel to scale with bore, axis, utility band, ground line; raises for an unbuilt utility or a source without a `tunnel`.
- Tests `tests/plot/test_cross_section.py`: AC 8, AC 9.

**Pause after step 5:** save PNGs of both figures for cases A, C and D (where they apply) to the scratchpad and show them to the user. Changes they ask for are made here, with the spec's decisions 10–12 updated in the same commit, before step 6.

### 6. `M1 (c): set up the docs site`
- `pyproject.toml`, `uv.lock`: `docs` group, `zensical==0.0.70`, `mkdocstrings-python>=2.0.9`.
- `zensical.toml`, `docs/prepare_site.py` (hangtu's `run_example`/`run_examples`, no logo), `docs/site/index.md`, `install.md`, `docs/site/reference/*.md` (`gs`, `gs.sources`, `gs.utilities`, `gs.plot`), `.gitignore` for `build/` and `docs/site/img/generated/`.
- `.github/workflows/ci.yml`: a `docs` job as hangtu's (strict build, griffe warnings fail); `.github/workflows/docs.yml`: publish to Pages from `main`.
- Tests `tests/docs/test_site.py`: every example runs clean in an empty folder; every name in the `__all__` of `garisenda`, `.sources`, `.utilities`, `.plot` (less `__version__`, `units`) has a `::: ` entry. AC 12 (part).

### 7. `M1 (c): write M1's user docs`
- `docs/site/getting-started.md`, `conventions.md`, `figures/profile.md`, `figures/cross-section.md`, `guides/sweep.md`, each with its example in `docs/site/examples/`; nav in `zensical.toml`. Invented geometry only; the getting-started page states the trough's sources are unverified (TODO #2) and explains each Phase 1 assumption on the result.
- `README.md`: link to the site.
- Verify: `uv run --group docs python docs/prepare_site.py && uv run --group docs zensical build --clean --strict`. AC 12.

### 8. `M1 (c): close out`
- `lowest` run locally (`UV_RESOLUTION=lowest-direct`, scratch env), then `git checkout uv.lock`.
- `docs/img/m1c/*.png`: the figures of decision 16, looked at (AC 11).
- Work file `## Result`: each AC with evidence.
- `SPEC.md`: settled items decided (§5.1 governing, §5.3 sweep, §9 contract and figures if the user approved them, §12.1 matplotlib, §12.3 docs site); §12.4 M1 done.
- `CLAUDE.md`: next is M2; the docs commands (`uv sync --group docs`, prepare and build); `docs/site/` is published and the rest of `docs/` internal; any recurring lesson.

### Verification
- Each step: the CI command from `CLAUDE.md`.
- Step 5: the figures looked at by the user and by me.
- Steps 6–7: the docs build with `--strict` locally; CI's docs job on push.
- Step 8: the floors run; every AC reported met or not in `## Result`.
