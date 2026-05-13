"""Tests for data profiling accuracy (T020, T021).

Validates column type detection, null counts, and statistics.
"""

from __future__ import annotations

import io
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.services.profiler import profile_dataframe, _detect_dtype


class TestColumnTypeDetection:
    """Unit tests for _detect_dtype."""

    def test_integer_column_detected_as_numeric(self) -> None:
        s = pd.Series([1, 2, 3, 4], dtype=int)
        assert _detect_dtype("Quantity", s, 4) == "numeric"

    def test_float_column_detected_as_numeric(self) -> None:
        s = pd.Series([1.5, 2.5, 3.0], dtype=float)
        assert _detect_dtype("Price", s, 3) == "numeric"

    def test_date_string_column_detected_as_datetime(self) -> None:
        s = pd.Series(["2009-12-01", "2010-01-15", "2010-06-30"])
        assert _detect_dtype("InvoiceDate", s, 3) == "datetime"

    def test_low_cardinality_string_is_categorical(self) -> None:
        s = pd.Series(["UK", "Germany", "France", "UK", "Germany"] * 10)
        result = _detect_dtype("Country", s, 50)
        assert result == "categorical"

    def test_high_cardinality_string_is_text(self) -> None:
        s = pd.Series([f"Desc {i}" for i in range(200)])
        result = _detect_dtype("Description", s, 200)
        assert result == "text"


class TestProfileDataframe:
    """Integration tests for profile_dataframe."""

    @pytest.fixture
    def sample_df(self) -> pd.DataFrame:
        return pd.DataFrame({
            "InvoiceNo": ["536365", "536366", "C536367", "536368"],
            "Quantity": [6, 6, -2, 8],
            "InvoiceDate": ["2009-12-01", "2009-12-01", "2009-12-01", "2009-12-02"],
            "Price": [2.55, 3.39, 2.75, None],
            "Country": ["United Kingdom", "United Kingdom", "Germany", "France"],
        })

    def test_all_columns_profiled(self, sample_df: pd.DataFrame) -> None:
        profiles = profile_dataframe(sample_df)
        assert len(profiles) == 5

    def test_numeric_null_count_correct(self, sample_df: pd.DataFrame) -> None:
        profiles = profile_dataframe(sample_df)
        price_profile = next(p for p in profiles if p.name == "Price")
        assert price_profile.null_count == 1
        assert price_profile.null_pct == 25.0

    def test_numeric_stats_computed(self, sample_df: pd.DataFrame) -> None:
        profiles = profile_dataframe(sample_df)
        qty = next(p for p in profiles if p.name == "Quantity")
        assert qty.stats["min"] == -2.0
        assert qty.stats["max"] == 8.0
        assert qty.stats["mean"] == pytest.approx(4.5)

    def test_categorical_top_values_present(self, sample_df: pd.DataFrame) -> None:
        profiles = profile_dataframe(sample_df)
        country = next(p for p in profiles if p.name == "Country")
        assert country.dtype == "categorical"
        assert len(country.stats["top_values"]) > 0
        assert country.stats["top_values"][0]["value"] == "United Kingdom"


class TestProfileEndpoint:
    """API-level tests for GET /api/datasets/{id}/profile."""

    def test_profile_endpoint_returns_200(
        self, client: TestClient, uploaded_dataset_id: str
    ) -> None:
        response = client.get(f"/api/datasets/{uploaded_dataset_id}/profile")
        assert response.status_code == 200

    def test_profile_has_correct_column_count(
        self, client: TestClient, uploaded_dataset_id: str
    ) -> None:
        response = client.get(f"/api/datasets/{uploaded_dataset_id}/profile")
        body = response.json()
        assert body["col_count"] == 8

    def test_profile_endpoint_404_for_unknown_id(self, client: TestClient) -> None:
        response = client.get("/api/datasets/nonexistent123/profile")
        assert response.status_code == 404
