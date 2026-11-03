"""Write the docs site's generated files before a build.

Spec: docs/work/m1c-figures-sweep-docs.md, decision 17. Every figure on the
site comes from a page example that runs.

Run from the repo root, then build:

    uv run --group docs python docs/prepare_site.py
    uv run --group docs zensical build --clean --strict
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SITE = Path(__file__).parent / "site"
EXAMPLES = SITE / "examples"
GENERATED = SITE / "img" / "generated"


def run_example(script: Path, folder: Path) -> subprocess.CompletedProcess[str]:
    """Run a page example in ``folder`` as a user would, in a fresh Python."""
    # Piped output on Windows defaults to cp1252, which can't encode the
    # symbols (µε, ±) that results print.
    env = {**os.environ, "MPLBACKEND": "Agg", "PYTHONIOENCODING": "utf-8"}
    env.pop("PYTHONWARNINGS", None)
    return subprocess.run(
        [sys.executable, str(script)],
        cwd=folder,
        env=env,
        capture_output=True,
        encoding="utf-8",
        timeout=300,
        check=False,
    )


def run_examples() -> None:
    """Run each page example and keep its figures and printed output.

    Figures (``<name>*.png``) and the output (``<name>.txt``) go to
    ``img/generated/``, where a page shows them below the code.
    """
    GENERATED.mkdir(parents=True, exist_ok=True)
    for script in sorted(EXAMPLES.glob("*.py")):
        with tempfile.TemporaryDirectory() as tmp:
            done = run_example(script, Path(tmp))
            if done.returncode != 0 or done.stderr:
                sys.exit(f"Example {script.name} failed or warned:\n{done.stderr}")
            for figure in Path(tmp).glob("*.png"):
                shutil.copy(figure, GENERATED / figure.name)
            if done.stdout:
                output = GENERATED / f"{script.stem}.txt"
                output.write_text(done.stdout, encoding="utf-8")
        print(f"Ran {script.name}")


def main() -> None:
    """Write every generated file."""
    run_examples()


if __name__ == "__main__":
    main()
