"""Run one calculation over arrays of one to three inputs (SPEC §5.3)."""

import itertools
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd

from garisenda._inputs import InputRecord, Sourced
from garisenda._result import Result, input_dict, unit_text
from garisenda._units import to_si

Mode = Literal["grid", "paired"]
"""How two or three varied inputs are combined."""

MODES: tuple[Mode, ...] = ("grid", "paired")
MAXIMUM_VARIED = 3
RELATIVE_TOLERANCE = 1e-12
"""How closely a recorded input must match the value given, relative."""


@dataclass(frozen=True)
class _Run:
    """One run's inputs and its result or error."""

    given: dict[str, Any]
    result: Result | None
    error: Exception | None


def sweep(
    run: Callable[..., Result], *, vary: Mapping[str, Any], mode: Mode | None = None
) -> pd.DataFrame:
    """Run a calculation over values of one to three inputs, one row per run.

    `run` is a function you write that builds the whole calculation from the
    varied inputs, given as keyword arguments, and returns its `Result`. For
    example, to vary the trough's volume loss and width parameter::

        def crossing(volume_loss, trough_width_parameter):
            trough = gs.sources.transverse_surface_trough(
                tunnel, volume_loss=volume_loss,
                trough_width_parameter=trough_width_parameter,
            )
            utility = gs.utilities.perpendicular_utility(trough.tunnel, ...)
            return gs.movement_profile(utility, trough, spacing=1 * gs.units.m)

        table = gs.sweep(
            crossing,
            vary={"volume_loss": [0.5, 1.0, 1.5] * gs.units.percent,
                  "trough_width_parameter": [0.4, 0.5]},
            mode="grid",
        )

    With several sources (`gs.superpose`), an input is named for its
    source, and `run` takes it with the dots as underscores::

        def twins(south_volume_loss):
            south_trough = gs.sources.transverse_surface_trough(
                south, volume_loss=south_volume_loss, trough_width_parameter=0.5
            )
            source = gs.superpose(north=north_trough, south=south_trough)
            return gs.movement_profile(utility, source, spacing=1 * gs.units.m)

        table = gs.sweep(
            twins, vary={"south.volume_loss": [1.0, 1.5, 2.0] * gs.units.percent}
        )

    The table's column is ``south.volume_loss``, the record's name.

    Parameters
    ----------
    run : callable
        Takes the varied inputs as keyword arguments, named as the inputs
        they set (``volume_loss``, not ``vl``), and returns a `Result`. An
        input named for its source (``south.volume_loss``) is passed with
        its dots as underscores (``south_volume_loss``).
    vary : mapping of str to sequence
        One to three input record names, each with a one-dimensional
        sequence of values: a list, a numpy array or a pint array. Each
        element is passed to `run` as it is (a pint array's element is a
        quantity).
    mode : {"grid", "paired"}, optional
        Required with two or three inputs, refused with one. ``"grid"`` runs
        every combination, the first input varying slowest (as
        `itertools.product`); ``"paired"`` runs element by element, and the
        sequences must have equal lengths.

    Returns
    -------
    pandas.DataFrame
        One row per run, in run order, with columns:

        - ``run``: 0, 1, ...;
        - each varied input, as used: the magnitude in its SI unit from the
          run's input record (1 % appears as 0.01);
        - for each row of `Result.governing`, ``<name>`` (signed, as in the
          result's values) and ``<name>_distance`` (m);
        - ``validity``: the result's verdict;
        - ``warnings``: how many flags it has;
        - ``error``: None, or ``"<ExceptionType>: <message>"`` for a run that
          raised, whose values are NaN and validity None (SPEC §10).

        ``attrs`` holds ``units`` (per column), ``run`` (the function's
        qualified name), ``mode``, ``vary`` (the names) and ``fixed_inputs``:
        every input record of the first successful run that isn't varied, as
        `Result.to_dict` gives them.

    Raises
    ------
    TypeError
        If `vary` names more than three inputs or none, a name doesn't
        become a Python identifier with its dots as underscores, two names
        become the same one, a sequence isn't
        one-dimensional, `mode` is missing with two or more inputs or given
        with one, or `run` returns something other than a `Result`.
    ValueError
        If a sequence is empty, `mode` is unknown, ``"paired"`` sequences
        differ in length, a varied input isn't among a run's input records
        with the value given (so `run` didn't pass it on), or an input that
        isn't varied changes between runs (so `run` varies something it
        wasn't asked to). These are mistakes in `run`, raised at once.
    Exception
        The first run's error, if every run raises.
    """
    names, keywords, sequences = _check_vary(vary)
    combinations = _combinations(sequences, mode)

    runs: list[_Run] = []
    reference: Result | None = None
    for index, combination in enumerate(combinations):
        given = dict(zip(names, combination, strict=True))
        try:
            result = run(**{keywords[name]: value for name, value in given.items()})
        except Exception as error:  # a failed run is recorded (SPEC §5.3)
            runs.append(_Run(given, None, error))
            continue
        if not isinstance(result, Result):
            raise TypeError(
                f"run must return a gs.Result, but run {index} returned "
                f"{type(result).__name__}."
            )
        _check_varied(result, given, index)
        if reference is None:
            reference = result
        else:
            _check_fixed(reference, result, names, index)
        runs.append(_Run(given, result, None))

    if reference is None:
        first = runs[0].error
        assert first is not None
        raise first
    return _table(run, names, mode, runs, reference)


