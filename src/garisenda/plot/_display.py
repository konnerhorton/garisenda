"""The units figures are drawn in (SPEC §9, spec decision 14)."""

from collections.abc import Mapping
from dataclasses import dataclass

import pint

from garisenda._units import units

DEFAULTS: dict[str, str] = {
    "length": "m",
    "displacement": "mm",
    "strain": "microstrain",
    "curvature": "1/km",
}
"""The display unit of each kind of quantity, unless the caller changes it."""

SI: dict[str, str] = {
    "length": "m",
    "displacement": "m",
    "strain": "dimensionless",
    "curvature": "1/m",
}
"""The unit each kind is held in, in a result's values."""


@dataclass(frozen=True)
class DisplayUnits:
    """The units a figure draws each kind of quantity in.

    Attributes
    ----------
    units : dict of str to pint.Unit
        The display unit of each kind: ``length``, ``displacement``,
        ``strain`` and ``curvature``.
    """

    units: dict[str, pint.Unit]

    def factor(self, kind: str) -> float:
        """Return what a value in its SI unit is multiplied by for display."""
        return float(units.Quantity(1.0, SI[kind]).m_as(self.units[kind]))

    def symbol(self, kind: str) -> str:
        """Return the display unit's symbol, such as ``mm`` or ``µε``."""
        text = f"{self.units[kind]:~P}"
        return text or "-"

    def label(self, quantity: str, kind: str) -> str:
        """Return an axis label, ``Quantity (unit)``."""
        return f"{quantity} ({self.symbol(kind)})"


def resolve(display_units: Mapping[str, object] | None) -> DisplayUnits:
    """Return the display units: the defaults, with any kinds the caller set.

    Parameters
    ----------
    display_units : mapping of str to str or pint.Unit, or None
        Units for any of ``length``, ``displacement``, ``strain`` and
        ``curvature``, such as ``{"displacement": "m"}``.

    Raises
    ------
    ValueError
        For a kind that isn't one of the four.
    pint.DimensionalityError
        For a unit that doesn't convert to its kind's SI unit.
    """
    given = dict(display_units or {})
    unknown = sorted(set(given) - set(DEFAULTS))
    if unknown:
        raise ValueError(
            f"display_units has no kind {', '.join(map(repr, unknown))}; the kinds "
            f"are {', '.join(map(repr, DEFAULTS))}."
        )
    chosen: dict[str, pint.Unit] = {}
    for kind, default in DEFAULTS.items():
        value = given.get(kind, default)
        unit = units.Unit(str(value)) if not isinstance(value, pint.Unit) else value
        if not units.Quantity(1.0, unit).is_compatible_with(SI[kind]):
            raise pint.DimensionalityError(
                unit,
                units.Unit(SI[kind]),
                extra_msg=f" for display_units[{kind!r}]",
            )
        chosen[kind] = unit
    return DisplayUnits(chosen)
