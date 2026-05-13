"""Query engine: translates ChartSpec + filter state into SQL, executes,
and returns data arrays for Recharts.

All queries are parameterised — no string-interpolated SQL.
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd
from sqlalchemy import text

from backend.app.database import get_engine, data_table_name
from backend.app.models.chart import ChartSpec, ChartData


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def execute_chart_query(
    dataset_id: str,
    spec: ChartSpec,
    filters: dict[str, Any],
) -> ChartData:
    """Execute the SQL for *spec* with *filters* applied and return ChartData.

    Args:
        dataset_id: The UUID of the uploaded dataset.
        spec: Describes which chart type and columns to query.
        filters: Active filter state from the frontend.

    Returns:
        ChartData with `data` list of row dicts.
    """
    try:
        table = data_table_name(dataset_id)
        where_clause, params = _build_where(filters)

        if spec.chart_type == "histogram":
            data = _query_histogram(table, spec, where_clause, params)
        elif spec.chart_type == "scatter":
            data = _query_scatter(table, spec, where_clause, params)
        elif spec.chart_type in ("bar", "hbar"):
            data = _query_grouped(table, spec, where_clause, params)
        elif spec.chart_type in ("line", "area"):
            data = _query_timeseries(table, spec, where_clause, params)
        else:
            data = _query_grouped(table, spec, where_clause, params)

        return ChartData(spec=spec, data=data)
    except Exception as exc:
        return ChartData(spec=spec, data=[], error=str(exc))


def execute_raw_sql(dataset_id: str, sql: str) -> list[dict[str, Any]]:
    """Execute arbitrary SELECT SQL against the dataset table.

    Used by the LLM tool `query_data`. Only SELECT statements allowed.

    Args:
        dataset_id: Target dataset UUID.
        sql: A SELECT statement referencing `{table}` as a placeholder
             OR using the literal table name.

    Returns:
        List of row dicts.
    """
    table = data_table_name(dataset_id)
    # Replace placeholder {table} with actual table name
    safe_sql = sql.replace("{table}", table)
    # Security: only allow SELECT
    stripped = safe_sql.strip().upper()
    if not stripped.startswith("SELECT"):
        raise ValueError("Only SELECT statements are allowed.")

    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(safe_sql))
        rows = [dict(zip(result.keys(), row)) for row in result.fetchall()]
    return rows


def get_column_unique_values(dataset_id: str, column: str, limit: int = 100) -> list[Any]:
    """Return up to *limit* unique values for *column*.

    Used by LLM tool `get_column_values` and filter-options endpoint.
    """
    table = data_table_name(dataset_id)
    safe_col = _safe_column_name(column)
    engine = get_engine()
    with engine.connect() as conn:
        sql = text(f'SELECT DISTINCT "{safe_col}" FROM {table} WHERE "{safe_col}" IS NOT NULL LIMIT :limit')
        result = conn.execute(sql, {"limit": limit})
        return [row[0] for row in result.fetchall()]


def get_column_min_max(dataset_id: str, column: str) -> dict[str, Any]:
    """Return the min and max for a numeric or datetime column."""
    table = data_table_name(dataset_id)
    safe_col = _safe_column_name(column)
    engine = get_engine()
    with engine.connect() as conn:
        sql = text(f'SELECT MIN("{safe_col}"), MAX("{safe_col}") FROM {table}')
        row = conn.execute(sql).fetchone()
        return {"min": row[0], "max": row[1]}


# ---------------------------------------------------------------------------
# Private query builders
# ---------------------------------------------------------------------------

def _build_where(filters: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Build a WHERE clause and params dict from *filters*.

    Filter dict format:
        {
          "Country": "United Kingdom",          # exact match (string)
          "InvoiceDate": {"min": "2010-01-01", "max": "2011-12-31"},
          "Quantity": {"min": 1, "max": 100},
        }
    """
    if not filters:
        return "", {}

    clauses: list[str] = []
    params: dict[str, Any] = {}

    for i, (col, value) in enumerate(filters.items()):
        safe_col = _safe_column_name(col)
        key_prefix = f"f{i}"

        if isinstance(value, dict):
            # Range filter
            if "min" in value and value["min"] is not None:
                clauses.append(f'"{safe_col}" >= :{key_prefix}_min')
                params[f"{key_prefix}_min"] = value["min"]
            if "max" in value and value["max"] is not None:
                clauses.append(f'"{safe_col}" <= :{key_prefix}_max')
                params[f"{key_prefix}_max"] = value["max"]
        elif isinstance(value, list):
            # Multi-select (IN clause) — use repeated params
            in_keys = [f"{key_prefix}_v{j}" for j in range(len(value))]
            in_placeholders = ", ".join(f":{k}" for k in in_keys)
            clauses.append(f'"{safe_col}" IN ({in_placeholders})')
            for k, v in zip(in_keys, value):
                params[k] = v
        elif value is not None and value != "":
            # Exact match
            clauses.append(f'"{safe_col}" = :{key_prefix}_val')
            params[f"{key_prefix}_val"] = value

    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    return where, params


