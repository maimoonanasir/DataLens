"""Filter-options endpoint.

GET /api/datasets/{dataset_id}/filter-options
    Returns filter control definitions: dropdowns (categoricals),
    date ranges (datetime), and sliders (numeric).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from backend.app.database import get_engine
from backend.app.models.dataset import FilterOption, FilterOptionsResponse
from backend.app.services.profiler import profiles_from_json
from backend.app.services.query_engine import get_column_unique_values, get_column_min_max

router = APIRouter(prefix="/api/datasets", tags=["filters"])

# Categorical columns with too many unique values make unusable dropdowns
MAX_DROPDOWN_VALUES = 100


@router.get("/{dataset_id}/filter-options", response_model=FilterOptionsResponse)
def get_filter_options(dataset_id: str) -> FilterOptionsResponse:
    """Return filter definitions for the dashboard filter panel.

    Args:
        dataset_id: UUID of the uploaded dataset.

    Returns:
        FilterOptionsResponse with a list of FilterOption objects.
    """
    engine = get_engine()

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT profile_json FROM datasets WHERE id = :id"),
            {"id": dataset_id},
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    profiles = profiles_from_json(row[0])
    filters: list[FilterOption] = []

    for p in profiles:
        if p.dtype == "categorical" and p.unique_count <= MAX_DROPDOWN_VALUES:
            values = get_column_unique_values(dataset_id, p.name, limit=MAX_DROPDOWN_VALUES)
            values_sorted = sorted([str(v) for v in values if v is not None])
            filters.append(FilterOption(
                column=p.name,
                filter_type="dropdown",
                label=p.name,
                options={"values": values_sorted},
            ))

        elif p.dtype == "datetime":
            mm = get_column_min_max(dataset_id, p.name)
            filters.append(FilterOption(
                column=p.name,
                filter_type="date_range",
                label=p.name,
                options={"min": str(mm["min"])[:10] if mm["min"] else None,
                         "max": str(mm["max"])[:10] if mm["max"] else None},
            ))

        elif p.dtype == "numeric":
            mm = get_column_min_max(dataset_id, p.name)
            filters.append(FilterOption(
                column=p.name,
                filter_type="slider",
                label=p.name,
                options={
                    "min": float(mm["min"]) if mm["min"] is not None else 0,
                    "max": float(mm["max"]) if mm["max"] is not None else 100,
                },
            ))

    return FilterOptionsResponse(dataset_id=dataset_id, filters=filters)
