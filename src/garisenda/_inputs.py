"""Input kinds, provenance and the required-judgment rule (SPEC §4)."""

import functools
import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, ParamSpec, TypeVar

import pint

from garisenda._units import Magnitude, PlainNumber, to_si, units

Kind = Literal["ground parameter", "design judgment", "constant or setting", "geometry"]
"""The kinds of input, each treated differently (SPEC §4)."""


@dataclass(frozen=True)
class Sourced:
    """An input value with the source it came from.

    Any argument accepts either a bare value or a `Sourced`. The source is kept
    on the input record, and so on the result.

    Parameters
    ----------
    value : object
        The value, as the argument would take it bare (usually a pint quantity).
    source : str
        Where it came from, as free text: a document and section, a project's
        basis of design, a test report.

    Examples
    --------
    >>> import garisenda as gs
    >>> gs.Sourced(1.0 * gs.units.percent, source="Basis of design, section 4.2")
    Sourced(value=..., source='Basis of design, section 4.2')
    """

    value: object
    source: str


@dataclass(frozen=True)
class InputRecord:
    """One input as used: its value in SI, its kind, how it was given and its source.

    Attributes
    ----------
    name : str
        The argument's name.
    value : pint.Quantity
        The value used, in its SI unit.
    kind : {"ground parameter", "design judgment", "constant or setting", "geometry"}
        Its kind (SPEC §4).
    given_as : str
        How it was given, for example ``"quantity in %"`` or
        ``"plain number, read as m"``.
    source : str or None
        The source given with `Sourced`, or None.
    """

    name: str
    value: pint.Quantity
    kind: Kind
    given_as: str
    source: str | None


def record(
    name: str,
    value: object,
    *,
    kind: Kind,
    unit: str,
    plain_number: PlainNumber,
) -> tuple[Magnitude, InputRecord]:
    """Unwrap a `Sourced`, convert to SI and record the input.

    Parameters
    ----------
    name, value, unit, plain_number
        As for `to_si`.
    kind : {"ground parameter", "design judgment", "constant or setting", "geometry"}
        The input's kind.

    Returns
    -------
    magnitude : float or numpy.ndarray
        The value in `unit`.
    record : InputRecord
        The record of it.
    """
    source = None
    if isinstance(value, Sourced):
        source = value.source
        value = value.value
    magnitude, given_as = to_si(name, value, unit=unit, plain_number=plain_number)
    quantity = units.Quantity(magnitude, unit)
    return magnitude, InputRecord(name, quantity, kind, given_as, source)


P = ParamSpec("P")
R = TypeVar("R")


def judgments(**explanations: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Explain each required judgment when it is missing (SPEC §4).

    Judgments stay required keyword-only arguments in the decorated function's
    signature. The decorator replaces Python's bare "missing 1 required
    keyword-only argument" with an error that says what the judgment depends on
    and how to set it.

    Parameters
    ----------
    **explanations : str
        For each judgment, what it depends on and how to set it, written to
        follow "<name> is a required design judgment with no default:".

    Raises
    ------
    TypeError
        At decoration, if a name isn't a keyword-only argument without a default.
    """

    def decorate(function: Callable[P, R]) -> Callable[P, R]:
        parameters = inspect.signature(function).parameters
        for name in explanations:
            parameter = parameters.get(name)
            if (
                parameter is None
                or parameter.kind is not inspect.Parameter.KEYWORD_ONLY
                or parameter.default is not inspect.Parameter.empty
            ):
                raise TypeError(
                    f"{function.__qualname__}: {name} must be a keyword-only "
                    "argument without a default to be declared a judgment."
                )

        @functools.wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for name, explanation in explanations.items():
                if name not in kwargs:
                    raise TypeError(
                        f"{function.__qualname__}() is missing {name}. {name} is a "
                        f"required design judgment with no default: {explanation}"
                    )
            return function(*args, **kwargs)

        return wrapper

    return decorate
