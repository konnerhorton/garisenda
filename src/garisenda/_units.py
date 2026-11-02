"""The unit registry and the one conversion every input goes through (SPEC §6)."""

from typing import Any, Literal

import numpy as np
import numpy.typing as npt
import pint

units = pint.UnitRegistry()
"""The registry every quantity given to or returned by garisenda belongs to."""

PlainNumber = Literal["read as SI", "refuse"]
"""What a plain number means for an input.

``"read as SI"`` reads it in the input's SI unit, as SPEC §6 allows. ``"refuse"``
is for inputs where a plain number is ambiguous: ratios practice writes as a
percentage (``0.5`` could be 0.5 % or 50 %) and angles (``30`` could be degrees
or radians).
"""

Magnitude = float | npt.NDArray[np.float64]

_EXAMPLES = {
    "dimensionless": "0.5 * gs.units.percent, or 0.005 * gs.units.dimensionless",
    "radian": "30 * gs.units.degree",
}


def _root(unit: Any) -> pint.Unit:
    return units.get_root_units(unit)[1]


def to_si(
    name: str, value: object, *, unit: str, plain_number: PlainNumber
) -> tuple[Magnitude, str]:
    """Convert an input to the magnitude in its SI unit.

    Parameters
    ----------
    name : str
        The argument's name, used in error messages.
    value : object
        A pint quantity, or a plain number or array of numbers.
    unit : str
        The SI unit the calculation works in, such as ``"m"``, ``"radian"`` or
        ``"dimensionless"``. A quantity must have the same root units: pint
        treats degrees and percent as both dimensionless, but their root units
        are radian and dimensionless, so one can't pass for the other.
    plain_number : {"read as SI", "refuse"}
        What a plain number means (see `PlainNumber`).

    Returns
    -------
    magnitude : float or numpy.ndarray
        The value in `unit`.
    given_as : str
        How it was given, for the input record: ``"quantity in <unit>"`` or
        ``"plain number, read as <unit>"``.

    Raises
    ------
    TypeError
        A plain number where one is refused, or a value that isn't a number.
    pint.DimensionalityError
        A quantity whose units don't convert to `unit`.
    """
    if isinstance(value, pint.Quantity):
        if _root(value.units) != _root(unit):
            raise pint.DimensionalityError(
                value.units,
                units.Unit(unit),
                extra_msg=f" for {name}: it is given in {value.units:~}, "
                f"which can't be converted to {unit}",
            )
        given_as = f"quantity in {value.units:~}" if value.units else "quantity"
        return _as_float(name, value.m_as(unit)), given_as
    if plain_number == "refuse":
        example = _EXAMPLES.get(unit, f"value * gs.units.{unit}")
        raise TypeError(
            f"{name} needs a pint quantity: a plain number is ambiguous for it "
            f"({value!r} could be read in more than one unit). "
            f"Write it as, for example, {name}={example}."
        )
    return _as_float(name, value), f"plain number, read as {unit}"


def _as_float(name: str, value: object) -> Magnitude:
    try:
        array = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError):
        raise TypeError(
            f"{name} must be a number, an array of numbers or a pint quantity, "
            f"not {type(value).__name__}."
        ) from None
    if array.ndim == 0:
        return float(array)
    return array
