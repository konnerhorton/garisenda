"""Several sources combined by superposition."""

import itertools
import math
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import cast

import numpy as np
import numpy.typing as npt

from garisenda._inputs import InputRecord, record
from garisenda.sources._critical import find_critical_distances
from garisenda.sources._movement import VERDICTS, MethodRecord, Movement, Source
from garisenda.sources._tunnel import IdealizedTunnel

CRITICAL_DISTANCE_SAMPLING = 1 / 8
"""The sampling interval for critical distances, as a fraction of the feature length."""

CRITICAL_DISTANCE_TOLERANCE = 1e-9
"""The length in m to which critical distances are found."""

GROUND_TOLERANCE = 1e-6
"""Difference in m within which two ground elevations are the same surface."""

PARALLEL_TOLERANCE = 1e-9
"""|sin| of the angle between two tunnels within which they are parallel."""

OVERLAP_TOLERANCE = 1e-6
"""Length in m by which two bores may overlap and still count as touching.

The offset between parallel axes is found from their coordinates, so bores
built touching can come out a rounding error closer than (D1 + D2) / 2.
"""

SOURCE_ATTRIBUTES = (
    "evaluate",
    "critical_distances",
    "feature_length",
    "inputs",
    "method",
    "assumptions",
)

METHOD = MethodRecord(
    "Superposition",
    (
        "u = sum over sources of u_s",
        "the same for each derivative",
        "verdict = worst over sources",
    ),
    "Linear superposition of the sources' fields; no external source",
)

ASSUMPTION = (
    "Superposition: each tunnel's movement is calculated as if the others "
    "weren't there, and the movements add. Interaction between tunnels (a later "
    "bore's larger volume loss, an eccentric trough over twin bores, the order "
    "of construction) isn't modeled; set each tunnel's volume loss to allow "
    "for it."
)


