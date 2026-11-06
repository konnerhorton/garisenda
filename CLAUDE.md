# garisenda

Open-source Python library for ground movements from tunneling and their effect on utilities and structures: greenfield closed-form and empirical methods, traceable, with figures for every result, flagging where numerical analysis is needed (SPEC §1). Published and imported as `garisenda` (`import garisenda as gs`). Status: `SPEC.md` is in draft; M0, M1, M2 and M3 (a) are done (SPEC §12.4). Phase 1 is a greenfield assessment with one analysis, always in 3D; spreadsheet-style input (station and offset) builds perpendicular 3D assets, and real polylines come after (SPEC §1.3, §3). Next: M3 (b), jointed pipes (joint rotation and pullout, pipe lengths, the iron limit presets), built on `gs.check_continuous_pipe`'s pattern; its open questions are TODO #4–#6.

## Where things are
- `SPEC.md`: product spec and cross-cutting decisions. Read the relevant section before designing anything.
- `docs/work/<id>.md`: intent, spec and plan for each unit of work (the spec-driven-development skill). Files for merged units are history.
- `docs/drafts/`: notes for later work, including `scope-discussion.md`. Not decisions unless marked "decided".
- `docs/reference/sources.md`: the bibliography, each source with its key and the date it was verified (SPEC §2.2).
- `docs/TODO.md`: research items and pending decisions, referenced as "TODO #n".
- `docs/site/`: the published docs site (Zensical); each page's example is a script in `docs/site/examples/`. The rest of `docs/` is internal.

## Commands
- `uv sync`: install
- `uv run pytest`: the tests (warnings are errors; assert expected ones with `pytest.warns`)
- `uv run ruff check . && uv run ruff format .`: lint and format
- `uv run mypy`: type check `src/` in strict mode; a `# type: ignore` names its error code and says why
- `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest`: what CI runs (`.github/workflows/ci.yml`)
- Newer Pythons, before a merge (CI tests 3.12–3.14; the local default is 3.12): `UV_PROJECT_ENVIRONMENT=<scratch dir> uv run --python 3.13 pytest`, and the same for 3.14
- Oldest allowed dependency versions: `UV_RESOLUTION=lowest-direct UV_PROJECT_ENVIRONMENT=<scratch dir> uv run pytest`, then `git checkout uv.lock`, because it rewrites the lock (commit an intended lock change first, or the checkout discards it)
- Docs: `uv sync --group docs`, then `uv run --group docs python docs/prepare_site.py && uv run --group docs zensical build --clean --strict` (CI fails on any `griffe:` warning too). Look at the figures in `docs/site/img/generated/` once the plot changes are done and the tests pass, not after each change; or check them in a new session ("check the figures against the spec")
- Release (needs approval): set `version` in `pyproject.toml`, `uv lock`, commit and push to `main`; rehearse with `gh workflow run release.yml --ref main` (TestPyPI); then `git tag vX.Y.Z && git push origin vX.Y.Z` (PyPI; the `pypi` environment waits for your approval on GitHub)

## Conventions
- **Judgments have no defaults.** A judgment is a required keyword-only argument. Standard values come only as named, cited presets the user passes explicitly (SPEC §4).
- **Sources produce a movement field; assessments consume it** as a profile along the asset, keyed by distance along it (SPEC §3).
- **Every result has the same shape** and a validity verdict; outside a method's range it is flagged, not raised (SPEC §2.5, §5).
- **Every assessment has a figure** (SPEC §9).
- **Test a source on segments at any angle, not only perpendicular to the tunnel**: an oblique segment has a lateral component, and its peaks (M1's lateral-curvature peaks) are missed by perpendicular-only hand calculations.
- **Never fill missing data**, never drop it silently (SPEC §10).
- **Names are written out in full**, no units in names, American spelling (SPEC §8.5).
- **Every input goes through `garisenda._inputs.record()`**, which unwraps `Sourced`, converts with `to_si()` and returns the input record, **or, for a named method object, `record_method()`**, which records its name. Percent-style ratios and angles use `plain_number="refuse"` (SPEC §6).
- **Code and tests run on the dependency floors** (numpy 1.26): no numpy 2-only functions such as `numpy.trapezoid`. The `lowest` job catches it, the default run doesn't.
- **Docstrings use ASCII `-` for minus** (ruff RUF002); the specs keep `−`.
- **Figures draw with `garisenda.plot._style.style()`** (an `rc_context`), never by setting `rcParams`; tests check `rcParams` are unchanged. Panels are found in tests by artist `gid`.
- **On the pint floor (0.24.4), write units with non-ASCII symbols as strings** (`u.Quantity(1, "µε")`): Python normalizes `µ` in an identifier to Greek mu, which old pint doesn't know.

## Git and commits
- Defaults from the spec-driven-development skill: a branch per unit off `main`, merged with `--no-ff`; a commit per loop step; stage files by name; `<scope>: <imperative summary>`.
- **Approval:** Claude commits intermediate build steps of an approved plan without asking. Intent, spec and plan commits, docs-only commits, branches, merges and pushes need approval first.
- **The repo is public.** No project data, client names or private sources in code, docs or commits. Real crossings are checked locally on the work machine only.

## Workflow rules
- If a change alters a decision recorded in `SPEC.md` or a feature spec, update that file in the same commit.
- Don't renumber `SPEC.md` sections.
- Test against the acceptance criteria in the feature's spec.
- **Docs as we go:** each milestone's close-out writes the user docs and figures for what it built (SPEC §9, §12.3).
- Cite sources as `SPEC.md` §2 says, checked against the source itself. Never cite from memory. Digitized charts are never shipped (SPEC §2.3).
