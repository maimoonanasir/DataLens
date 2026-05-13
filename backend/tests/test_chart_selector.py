"""Tests for the chart auto-selection algorithm (T030).

Validates that the right chart types are chosen for the right column types.
"""

from __future__ import annotations

import pytest

from backend.app.models.dataset import ColumnProfile
from backend.app.services.chart_selector import select_charts


def make_numeric(name: str, mean: float = 100.0, std: float = 20.0) -> ColumnProfile:
    return ColumnProfile(
        name=name, dtype="numeric", null_count=0, null_pct=0.0, unique_count=50,
        stats={"min": 0.0, "max": 500.0, "mean": mean, "median": 90.0, "std": std},
    )


def make_categorical(name: str, unique: int = 30) -> ColumnProfile:
    return ColumnProfile(
        name=name, dtype="categorical", null_count=0, null_pct=0.0, unique_count=unique,
        stats={"top_values": [{"value": f"v{i}", "count": 100} for i in range(min(unique, 5))]},
    )


def make_datetime(name: str) -> ColumnProfile:
    return ColumnProfile(
        name=name, dtype="datetime", null_count=0, null_pct=0.0, unique_count=365,
        stats={"min": "2009-12-01", "max": "2011-12-09"},
    )


class TestChartAutoSelection:
    def test_datetime_column_produces_line_chart(self) -> None:
        profiles = [make_datetime("InvoiceDate"), make_numeric("Price"), make_categorical("Country")]
        specs = select_charts(profiles)
        types = [s.chart_type for s in specs]
        assert "line" in types

    def test_categorical_column_produces_bar_chart(self) -> None:
        profiles = [make_categorical("Country", unique=37), make_numeric("Price")]
        specs = select_charts(profiles)
        types = [s.chart_type for s in specs]
        assert "bar" in types or "hbar" in types

    def test_numeric_column_produces_histogram(self) -> None:
        profiles = [make_numeric("Quantity"), make_categorical("Country")]
        specs = select_charts(profiles)
        types = [s.chart_type for s in specs]
        assert "histogram" in types

    def test_two_numerics_produce_scatter(self) -> None:
        profiles = [make_numeric("Price"), make_numeric("Quantity"), make_categorical("Country")]
        specs = select_charts(profiles)
        types = [s.chart_type for s in specs]
        assert "scatter" in types

    def test_minimum_four_charts_returned(self) -> None:
        profiles = [
            make_datetime("InvoiceDate"),
            make_numeric("Price"),
            make_numeric("Quantity"),
            make_categorical("Country"),
        ]
        specs = select_charts(profiles)
        assert len(specs) >= 4

    def test_maximum_six_charts_returned(self) -> None:
        profiles = [
            make_datetime("InvoiceDate"),
            make_numeric("Price"),
            make_numeric("Quantity"),
            make_numeric("Revenue"),
            make_categorical("Country"),
            make_categorical("StockCode"),
            make_categorical("Description"),
        ]
        specs = select_charts(profiles)
        assert len(specs) <= 6

    def test_chart_ids_are_unique(self) -> None:
        profiles = [
            make_datetime("InvoiceDate"),
            make_numeric("Price"),
            make_numeric("Quantity"),
            make_categorical("Country"),
        ]
        specs = select_charts(profiles)
        ids = [s.chart_id for s in specs]
        assert len(ids) == len(set(ids))
