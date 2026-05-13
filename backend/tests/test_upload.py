"""Tests for the CSV upload endpoint (T011).

Covers: valid upload, non-CSV rejection, file too large, empty file.
"""

from __future__ import annotations

import io
import pandas as pd
import pytest
from fastapi.testclient import TestClient


def test_valid_csv_upload_returns_200(client: TestClient, sample_csv_bytes: bytes) -> None:
    """A valid CSV upload returns HTTP 200 with a dataset_id."""
    response = client.post(
        "/api/upload",
        files={"file": ("retail.csv", sample_csv_bytes, "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert "dataset_id" in body
    assert len(body["dataset_id"]) > 0
    assert body["row_count"] == 4  # sample has 4 rows


def test_upload_returns_correct_metadata(client: TestClient, sample_csv_bytes: bytes) -> None:
    """Upload response includes correct row count and column count."""
    response = client.post(
        "/api/upload",
        files={"file": ("retail.csv", sample_csv_bytes, "text/csv")},
    )
    body = response.json()
    assert body["col_count"] == 8  # sample has 8 columns
    assert body["name"] == "retail.csv"


def test_non_csv_file_returns_400(client: TestClient) -> None:
    """Non-CSV files are rejected with HTTP 400."""
    fake_excel = b"PK\x03\x04\x14\x00\x00\x00"  # fake xlsx header
    response = client.post(
        "/api/upload",
        files={"file": ("data.xlsx", fake_excel, "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "csv" in response.json()["detail"].lower()


def test_empty_file_returns_400(client: TestClient) -> None:
    """An empty file is rejected with HTTP 400."""
    response = client.post(
        "/api/upload",
        files={"file": ("empty.csv", b"", "text/csv")},
    )
    assert response.status_code == 400


def test_file_exceeding_50mb_returns_413(client: TestClient) -> None:
    """A file larger than 50 MB is rejected with HTTP 413."""
    # 51 MB of zeros as a 'CSV' with just a header line
    oversized = b"col1,col2\n" + b"a,b\n" * (51 * 1024 * 1024 // 4)
    response = client.post(
        "/api/upload",
        files={"file": ("huge.csv", oversized, "text/csv")},
    )
    assert response.status_code == 413


def test_uploaded_dataset_persists_in_listing(client: TestClient, sample_csv_bytes: bytes) -> None:
    """After upload, the dataset appears in GET /api/datasets."""
    upload_resp = client.post(
        "/api/upload",
        files={"file": ("retail.csv", sample_csv_bytes, "text/csv")},
    )
    dataset_id = upload_resp.json()["dataset_id"]

    list_resp = client.get("/api/datasets")
    assert list_resp.status_code == 200
    ids = [d["id"] for d in list_resp.json()]
    assert dataset_id in ids


def test_health_endpoint(client: TestClient) -> None:
    """The /api/health endpoint returns status ok."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
