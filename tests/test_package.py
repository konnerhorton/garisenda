import importlib.metadata
import importlib.resources
import tomllib
from pathlib import Path

import garisenda as gs

PYPROJECT = tomllib.loads(
    (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
)


def test_version_has_one_source():
    assert gs.__version__ == importlib.metadata.version("garisenda")
    assert gs.__version__ == PYPROJECT["project"]["version"]


def test_only_allowed_runtime_dependencies():
    # SPEC §12.1 lists the dependencies; adding another needs a decision there.
    allowed = {"pint", "numpy", "pandas", "matplotlib"}
    names = {
        requirement.split(">")[0].split("=")[0].split("<")[0].strip()
        for requirement in PYPROJECT["project"]["dependencies"]
    }
    assert names <= allowed


def test_package_is_typed():
    assert importlib.resources.files("garisenda").joinpath("py.typed").is_file()
