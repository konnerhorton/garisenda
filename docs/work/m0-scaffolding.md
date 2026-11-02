# M0: scaffold the package, lint, tests and CI

## Intent

### Goal
`garisenda` is an installable, empty package (`import garisenda as gs` works and reports its version), with lint, format, type and test checks that run with one command each, and CI running them on every supported platform and Python version. After this, M1 can start writing code.

### Why
- SPEC §12.4: M0 is the first milestone, and every later milestone needs somewhere to put code and tests, and a CI that shows they pass.
- CLAUDE.md's "Commands" section is still "Set by M0".
- The setup follows hangtu, the author's other library, so the two work the same way. What hangtu learned is kept, such as setting `UV_RESOLUTION` for the oldest-dependencies job so `uv run` doesn't re-resolve to the newest versions. The one deliberate difference is a type checker (decision 4).

### Constraints
- **SPEC §12.1:** Python ≥ 3.12 and `uv`. CI on Windows, macOS and Linux × Python 3.12–3.14, with a job on the oldest allowed dependency versions. Dependencies are added when code first uses them, so M0 has **no runtime dependencies**.
- **SPEC §12.2:** `src/` layout, package `garisenda`, tests mirroring the package.
- **SPEC §11:** pytest; hypothesis for property tests, added when M1 first uses it.
- **SPEC §1.1:** MIT license, public repo. No project data anywhere (CLAUDE.md).

### Out of scope
- **Modules from SPEC §12.2** (`sources`, `profile`, `utilities`, ...): each comes with the milestone that first puts code in it, not as empty files now.
- **The docs site** (Zensical) and its CI job: M1, per SPEC §12.3.
- **Claiming `garisenda` on PyPI** and the release workflow, including hangtu's wheel and examples tests: TODO #8, its own unit after M0.
- **Creating the GitHub repo:** TODO #9, yours. See decision 7.
- **`.gitattributes`:** hangtu needs it for byte-compared test data; garisenda has none yet.

### SPEC sections touched
- **SPEC §12.1:** record the tooling that binds later milestones (ruff rules, mypy strict, warnings as errors), in the spec commit.
- `CLAUDE.md`: fill in "Commands" at close-out.

### Decisions (intent review, 2026-11-02)
1. **Build backend `uv_build`**, as in hangtu.
2. **Version single-sourced in `pyproject.toml`**, starting at `0.0.0`, read at runtime with `importlib.metadata` (`__version__ = version("garisenda")`), as in hangtu, so it can't drift from the package metadata.
3. **Ruff for lint and format with hangtu's rule set:** E, F, W, I, UP, B, SIM, RUF and D in numpy convention (SPEC §8.5 makes docstrings the reference entry, so their structure is checked from the start). Tests are exempt from D; Markdown isn't formatted. NPY is added when numpy becomes a dependency.
4. **mypy in strict mode on `src/`**, which hangtu doesn't have. The judgment-argument rule (SPEC §4) and the result shape (§5.1) are contracts across modules, and typed signatures catch a wrong kind of input before a test has to. Accepted cost: pint and pandas types are loose, so some `# type: ignore` comments, each with its reason.
5. **Dev tools in a uv `dev` dependency group** (pytest, ruff, mypy now; hypothesis and pytest-xdist when tests need them). No pre-commit hooks; CI is the gate. As in hangtu.
6. **Strict pytest, as in hangtu:** `--strict-markers`, `--strict-config`, `--import-mode=importlib`, `xfail_strict`, and warnings as errors, so a stray warning fails the run rather than scrolling past. An expected warning is asserted with `pytest.warns`.
7. **CI is hangtu's `ci.yml` minus the docs job:** the OS × Python matrix with `uv sync --locked`, ruff check, ruff format check, mypy and pytest; a `lowest` job with `UV_RESOLUTION: lowest-direct` as a job environment variable; `concurrency` and read-only `permissions`. "CI green" means green on GitHub, which needs the public repo (TODO #9) and a push, both yours to approve. If the repo isn't ready at close-out, M0 closes with every check passing locally, and the GitHub run carries over to TODO #9.
8. **Files:** `pyproject.toml` (with authors, `license-files`, project URLs and classifiers as in hangtu), `uv.lock` and `.python-version` (3.12), both committed; `src/garisenda/__init__.py`, `src/garisenda/py.typed`, `tests/test_package.py`, `.github/workflows/ci.yml`, `LICENSE` (MIT, Konner Horton), a short `README.md`, and `.gitignore` adapted from hangtu's.

