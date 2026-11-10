"""Published text holds no references to internal documents.

Every string literal in the package (docstrings, assumptions, sources, caveats,
messages, f-string parts), the docs site's pages and examples, and the README
are read by users, who can't follow a reference to the project's spec, its TODO
list or a milestone. Comments may keep them.
"""

import ast
import io
import re
import tokenize
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "garisenda"
SITE = ROOT / "docs" / "site"

INTERNAL = re.compile(
    r"SPEC\s*§|TODO\s*#|\bM\d+\b|\b(?:spec|intent),?\s+decisions?\b"
    r"|\bdecisions?\s+\d|spec's case"
)


def _string_hits(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return [
        f"{path.relative_to(ROOT)}:{node.lineno}: {match.group(0)!r}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        for match in [INTERNAL.search(node.value)]
        if match
    ]


def _script_hits(path: Path) -> list[str]:
    """Hits in a script's code and strings, not its comments."""
    source = path.read_text(encoding="utf-8")
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    return [
        f"{path.relative_to(ROOT)}:{token.start[0]}: {match.group(0)!r}"
        for token in tokens
        if token.type != tokenize.COMMENT
        for match in [INTERNAL.search(token.string)]
        if match
    ]


def _text_hits(path: Path) -> list[str]:
    return [
        f"{path.relative_to(ROOT)}:{number}: {match.group(0)!r}"
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        )
        for match in [INTERNAL.search(line)]
        if match
    ]


@pytest.mark.parametrize(
    "text",
    [
        "(SPEC §1.3)",
        "unverified (TODO #2)",
        "come with M5",
        "the M3 (b) spec",
        "spec decision 14",
        "intent decision 2",
        "(decisions 9 and 10)",
        "the M3 (b) spec's case J-A",
    ],
)
def test_the_pattern_finds_internal_references(text):
    assert INTERNAL.search(text)


@pytest.mark.parametrize(
    "text", ["Mair et al. (1993)", "1 MPa", "a 4 m pipe", "M_max", "SPECIFIC"]
)
def test_the_pattern_leaves_other_text(text):
    assert not INTERNAL.search(text)


def test_package_strings_have_no_internal_references():
    hits = [hit for path in sorted(PACKAGE.rglob("*.py")) for hit in _string_hits(path)]
    assert not hits, "\n".join(hits)


def test_docs_site_and_readme_have_no_internal_references():
    hits = [
        *(hit for path in sorted(SITE.rglob("*.md")) for hit in _text_hits(path)),
        *(hit for path in sorted(SITE.rglob("*.py")) for hit in _script_hits(path)),
        *_text_hits(ROOT / "README.md"),
    ]
    assert not hits, "\n".join(hits)
