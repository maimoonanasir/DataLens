"""Data profiling service.

Analyses a Pandas DataFrame and returns a list of ColumnProfile objects
describing column types, null rates, and basic statistics.

Column type detection rules
----------------------------
- datetime  : column name contains 'date'/'time', or pd.to_datetime succeeds
              on >80% of non-null values
- numeric   : Pandas dtype is numeric (int / float)
- categorical: object dtype with unique_count <= 100 OR unique_count / len <= 0.05
- text       : everything else (high-cardinality string columns)
"""

from __future__ import annotations

import json
import math
from typing import Any

import pandas as pd

from backend.app.models.dataset import ColumnProfile


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def profile_dataframe(df: pd.DataFrame) -> list[ColumnProfile]:
    """Return a ColumnProfile for every column in *df*.

    Args:
        df: Raw dataframe loaded from the uploaded CSV.

    Returns:
        Ordered list of ColumnProfile objects matching df.columns order.
    """
    profiles: list[ColumnProfile] = []
    for col in df.columns:
        series = df[col]
        dtype = _detect_dtype(col, series, len(df))
        profiles.append(
            ColumnProfile(
                name=col,
                dtype=dtype,
                null_count=int(series.isna().sum()),
                null_pct=round(float(series.isna().mean()) * 100, 2),
                unique_count=int(series.nunique()),
                stats=_compute_stats(series, dtype),
            )
        )
    return profiles


def profiles_to_json(profiles: list[ColumnProfile]) -> str:
    """Serialise profiles to a JSON string for SQLite storage."""
    return json.dumps([p.model_dump() for p in profiles])


def profiles_from_json(raw: str) -> list[ColumnProfile]:
    """Deserialise profiles from a JSON string stored in SQLite."""
    return [ColumnProfile(**item) for item in json.loads(raw)]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _detect_dtype(col_name: str, series: pd.Series, n_rows: int) -> str:
    """Infer a human-readable dtype tag for *series*."""
    # Numeric first (most reliable)
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"

    # Datetime: check column name heuristic + try parsing
    col_lower = col_name.lower()
    if any(token in col_lower for token in ("date", "time", "dt", "timestamp")):
        parsed = pd.to_datetime(series, errors="coerce", format="mixed")
        if parsed.notna().mean() > 0.5:
            return "datetime"

    # Try datetime parsing regardless of column name
    if pd.api.types.is_object_dtype(series) and n_rows > 0:
        sample = series.dropna().head(200)
        if len(sample) > 0:
            parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
            if parsed.notna().mean() > 0.8:
                return "datetime"

    # Categorical: low cardinality or low cardinality ratio
    if pd.api.types.is_object_dtype(series):
        unique_count = series.nunique()
        ratio = unique_count / max(n_rows, 1)
        if unique_count <= 100 or ratio <= 0.05:
            return "categorical"
        return "text"

    # Boolean
    if pd.api.types.is_bool_dtype(series):
        return "categorical"

    return "text"


def _compute_stats(series: pd.Series, dtype: str) -> dict[str, Any]:
    """Compute dtype-appropriate statistics for *series*."""
    stats: dict[str, Any] = {}

    if dtype == "numeric":
        clean = series.dropna()
        if len(clean) == 0:
            return {"min": None, "max": None, "mean": None, "median": None, "std": None}
        stats["min"] = _safe_float(clean.min())
        stats["max"] = _safe_float(clean.max())
        stats["mean"] = _safe_float(clean.mean())
        stats["median"] = _safe_float(clean.median())
        stats["std"] = _safe_float(clean.std())

    elif dtype == "datetime":
        parsed = pd.to_datetime(series, errors="coerce", format="mixed")
        clean = parsed.dropna()
        if len(clean) == 0:
            return {"min": None, "max": None}
        stats["min"] = str(clean.min())[:10]
        stats["max"] = str(clean.max())[:10]

    elif dtype == "categorical":
        top = series.value_counts().head(10)
        stats["top_values"] = [
            {"value": str(k), "count": int(v)} for k, v in top.items()
        ]
        stats["most_common"] = str(top.index[0]) if len(top) > 0 else None

    else:  # text
        lengths = series.dropna().str.len()
        if len(lengths) > 0:
            stats["avg_length"] = _safe_float(lengths.mean())
            stats["max_length"] = int(lengths.max())
        else:
            stats["avg_length"] = None
            stats["max_length"] = None

    return stats


def _safe_float(value: Any) -> float | None:
    """Convert *value* to a JSON-safe float, returning None for NaN/Inf."""
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, 4)
    except (TypeError, ValueError):
        return None
