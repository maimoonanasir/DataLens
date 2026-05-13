"""Chart auto-selection service.

Given a list of ColumnProfile objects, selects 4-6 meaningful chart types
appropriate to the data and returns ChartSpec objects the frontend renders.

This version is dataset-aware: it prioritises columns that look like
outcome / measure variables (readmitted, A1Cresult, time_in_hospital,
num_medications, diabetesMed, change) and excludes identifier columns
(encounter_id, patient_nbr).
"""

from __future__ import annotations

import uuid

from backend.app.models.chart import ChartSpec
from backend.app.models.dataset import ColumnProfile


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def select_charts(profiles: list[ColumnProfile]) -> list[ChartSpec]:
    """Return up to 6 ChartSpec objects, picking the most insightful charts."""

    # Exclude IDs from being used as measures or x-axes
    numerics = [p for p in profiles if p.dtype == "numeric" and not _is_id_column(p.name)]
    categoricals = [p for p in profiles if p.dtype == "categorical" and not _is_id_column(p.name)]
    datetimes = [p for p in profiles if p.dtype == "datetime"]

    by_name = {p.name.lower(): p for p in profiles}

    specs: list[ChartSpec] = []
    used_columns: set[str] = set()

    def has(name: str) -> bool:
        return name.lower() in by_name

    def col(name: str) -> ColumnProfile:
        return by_name[name.lower()]

    # -----------------------------------------------------------------------
    # 1. KEY OUTCOME — "Readmission status" or similar binary/tri-class column
    # -----------------------------------------------------------------------
    outcome_candidates = ["readmitted", "outcome", "status", "result", "label", "target", "churn"]
    for c in outcome_candidates:
        if has(c) and c not in used_columns:
            p = col(c)
            specs.append(ChartSpec(
                chart_id=f"count_{c}",
                chart_type="bar",
                title=f"Patient Count by {p.name}",
                x_col=p.name,
                y_col=None,
                agg="count",
                limit=20,
            ))
            used_columns.add(c)
            break

    # -----------------------------------------------------------------------
    # 2. KEY MEASURE BY DEMOGRAPHIC — e.g. "Average time_in_hospital by age"
    # -----------------------------------------------------------------------
    measure_candidates = [
        "time_in_hospital", "los", "length_of_stay", "duration_days",
        "num_medications", "num_lab_procedures", "total", "amount", "revenue",
    ]
    demo_candidates = ["age", "age_group", "gender", "race", "region", "country", "department"]

    measure_col_name = next((m for m in measure_candidates if has(m) and m not in used_columns), None)
    demo_col_name = next((d for d in demo_candidates if has(d) and d not in used_columns), None)

    if measure_col_name and demo_col_name:
        m = col(measure_col_name)
        d = col(demo_col_name)
        specs.append(ChartSpec(
            chart_id=f"avg_{measure_col_name}_by_{demo_col_name}",
            chart_type="bar",
            title=f"Average {m.name} by {d.name}",
            x_col=d.name,
            y_col=m.name,
            agg="mean",
            limit=20,
        ))
        used_columns.add(measure_col_name)
        used_columns.add(demo_col_name)

    # -----------------------------------------------------------------------
    # 3. DEMOGRAPHIC BREAKDOWN — Patient count by age (or another demographic)
    # -----------------------------------------------------------------------
    for d in demo_candidates:
        if has(d) and d not in used_columns:
            p = col(d)
            if 2 <= p.unique_count <= 30:
                specs.append(ChartSpec(
                    chart_id=f"count_{d}",
                    chart_type="hbar" if p.unique_count > 6 else "bar",
                    title=f"Patient Count by {p.name}",
                    x_col=p.name,
                    y_col=None,
                    agg="count",
                    limit=20,
                ))
                used_columns.add(d)
                break

    # -----------------------------------------------------------------------
    # 4. MEDICATION USAGE — diabetesMed, change, insulin, or generic binary med flag
    # -----------------------------------------------------------------------
    med_candidates = ["diabetesmed", "insulin", "metformin", "change", "medication", "treatment"]
    for c in med_candidates:
        if has(c) and c not in used_columns:
            p = col(c)
            if 2 <= p.unique_count <= 10:
                specs.append(ChartSpec(
                    chart_id=f"count_{c}",
                    chart_type="bar",
                    title=f"Patient Count by {p.name}",
                    x_col=p.name,
                    y_col=None,
                    agg="count",
                    limit=20,
                ))
                used_columns.add(c)
                break

    # -----------------------------------------------------------------------
    # 5. LAB RESULT / SEVERITY — A1Cresult, max_glu_serum, severity
    # -----------------------------------------------------------------------
    lab_candidates = ["a1cresult", "max_glu_serum", "severity", "grade", "stage", "level"]
    for c in lab_candidates:
        if has(c) and c not in used_columns:
            p = col(c)
            if p.unique_count <= 15:
                specs.append(ChartSpec(
                    chart_id=f"count_{c}",
                    chart_type="bar",
                    title=f"Patient Count by {p.name}",
                    x_col=p.name,
                    y_col=None,
                    agg="count",
                    limit=20,
                ))
                used_columns.add(c)
                break

    # -----------------------------------------------------------------------
    # 6. DISTRIBUTION OF A KEY NUMERIC — fill remaining slot with histogram
    # -----------------------------------------------------------------------
    if len(specs) < 6:
        hist_candidates = [n for n in numerics if n.name.lower() not in used_columns]
        if hist_candidates:
            preferred = ["time_in_hospital", "num_medications", "num_lab_procedures", "num_procedures"]
            chosen = None
            for p in preferred:
                if has(p) and p not in used_columns:
                    chosen = col(p)
                    used_columns.add(p)
                    break
            if chosen is None:
                chosen = _pick_most_variable_numeric(hist_candidates)
                used_columns.add(chosen.name.lower())
            specs.append(ChartSpec(
                chart_id=f"hist_{chosen.name.lower()}",
                chart_type="histogram",
                title=f"Distribution of {chosen.name}",
                x_col=chosen.name,
                y_col=None,
                agg="count",
                limit=30,
            ))

    # -----------------------------------------------------------------------
    # FALLBACK — Generic charts if we still have < 4
    # -----------------------------------------------------------------------
    if len(specs) < 4 and categoricals:
        for c in categoricals:
            if len(specs) >= 4:
                break
            if c.name.lower() in used_columns:
                continue
            if 2 <= c.unique_count <= 30:
                specs.append(ChartSpec(
                    chart_id=f"count_extra_{c.name.lower()}",
                    chart_type="bar",
                    title=f"Patient Count by {c.name}",
                    x_col=c.name,
                    y_col=None,
                    agg="count",
                    limit=20,
                ))
                used_columns.add(c.name.lower())

    if len(specs) < 4 and numerics:
        for n in numerics:
            if len(specs) >= 4:
                break
            if n.name.lower() in used_columns:
                continue
            specs.append(ChartSpec(
                chart_id=f"hist_extra_{n.name.lower()}",
                chart_type="histogram",
                title=f"Distribution of {n.name}",
                x_col=n.name,
                y_col=None,
                agg="count",
                limit=30,
            ))
            used_columns.add(n.name.lower())

    return specs[:6]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _is_id_column(name: str) -> bool:
    """Return True if *name* looks like an identifier rather than a measure."""
    n = name.lower().strip()
    if n in {"id", "uuid", "guid", "ssn", "key"}:
        return True
    if n.endswith(("_id", "_nbr", "_num", "_key", "_uuid")):
        return True
    # 'number' as suffix is usually an identifier, but keep counts named 'number_*'
    if n.endswith("number") and not n.startswith("number_"):
        return True
    return False


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
