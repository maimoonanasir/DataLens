"""Executive summary endpoint.

POST /api/datasets/{dataset_id}/summary
    Uses the LLM to generate a business-analyst-style narrative summary
    of the dataset based on the profile and key chart data.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from backend.app.database import get_engine
from backend.app.models.chat import SummaryRequest, SummaryResponse
from backend.app.models.chart import ChartsRequest
from backend.app.services.profiler import profiles_from_json
from backend.app.services.chart_selector import select_charts
from backend.app.services.query_engine import execute_chart_query
from backend.app.services.llm import generate_summary

router = APIRouter(prefix="/api/datasets", tags=["summary"])


@router.post("/{dataset_id}/summary", response_model=SummaryResponse)
def get_summary(dataset_id: str, request: SummaryRequest) -> SummaryResponse:
    """Generate an LLM executive summary for the dataset.

    Args:
        dataset_id: UUID of the uploaded dataset.
        request: Optional active filter state.

    Returns:
        SummaryResponse with the narrative text.
    """
    engine = get_engine()

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT profile_json, name FROM datasets WHERE id = :id"),
            {"id": dataset_id},
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    profiles = profiles_from_json(row[0])
    dataset_name = row[1]

    # Gather key chart data as text context for the LLM
    specs = select_charts(profiles)
    chart_summary_lines: list[str] = []
    for spec in specs[:4]:  # Use first 4 charts for context
        chart_data = execute_chart_query(dataset_id, spec, request.filters)
        if chart_data.data:
            top_items = chart_data.data[:5]
            items_str = "; ".join(
                f"{row.get('name', row.get('x', '?'))}: {row.get('y', '?')}"
                for row in top_items
            )
            chart_summary_lines.append(f"• {spec.title}: {items_str}")

    chart_context = "\n".join(chart_summary_lines) if chart_summary_lines else "No chart data available."

    try:
        narrative = generate_summary(
            dataset_id=dataset_id,
            profiles=profiles,
            chart_data_summary=f"Dataset: {dataset_name}\n\n{chart_context}",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {exc}")

    return SummaryResponse(
        summary=narrative,
        generated_at=datetime.utcnow().isoformat(),
    )
