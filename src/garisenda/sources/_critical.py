"""Critical distances of any source, found by root-finding (SPEC §3)."""

import math
import re
from collections.abc import Callable

import numpy as np
import numpy.typing as npt

from garisenda.sources._movement import Movement, Source
from garisenda.sources._segment import directions, read_segment

FloatArray = npt.NDArray[np.float64]

NEGLIGIBLE = 1e-10
"""Fraction of an order's scale below which two samples bracket nothing."""

FUNCTIONS = (
    "d/ds along",
    "d/ds vertical",
    "d/ds lateral",
    "d2/ds2 along",
    "d2/ds2 vertical",
    "d2/ds2 lateral",
    "d3/ds3 vertical",
    "d3/ds3 lateral",
)
"""The functions of distance s whose zeros are critical distances."""

ORDER = np.array([0, 0, 0, 1, 1, 1, 2, 2])
DIRECTION = np.array([0, 1, 2, 0, 1, 2, 1, 2])
"""Each function's order (less one) and direction (a, v, l) in `_derivatives`."""


def find_critical_distances(
    source: Source,
    *,
    start: object,
    end: object,
    sampling: float,
    tolerance: float,
) -> FloatArray:
    """Return where a source's quantities peak along a segment, by root-finding.

    With a, v and l the segment's along, vertical and lateral directions and u
    the source's displacement, the critical distances are the zeros of eight
    functions of distance s along the segment, from the source's exact
    derivatives G, H and T (gradient, Hessian, third derivative):

    - d(u.e)/ds = e_i G_ij a_j for e = a, v, l (peaks of movement);
    - d2(u.e)/ds2 = e_i H_ijk a_j a_k for e = a, v, l (peaks of strain and
      slope);
    - d3(u.e)/ds3 = e_i T_ijkl a_j a_k a_l for e = v, l (peaks of curvature).

    They are found in three steps:

    - sampling: the segment, length L, at h = L / ceil(L / (sampling f)),
      with f the source's `feature_length` on it, ends included;
    - bracketing: a function brackets a zero between consecutive samples whose
      signs differ (an exact zero counts as a sign of its own), unless both
      values are below 1e-10 of the order's scale: the largest value of that
      order over the samples and the three directions, or the largest
      displacement over the samples divided by f^n for order n, whichever is
      larger. That leaves out rounding noise (lateral on a perpendicular
      segment, or every derivative on a segment parallel to a tunnel) and the
      far tails of a trough;
    - refining: bisection of every bracket at once, until each is shorter than
      `tolerance`.

    Parameters
    ----------
    source : Source
        The source; its `evaluate` must return third derivatives.
    start, end : array of three lengths
        The segment's ends as (x, y, depth), in m if plain numbers.
    sampling : float
        The sampling interval as a fraction of the feature length, such as 1/8.
    tolerance : float
        The length in m to which each zero is found; zeros closer than this
        are merged.

    Returns
    -------
    numpy.ndarray
        The distances from `start` in m, sorted, within [0, L].

    Raises
    ------
    ValueError
        If the segment is bad (see `read_segment`) or vertical, or the source
        can't evaluate a sample, in which case the source's error is raised
        again as the same type with the sample indices replaced by their
        distances along the segment.

    Notes
    -----
    What this can miss: two zeros of the same function closer together than h,
    which bound a peak narrower than h. For a Gaussian trough and h = i/8 this
    needs two troughs placed to nearly cancel: one trough's own zeros are at
    least (sqrt(3) - 1) i, about 0.73 i, apart. A profile still has its spacing
    stations there, so such a peak is under-resolved, not lost. On a segment
    within a small angle of parallel to a trough, where a derivative's n-th
    order is below 1e-10 of the trough's own, its zeros aren't searched: the
    quantity hardly changes along the segment.
    """
    start_m, end_m, length = read_segment(start, end)
    a, v, lat = directions(start_m, end_m)
    feature = float(source.feature_length(start=start_m, end=end_m))
    count = math.ceil(length / (sampling * feature))
    samples = np.linspace(0.0, length, count + 1)

    def evaluate(distance: FloatArray) -> Movement:
        points = start_m + distance[:, None] * a
        try:
            return source.evaluate(x=points[:, 0], y=points[:, 1], depth=points[:, 2])
        except ValueError as error:
            raise type(error)(_with_distances(str(error), distance)) from error

    movement = evaluate(samples)
    derivatives = _derivatives(movement, a, v, lat)
    displacement = float(np.max(np.linalg.norm(movement.displacement, axis=1)))
    scales = np.array(
        [
            max(
                float(np.max(np.abs(derivatives[:, n]))),
                displacement / feature ** (n + 1),
            )
            for n in range(3)
        ]
    )

    def functions(distance: FloatArray) -> FloatArray:
        derivatives = _derivatives(evaluate(distance), a, v, lat)
        values: FloatArray = derivatives[:, ORDER, DIRECTION]
        return values

    return find_zeros(
        functions,
        length=length,
        step=sampling * feature,
        tolerance=tolerance,
        scales=scales[ORDER],
    )