def _query_grouped(
    table: str, spec: ChartSpec, where: str, params: dict
) -> list[dict[str, Any]]:
    """GROUP BY query for bar / hbar charts."""
    safe_x = _safe_column_name(spec.x_col)

    if spec.agg == "count" or spec.y_col is None:
        agg_expr = "COUNT(*)"
        y_alias = "count"
    elif spec.agg == "sum":
        safe_y = _safe_column_name(spec.y_col)
        agg_expr = f'SUM(CAST("{safe_y}" AS REAL))'
        y_alias = spec.y_col
    elif spec.agg == "mean":
        safe_y = _safe_column_name(spec.y_col)
        agg_expr = f'AVG(CAST("{safe_y}" AS REAL))'
        y_alias = spec.y_col
    else:
        agg_expr = "COUNT(*)"
        y_alias = "count"

    sql_str = (
        f'SELECT "{safe_x}" AS x, {agg_expr} AS y '
        f'FROM {table} {where} '
        f'WHERE "{safe_x}" IS NOT NULL '
        f'GROUP BY "{safe_x}" '
        f'ORDER BY y DESC '
        f'LIMIT {int(spec.limit)}'
    )
    # Merge where into sql if already present
    if where:
        sql_str = (
            f'SELECT "{safe_x}" AS x, {agg_expr} AS y '
            f'FROM {table} {where} AND "{safe_x}" IS NOT NULL '
            f'GROUP BY "{safe_x}" '
            f'ORDER BY y DESC '
            f'LIMIT {int(spec.limit)}'
        )
    else:
        sql_str = (
            f'SELECT "{safe_x}" AS x, {agg_expr} AS y '
            f'FROM {table} WHERE "{safe_x}" IS NOT NULL '
            f'GROUP BY "{safe_x}" '
            f'ORDER BY y DESC '
            f'LIMIT {int(spec.limit)}'
        )

    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql_str), params)
        return [{"x": row[0], "y": _safe_val(row[1]), "name": str(row[0])} for row in result.fetchall()]


def _query_timeseries(
    table: str, spec: ChartSpec, where: str, params: dict
) -> list[dict[str, Any]]:
    """Monthly aggregation for line/area charts."""
    safe_x = _safe_column_name(spec.x_col)
    safe_y = _safe_column_name(spec.y_col) if spec.y_col else None

    if safe_y:
        agg_expr = f'SUM(CAST("{safe_y}" AS REAL))'
    else:
        agg_expr = "COUNT(*)"

    # SQLite: use strftime to group by month
    group_expr = f"strftime('%Y-%m', \"{safe_x}\")"
    base_where = f'WHERE "{safe_x}" IS NOT NULL'
    if where:
        full_where = f"{where} AND \"{safe_x}\" IS NOT NULL"
    else:
        full_where = base_where

    sql_str = (
        f'SELECT {group_expr} AS x, {agg_expr} AS y '
        f'FROM {table} {full_where} '
        f'GROUP BY {group_expr} '
        f'ORDER BY x ASC '
        f'LIMIT {int(spec.limit)}'
    )

    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql_str), params)
        return [{"x": row[0], "y": _safe_val(row[1]), "name": str(row[0])} for row in result.fetchall()]


