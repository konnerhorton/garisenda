"""The one result shape every analysis returns."""

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd

from garisenda._inputs import InputRecord
from garisenda.sources._movement import Flag, MethodRecord, Verdict

if TYPE_CHECKING:
    from garisenda._asset import Asset
    from garisenda.sources._movement import Source

CHECK_COLUMNS = (
    "check",
    "value",
    "unit",
    "limit",
    "utilization",
    "governing_distance",
    "passes",
    "governed_by",
    "analytical",
    "analytical_distance",
    "discrete",
    "discrete_distance",
    "difference",
)
"""The columns of `Result.checks`, empty for an analysis with no checks."""

CHECK_TYPES = {
    "check": "object",
    "value": "float64",
    "unit": "object",
    "limit": "float64",
    "utilization": "float64",
    "governing_distance": "float64",
    "passes": "boolean",
    "governed_by": "object",
    "analytical": "float64",
    "analytical_distance": "float64",
    "discrete": "float64",
    "discrete_distance": "float64",
    "difference": "float64",
}
"""Each column's dtype: ``passes`` is pandas' nullable boolean, NA with no limit."""

GOVERNING_COLUMNS = ("name", "column", "value", "unit", "distance", "verdict")
"""The columns of `Result.governing()`."""

# The governing values, in order: the row's name, the column it reads, and the
# sign of the extreme (+1 the largest positive, -1 the most negative).
EXTREMES: tuple[tuple[str, str, int], ...] = (
    ("largest_settlement", "vertical", 1),
    ("largest_tension", "along_strain", 1),
    ("largest_compression", "along_strain", -1),
    ("largest_hogging", "vertical_curvature", 1),
    ("largest_sagging", "vertical_curvature", -1),
)

# How the summary prints them: per column, its label and the rows' short names.
SUMMARY: tuple[tuple[str, str, tuple[tuple[str, str], ...]], ...] = (
    ("vertical", "settlement", (("largest_settlement", "largest"),)),
    (
        "along_strain",
        "strain along",
        (("largest_tension", "tension"), ("largest_compression", "compression")),
    ),
    (
        "vertical_curvature",
        "vertical curvature",
        (("largest_hogging", "hogging"), ("largest_sagging", "sagging")),
    ),
)


def empty_checks() -> pd.DataFrame:
    """Return an empty checks table with its columns and their dtypes."""
    return pd.DataFrame(
        {name: pd.Series([], dtype=CHECK_TYPES[name]) for name in CHECK_COLUMNS}
    )


