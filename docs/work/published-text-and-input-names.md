# TODO #19 and #22: internal references in published text, and input names by owner

A short intent and a plan, without a separate spec (agreed 2026-11-10). Branch `published-text-and-input-names` off `main`.

## Intent

- **Goal (#19):** no text a user or reviewer reads contains an internal reference (`SPEC §`, `TODO #`, a milestone id such as `M3 (b)`, "spec decision 14"). The engineer signing off can't follow them. Replace each with what it points to: the statement itself, the docs page, or the published source.
- **Goal (#22):** an input record's name says who owns it, so an audit table or memo built from `result.inputs` can't mix up the tunnel's `diameter` and the utility's.
- **Why:** both came out of the agent-use review (2026-11-09).
- **Approved (2026-11-10):** every string is tested; a single tunnel's inputs stay bare; breaking changes are fine (garisenda has one user so far).
- **Out of scope:** comments and tests, which are internal and keep their references. The released sections of `CHANGELOG.md` (history). TODO #15, #16 and #17, decided 2026-11-10 and recorded in `docs/TODO.md`, are a separate unit.
- **SPEC sections touched:** §2.2 (citations), §5.1 (the result's inputs), §5.3 (sweep names), §8.5 (naming).

### Decisions (intent review, 2026-11-10)

1. **What counts as published text (#19):** every string literal in `src/garisenda` (docstrings, assumptions, sources, caveats, error and warning messages, f-string parts), and the Markdown and example scripts in `docs/site/`, plus `README.md`. One rule with no "is this rendered?" judgment, so private docstrings are cleaned too. Comments (`#`) are allowed to keep internal references.
2. **The pattern the test forbids:** `SPEC §`, `TODO #`, a milestone id (`\bM\d+\b`, which also catches `M3 (b)`), and `spec decision` / `spec's case`. If the milestone pattern catches an unrelated string, the string is rephrased rather than the pattern loosened.
3. **How each kind of reference is replaced:**
   - A convention (`SPEC §8.1`, §8.2, §6): drop it, or point to the Conventions page (`docs/site/conventions.md`: Plan, Depth and elevation, Signs, Units) where the text relies on it.
   - A Phase 1 assumption (`SPEC §1.3`): drop it; the sentence states the assumption already.
   - Unverified sources (`TODO #2`): "not yet verified against the sources", keeping the 🔬.
   - A derivation in a work file ("derived in the M3 (a) spec"): "derived here" with the docstring's own steps, which it already gives, and "not from a published source" where that's true. The docs guides' "What it assumes" sections say the same, if they don't already.
   - A worked case in a work file (the pullout caveat's "M3 (b) spec's case J-A"): state the case's inputs inline (taken from `docs/work/m3b-jointed-pipes.md`, case J-A), so the number can be checked without the work file.
   - A later milestone ("comes in M5", "the plan figure (M5)"): "isn't supported yet" / "a later release". The error still says what to do now.
   - A design decision ("spec decision 14", "intent decision 2"): drop the reference; keep the reason if the text needs one.
4. **Who gets a prefix (#22):** the utility's inputs are named `utility.<name>` (`utility.diameter`, `utility.depth`, `utility.vertices`), added where `movement_profile` combines the inputs, as `Superposition` prefixes its sources' inputs. The source's inputs stay as they are: bare for a single source, `<name>.` in a superposition. Bare means the source, so `vary={"volume_loss": ...}` in every guide still works. A check's own inputs (`interval`, limits, `pipe_type`, `pipe_length`) and the profile's settings (`spacing`) stay bare. The alternative, prefixing a single tunnel's inputs with `tunnel.`, would break every sweep in the docs.
5. **A superposition source named `utility`** is refused, since its inputs would collide with the utility's.
6. **Sweeps over a utility input** name it `utility.depth`, so `run` takes `utility_depth` (sweep's rule: dots become underscores). This is a breaking change, recorded in `CHANGELOG.md`.

## Plan

All steps are on Opus: #19 rewrites citations and reference docstrings, and #22 is too small to justify a separate session. After each step, run `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest`.

### 1. `published text: drop internal references from sources` (Opus)
- `src/garisenda/sources/`: `__init__.py`, `_critical.py`, `_segment.py`, `_movement.py`, `_superposition.py`, `_tunnel.py`, `_transverse.py`, `_transverse_trough.py`, `_trough_width.py`.
- `_transverse.py` `SOURCES` and `ASSUMPTIONS`, and `_transverse_trough.py` `ASSUMPTIONS` (`TODO #2`, `SPEC §1.3`): use the replacements in decision 3.
- `_transverse_trough.py:294` ("the polynomials P_ab and R_ab of the M2 (b) spec"): give the polynomials or their source in the docstring. Read `docs/work/m2b-subsurface.md` for where they come from, and don't cite from memory.
- Tests: `tests/sources/test_transverse.py:230` (`"TODO #2" in method.source`) asserts the new wording instead. Update any test that matches an assumption or error text that changed.

### 2. `published text: drop internal references from profiles, utilities and presets` (Opus)
- `src/garisenda/profile/` (`__init__.py`, `_movement_profile.py`: the `(the utility checks are M3)` docstrings are stale too, now that the checks exist), `src/garisenda/utilities/` (`__init__.py`, `_utility.py`, `_continuous_pipe.py`, `_jointed_pipe.py`), `src/garisenda/presets.py`.
- `PULLOUT_CAVEAT` and the `presets` docstring (decision 3, case J-A).
- The `_utility.py` polyline error ("until M5") and `_jointed_pipe.py`'s "given joint locations come with M5".
- Tests: update the matching tests in `tests/utilities/`, `tests/profile/` and `tests/test_presets.py`.

### 3. `published text: drop internal references from the core and plots, and test it` (Opus)
- `src/garisenda/_units.py`, `_result.py`, `_sweep.py`, `_inputs.py`, `plot/` (`__init__.py`, `_display.py`, `_style.py`, `_profile.py`, `_cross_section.py`: the "(M5)" errors and "M1's gids" / "M1's surface width").
- `README.md` and the opening paragraph of `CHANGELOG.md` (`TODO #2`); `docs/site/` has none today.
- New `tests/test_published_text.py`:
  - Walks every `.py` in `src/garisenda` with `ast` and checks each `str` constant (which covers docstrings and f-string parts) against decision 2's pattern; a failure names the file, line and match.
  - Checks `docs/site/**/*.md`, `docs/site/examples/*.py` and `README.md` as text, outside comments in the scripts.
  - Before writing it, confirm the pattern finds every hit of today's `grep` on a copy of `main`, then that the test passes once steps 1–3 are done.
- Check: the strict docs build (`uv run --group docs python docs/prepare_site.py && uv run --group docs zensical build --clean --strict`), since docstrings changed.

### 4. `inputs: name the utility's inputs utility.<name>` (Opus)
- `src/garisenda/profile/_movement_profile.py` (`inputs=(*source.inputs, *utility.inputs, ...)`, about line 185): `replace(entry, name=f"utility.{entry.name}")` for each utility input. Update the docstring's description of `inputs`.
- `src/garisenda/sources/_superposition.py`: refuse a source named `utility` (decision 5), with a message saying why.
- Check results (`_continuous_pipe.py`, `_jointed_pipe.py`) take the profile's inputs, so they inherit the names. Check that nothing looks a utility input up by its bare name (`grep -rn '"diameter"\|"depth"\|"vertices"\|"station"\|"offset"' src/`).
- Tests:
  - New, in `tests/profile/test_movement_profile.py`: a single-tunnel result has `diameter` (the tunnel's) and `utility.diameter`, and no two inputs share a name. The same for a twin-tunnel result (`north.diameter`, `south.diameter`, `utility.diameter`), and for both check results.
  - New, in `tests/sources/test_superposition.py`: a source named `utility` is refused.
  - `tests/test_sweep.py:184` (`vary={"depth": ...}`): becomes `vary={"utility.depth": ...}`, with `run` taking `utility_depth`. Check the other sweep tests over utility inputs, and the column names they assert.
  - Any test that looks up the utility's inputs by bare name.
- `docs/site/`: check the guides and examples for a utility input named bare, or a sweep over one (none found today), and the inputs table in the generated `*.txt` outputs after `prepare_site.py`.

### Close (in step 4's commit)
- `CHANGELOG.md`: add `## Unreleased` with: the utility's inputs are named `utility.<name>`, and a sweep over one names it so (`vary={"utility.depth": ...}`, with `run` taking `utility_depth`); a source in a superposition can't be named `utility`; and messages, assumptions and docstrings no longer refer to internal documents.
- `SPEC.md` §5.1 (inputs) and §5.3 (sweep names): record the owner prefix if they describe input naming. §2.2: add the rule that published text holds no internal references, and that the test enforces it.
- `docs/TODO.md`: delete #19 and #22.
- `CLAUDE.md` Conventions: one line, "Published text (string literals in `src/`, `docs/site/`, `README.md`) has no `SPEC §`, `TODO #` or milestone references; comments may keep them. `tests/test_published_text.py` checks it."
- What CI runs, the strict docs build, and Python 3.13 and 3.14. Merge with `--no-ff` after approval.
