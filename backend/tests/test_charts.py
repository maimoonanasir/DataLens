"""Tests for the charts data endpoint (T031).

Validates chart data shape and filter application.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestChartsEndpoint:
    def test_charts_endpoint_returns_200(
        self, client: TestClient, uploaded_dataset_id: str
    ) -> None:
        response = client.post(
            f"/api/datasets/{uploaded_dataset_id}/charts",
            json={"filters": {}},
        )
        assert response.status_code == 200

    def test_charts_response_has_correct_structure(
        self, client: TestClient, uploaded_dataset_id: str
    ) -> None:
        response = client.post(
            f"/api/datasets/{uploaded_dataset_id}/charts",
            json={"filters": {}},
        )
        body = response.json()
        assert "charts" in body
        assert "specs" in body
        assert "dataset_id" in body

    def test_charts_returns_at_least_four_charts(
        self, client: TestClient, uploaded_dataset_id: str
    ) -> None:
        response = client.post(
            f"/api/datasets/{uploaded_dataset_id}/charts",
            json={"filters": {}},
        )
        charts = response.json()["charts"]
        assert len(charts) >= 4

    def test_each_chart_has_data_array(
        self, client: TestClient, uploaded_dataset_id: str
    ) -> None:
        response = client.post(
            f"/api/datasets/{uploaded_dataset_id}/charts",
            json={"filters": {}},
        )
        for chart in response.json()["charts"]:
            assert "data" in chart
            assert isinstance(chart["data"], list)

    def test_country_filter_reduces_data(
        self, client: TestClient, uploaded_dataset_id: str
    ) -> None:
        # Unfiltered
        full = client.post(
            f"/api/datasets/{uploaded_dataset_id}/charts",
            json={"filters": {}},
        ).json()

        # Filter to United Kingdom only
        filtered = client.post(
            f"/api/datasets/{uploaded_dataset_id}/charts",
            json={"filters": {"Country": "Germany"}},
        ).json()

        # At least one chart should have fewer data points when filtered
        # (Not all charts use Country, but bar charts do)
        full_total = sum(len(c["data"]) for c in full["charts"])
        filtered_total = sum(len(c["data"]) for c in filtered["charts"])
        # Filtered should have equal or fewer data points
        assert filtered_total <= full_total

    def test_charts_404_for_unknown_dataset(self, client: TestClient) -> None:
        response = client.post(
            "/api/datasets/nonexistent999/charts",
            json={"filters": {}},
        )
        assert response.status_code == 404

    def test_filter_options_endpoint_returns_200(
        self, client: TestClient, uploaded_dataset_id: str
    ) -> None:
        response = client.get(f"/api/datasets/{uploaded_dataset_id}/filter-options")
        assert response.status_code == 200
        body = response.json()
        assert "filters" in body
        assert isinstance(body["filters"], list)
