"""The source interface: what every source returns (SPEC §3)."""

from dataclasses import dataclass
from typing import Literal, Protocol

import numpy as np
import numpy.typing as npt

from garisenda._inputs import InputRecord

Verdict = Literal["within", "marginal", "outside"]
"""A validity verdict (SPEC §5.2), from best to worst."""

VERDICTS: tuple[Verdict, ...] = ("within", "marginal", "outside")


def worst(verdicts: npt.ArrayLike) -> Verdict:
    """Return the worst of some verdicts, or ``"within"`` if there are none."""
    present = set(np.asarray(verdicts, dtype=str).ravel())
    for verdict in reversed(VERDICTS):
        if verdict in present:
            return verdict
    return "within"


@dataclass(frozen=True)
class Flag:
    """Something flagged about some points of an evaluation.

    Attributes
    ----------
    verdict : {"within", "marginal", "outside"}
        The verdict it sets for its points.
    reason : str
        What is wrong and what it means for the values.
    limit : str
        The limit that set the verdict.
    points : tuple of int
        The indices of the points it applies to.
    source : str, default ""
        The name of the source in a superposition it came from, nested names
        joined by dots (``"north"``, ``"twins.north"``); empty for a lone
        source.
    """

    verdict: Verdict
    reason: str
    limit: str
    points: tuple[int, ...]
    source: str = ""


@dataclass(frozen=True)
class MethodRecord:
    """A method a source used: its name, equations and source.

    Attributes
    ----------
    name : str
        The method's name.
    equations : tuple of str
        The equations, as written in the docstring.
    source : str
        Its source, as SPEC §2.2 cites it; 🔬 while unverified.
    """

    name: str
    equations: tuple[str, ...]
    source: str


@dataclass(frozen=True)
class Movement:
    """Ground movement at N points, with its exact derivatives (SPEC §3).

    Components are in the order (x, y, depth), with depth positive downward, so
    the third displacement component is settlement, positive downward. Arrays
    are plain numpy in SI; the units below are fixed.

    Attributes
    ----------
    displacement : numpy.ndarray, shape (N, 3)
        u_x, u_y and settlement, in m.
    gradient : numpy.ndarray, shape (N, 3, 3)
        ``gradient[n, i, j]`` is du_i/dx_j, dimensionless.
    hessian : numpy.ndarray, shape (N, 3, 3, 3)
        ``hessian[n, i, j, k]`` is d2u_i/dx_j dx_k, in 1/m; symmetric in j, k.
    third_derivative : numpy.ndarray, shape (N, 3, 3, 3, 3)
        ``third_derivative[n, i, j, k, l]`` is d3u_i/dx_j dx_k dx_l, in 1/m^2;
        symmetric in j, k, l. A superposition needs it to find where curvature
        peaks (SPEC §3).
    verdict : numpy.ndarray of str, shape (N,)
        ``"within"``, ``"marginal"`` or ``"outside"`` for each point.
    flags : tuple of Flag
        Everything flagged, each with the indices of its points.
    """

    displacement: npt.NDArray[np.float64]
    gradient: npt.NDArray[np.float64]
    hessian: npt.NDArray[np.float64]
    third_derivative: npt.NDArray[np.float64]
    verdict: npt.NDArray[np.str_]
    flags: tuple[Flag, ...]

    def __post_init__(self) -> None:
        """Check that the arrays agree in shape."""
        count = self.displacement.shape[0]
        expected = {
            "displacement": (count, 3),
            "gradient": (count, 3, 3),
            "hessian": (count, 3, 3, 3),
            "third_derivative": (count, 3, 3, 3, 3),
            "verdict": (count,),
        }
        for name, shape in expected.items():
            actual = getattr(self, name).shape
            if actual != shape:
                raise ValueError(f"Movement.{name} has shape {actual}, not {shape}.")


class Source(Protocol):
    """Anything that causes ground movement (SPEC §3).

    A source is a function of points: `evaluate` returns the movement at them,
    and the attributes carry what a result needs to be checked.
    """

    @property
    def inputs(self) -> tuple[InputRecord, ...]:
        """Every input as used."""
        ...

    @property
    def method(self) -> tuple[MethodRecord, ...]:
        """The methods used, with their equations and sources."""
        ...

    @property
    def assumptions(self) -> tuple[str, ...]:
        """What the method assumes and garisenda can't check."""
        ...

    def evaluate(self, *, x: object, y: object, depth: object) -> Movement:
        """Return the movement at points (x, y, depth)."""
        ...

    def critical_distances(
        self, *, start: object, end: object
    ) -> npt.NDArray[np.float64]:
        """Return where the source's quantities peak or change sign on a segment.

        For the straight segment from `start` to `end`, each (x, y, depth) in m,
        the distances from `start` in m, sorted and within [0, L], so a profile
        that puts stations there never misses a peak between them.
        """
        ...

    def feature_length(self, *, start: object, end: object) -> float:
        """Return the shortest length over which the field changes on a segment.

        For the straight segment from `start` to `end`, each (x, y, depth) in m,
        a length in m that a sampling interval can be tied to, such as a
        trough's width i.
        """
        ...
