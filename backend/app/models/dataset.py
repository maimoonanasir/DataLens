"""Pydantic models for dataset metadata and data profiling."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DatasetMeta(BaseModel):
    """Metadata record stored in the `datasets` SQLite table."""

    id: str
    name: str
    row_count: int
    col_count: int
    file_size: int
    created_at: str


class UploadResponse(BaseModel):
    """Response returned after a successful CSV upload."""

    dataset_id: str
    name: str
    row_count: int
    col_count: int
    message: str = "Dataset uploaded and stored successfully."


class ColumnProfile(BaseModel):
    """Profile for a single column in the uploaded dataset."""

    name: str
    dtype: str  # "numeric" | "categorical" | "datetime" | "text"
    null_count: int
    null_pct: float
    unique_count: int
    stats: dict[str, Any] = Field(default_factory=dict)
    # For categoricals: top_values list; for numerics: min/max/mean/median/std


class ProfileResponse(BaseModel):
    """Full dataset profile returned by the /profile endpoint."""

    dataset_id: str
    name: str
    row_count: int
    col_count: int
    columns: list[ColumnProfile]


class FilterOption(BaseModel):
    """Describes a single filter control the frontend should render."""

    column: str
    filter_type: str  # "dropdown" | "date_range" | "slider" | "text_search"
    label: str
    # For dropdown: values list; for slider: min/max; for date_range: min/max strings
    options: dict[str, Any] = Field(default_factory=dict)


class FilterOptionsResponse(BaseModel):
    """All available filter definitions for a dataset."""

    dataset_id: str
    filters: list[FilterOption]
