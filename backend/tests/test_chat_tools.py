"""Unit tests for LLM tool handler functions (T050).

These tests exercise the Python-side tool implementations without calling
the real Anthropic API. They validate that tool functions return correct shapes.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from backend.app.services.query_engine import (
    execute_raw_sql,
    get_column_unique_values,
    get_column_min_max,
)


class TestQueryTools:
    def test_execute_raw_sql_returns_rows(
        self, uploaded_dataset_id: str
    ) -> None:
        from backend.app.database import data_table_name
        table = data_table_name(uploaded_dataset_id)
        rows = execute_raw_sql(
            uploaded_dataset_id,
            f"SELECT Country, COUNT(*) as cnt FROM {table} GROUP BY Country ORDER BY cnt DESC",
        )
        assert len(rows) > 0
        assert "Country" in rows[0]
        assert "cnt" in rows[0]

    def test_execute_raw_sql_rejects_non_select(
        self, uploaded_dataset_id: str
    ) -> None:
        with pytest.raises(ValueError, match="Only SELECT"):
            execute_raw_sql(uploaded_dataset_id, "DROP TABLE datasets")

    def test_get_column_unique_values_returns_list(
        self, uploaded_dataset_id: str
    ) -> None:
        values = get_column_unique_values(uploaded_dataset_id, "Country", limit=50)
        assert isinstance(values, list)
        assert "United Kingdom" in values

    def test_get_column_min_max_numeric(
        self, uploaded_dataset_id: str
    ) -> None:
        mm = get_column_min_max(uploaded_dataset_id, "Quantity")
        assert mm["min"] is not None
        assert mm["max"] is not None
        assert float(mm["min"]) <= float(mm["max"])

    def test_sql_aggregation_returns_correct_sum(
        self, uploaded_dataset_id: str
    ) -> None:
        from backend.app.database import data_table_name
        table = data_table_name(uploaded_dataset_id)
        rows = execute_raw_sql(
            uploaded_dataset_id,
            f"SELECT SUM(Quantity) as total_qty FROM {table}",
        )
        # Sample data: 6 + 6 + (-2) + 8 = 18
        assert rows[0]["total_qty"] == 18


class TestChatEndpointWithoutLLM:
    """Test the chat endpoint validation logic without hitting the LLM."""

    def test_chat_endpoint_404_for_unknown_dataset(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/api/datasets/nonexistent/chat",
            json={"messages": [{"role": "user", "content": "hello"}], "filters": {}},
        )
        assert response.status_code == 404

    def test_summary_endpoint_404_for_unknown_dataset(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/api/datasets/nonexistent/summary",
            json={"filters": {}},
        )
        assert response.status_code == 404
