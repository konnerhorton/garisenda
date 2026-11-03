"""The idealized straight tunnel (SPEC §8.3)."""

import math
from dataclasses import dataclass, replace

import numpy as np

from garisenda._inputs import InputRecord, record
from garisenda._units import Magnitude, units

IDEALIZED_ASSUMPTION = (
    "Idealized straight tunnel: no ends, shafts, curves or junctions, and the "
    "face long passed (SPEC §1.3)."
)


@dataclass(frozen=True, init=False)
class IdealizedTunnel:
    """A straight tunnel with no ends: the tunnel of a traditional assessment.

    Parameters
    ----------
    reference_point : tuple of two lengths
        A point (x, y) on the tunnel axis in plan, in m if given as plain numbers.
    azimuth : pint angle
        The plan direction of increasing station, clockwise from the +y axis (a
        bearing when +y is north; SPEC §8.1). A plain number is refused, because
        it could be degrees or radians.
    diameter : length
        The excavated diameter D, in m if a plain number. Must be positive.
    axis_depth : length, optional
        The depth of the axis below the ground surface, z₀.
    axis_elevation, ground_elevation : length, optional
        Instead of `axis_depth`: the axis elevation with the ground elevation,
        both in the site's one length unit. z₀ = ground_elevation - axis_elevation.
    reference_station : length, default 0
        The station at `reference_point`, so spreadsheet stations can be used as
        they are.

    Attributes
    ----------
    reference_x, reference_y, axis_depth, diameter, reference_station : float
        In m.
    azimuth : float
        In radians.
    tangent, normal : tuple of float
        Unit vectors in plan: t = (sin θ, cos θ) along increasing station, and
        n = (cos θ, -sin θ) to the right looking up-station.
    inputs : tuple of InputRecord
        Every input as used.
    assumptions : tuple of str
        That the tunnel is idealized (SPEC §1.3).

    Raises
    ------
    TypeError
        If the axis isn't given by exactly one of `axis_depth` or `axis_elevation`
        with `ground_elevation`, or `azimuth` is a plain number.
    ValueError
        If the diameter isn't positive, the axis depth is at most D/2 (the bore
        would break the ground surface), or an input isn't finite.
    """

    reference_x: float
    reference_y: float
    azimuth: float
    diameter: float
    axis_depth: float
    reference_station: float
    tangent: tuple[float, float]
    normal: tuple[float, float]
    inputs: tuple[InputRecord, ...]
    assumptions: tuple[str, ...]

    def __init__(
        self,
        *,
        reference_point: object,
        azimuth: object,
        diameter: object,
        axis_depth: object = None,
        axis_elevation: object = None,
        ground_elevation: object = None,
        reference_station: object = None,
    ) -> None:
        inputs: list[InputRecord] = []

        def read(name: str, value: object, *, unit: str = "m") -> Magnitude:
            magnitude, entry = record(
                name,
                value,
                kind="geometry",
                unit=unit,
                plain_number="read as SI" if unit == "m" else "refuse",
            )
            if not np.all(np.isfinite(magnitude)):
                raise ValueError(f"{name} must be finite, not {magnitude}.")
            inputs.append(entry)
            return magnitude

        point = np.asarray(read("reference_point", reference_point))
        if point.shape != (2,):
            raise ValueError(
                "reference_point must be two lengths (x, y), "
                f"not an array of shape {point.shape}."
            )
        theta = float(read("azimuth", azimuth, unit="radian"))
        diameter_m = float(read("diameter", diameter))
        if diameter_m <= 0:
            raise ValueError(f"diameter must be positive, not {diameter_m} m.")

        given = [
            name
            for name, value in [
                ("axis_depth", axis_depth),
                ("axis_elevation", axis_elevation),
                ("ground_elevation", ground_elevation),
            ]
            if value is not None
        ]
        if given == ["axis_depth"]:
            depth_m = float(read("axis_depth", axis_depth))
        elif given == ["axis_elevation", "ground_elevation"]:
            depth_m = float(read("ground_elevation", ground_elevation)) - float(
                read("axis_elevation", axis_elevation)
            )
        else:
            raise TypeError(
                "Give the tunnel axis either as axis_depth, or as axis_elevation "
                "with ground_elevation (SPEC §8.2); got "
                f"{', '.join(given) if given else 'none of them'}."
            )
        if depth_m <= diameter_m / 2:
            raise ValueError(
                f"The axis depth ({depth_m} m) must be more than half the diameter "
                f"({diameter_m / 2} m), or the bore breaks the ground surface."
            )

        if reference_station is None:
            station_m = 0.0
            _, entry = record(
                "reference_station",
                0.0,
                kind="geometry",
                unit="m",
                plain_number="read as SI",
            )
            inputs.append(replace(entry, given_as="default, 0 m"))
        else:
            station_m = float(read("reference_station", reference_station))

        values = {
            "reference_x": float(point[0]),
            "reference_y": float(point[1]),
            "azimuth": theta,
            "diameter": diameter_m,
            "axis_depth": depth_m,
            "reference_station": station_m,
            "tangent": (math.sin(theta), math.cos(theta)),
            "normal": (math.cos(theta), -math.sin(theta)),
            "inputs": tuple(inputs),
            "assumptions": (IDEALIZED_ASSUMPTION,),
        }
        for name, value in values.items():
            object.__setattr__(self, name, value)

    def parallel(
        self,
        *,
        offset: object,
        diameter: object,
        axis_depth: object = None,
        axis_elevation: object = None,
        ground_elevation: object = None,
    ) -> "IdealizedTunnel":
        """Return an idealized tunnel parallel to this one, such as a twin bore.

        The new tunnel has the same azimuth and reference station, and its
        reference point is p0 + offset n, so a point's station is the same from
        either tunnel and its offset from the new one is o - offset (SPEC §8.3).

        Parameters
        ----------
        offset : length
            The plan offset of the new axis from this one, positive to the
            right looking up-station (SPEC §8.1), in m if a plain number. Zero
            is allowed: stacked bores.
        diameter : length
            The new tunnel's excavated diameter, in m if a plain number. Not
            copied from this tunnel: twin bores can differ.
        axis_depth : length, optional
            The new axis's depth below the ground surface.
        axis_elevation, ground_elevation : length, optional
            Instead of `axis_depth`, as for the constructor. Not copied either:
            stacked bores are at different depths.

        Returns
        -------
        IdealizedTunnel
            The new tunnel. Its input records are `offset`, `diameter` and the
            axis as given, and `reference_point`, `azimuth` and
            `reference_station` as derived, given as ``"parallel to a tunnel
            at offset <o> m"``. Whether the two bores overlap is checked where
            they are combined (`garisenda.superpose`).

        Raises
        ------
        TypeError
            As the constructor, if the axis isn't given one way.
        ValueError
            As the constructor, or if `offset` isn't finite.
        """
        offset_m, offset_record = record(
            "offset", offset, kind="geometry", unit="m", plain_number="read as SI"
        )
        offset_m = float(offset_m)
        if not math.isfinite(offset_m):
            raise ValueError(f"offset must be finite, not {offset_m}.")
        new = IdealizedTunnel(
            reference_point=(
                self.reference_x + offset_m * self.normal[0],
                self.reference_y + offset_m * self.normal[1],
            ),
            azimuth=self.azimuth * units.radian,
            diameter=diameter,
            axis_depth=axis_depth,
            axis_elevation=axis_elevation,
            ground_elevation=ground_elevation,
            reference_station=self.reference_station,
        )
        derived = f"parallel to a tunnel at offset {offset_m:.6g} m"
        inputs = tuple(
            replace(entry, given_as=derived, source=None)
            if entry.name in {"reference_point", "azimuth", "reference_station"}
            else entry
            for entry in new.inputs
        )
        object.__setattr__(new, "inputs", (offset_record, *inputs))
        return new

    def station_offset(self, *, x: object, y: object) -> tuple[Magnitude, Magnitude]:
        """Return the station and offset of points in plan.

        s = s₀ + (p - p₀)·t and o = (p - p₀)·n, with p₀ the reference point and
        s₀ its station, t the unit tangent and n the unit normal to the right
        (SPEC §8.1).

        Parameters
        ----------
        x, y : length or array of lengths
            Plan coordinates, in m if plain numbers.

        Returns
        -------
        station, offset : float or numpy.ndarray
            In m. Offset is positive to the right looking up-station.
        """
        x_m, _ = record("x", x, kind="geometry", unit="m", plain_number="read as SI")
        y_m, _ = record("y", y, kind="geometry", unit="m", plain_number="read as SI")
        dx = np.subtract(x_m, self.reference_x)
        dy = np.subtract(y_m, self.reference_y)
        station = self.reference_station + dx * self.tangent[0] + dy * self.tangent[1]
        offset = dx * self.normal[0] + dy * self.normal[1]
        return _plain(station), _plain(offset)


def _plain(value: object) -> Magnitude:
    array = np.asarray(value, dtype=np.float64)
    return float(array) if array.ndim == 0 else array
