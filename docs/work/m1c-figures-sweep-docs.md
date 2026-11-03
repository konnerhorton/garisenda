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
