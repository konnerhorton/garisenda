import inspect

import pytest

import garisenda as gs
from garisenda._inputs import judgments, record

u = gs.units


def test_record_without_source():
    magnitude, entry = record(
        "axis_depth", 20, kind="design judgment", unit="m", plain_number="read as SI"
    )
    assert magnitude == 20.0
    assert entry.name == "axis_depth"
    assert entry.value == 20 * u.m
    assert entry.kind == "design judgment"
    assert entry.given_as == "plain number, read as m"
    assert entry.source is None


def test_record_keeps_the_source():
    magnitude, entry = record(
        "volume_loss",
        gs.Sourced(1 * u.percent, source="Basis of design, section 4.2"),
        kind="design judgment",
        unit="dimensionless",
        plain_number="refuse",
    )
    assert magnitude == pytest.approx(0.01)
    assert entry.source == "Basis of design, section 4.2"
    assert entry.given_as == "quantity in %"


def test_sourced_plain_ratio_is_still_refused():
    with pytest.raises(TypeError, match="volume_loss needs a pint quantity"):
        record(
            "volume_loss",
            gs.Sourced(0.01, source="x"),
            kind="design judgment",
            unit="dimensionless",
            plain_number="refuse",
        )


@judgments(
    volume_loss="it depends on the tunneling method. Pass it as 1 * gs.units.percent."
)
def analysis(tunnel: str, *, volume_loss: float) -> float:
    return volume_loss


def test_missing_judgment_says_what_it_depends_on():
    with pytest.raises(
        TypeError,
        match=r"analysis\(\) is missing volume_loss\. volume_loss is a required "
        r"design judgment with no default: it depends on the tunneling method",
    ):
        analysis("t")


def test_judgment_given_passes_through():
    assert analysis("t", volume_loss=2.0) == 2.0


def test_signature_is_kept():
    parameter = inspect.signature(analysis).parameters["volume_loss"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty


def test_judgment_with_default_is_refused_at_decoration():
    with pytest.raises(TypeError, match="keyword-only argument without a default"):

        @judgments(volume_loss="x")
        def defaulted(*, volume_loss: float = 0.01) -> float:
            return volume_loss
