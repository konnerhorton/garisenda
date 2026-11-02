# garisenda

Open-source Python library for ground movements from tunneling and their effect on utilities and structures: greenfield closed-form and empirical methods, traceable, with figures for every result, flagging where numerical analysis is needed (SPEC §1). Published and imported as `garisenda` (`import garisenda as gs`). Status: `SPEC.md` is in draft; M0 (scaffolding) is done, no analysis code yet. Phase 1 is a greenfield assessment with one analysis, always in 3D; spreadsheet-style input (station and offset) builds perpendicular 3D assets, and real polylines come after (SPEC §1.3, §3). Next: M1 (framework, the profile along an asset, the idealized straight tunnel and station-and-offset builder, the transverse trough).

## Where things are
- `SPEC.md`: product spec and cross-cutting decisions. Read the relevant section before designing anything.
- `docs/work/<id>.md`: intent, spec and plan for each unit of work (the spec-driven-development skill). Files for merged units are history.
- `docs/drafts/`: notes for later work, including `scope-discussion.md`. Not decisions unless marked "decided".
- `docs/TODO.md`: research items and pending decisions, referenced as "TODO #n".

## Commands
- `uv sync`: install
- `uv run pytest`: the tests (warnings are errors; assert expected ones with `pytest.warns`)
- `uv run ruff check . && uv run ruff format .`: lint and format
- `uv run mypy`: type check `src/` in strict mode; a `# type: ignore` names its error code and says why
- `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest`: what CI runs (`.github/workflows/ci.yml`)
- Oldest allowed dependency versions: `UV_RESOLUTION=lowest-direct UV_PROJECT_ENVIRONMENT=<scratch dir> uv run pytest`, then `git checkout uv.lock`, because it rewrites the lock (commit an intended lock change first, or the checkout discards it)

## Conventions
- **Judgments have no defaults.** A judgment is a required keyword-only argument. Standard values come only as named, cited presets the user passes explicitly (SPEC §4).
- **Sources produce a movement field; assessments consume it** as a profile along the asset, keyed by distance along it (SPEC §3).
- **Every result has the same shape** and a validity verdict; outside a method's range it is flagged, not raised (SPEC §2.5, §5).
- **Every assessment has a figure** (SPEC §9).
- **Never fill missing data**, never drop it silently (SPEC §10).
- **Names are written out in full**, no units in names, American spelling (SPEC §8.5).

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
