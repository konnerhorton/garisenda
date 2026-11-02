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