def superpose(*arguments: object, **sources: object) -> "Superposition":
    """Return several sources combined into one by superposition.

    Each source's movement is evaluated at the same points and the results
    add: with u_s the displacement of source s,

    - u = sum over sources of u_s, and the same for its gradient, Hessian and
      third derivative, which are global components, so the sum is
      exact;
    - the verdict at a point is the worst over the sources.

    Parameters
    ----------
    **sources : Source
        At least two sources, each by a name that is a Python identifier, such
        as ``north=`` and ``south=``. A superposition is a source, so they nest.

    Returns
    -------
    Superposition
        The combined source. Its inputs are each source's, renamed
        ``<name>.<input>`` (``north.volume_loss``), and two constants of its
        own for finding critical distances; its methods and assumptions are
        each source's, an identical one kept once, then superposition's own.
        Its flags keep the name of the source they came from (`Flag.source`).

    Raises
    ------
    TypeError
        If a source is given by position, fewer than two are given, a name
        isn't an identifier, or a value isn't a source.
    ValueError
        If a source is named ``utility``, whose inputs would share names with
        a movement profile's utility inputs. If the inputs are inconsistent: two
        ``ground_elevation`` records, at any depth of nesting, differ by more
        than 1 um; or two tunnels' bores overlap, the shortest distance between
        their axes being less than (D1 + D2) / 2. Both axes are horizontal
        lines, so for parallel tunnels (|sin of the angle between them| at most
        1e-9) that is sqrt(do^2 + dz0^2), do the plan offset between the axes,
        and otherwise their plans cross and it is |dz0|. Touching bores are
        allowed. Sources with no ``tunnel`` are left out of the overlap check.

    Notes
    -----
    Assumption, recorded on the result: each tunnel's movement is calculated
    as if the others weren't there. Interaction between tunnels (a later bore's
    larger volume loss, an eccentric trough over twin bores, the order of
    construction) isn't modeled; each tunnel's volume loss is the user's
    judgment for it.

    Source: linear superposition of the sources' fields; no external source.

    Examples
    --------
    >>> import garisenda as gs
    >>> u = gs.units
    >>> north = gs.sources.IdealizedTunnel(
    ...     reference_point=(0, 0), azimuth=0 * u.degree, diameter=6, axis_depth=20
    ... )
    >>> south = north.parallel(offset=15, diameter=6, axis_depth=20)
    >>> twins = gs.superpose(
    ...     north=gs.sources.transverse_surface_trough(
    ...         north, volume_loss=1 * u.percent, trough_width_parameter=0.5
    ...     ),
    ...     south=gs.sources.transverse_surface_trough(
    ...         south, volume_loss=1.5 * u.percent, trough_width_parameter=0.5
    ...     ),
    ... )
    >>> [entry.name for entry in twins.inputs if entry.name.endswith("volume_loss")]
    ['north.volume_loss', 'south.volume_loss']
    """
    if arguments:
        raise TypeError(
            "superpose takes its sources by name, such as "
            "superpose(north=..., south=...), so each input can be named for "
            f"its source; got {len(arguments)} by position."
        )
    if len(sources) < 2:
        raise TypeError(
            "superpose needs at least two sources; with one there is nothing "
            f"to add. Got {len(sources)}."
        )
    for name, value in sources.items():
        if not name.isidentifier():
            raise TypeError(
                f"Source name {name!r} isn't a Python identifier: names are "
                "joined by dots in input names (north.volume_loss), so they "
                "can't hold dots or spaces."
            )
        if name == "utility":
            raise ValueError(
                "A source can't be named 'utility': a movement profile names "
                "the utility's inputs utility.<name>, and this source's inputs "
                "would share those names. Name it for the tunnel, such as north."
            )
        missing = [
            attribute
            for attribute in SOURCE_ATTRIBUTES
            if not hasattr(value, attribute)
        ]
        if missing:
            raise TypeError(f"{name} isn't a source: it has no {', '.join(missing)}.")
    # Each value was checked above to have every attribute of a source.
    named = {name: cast(Source, value) for name, value in sources.items()}

    inputs = [
        replace(entry, name=f"{name}.{entry.name}")
        for name, source in named.items()
        for entry in source.inputs
    ]
    _check_ground(inputs)
    _check_overlap(named)
    for constant, value, unit in (
        ("critical_distance_sampling", CRITICAL_DISTANCE_SAMPLING, "dimensionless"),
        ("critical_distance_tolerance", CRITICAL_DISTANCE_TOLERANCE, "m"),
    ):
        _, entry = record(
            constant,
            value,
            kind="constant or setting",
            unit=unit,
            plain_number="read as SI",
        )
        inputs.append(entry)

    methods = _unique(
        entry for source in named.values() for entry in source.method if entry != METHOD
    )
    assumptions = _unique(
        text
        for source in named.values()
        for text in source.assumptions
        if text != ASSUMPTION
    )
    return Superposition(
        sources=MappingProxyType(named),
        inputs=tuple(inputs),
        method=(*methods, METHOD),
        assumptions=(*assumptions, ASSUMPTION),
    )


