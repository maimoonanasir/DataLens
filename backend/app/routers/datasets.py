"""Dataset listing and detail endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from backend.app.database import get_engine
from backend.app.models.dataset import DatasetMeta

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.get("", response_model=list[DatasetMeta])
def list_datasets() -> list[DatasetMeta]:
    """Return all datasets stored in SQLite, newest first."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, name, row_count, col_count, file_size, created_at FROM datasets ORDER BY created_at DESC")
        )
        rows = result.fetchall()

    return [
        DatasetMeta(
            id=row[0],
            name=row[1],
            row_count=row[2],
            col_count=row[3],
            file_size=row[4],
            created_at=row[5],
        )
        for row in rows
    ]


@router.get("/{dataset_id}", response_model=DatasetMeta)
def get_dataset(dataset_id: str) -> DatasetMeta:
    """Return metadata for a single dataset."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, name, row_count, col_count, file_size, created_at FROM datasets WHERE id = :id"),
            {"id": dataset_id},
        )
        row = result.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    return DatasetMeta(
        id=row[0],
        name=row[1],
        row_count=row[2],
        col_count=row[3],
        file_size=row[4],
        created_at=row[5],
    )


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: str) -> dict:
    """Remove a dataset and its data table from SQLite."""
    from backend.app.database import data_table_name
    engine = get_engine()
    table = data_table_name(dataset_id)
    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
        conn.execute(text("DELETE FROM datasets WHERE id = :id"), {"id": dataset_id})
        conn.commit()
    return {"message": f"Dataset {dataset_id} deleted."}