def _check_vary(
    vary: object,
) -> tuple[list[str], dict[str, str], list[list[Any]]]:
    """Check the varied inputs; return their names, `run`'s keywords and values."""
    if not isinstance(vary, Mapping) or not 1 <= len(vary) <= MAXIMUM_VARIED:
        count = len(vary) if isinstance(vary, Mapping) else "no mapping"
        raise TypeError(
            f"vary maps one to {MAXIMUM_VARIED} input names to their values "
            f"({count} given). For more, write a loop over sweeps."
        )
    names: list[str] = []
    keywords: dict[str, str] = {}
    sequences: list[list[Any]] = []
    for name, values in vary.items():
        keyword = _keyword(name)
        clash = [other for other, used in keywords.items() if used == keyword]
        if clash:
            raise TypeError(
                f"vary names {clash[0]!r} and {name!r}, which are both passed to "
                f"run as {keyword}. Name each input once."
            )
        if isinstance(values, str | bytes) or np.ndim(_magnitude(values)) != 1:
            raise TypeError(
                f"vary[{name!r}] must be a one-dimensional sequence of values, "
                f"not {type(values).__name__}."
            )
        items = list(values)
        if not items:
            raise ValueError(f"vary[{name!r}] is empty: there is nothing to run.")
        names.append(name)
        keywords[name] = keyword
        sequences.append(items)
    return names, keywords, sequences


def _keyword(name: object) -> str:
    """Return the keyword `run` takes an input as: its dots as underscores."""
    keyword = name.replace(".", "_") if isinstance(name, str) else ""
    if not keyword.isidentifier():
        raise TypeError(
            f"vary's key {name!r} must be an input record's name, which with "
            "its dots as underscores is a Python identifier (such as "
            '"volume_loss" or "south.volume_loss").'
        )
    return keyword


def _magnitude(values: Any) -> Any:
    """Return a pint array's magnitude, or the values as they are."""
    if isinstance(values, Sequence) and not isinstance(values, str | bytes):
        return [getattr(item, "magnitude", item) for item in values]
    return getattr(values, "magnitude", values)


def _combinations(sequences: list[list[Any]], mode: object) -> list[tuple[Any, ...]]:
    """Return the runs' values, in order, for the mode."""
    if len(sequences) == 1:
        if mode is not None:
            raise TypeError(
                f"mode is for two or more varied inputs; with one, there is one "
                f"run per value (mode={mode!r} given)."
            )
        return [(value,) for value in sequences[0]]
    if mode is None:
        counts = " x ".join(str(len(values)) for values in sequences)
        raise TypeError(
            f"mode is required with {len(sequences)} varied inputs, since the "
            f'runs differ: mode="grid" runs every combination ({counts}), '
            'mode="paired" runs them element by element.'
        )
    if mode not in MODES:
        raise ValueError(f'mode must be "grid" or "paired", not {mode!r}.')
    if mode == "grid":
        return list(itertools.product(*sequences))
    lengths = [len(values) for values in sequences]
    if len(set(lengths)) != 1:
        raise ValueError(
            f'mode="paired" needs sequences of equal length, not {lengths}.'
        )
    return list(zip(*sequences, strict=True))


def _as_used(entry: InputRecord, value: object) -> Any:
    """Return a given value in the record's unit, or None if it won't convert."""
    if isinstance(value, Sourced):
        value = value.value
    try:
        magnitude, _ = to_si(
            entry.name, value, unit=str(entry.value.units), plain_number="read as SI"
        )
    except Exception:
        return None
    return magnitude


def _same(first: object, second: object) -> bool:
    """Whether two magnitudes are equal to the relative tolerance."""
    a = np.asarray(first, dtype=np.float64)
    b = np.asarray(second, dtype=np.float64)
    if a.shape != b.shape:
        return False
    scale = np.maximum(np.abs(a), np.abs(b))
    return bool(np.all(np.abs(a - b) <= RELATIVE_TOLERANCE * scale))


def _match(result: Result, name: str, value: object) -> InputRecord | None:
    """Return the input record of `name` that holds `value`, if one does."""
    for entry in result.inputs:
        if entry.name != name:
            continue
        used = _as_used(entry, value)
        if used is not None and _same(used, entry.value.magnitude):
            return entry
    return None


