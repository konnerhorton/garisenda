"""Damage categories: bands of limiting tensile strain."""

import itertools
import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Band:
    """One damage category: its number, label, severity and upper strain limit.

    Attributes
    ----------
    number : int
        The category's number, as `acceptable_category` names it.
    label : str
        How it is printed, such as ``"2"`` or ``"4 to 5"``.
    severity : str
        Its normal degree of severity, such as ``"slight"``.
    upper_limit : float
        The largest tensile strain in the band, dimensionless; ``math.inf``
        for the last band.
    """

    number: int
    label: str
    severity: str
    upper_limit: float


@dataclass(frozen=True, init=False)
class DamageCategories:
    """An ordered table of damage categories by limiting tensile strain.

    Band n holds the strains limit(n-1) < eps <= limit(n): a strain exactly on
    a boundary falls in the lower band, so a check against a band's upper
    limit passes at utilization exactly 1, as every other check does. The
    first band starts at zero; a strain of zero or less is in it.

    `garisenda.presets.damage_categories` gives the published table. A user
    may build their own.

    Parameters
    ----------
    name : str
        The table's name, recorded on the result.
    bands : sequence of Band
        In order. The numbers must be distinct, the upper limits must
        increase, and the last must be ``math.inf``.

    Raises
    ------
    ValueError
        If there are no bands, a number repeats, the limits don't increase or
        aren't positive, or the last band isn't unbounded.
    """

    name: str
    bands: tuple[Band, ...]

    def __init__(self, *, name: str, bands: Sequence[Band]) -> None:
        bands = tuple(bands)
        if not bands:
            raise ValueError("DamageCategories needs at least one band.")
        numbers = [band.number for band in bands]
        if len(set(numbers)) != len(numbers):
            raise ValueError(f"The bands' numbers must be distinct, not {numbers}.")
        limits = [band.upper_limit for band in bands]
        if not math.isinf(limits[-1]) or limits[-1] < 0:
            raise ValueError(
                "The last band must be unbounded (upper_limit math.inf), so every "
                f"strain has a category; its upper limit is {limits[-1]}."
            )
        if limits[0] <= 0 or any(b <= a for a, b in itertools.pairwise(limits)):
            raise ValueError(
                f"The bands' upper limits must be positive and increase, not {limits}."
            )
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "bands", bands)

    def category(self, strain: float) -> Band:
        """Return the band a tensile strain falls in, a boundary in the lower band."""
        for band in self.bands:
            if strain <= band.upper_limit:
                return band
        return self.bands[-1]

    def band(self, number: int) -> Band:
        """Return the band with a number, or raise `ValueError` listing them."""
        for band in self.bands:
            if band.number == number:
                return band
        listed = ", ".join(str(band.number) for band in self.bands)
        raise ValueError(
            f"There is no damage category {number!r} in {self.name}; its "
            f"categories are {listed}."
        )
