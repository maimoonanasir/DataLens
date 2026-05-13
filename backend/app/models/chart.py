"""Pydantic models for chart specification and chart data responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChartSpec(BaseModel):
    """Describes a single auto-selected chart: type and columns to use."""

    chart_id: str  # e.g. "bar_country", "line_invoicedate", "hist_quantity"
    chart_type: str  # "bar" | "line" | "area" | "scatter" | "histogram" | "hbar"
    title: str
    x_col: str | None = None  # Main x-axis or groupby column
    y_col: str | None = None  # Aggregation target column
    agg: str = "count"  # "count" | "sum" | "mean"
    limit: int = 20  # Max data points to return


class ChartData(BaseModel):
    """Data returned for a single chart."""

    spec: ChartSpec
    data: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


class ChartsRequest(BaseModel):
    """Request body for the /charts endpoint."""

    filters: dict[str, Any] = Field(default_factory=dict)


class ChartsResponse(BaseModel):
    """Response from the /charts endpoint."""

    dataset_id: str
    specs: list[ChartSpec]
    charts: list[ChartData]
