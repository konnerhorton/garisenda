"""The one result shape every analysis returns (SPEC §5.1)."""

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from garisenda._inputs import InputRecord
from garisenda.sources._movement import Flag, MethodRecord, Verdict

CHECK_COLUMNS = (
    "check",
    "value",
    "limit",
    "utilization",
    "governing_distance",
    "passes",
)
"""The columns of `Result.checks`, empty until the utility checks (M3)."""

# The extremes the summary reports, for the columns a result has: the column,
# its label, and the labels of its largest and smallest values (None to skip).
EXTREMES: tuple[tuple[str, str, str | None, str | None], ...] = (
    ("vertical", "settlement", "largest", None),
    ("along_strain", "strain along", "tension", "compression"),
    ("vertical_curvature", "vertical curvature", "hogging", "sagging"),
    ("lateral_curvature", "lateral curvature", "largest", "smallest"),
)


def empty_checks() -> pd.DataFrame:
    """Return an empty checks table with its columns."""
    return pd.DataFrame({name: [] for name in CHECK_COLUMNS})


@dataclass(frozen=True)
class Result:
    """The result of an analysis: one shape for every analysis (SPEC §5.1).

    Views (`to_frame`, `to_dict`, the text summary of `repr`) read these parts
    and never recalculate, so two views can't disagree.

    Attributes
    ----------
    analysis : str
        The analysis that made it, for example ``"movement_profile"``.
    subject : str
        What it was run on: the utility's id.
    values : pandas.DataFrame
        The computed quantities, one row per station, keyed by the
        ``distance`` column (m along the asset), with units in
        ``values.attrs["units"]`` (SPEC §6).
    checks : pandas.DataFrame
        Each quantity against its limit: columns ``check``, ``value``,
        ``limit``, ``utilization``, ``governing_distance`` and ``passes``.
        Empty until the utility checks (M3).
    method : tuple of MethodRecord
        The methods used, with their equations and sources.
    assumptions : tuple of str
        What the methods assume and garisenda can't check.
    inputs : tuple of InputRecord
        Every input used, with its kind and source (SPEC §4).
    validity : {"within", "marginal", "outside"}
        The worst verdict over the stations and the flags (SPEC §5.2).
    warnings : tuple of Flag
        Everything flagged, with ``points`` as row positions in `values`.
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
            ``given_as`` and ``source``), ``validity`` and ``warnings``.
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
            "inputs": [
                {
                    "name": entry.name,
                    "magnitude": _plain(np.asarray(entry.value.magnitude).tolist()),
                    "unit": f"{entry.value.units:~}" or "dimensionless",
                    "kind": entry.kind,
                    "given_as": entry.given_as,
                    "source": entry.source,
                }
                for entry in self.inputs
            ],
            "validity": self.validity,
            "warnings": [
                {
                    "verdict": flag.verdict,
                    "reason": flag.reason,
                    "limit": flag.limit,
                    "points": list(flag.points),
                }
                for flag in self.warnings
            ],
        }

    def __repr__(self) -> str:
        """Return a short text summary: validity, warnings and the extremes."""
        values = self.values
        units: dict[str, str] = values.attrs.get("units", {})
        lines = [
            f"{self.analysis} of {self.subject!r}: {self.validity}, "
            f"{len(values)} stations"
        ]
        distance = values.get("distance")
        for column, label, high, low in EXTREMES:
            if column not in values or len(values) == 0:
                continue
            data = values[column].to_numpy(dtype=np.float64)
            if not np.isfinite(data).any():
                continue
            parts = []
            for name, index in ((high, np.nanargmax(data)), (low, np.nanargmin(data))):
                if name is None:
                    continue
                where = "" if distance is None else f" at {distance.iloc[index]:.4g} m"
                parts.append(
                    f"{name} {data[index]:.5g}{_unit(units.get(column))}{where}"
                )
            lines.append(f"  {label}: {'; '.join(parts)}")
        if not self.checks.empty:
            failing = int((~self.checks["passes"].astype(bool)).sum())
            lines.append(f"  checks: {len(self.checks)}, {failing} failing")
        for flag in self.warnings:
            lines.append(f"  {flag.verdict}: {flag.reason}")
            if distance is not None and flag.points:
                covered = distance.iloc[list(flag.points)]
                lines.append(
                    f"    at {len(flag.points)} stations, distance "
                    f"{covered.min():.4g} m to {covered.max():.4g} m"
                )
        lines.append(f"  {len(self.assumptions)} assumptions (see .assumptions)")
        return "\n".join(lines)


def _unit(unit: str | None) -> str:
    return "" if unit in (None, "", "dimensionless") else f" {unit}"


def _plain(value: Any) -> Any:
    """Make a value JSON-ready: numpy scalars as Python, non-finite as None."""
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_plain(item) for item in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value