@dataclass(frozen=True)
class Result:
    """The result of an analysis: one shape for every analysis.

    Views (`to_frame`, `to_dict`, the text summary of `repr`) read these parts
    and never recalculate, so two views can't disagree.

    Attributes
    ----------
    analysis : str
        The analysis that made it, for example ``"movement_profile"``.
    subject : str
        What it was run on: the utility's or building's id.
    values : pandas.DataFrame
        The computed quantities, one row per station, keyed by the
        ``distance`` column (m along the asset), with units in
        ``values.attrs["units"]``.
    checks : pandas.DataFrame
        Each check against its limit, one row per check: ``check`` (its
        name), ``value`` (the governing value, in ``unit``), ``limit`` (NaN
        if none was given), ``utilization``, ``governing_distance`` (m),
        ``passes`` (pandas NA with no limit), ``governed_by``
        (``"analytical"`` or ``"discrete"``), ``analytical`` and
        ``analytical_distance``, ``discrete`` and ``discrete_distance``, and
        ``difference`` (discrete - analytical). Empty for an analysis with no
        checks, such as a movement profile.
    method : tuple of MethodRecord
        The methods used, with their equations and sources.
    assumptions : tuple of str
        What the methods assume and garisenda can't check.
    inputs : tuple of InputRecord
        Every input used, with its kind and source.
    validity : {"within", "marginal", "outside"}
        The worst verdict over the stations and the flags.
    warnings : tuple of Flag
        Everything flagged, with ``points`` as row positions in `values`.
    source : Source or None
        The source the analysis evaluated, kept so a figure can draw the field
        beyond the asset. Not part of the views or of equality.
    asset : Utility, Building or None
        The asset it was run on, kept for the same reason.
    """

    analysis: str
    subject: str
    values: pd.DataFrame
    checks: pd.DataFrame
    method: tuple[MethodRecord, ...]
    assumptions: tuple[str, ...]
    inputs: tuple[InputRecord, ...]
    validity: Verdict
    warnings: tuple[Flag, ...]
    source: "Source | None" = field(default=None, repr=False, compare=False)
    asset: "Asset | None" = field(default=None, repr=False, compare=False)

    def __eq__(self, other: object) -> bool:
        """Compare every part but `source` and `asset`, tables by content.

        The generated `__eq__` compares DataFrames with ``==``, which is
        elementwise and can't be a bool (and from Python 3.13 it no longer
        short-cuts on identity), so the tables are compared with
        `DataFrame.equals` and their ``attrs``.
        """
        if not isinstance(other, Result):
            return NotImplemented
        for table in ("values", "checks"):
            mine, theirs = getattr(self, table), getattr(other, table)
            if not (mine.equals(theirs) and mine.attrs == theirs.attrs):
                return False
        return (
            self.analysis,
            self.subject,
            self.method,
            self.assumptions,
            self.inputs,
            self.validity,
            self.warnings,
        ) == (
            other.analysis,
            other.subject,
            other.method,
            other.assumptions,
            other.inputs,
            other.validity,
            other.warnings,
        )

    __hash__ = None  # type: ignore[assignment]  # holds DataFrames: unhashable

    def governing(self) -> pd.DataFrame:
        """Return the governing values: the extremes of `values`, never recalculated.

        One row per extreme whose column the result has, in this order:

        - ``largest_settlement``: the largest positive ``vertical``;
        - ``largest_tension``: the largest positive ``along_strain``;
        - ``largest_compression``: the most negative ``along_strain``;
        - ``largest_hogging``: the largest positive ``vertical_curvature``;
        - ``largest_sagging``: the most negative ``vertical_curvature``.

        Returns
        -------
        pandas.DataFrame
            Columns ``name``, ``column``, ``value`` (signed, as in `values`),
            ``unit``, ``distance`` (m, where it occurs) and ``verdict`` (the
            station's, or None if `values` has no verdicts). If no station has
            a value of the extreme's sign, ``value`` and ``distance`` are NaN
            and ``verdict`` None: nothing is there to report, and nothing is
            filled in. Equal extremes, within 1e-9 of the
            extreme's size, go to the smallest distance.
        """
        values = self.values
        units: dict[str, str] = values.attrs.get("units", {})
        rows = []
        for name, column, sign in EXTREMES:
            if column not in values:
                continue
            row: dict[str, Any] = {
                "name": name,
                "column": column,
                "value": math.nan,
                "unit": units.get(column, ""),
                "distance": math.nan,
                "verdict": None,
            }
            signed = sign * values[column].to_numpy(dtype=np.float64)
            found = np.isfinite(signed) & (signed > 0)
            if found.any():
                extreme = float(np.max(signed[found]))
                tied = np.flatnonzero(found & (signed >= extreme * (1 - 1e-9)))
                index = _first_by_distance(values, tied)
                row["value"] = float(values[column].iloc[index])
                if "distance" in values:
                    row["distance"] = float(values["distance"].iloc[index])
                if "verdict" in values:
                    row["verdict"] = str(values["verdict"].iloc[index])
            rows.append(row)
        return pd.DataFrame(rows, columns=list(GOVERNING_COLUMNS))

    def to_frame(self) -> pd.DataFrame:
        """Return a copy of `values`, with its units in ``attrs["units"]``."""
        frame = self.values.copy()
        frame.attrs = {"units": dict(self.values.attrs.get("units", {}))}
        return frame

    def to_dict(self) -> dict[str, Any]:
        """Return every part as plain JSON types (non-finite numbers as None).

        Returns
        -------
        dict
            ``analysis``, ``subject``, ``values`` (a list per column),
            ``units``, ``checks`` (a list of rows), ``method``, ``assumptions``,
            ``inputs`` (each with ``name``, ``magnitude``, ``unit``, ``kind``,
            ``given_as`` and ``source``), ``validity`` and ``warnings`` (each
            with ``verdict``, ``reason``, ``limit``, ``points`` and
            ``source``, the name of the source in a superposition it came
            from, empty for a lone source).
        """
        return {
            "analysis": self.analysis,
            "subject": self.subject,
            "values": {
                str(name): _plain(column.tolist())
                for name, column in self.values.items()
            },
            "units": dict(self.values.attrs.get("units", {})),
            "checks": _plain(self.checks.to_dict(orient="records")),
            "method": [
                {
                    "name": record.name,
                    "equations": list(record.equations),
                    "source": record.source,
                }
                for record in self.method
            ],
            "assumptions": list(self.assumptions),
            "inputs": [input_dict(entry) for entry in self.inputs],
            "validity": self.validity,
            "warnings": [
                {
                    "verdict": flag.verdict,
                    "reason": flag.reason,
                    "limit": flag.limit,
                    "points": list(flag.points),
                    "source": flag.source,
                }
                for flag in self.warnings
            ],
        }

    def __repr__(self) -> str:
        """Return a short text summary: validity, warnings and the extremes."""
        values = self.values
        lines = [
            f"{self.analysis} of {self.subject!r}: {self.validity}, "
            f"{len(values)} stations"
        ]
        distance = values.get("distance")
        governing = self.governing().set_index("name")
        for column, label, names in SUMMARY:
            if column not in values:
                continue
            parts = []
            for name, short in names:
                row = governing.loc[name]
                if not math.isfinite(row["value"]):
                    parts.append(f"{short} none")
                    continue
                where = (
                    ""
                    if not math.isfinite(row["distance"])
                    else f" at {row['distance']:.4g} m"
                )
                parts.append(f"{short} {row['value']:.5g}{_unit(row['unit'])}{where}")
            lines.append(f"  {label}: {'; '.join(parts)}")
        checks = list(self.checks.itertuples(index=False))
        joints = [check for check in checks if check.check.startswith("joint_")]
        if joints:
            groups = [
                ("joints", joints),
                ("barrel", [check for check in checks if check not in joints]),
            ]
            for heading, group in groups:
                lines.append(f"  {heading}:")
                lines.extend(
                    f"    {check.check}: {_check_text(check)}" for check in group
                )
        else:
            lines.extend(f"  {check.check}: {_check_text(check)}" for check in checks)
        for flag in self.warnings:
            lines.append(f"  {flag.verdict}: {flag_text(flag)}")
            if distance is not None and flag.points:
                covered = distance.iloc[list(flag.points)]
                lines.append(
                    f"    at {len(flag.points)} stations, distance "
                    f"{covered.min():.4g} m to {covered.max():.4g} m"
                )
        lines.append(f"  {len(self.assumptions)} assumptions (see .assumptions)")
        return "\n".join(lines)