@dataclass(frozen=True)
class Superposition:
    """Several sources whose movements add, as one source.

    Made by `garisenda.superpose`, which documents the method.

    Attributes
    ----------
    sources : mapping of str to Source
        The sources by name, in the order given; read-only.
    inputs : tuple of InputRecord
        Every source's inputs, named ``<source>.<input>``, and the two
        constants for critical distances.
    method : tuple of MethodRecord
        Each source's methods, an identical one kept once, then superposition.
    assumptions : tuple of str
        Each source's assumptions, an identical one kept once, then
        superposition's.
    """

    sources: Mapping[str, Source]
    inputs: tuple[InputRecord, ...]
    method: tuple[MethodRecord, ...]
    assumptions: tuple[str, ...]

    def evaluate(self, *, x: object, y: object, depth: object) -> Movement:
        """Return the summed movement and its exact derivatives at points.

        Every source is evaluated at the same points. The displacement,
        gradient, Hessian and third derivative are the sums of the sources';
        the verdict at a point is the worst of theirs; and each source's flags
        are kept, one for one, with `Flag.source` set to its name (prefixed for
        a nested superposition).

        Parameters
        ----------
        x, y : length or array of lengths
            Plan coordinates, in m if plain numbers.
        depth : length or array of lengths
            Depth below the ground surface, positive downward, in m if plain
            numbers.

        Returns
        -------
        Movement
            The combined movement.

        Raises
        ------
        ValueError, TypeError
            A source's error, raised again as the same type with its message
            prefixed ``"<name>: "``, such as for a point inside that source's
            bore.
        """
        movements = []
        for name, source in self.sources.items():
            try:
                movements.append(source.evaluate(x=x, y=y, depth=depth))
            except (ValueError, TypeError) as error:
                raise type(error)(f"{name}: {error}") from error
        rank = np.max(
            [
                [VERDICTS.index(verdict) for verdict in movement.verdict.tolist()]
                for movement in movements
            ],
            axis=0,
        )
        flags = tuple(
            replace(flag, source=f"{name}.{flag.source}" if flag.source else name)
            for name, movement in zip(self.sources, movements, strict=True)
            for flag in movement.flags
        )
        return Movement(
            displacement=_sum(movement.displacement for movement in movements),
            gradient=_sum(movement.gradient for movement in movements),
            hessian=_sum(movement.hessian for movement in movements),
            third_derivative=_sum(movement.third_derivative for movement in movements),
            verdict=np.array(VERDICTS)[rank],
            flags=flags,
        )

    def critical_distances(
        self, *, start: object, end: object
    ) -> npt.NDArray[np.float64]:
        """Return where the combined field's quantities peak on a segment.

        Found by root-finding on the exact derivatives along the segment
        (`find_critical_distances`), sampled at 1/8 of the feature length and
        refined to 1e-9 m, not taken from the sources: two overlapping troughs
        peak between their axes.

        Parameters
        ----------
        start, end : array of three lengths
            The segment's ends as (x, y, depth), in m if plain numbers.

        Returns
        -------
        numpy.ndarray
            The distances from `start` in m, sorted, within [0, L].

        Raises
        ------
        ValueError
            If the segment is bad or vertical, or a sample can't be evaluated,
            naming its distance along the segment.
        """
        return find_critical_distances(
            self,
            start=start,
            end=end,
            sampling=CRITICAL_DISTANCE_SAMPLING,
            tolerance=CRITICAL_DISTANCE_TOLERANCE,
        )

    def feature_length(self, *, start: object, end: object) -> float:
        """Return the least of the sources' feature lengths on a segment, in m."""
        return min(
            float(source.feature_length(start=start, end=end))
            for source in self.sources.values()
        )


def _sum(arrays: Iterator[npt.NDArray[np.float64]]) -> npt.NDArray[np.float64]:
    total: npt.NDArray[np.float64] = np.sum(list(arrays), axis=0)
    return total


def _unique[T](items: Iterator[T]) -> list[T]:
    kept: list[T] = []
    for item in items:
        if item not in kept:
            kept.append(item)
    return kept


def tunnels(sources: Mapping[str, Source]) -> Iterator[tuple[str, IdealizedTunnel]]:
    """Yield each source's tunnel by its name path, through nested superpositions."""
    for name, source in sources.items():
        if isinstance(source, Superposition):
            for inner, tunnel in tunnels(source.sources):
                yield f"{name}.{inner}", tunnel
        elif isinstance(own := getattr(source, "tunnel", None), IdealizedTunnel):
            yield name, own


def _check_ground(inputs: list[InputRecord]) -> None:
    grounds = [
        (entry.name, float(entry.value.to("m").magnitude))
        for entry in inputs
        if entry.name.rsplit(".", 1)[-1] == "ground_elevation"
        and not isinstance(entry.value, str)
    ]
    if not grounds:
        return
    low = min(grounds, key=lambda item: item[1])
    high = max(grounds, key=lambda item: item[1])
    if high[1] - low[1] > GROUND_TOLERANCE:
        raise ValueError(
            "The sources don't share a ground surface: "
            f"{low[0]} is {low[1]:.6g} m and {high[0]} is {high[1]:.6g} m. "
            "Give every tunnel's ground_elevation as the same surface, or its "
            "axis_depth."
        )


def _check_overlap(sources: Mapping[str, Source]) -> None:
    for (first_name, first), (second_name, second) in itertools.combinations(
        tunnels(sources), 2
    ):
        depth = abs(first.axis_depth - second.axis_depth)
        if abs(math.sin(first.azimuth - second.azimuth)) <= PARALLEL_TOLERANCE:
            _, offset = first.station_offset(x=second.reference_x, y=second.reference_y)
            distance = math.hypot(float(offset), depth)
            between = "in section"
        else:
            distance = depth
            between = "where their plans cross"
        clear = (first.diameter + second.diameter) / 2
        if distance < clear - OVERLAP_TOLERANCE:
            raise ValueError(
                f"The bores of {first_name} and {second_name} overlap: their "
                f"axes are {distance:.6g} m apart {between}, less than "
                f"(D1 + D2) / 2 = {clear:.6g} m."
            )