## Spec

No topic doc holds this, so the spec is here. Nothing in M0 is numerical, so there are no sources or golden values.

### Changes
- **SPEC §12.1:** Python and `uv` marked decided; a new bullet records the tooling that binds later milestones (hangtu's setup, warnings as errors, mypy strict and how `# type: ignore` is written). In this commit.
- **CLAUDE.md, Commands:** filled in at close-out, in hangtu's form (install, run tests, lint and format, types, what CI runs, the oldest-dependencies check run locally).
- **New files:** as listed in intent decision 8.

### Decisions
1. **`requires-python = ">=3.12"` and classifiers for 3.12, 3.13 and 3.14**, matching the CI matrix (SPEC §12.1). Development status "2 - Pre-Alpha".
2. **`dependencies = []`.** The first runtime dependency arrives with the code that uses it (SPEC §12.1).
3. **`uv_build` pinned to the 0.9 series** (`>=0.9.9,<0.10`), as in hangtu, so a new major build backend can't change the build silently.
4. **`gs.__version__` is the only public name in M0.** `__all__ = ["__version__"]`.
5. **mypy configuration:** `strict = true`, `files = ["src"]`, `python_version = "3.12"`, `warn_unreachable = true`, and `enable_error_code` for `ignore-without-code` and `redundant-expr`, so every `# type: ignore` names its code (SPEC §12.1). Tests aren't type-checked: they exercise wrong inputs on purpose.
6. **The CI matrix job runs four checks in order:** ruff check, ruff format check, mypy, pytest. `fail-fast: false`, so one platform's failure doesn't hide another's. The `lowest` job runs pytest only, on Linux and Python 3.12.
7. **CI triggers:** push to `main` and every pull request, as in hangtu.
8. **`.gitignore`** is hangtu's, minus the entries that belong to hangtu alone (public test data, its generated docs pages, `.sqlite`).

### Acceptance criteria
1. **Installs from a clean clone:** `uv sync --locked` succeeds, and `uv run python -c "import garisenda as gs; print(gs.__version__)"` prints `0.0.0`.
2. **One source for the version:** a test checks that `gs.__version__` equals `importlib.metadata.version("garisenda")` and the `version` in `pyproject.toml`.
3. **No runtime dependencies:** a test checks that `pyproject.toml` lists none.
4. **Typed package:** `py.typed` is in the built wheel; a test checks it in the installed package, and `uv build` is run once at test time with the wheel's file list checked.
5. **Lint and format clean:** `uv run ruff check .` and `uv run ruff format --check .` report nothing.
6. **Types clean:** `uv run mypy` passes in strict mode with no `# type: ignore`.
7. **Strict pytest works:** `uv run pytest` passes. Checked by hand at test time, not committed: a test that emits an unasserted warning fails, and an unknown marker is an error.
8. **Oldest dependencies:** the `lowest` job's command, run locally as CLAUDE.md will document it, passes and leaves `uv.lock` unchanged.
9. **CI green on GitHub** on all nine matrix jobs and `lowest`. If the repo (TODO #9) isn't ready at close-out, the workflow is reviewed and every job's commands pass locally on Linux, and this criterion is carried to TODO #9 as unmet.
10. **Commands documented:** every command in CLAUDE.md's Commands section runs as written.
11. **License and metadata:** `LICENSE` is the MIT text with "Konner Horton"; the built wheel's metadata shows `License-Expression: MIT`, the author and the project URLs.
