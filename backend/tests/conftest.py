"""Shared pytest fixtures for DataLens backend tests.

Uses an in-memory SQLite database to isolate tests from the production DB.
"""

from __future__ import annotations

import io
import os
import tempfile
from collections.abc import Generator

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

# Override DB path before importing the app
os.environ["DB_PATH"] = ":memory:"

# Patch engine to use in-memory DB
from backend.app import database as db_module

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
db_module._engine = _test_engine

from backend.app.main import app
from backend.app.database import init_db


@pytest.fixture(autouse=True)
def setup_db() -> Generator:
    """Reset and initialise the test database before each test."""
    init_db()
    yield
    # No teardown needed — each test uses a fresh state via fixture isolation


@pytest.fixture
def client() -> TestClient:
    """Return a synchronous TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_csv_bytes() -> bytes:
    """Return CSV bytes matching Online Retail II column structure."""
    df = pd.DataFrame({
        "InvoiceNo": ["536365", "536366", "C536367", "536368"],
        "StockCode": ["85123A", "71053", "84406B", "84029G"],
        "Description": ["WHITE HANGING HEART", "WHITE METAL LANTERN", "CREAM CUPID HEARTS", "KNITTED UNION FLAG"],
        "Quantity": [6, 6, -2, 8],
        "InvoiceDate": ["2009-12-01", "2009-12-01", "2009-12-01", "2009-12-01"],
        "Price": [2.55, 3.39, 2.75, 3.39],
        "Customer ID": [17850, 17850, None, 17850],
        "Country": ["United Kingdom", "United Kingdom", "United Kingdom", "United Kingdom"],
    })
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


@pytest.fixture
def uploaded_dataset_id(client: TestClient, sample_csv_bytes: bytes) -> str:
    """Upload a sample CSV and return the resulting dataset_id."""
    response = client.post(
        "/api/upload",
        files={"file": ("test_retail.csv", sample_csv_bytes, "text/csv")},
    )
    assert response.status_code == 200
    return response.json()["dataset_id"]