def _check_varied(result: Result, given: dict[str, Any], index: int) -> None:
    """Raise if a varied input isn't recorded with the value given."""
    for name, value in given.items():
        if _match(result, name, value) is None:
            recorded = [
                f"{entry.value:~}" for entry in result.inputs if entry.name == name
            ]
            found = (
                f"its records of {name} hold {', '.join(recorded)}"
                if recorded
                else f"it has no input record named {name}"
            )
            raise ValueError(
                f"run {index} was given {name}={value!r}, but {found}: run didn't "
                f"pass {name} on. Name run's arguments as the inputs they set, "
                "and pass each one to the function that takes it."
            )


def _grouped(result: Result, skip: Sequence[str]) -> dict[str, list[InputRecord]]:
    groups: dict[str, list[InputRecord]] = {}
    for entry in result.inputs:
        if entry.name not in skip:
            groups.setdefault(entry.name, []).append(entry)
    return groups


def _check_fixed(
    reference: Result, result: Result, names: Sequence[str], index: int
) -> None:
    """Raise if an input that isn't varied differs from the first run's."""
    first = _grouped(reference, names)
    this = _grouped(result, names)
    for name in sorted(first.keys() | this.keys()):
        before, after = first.get(name, []), this.get(name, [])
        same = len(before) == len(after) and all(
            unit_text(a) == unit_text(b) and _same(a.value.magnitude, b.value.magnitude)
            for a, b in zip(before, after, strict=True)
        )
        if not same:
            was = ", ".join(f"{entry.value:~}" for entry in before) or "absent"
            now = ", ".join(f"{entry.value:~}" for entry in after) or "absent"
            raise ValueError(
                f"{name} isn't in vary but changed between runs ({was} in the "
                f"first successful run, {now} in run {index}), so the sweep's "
                f"fixed inputs would be wrong. Add {name} to vary, or keep it "
                "fixed in run."
            )


def _table(
    run: Callable[..., Result],
    names: list[str],
    mode: Mode | None,
    runs: list[_Run],
    reference: Result,
) -> pd.DataFrame:
    """Build the sweep's table and its attrs."""
    units: dict[str, str] = {}
    unit_of: dict[str, InputRecord] = {}
    for name in names:
        entry = _match(reference, name, runs[_first_success(runs)].given[name])
        assert entry is not None  # checked when the run completed
        unit_of[name] = entry
        units[name] = unit_text(entry)

    governing_names: list[str] = []
    for outcome in runs:
        if outcome.result is not None:
            for item in outcome.result.governing().itertuples():
                if item.name not in governing_names:
                    governing_names.append(str(item.name))
                    units[str(item.name)] = str(item.unit)
                    units[f"{item.name}_distance"] = "m"

    rows = []
    for number, outcome in enumerate(runs):
        row: dict[str, Any] = {"run": number}
        for name in names:
            row[name] = _used_value(outcome, name, unit_of[name])
        governing = (
            outcome.result.governing().set_index("name")
            if outcome.result is not None
            else None
        )
        for name in governing_names:
            if governing is not None and name in governing.index:
                row[name] = float(governing.loc[name, "value"])
                row[f"{name}_distance"] = float(governing.loc[name, "distance"])
            else:
                row[name] = math.nan
                row[f"{name}_distance"] = math.nan
        if outcome.result is not None:
            row["validity"] = outcome.result.validity
            row["warnings"] = len(outcome.result.warnings)
            row["error"] = None
        else:
            row["validity"] = None
            row["warnings"] = 0
            error = outcome.error
            row["error"] = f"{type(error).__name__}: {error}"
        rows.append(row)

    columns = ["run", *names]
    for name in governing_names:
        columns += [name, f"{name}_distance"]
    columns += ["validity", "warnings", "error"]
    table = pd.DataFrame(rows, columns=columns)
    table.attrs = {
        "units": units,
        "run": getattr(run, "__qualname__", repr(run)),
        "mode": mode,
        "vary": list(names),
        "fixed_inputs": [
            input_dict(entry) for entry in reference.inputs if entry.name not in names
        ],
    }
    return table


def _first_success(runs: list[_Run]) -> int:
    return next(
        index for index, outcome in enumerate(runs) if outcome.result is not None
    )


def _used_value(outcome: _Run, name: str, entry: InputRecord) -> Any:
    """Return a varied input as used: its record's, or converted if the run failed."""
    if outcome.result is not None:
        matched = _match(outcome.result, name, outcome.given[name])
        assert matched is not None  # checked when the run completed
        used: Any = matched.value.magnitude
    else:
        used = _as_used(entry, outcome.given[name])
        if used is None:
            return math.nan
    array = np.asarray(used, dtype=np.float64)
    return float(array) if array.ndim == 0 else array