def flag_text(flag: Flag) -> str:
    """Return a flag's reason, prefixed ``"<source>: "`` when it has one."""
    return f"{flag.source}: {flag.reason}" if flag.source else flag.reason


def input_dict(entry: InputRecord) -> dict[str, Any]:
    """Return an input record as plain JSON types, as `Result.to_dict` gives it."""
    return {
        "name": entry.name,
        "magnitude": (
            entry.value
            if isinstance(entry.value, str)
            else _plain(np.asarray(entry.value.magnitude).tolist())
        ),
        "unit": unit_text(entry),
        "kind": entry.kind,
        "given_as": entry.given_as,
        "source": entry.source,
    }


def unit_text(entry: InputRecord) -> str:
    """Return an input record's unit as text, ``"dimensionless"`` for none.

    A named method (a string value) has no unit: ``""``, so it doesn't read
    as a number.
    """
    if isinstance(entry.value, str):
        return ""
    return f"{entry.value.units:~}" or "dimensionless"


def value_text(entry: InputRecord) -> str:
    """Return an input record's value as text: the quantity, or the method's name."""
    if isinstance(entry.value, str):
        return entry.value
    return f"{entry.value:~}"


def _first_by_distance(values: pd.DataFrame, positions: Any) -> int:
    """Return the position, of some, with the smallest distance (or the first)."""
    if "distance" not in values:
        return int(positions[0])
    distance = values["distance"].to_numpy(dtype=np.float64)[positions]
    return int(positions[int(np.argmin(distance))])


def _check_text(check: Any) -> str:
    """Return a check's line of the summary, after its name."""
    if not math.isfinite(check.value):
        return (
            "not determined"
            if check.passes is pd.NA and math.isfinite(check.limit)
            else "none"
        )
    unit = _unit(check.unit)
    text = f"{check.value:.5g}{unit}"
    if math.isfinite(check.governing_distance):
        text += f" at {check.governing_distance:.4g} m"
    text += f" ({check.governed_by})"
    if not math.isfinite(check.limit):
        return f"{text}, no limit"
    limit = f"{check.limit:.5g}{unit}"
    return f"{text}, utilization {check.utilization:.3g} against {limit}"


def _unit(unit: str | None) -> str:
    return "" if unit in (None, "", "dimensionless") else f" {unit}"


def _plain(value: Any) -> Any:
    """Make a value JSON-ready: numpy scalars as Python, NA and non-finite as None."""
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_plain(item) for item in value]
    if value is pd.NA:
        return None
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value
