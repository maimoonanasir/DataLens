"""Chart data endpoint.

POST /api/datasets/{dataset_id}/charts
    - Reads cached profile to select charts
    - Applies active filters from request body
    - Queries SQLite for each ChartSpec
    - Returns ChartsResponse
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from backend.app.database import get_engine
from backend.app.models.chart import ChartsRequest, ChartsResponse, ChartData
from backend.app.services.chart_selector import select_charts
from backend.app.services.profiler import profiles_from_json
from backend.app.services.query_engine import execute_chart_query

router = APIRouter(prefix="/api/datasets", tags=["charts"])


@router.post("/{dataset_id}/charts", response_model=ChartsResponse)
def get_charts(dataset_id: str, request: ChartsRequest) -> ChartsResponse:
    """Return chart data for all auto-selected charts.

    Args:
        dataset_id: UUID of the uploaded dataset.
        request: Contains active filter state.

    Returns:
        ChartsResponse with specs and data arrays.
    """
    engine = get_engine()

    # Load cached profile
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT profile_json FROM datasets WHERE id = :id"),
            {"id": dataset_id},
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    if not row[0]:
        raise HTTPException(status_code=400, detail="Dataset has no profile. Upload may be incomplete.")

    profiles = profiles_from_json(row[0])

    # Auto-select chart specs
    specs = select_charts(profiles)

    # Execute each chart query
    charts: list[ChartData] = []
    for spec in specs:
        chart_data = execute_chart_query(dataset_id, spec, request.filters)
        charts.append(chart_data)

    return ChartsResponse(
        dataset_id=dataset_id,
        specs=specs,
        charts=charts,
    )
