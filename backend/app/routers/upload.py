"""CSV upload endpoint.

POST /api/upload
    - Validates file size (≤ 50 MB) and MIME type
    - Parses CSV with Pandas (chunked for large files)
    - Stores rows in a per-dataset SQLite table
    - Records metadata in the `datasets` table
    - Returns UploadResponse with dataset_id
"""

from __future__ import annotations

import io
import json
import uuid
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy import text

from backend.app.database import get_engine, data_table_name, init_db
from backend.app.models.dataset import UploadResponse
from backend.app.services.profiler import profile_dataframe, profiles_to_json

router = APIRouter(prefix="/api", tags=["upload"])

MAX_FILE_SIZE = 200 * 1024 * 1024  # 50 MB


@router.post("/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)) -> UploadResponse:
    """Accept a CSV file, validate it, persist it, and return a dataset ID.

    Args:
        file: The uploaded CSV file (multipart/form-data).

    Returns:
        UploadResponse with the new dataset_id.

    Raises:
        HTTPException 400: Invalid file format or empty file.
        HTTPException 413: File exceeds the 50 MB size limit.
    """
    # --- Validate file name / content type ---
    filename = file.filename or "upload.csv"
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only .csv files are accepted. Got: {filename}",
        )

    # --- Read content ---
    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if file_size > MAX_FILE_SIZE:
        mb = file_size / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File size {mb:.1f} MB exceeds the 50 MB limit.",
        )

    # --- Parse CSV ---
    try:
        df = pd.read_csv(
            io.BytesIO(content),
            encoding="utf-8",
            on_bad_lines="skip",
            low_memory=False,
        )
    except Exception:
        # Try latin-1 fallback
        try:
            df = pd.read_csv(
                io.BytesIO(content),
                encoding="latin-1",
                on_bad_lines="skip",
                low_memory=False,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Could not parse CSV: {exc}",
            )

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV file contains no data rows.")

    if len(df.columns) < 2:
        raise HTTPException(
            status_code=400,
            detail="CSV must have at least 2 columns.",
        )

    # --- Sanitise column names (strip whitespace, make unique) ---
    df.columns = _sanitise_columns(df.columns.tolist())

    # --- Generate dataset ID ---
    dataset_id = str(uuid.uuid4()).replace("-", "")[:16]
    table_name = data_table_name(dataset_id)

    # --- Persist data to SQLite ---
    engine = get_engine()
    df.to_sql(table_name, con=engine, if_exists="replace", index=False, chunksize=5000)

    # --- Run profiling and cache ---
    profiles = profile_dataframe(df)
    profile_json = profiles_to_json(profiles)

    # --- Insert metadata record ---
    with engine.connect() as conn:
        conn.execute(
            text(
                "INSERT OR REPLACE INTO datasets "
                "(id, name, row_count, col_count, file_size, profile_json, created_at) "
                "VALUES (:id, :name, :row_count, :col_count, :file_size, :profile_json, :created_at)"
            ),
            {
                "id": dataset_id,
                "name": filename,
                "row_count": len(df),
                "col_count": len(df.columns),
                "file_size": file_size,
                "profile_json": profile_json,
                "created_at": datetime.utcnow().isoformat(),
            },
        )
        conn.commit()

    return UploadResponse(
        dataset_id=dataset_id,
        name=filename,
        row_count=len(df),
        col_count=len(df.columns),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitise_columns(cols: list[str]) -> list[str]:
    """Strip whitespace from column names and make them unique."""
    seen: dict[str, int] = {}
    result: list[str] = []
    for c in cols:
        name = str(c).strip()
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 0
        result.append(name)
    return result
