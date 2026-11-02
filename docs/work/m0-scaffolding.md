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

## Plan

Three build commits, each with ruff check, ruff format check, mypy and pytest green.

### 1. `M0: add the package, its checks and tests`
- `pyproject.toml`: hangtu's layout and metadata (version `0.0.0`, no dependencies, `dev` group with pytest, ruff and mypy, `uv_build>=0.9.9,<0.10`), ruff, pytest and mypy configured as in spec decisions 1–5.
- `uv.lock`, `.python-version` (3.12).
- `src/garisenda/__init__.py` (`__version__`, `__all__`), `src/garisenda/py.typed`.
- `LICENSE`, `README.md`, `.gitignore`.
- Tests: `tests/test_package.py`: the version matches `importlib.metadata` and `pyproject.toml` (AC 2); no runtime dependencies (AC 3); `py.typed` is in the installed package (AC 4).

### 2. `M0: add CI`
- `.github/workflows/ci.yml`: hangtu's minus the docs job; the matrix runs `uv sync --locked`, ruff check, ruff format check, mypy and pytest; `lowest` sets `UV_RESOLUTION: lowest-direct` and runs pytest.
- Tests: each job's commands run locally on Python 3.12, 3.13 and 3.14 (AC 9).

### 3. `M0: close out`
- `CLAUDE.md`: Commands section (AC 10) and the "Next" sentence.
- `docs/work/m0-scaffolding.md`: `## Result`, each acceptance criterion met or not, with evidence.
- `docs/TODO.md` #9: the GitHub CI run waiting on the repo, if it is.

## Result (2026-11-02)

Checked on Linux with Python 3.12.3, 3.13.0 and 3.14.0.

1. **Installs from a clean clone:** met. A fresh clone, `uv sync --locked`, prints `0.0.0`.
2. **One source for the version:** met. `test_version_has_one_source`.
3. **No runtime dependencies:** met. `test_no_runtime_dependencies`.
4. **Typed package:** met. `test_package_is_typed`; the wheel from `uv build` contains `garisenda/py.typed`.
5. **Lint and format clean:** met.
6. **Types clean:** met. mypy strict, no `# type: ignore` in `src/`.
7. **Strict pytest:** met, by hand. A test emitting an unasserted `UserWarning` fails; an unknown marker stops collection with an error.
8. **Oldest dependencies:** met. Passes with `UV_RESOLUTION=lowest-direct`; it rewrites `uv.lock` as expected, and `git checkout uv.lock` restores it.
9. **CI green on GitHub:** met. Not met at close-out because the repo didn't exist; after the first push, all nine matrix jobs and `lowest` passed (run 41426957716, 2026-11-02).
10. **Commands documented:** met. Each command in CLAUDE.md run as written.
11. **License and metadata:** met. Wheel metadata: `License-Expression: MIT`, author Konner Horton, four project URLs; `LICENSE` is in the wheel.

**For later milestones:** `mypy` was locked at 2.4.1, so its floor is `>=2.4`, the version the configuration was checked on. Dev-tool floors aren't exercised by the `lowest` job, which runs pytest only.

## Release (added 2026-11-02)

### Intent
Release `garisenda` 0.0.1 on PyPI, claiming the name (TODO #8), with hangtu's release workflow, so every later release is a tag. The PyPI and TestPyPI trusted publishers and the GitHub environments `pypi` and `testpypi` are set up. This closes TODO #8, and TODO #9 now that CI ran green on GitHub (run 41426957716). Out of scope: hangtu's `examples` job, because garisenda has no examples yet; it's added with the first example script.

### Decisions
1. **hangtu's `release.yml` without the `examples` job and `MPLBACKEND`.** A `v*` tag publishes to PyPI; a manual run publishes to TestPyPI as a rehearsal. Both use trusted publishing, so no token is stored. The tag must match the version in `pyproject.toml`. The tests run against the built wheel with `src/` removed, on three operating systems × Python 3.12 and 3.14, before either upload.
2. **Rehearse on TestPyPI before tagging**, because a version uploaded to PyPI can never be uploaded again.
3. **SPEC §12.1** records the release rule, as hangtu's SPEC does; CLAUDE.md gets the release commands.

### Acceptance criteria
12. **Release workflow:** `.github/workflows/release.yml` as in decision 1; a tag that doesn't match the version stops the run before anything is built.
13. **TestPyPI rehearsal:** a manual run succeeds, and `garisenda` 0.0.1 installed from TestPyPI imports and prints `0.0.1`.
14. **On PyPI:** the `v0.0.1` tag's run succeeds, and `garisenda` 0.0.1 installed from PyPI imports and prints `0.0.1`.

### Plan
1. `M0: add the release workflow`: `release.yml`; version `0.0.1` in `pyproject.toml` and `uv.lock`; SPEC §12.1; CLAUDE.md release commands; README install line; TODO #8 and #9 deleted; criterion 9 in Result marked met.
2. Merge to `main`, push, run the TestPyPI rehearsal from `main`, then tag `v0.0.1` and push the tag.
3. `M0: record the release`: criteria 12–14 with evidence in Result.

### Result (2026-11-02)
12. **Release workflow:** met. `release.yml` as in decision 1. The tag check ran and passed on `v0.0.1`; its failure path wasn't exercised.
13. **TestPyPI rehearsal:** met. Manual run 41428634918: build, six wheel tests and the TestPyPI upload passed; 0.0.1 installed from TestPyPI prints `0.0.1`.
14. **On PyPI:** met. Tag run 41428872221 passed after the `pypi` environment's required review was approved; 0.0.1 installed from PyPI prints `0.0.1`.

**For later releases:** the `pypi` environment requires a reviewer, so a tag's run waits at "publish to PyPI" until it's approved on GitHub.