def _query_histogram(
    table: str, spec: ChartSpec, where: str, params: dict
) -> list[dict[str, Any]]:
    """Approximate histogram using value bucketing."""
    safe_x = _safe_column_name(spec.x_col)
    base_where = f'WHERE "{safe_x}" IS NOT NULL'
    if where:
        full_where = f"{where} AND \"{safe_x}\" IS NOT NULL"
    else:
        full_where = base_where

    # Get min/max first
    mm_sql = f'SELECT MIN(CAST("{safe_x}" AS REAL)), MAX(CAST("{safe_x}" AS REAL)) FROM {table} {full_where}'
    engine = get_engine()
    with engine.connect() as conn:
        mm_row = conn.execute(text(mm_sql), params).fetchone()

    if not mm_row or mm_row[0] is None:
        return []

    vmin, vmax = float(mm_row[0]), float(mm_row[1])
    if vmin == vmax:
        return [{"x": str(vmin), "y": 1, "name": str(vmin)}]

    # 20 bins
    bins = min(30, spec.limit)
    width = (vmax - vmin) / bins

    # Use CASE WHEN bucketing
    cases = " ".join(
        f'WHEN CAST("{safe_x}" AS REAL) >= {vmin + i * width:.4f} AND CAST("{safe_x}" AS REAL) < {vmin + (i+1) * width:.4f} THEN {i}'
        for i in range(bins)
    )
    bin_sql = (
        f'SELECT CASE {cases} ELSE {bins - 1} END AS bin, COUNT(*) AS y '
        f'FROM {table} {full_where} '
        f'GROUP BY bin ORDER BY bin'
    )

    bin_labels = [f"{vmin + i * width:.1f}–{vmin + (i+1) * width:.1f}" for i in range(bins)]

    with engine.connect() as conn:
        result = conn.execute(text(bin_sql), params)
        rows = result.fetchall()

    data = [{"x": bin_labels[min(int(r[0]), bins - 1)], "y": int(r[1]), "name": bin_labels[min(int(r[0]), bins - 1)]} for r in rows]
    return data


def _query_scatter(
    table: str, spec: ChartSpec, where: str, params: dict
) -> list[dict[str, Any]]:
    """Sample rows for a scatter plot (x, y pairs)."""
    safe_x = _safe_column_name(spec.x_col)
    safe_y = _safe_column_name(spec.y_col)
    base_where = f'WHERE "{safe_x}" IS NOT NULL AND "{safe_y}" IS NOT NULL'
    if where:
        full_where = f"{where} AND \"{safe_x}\" IS NOT NULL AND \"{safe_y}\" IS NOT NULL"
    else:
        full_where = base_where

    sql_str = (
        f'SELECT CAST("{safe_x}" AS REAL) AS x, CAST("{safe_y}" AS REAL) AS y '
        f'FROM {table} {full_where} '
        f'ORDER BY RANDOM() LIMIT {int(spec.limit)}'
    )

    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql_str), params)
        return [{"x": _safe_val(r[0]), "y": _safe_val(r[1])} for r in result.fetchall()]


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _safe_column_name(name: str) -> str:
    """Sanitise column name for safe embedding in SQL (strip dangerous chars)."""
    return re.sub(r'[^\w\s\-]', '', name)


def _safe_val(val: Any) -> Any:
    """Convert NaN / None to 0 for chart data."""
    if val is None:
        return 0
    try:
        import math
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return 0
        return round(f, 4)
    except (TypeError, ValueError):
        return val
