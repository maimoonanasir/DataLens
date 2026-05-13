"""Data profiling endpoint.

GET /api/datasets/{dataset_id}/profile
    Returns column profiles cached in the datasets metadata table.
    If not cached (e.g., after DB migration), re-runs profiling.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from backend.app.database import get_engine, data_table_name
from backend.app.models.dataset import ProfileResponse
from backend.app.services.profiler import profiles_from_json, profile_dataframe, profiles_to_json

router = APIRouter(prefix="/api/datasets", tags=["profile"])


@router.get("/{dataset_id}/profile", response_model=ProfileResponse)
def get_profile(dataset_id: str) -> ProfileResponse:
    """Return the column profile for *dataset_id*.

    Profiles are cached in the `profile_json` column of the `datasets` table.
    If not cached, the profiler is re-run against the stored data.

    Args:
        dataset_id: UUID of the uploaded dataset.

    Returns:
        ProfileResponse with column profiles.
    """
    engine = get_engine()

    # Fetch metadata
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, name, row_count, col_count, profile_json FROM datasets WHERE id = :id"),
            {"id": dataset_id},
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    ds_id, name, row_count, col_count, profile_json = row

    if profile_json:
        profiles = profiles_from_json(profile_json)
    else:
        # Re-run profiling from stored table
        import pandas as pd
        table = data_table_name(dataset_id)
        df = pd.read_sql_table(table, con=engine)
        profiles = profile_dataframe(df)
        cached_json = profiles_to_json(profiles)
        with engine.connect() as conn:
            conn.execute(
                text("UPDATE datasets SET profile_json = :pj WHERE id = :id"),
                {"pj": cached_json, "id": dataset_id},
            )
            conn.commit()

    return ProfileResponse(
        dataset_id=dataset_id,
        name=name,
        row_count=row_count,
        col_count=col_count,
        columns=profiles,
    )
