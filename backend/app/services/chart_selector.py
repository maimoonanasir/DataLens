"""Chart auto-selection service.

Given a list of ColumnProfile objects, selects 4–6 meaningful chart types
appropriate to the data and returns ChartSpec objects the frontend renders.

Selection algorithm
--------------------
1. Line/Area chart  → first datetime column vs a numeric (revenue/sales over time)
2. Bar chart        → highest-cardinality categorical (≤50 unique) vs numeric sum
3. Horizontal bar   → second categorical vs numeric (top-N)
4. Histogram        → most interesting numeric (highest std relative to mean)
5. Scatter plot     → two numerics with lowest correlation to catch relationships
6. Donut/Bar        → categorical with fewest unique values (e.g., boolean flags)

The function always tries to return ≥ 4 charts and at most 6.
"""

from __future__ import annotations

import uuid

from backend.app.models.chart import ChartSpec
from backend.app.models.dataset import ColumnProfile


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def select_charts(profiles: list[ColumnProfile]) -> list[ChartSpec]:
    """Return 4–6 ChartSpec objects auto-selected from *profiles*.

    Args:
        profiles: Output of profiler.profile_dataframe()

    Returns:
        Between 4 and 6 ChartSpec objects, ordered for dashboard display.
    """
    specs: list[ChartSpec] = []

    numerics = [p for p in profiles if p.dtype == "numeric"]
    categoricals = [p for p in profiles if p.dtype == "categorical"]
    datetimes = [p for p in profiles if p.dtype == "datetime"]

    # -----------------------------------------------------------------------
    # 1. Time-series line chart (datetime × numeric)
    # -----------------------------------------------------------------------
    if datetimes and numerics:
        dt_col = datetimes[0]
        num_col = _pick_numeric_for_agg(numerics)
        specs.append(ChartSpec(
            chart_id=f"line_{dt_col.name.lower().replace(' ', '_')}",
            chart_type="line",
            title=f"{num_col.name} Over Time",
            x_col=dt_col.name,
            y_col=num_col.name,
            agg="sum",
            limit=100,
        ))

    # -----------------------------------------------------------------------
    # 2. Bar chart — top categorical × numeric
    # -----------------------------------------------------------------------
    if categoricals and numerics:
        cat_col = _pick_categorical(categoricals, prefer_mid_cardinality=True)
        num_col = _pick_numeric_for_agg(numerics)
        specs.append(ChartSpec(
            chart_id=f"bar_{cat_col.name.lower().replace(' ', '_')}",
            chart_type="bar",
            title=f"{num_col.name} by {cat_col.name}",
            x_col=cat_col.name,
            y_col=num_col.name,
            agg="sum",
            limit=20,
        ))

    # -----------------------------------------------------------------------
    # 3. Horizontal bar — second categorical (top-N)
    # -----------------------------------------------------------------------
    remaining_cats = [c for c in categoricals if c.name != (specs[-1].x_col if specs else "")]
    if remaining_cats and numerics:
        cat2 = _pick_categorical(remaining_cats, prefer_mid_cardinality=False)
        num2 = _pick_numeric_for_agg(numerics)
        specs.append(ChartSpec(
            chart_id=f"hbar_{cat2.name.lower().replace(' ', '_')}",
            chart_type="hbar",
            title=f"Top {cat2.name} by {num2.name}",
            x_col=cat2.name,
            y_col=num2.name,
            agg="sum",
            limit=15,
        ))

    # -----------------------------------------------------------------------
    # 4. Histogram — most variable numeric
    # -----------------------------------------------------------------------
    if numerics:
        num_hist = _pick_most_variable_numeric(numerics)
        specs.append(ChartSpec(
            chart_id=f"hist_{num_hist.name.lower().replace(' ', '_')}",
            chart_type="histogram",
            title=f"Distribution of {num_hist.name}",
            x_col=num_hist.name,
            y_col=None,
            agg="count",
            limit=30,
        ))

    # -----------------------------------------------------------------------
    # 5. Scatter plot — two numerics (if available)
    # -----------------------------------------------------------------------
    if len(numerics) >= 2:
        n1, n2 = _pick_scatter_pair(numerics)
        specs.append(ChartSpec(
            chart_id=f"scatter_{n1.name.lower().replace(' ', '_')}_{n2.name.lower().replace(' ', '_')}",
            chart_type="scatter",
            title=f"{n1.name} vs {n2.name}",
            x_col=n1.name,
            y_col=n2.name,
            agg="none",
            limit=500,
        ))

    # -----------------------------------------------------------------------
    # 6. Count bar — low-cardinality categorical (if not already used)
    # -----------------------------------------------------------------------
    used_cats = {s.x_col for s in specs}
    low_card_cats = [c for c in categoricals if c.name not in used_cats and c.unique_count <= 10]
    if low_card_cats and len(specs) < 6:
        cat3 = low_card_cats[0]
        specs.append(ChartSpec(
            chart_id=f"count_{cat3.name.lower().replace(' ', '_')}",
            chart_type="bar",
            title=f"Order Count by {cat3.name}",
            x_col=cat3.name,
            y_col=None,
            agg="count",
            limit=20,
        ))

    # Clamp to 4–6
    if len(specs) < 4 and numerics:
        # Fallback: add more numeric histograms
        for n in numerics:
            if len(specs) >= 4:
                break
            cid = f"hist_extra_{n.name.lower().replace(' ', '_')}"
            if not any(s.chart_id == cid for s in specs):
                specs.append(ChartSpec(
                    chart_id=cid,
                    chart_type="histogram",
                    title=f"Distribution of {n.name}",
                    x_col=n.name,
                    y_col=None,
                    agg="count",
                    limit=30,
                ))

    return specs[:6]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _pick_numeric_for_agg(numerics: list[ColumnProfile]) -> ColumnProfile:
    """Pick the numeric column most appropriate for SUM aggregation.

    Prefers columns that look like value/amount/price/revenue.
    """
    keywords = ("price", "amount", "revenue", "value", "sales", "quantity", "qty", "total")
    for kw in keywords:
        for n in numerics:
            if kw in n.name.lower():
                return n
    return numerics[0]


