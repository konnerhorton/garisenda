"""The docs site (docs/work/m1c-figures-sweep-docs.md, AC 12)."""

import importlib.util
import inspect
import re
from pathlib import Path

import pytest

import garisenda as gs

ROOT = Path(__file__).parents[2]
EXAMPLES = sorted((ROOT / "docs" / "site" / "examples").glob("*.py"))


def _load_prepare_site():
    script = ROOT / "docs" / "prepare_site.py"
    spec = importlib.util.spec_from_file_location("prepare_site", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare_site = _load_prepare_site()


@pytest.mark.parametrize("script", EXAMPLES, ids=lambda path: path.name)
def test_page_example_runs_clean(tmp_path, script):
    # Each example runs in an empty folder, with no warning and no traceback.
    done = prepare_site.run_example(script, tmp_path)
    assert done.returncode == 0, done.stderr
    assert done.stderr == ""
    for figure in re.findall(r'savefig\("([^"]+)"', script.read_text("utf-8")):
        assert (tmp_path / figure).is_file()


def _documented():
    pages = (ROOT / "docs" / "site" / "reference").glob("*.md")
    text = "\n".join(page.read_text(encoding="utf-8") for page in pages)
    return set(re.findall(r"^::: (\S+)", text, flags=re.MULTILINE))


# Exported but not documented with a directive, with the reason.
UNDOCUMENTED = {
    "garisenda.__version__",  # shown on the install page
    "garisenda.units",  # pint's registry, described on the garisenda page
}


def test_every_public_name_has_a_reference_entry():
    expected = set()

    def add(path, obj):
        if path in UNDOCUMENTED:
            return
        if inspect.ismodule(obj) and hasattr(obj, "__all__"):
            for member in obj.__all__:
                add(f"{path}.{member}", getattr(obj, member))
        else:
            expected.add(path)

    for name in gs.__all__:
        add(f"garisenda.{name}", getattr(gs, name))
    assert expected - _documented() == set()
