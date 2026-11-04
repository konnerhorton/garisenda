import inspect
from dataclasses import dataclass

import pytest

import garisenda as gs
from garisenda._inputs import judgments, record, record_method

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


# M2 (b), plan step 1: an input record holding a named method


@dataclass(frozen=True)
class StandIn:
    """A stand-in method object: only its name is recorded."""

    name: str


HOW = "Write it as StandIn('a') or StandIn('b')."


def test_record_method_records_the_name():
    method, entry = record_method(
        "trough_width",
        StandIn("a"),
        kind="design judgment",
        expected=StandIn,
        how=HOW,
    )
    assert method == StandIn("a")
    assert entry.name == "trough_width"
    assert entry.value == "a"
    assert entry.kind == "design judgment"
    assert entry.given_as == "method"
    assert entry.source is None


def test_record_method_keeps_the_source():
    method, entry = record_method(
        "trough_width",
        gs.Sourced(StandIn("b"), source="Basis of design, section 5"),
        kind="design judgment",
        expected=StandIn,
        how=HOW,
    )
    assert method == StandIn("b")
    assert entry.value == "b"
    assert entry.source == "Basis of design, section 5"


@pytest.mark.parametrize("value", [0.5, "a", 0.5 * u.dimensionless, None])
def test_record_method_refuses_anything_else(value):
    with pytest.raises(
        TypeError, match=r"trough_width must be a method.*StandIn\('a'\)"
    ):
        record_method(
            "trough_width",
            gs.Sourced(value, source="x") if value is None else value,
            kind="design judgment",
            expected=StandIn,
            how=HOW,
        )