def _pick_categorical(cats: list[ColumnProfile], prefer_mid_cardinality: bool) -> ColumnProfile:
    """Pick a categorical column.

    If prefer_mid_cardinality=True, prefer columns with 5–50 unique values
    (good for bar charts with readable x-axis labels).
    """
    if prefer_mid_cardinality:
        mid = [c for c in cats if 5 <= c.unique_count <= 50]
        if mid:
            return mid[0]
    return cats[0]


def _pick_most_variable_numeric(numerics: list[ColumnProfile]) -> ColumnProfile:
    """Pick the numeric with the highest coefficient of variation (std/mean)."""
    best = numerics[0]
    best_cv = 0.0
    for n in numerics:
        mean = n.stats.get("mean")
        std = n.stats.get("std")
        if mean and std and abs(float(mean)) > 0:
            cv = abs(float(std) / float(mean))
            if cv > best_cv:
                best_cv = cv
                best = n
    return best


def _pick_scatter_pair(numerics: list[ColumnProfile]) -> tuple[ColumnProfile, ColumnProfile]:
    """Pick two numeric columns for a scatter plot.

    Prefers pairs that represent different concepts (e.g., price × quantity).
    """
    price_kw = ("price", "unit", "value", "cost")
    qty_kw = ("quantity", "qty", "count", "amount", "volume")

    price_cols = [n for n in numerics if any(k in n.name.lower() for k in price_kw)]
    qty_cols = [n for n in numerics if any(k in n.name.lower() for k in qty_kw)]

    if price_cols and qty_cols and price_cols[0] != qty_cols[0]:
        return price_cols[0], qty_cols[0]

    return numerics[0], numerics[1]