def find_zeros(
    functions: Callable[[FloatArray], FloatArray],
    *,
    length: float,
    step: float,
    tolerance: float,
    scales: FloatArray,
) -> FloatArray:
    """Return the zeros of several functions of distance along a segment.

    The segment [0, L] is sampled at h = L / ceil(L / step), ends included.
    Function f brackets a zero between consecutive samples whose signs differ
    (an exact zero counts as a sign of its own), unless both values are below
    1e-10 of ``scales[f]``. Every bracket is refined by bisection at once until
    it is shorter than `tolerance`, and the zeros of all the functions are
    returned together, sorted, clipped to [0, L] and with those closer than
    `tolerance` merged.

    Parameters
    ----------
    functions : callable
        Takes distances, shape (N,), and returns the functions' values there,
        shape (N, F).
    length : float
        The segment's length L in m.
    step : float
        The largest sampling interval in m.
    tolerance : float
        The length in m to which each zero is found.
    scales : numpy.ndarray
        Shape (F,): each function's scale, below 1e-10 of which a value is
        negligible.

    Returns
    -------
    numpy.ndarray
        The distances of the zeros in m.
    """
    count = max(math.ceil(length / step), 1)
    samples = np.linspace(0.0, length, count + 1)
    values = functions(samples)
    band = NEGLIGIBLE * np.asarray(scales, dtype=np.float64)

    sign = np.sign(values)
    changes = (sign[:-1] != sign[1:]) & ~(
        (np.abs(values[:-1]) < band) & (np.abs(values[1:]) < band)
    )
    left, function = np.nonzero(changes)
    low, high = samples[left], samples[left + 1]
    low_sign, high_sign = sign[left, function], sign[left + 1, function]

    # A zero exactly at a sample needs no refining.
    exact = (low_sign == 0) | (high_sign == 0)
    found = [low[exact & (low_sign == 0)], high[exact & (high_sign == 0)]]
    low, high, low_sign, function = (
        array[~exact] for array in (low, high, low_sign, function)
    )
    while low.size and np.max(high - low) >= tolerance:
        middle = (low + high) / 2
        middle_sign = np.sign(functions(middle)[np.arange(middle.size), function])
        at_zero = middle_sign == 0
        found.append(middle[at_zero])
        keep = ~at_zero
        same = middle_sign[keep] == low_sign[keep]
        low = np.where(same, middle[keep], low[keep])
        high = np.where(same, high[keep], middle[keep])
        low_sign, function = low_sign[keep], function[keep]
    found.append((low + high) / 2)

    distances: FloatArray = np.sort(np.clip(np.concatenate(found), 0.0, length))
    merged: list[float] = []
    for distance in distances.tolist():
        if not merged or distance - merged[-1] >= tolerance:
            merged.append(distance)
    result: FloatArray = np.array(merged, dtype=np.float64)
    return result


def _derivatives(
    movement: Movement, a: FloatArray, v: FloatArray, lat: FloatArray
) -> FloatArray:
    """Return d^n(u.e)/ds^n, shape (N, 3, 3): order n = 1-3, then e = a, v, l."""
    e = np.stack([a, v, lat])
    result: FloatArray = np.stack(
        [
            np.einsum("ei,nij,j->ne", e, movement.gradient, a),
            np.einsum("ei,nijk,j,k->ne", e, movement.hessian, a, a),
            np.einsum("ei,nijkl,j,k,l->ne", e, movement.third_derivative, a, a, a),
        ],
        axis=1,
    )
    return result


def _with_distances(message: str, distance: FloatArray) -> str:
    """Replace the last list of point indices in a message with distances."""
    lists = list(re.finditer(r":? ?\[(\d+(?:, \d+)*)\]", message))
    if not lists:
        return message
    last = lists[-1]
    indices = [int(index) for index in last.group(1).split(", ")]
    named = ", ".join(f"{distance[index]:.6g}" for index in indices)
    return (
        f"{message[: last.start()]} at distances {named} m along the segment"
        f"{message[last.end() :]}"
    )
