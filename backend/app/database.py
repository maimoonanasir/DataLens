"""SQLite database engine, connection management, and schema bootstrap.

On startup, creates the `datasets` metadata table if it does not yet exist.
CSV data is stored in per-dataset dynamic tables named `data_<dataset_id>`.
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# ---------------------------------------------------------------------------
# Engine singleton
# ---------------------------------------------------------------------------

DB_PATH = Path(os.getenv("DB_PATH", "datalens.db"))

_engine: Engine | None = None


def get_engine() -> Engine:
    """Return the shared SQLAlchemy engine, creating it on first call."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            f"sqlite:///{DB_PATH}",
            connect_args={"check_same_thread": False},
            echo=False,
        )
    return _engine


# ---------------------------------------------------------------------------
# Schema bootstrap
# ---------------------------------------------------------------------------

METADATA_DDL = """
CREATE TABLE IF NOT EXISTS datasets (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    row_count   INTEGER NOT NULL DEFAULT 0,
    col_count   INTEGER NOT NULL DEFAULT 0,
    file_size   INTEGER NOT NULL DEFAULT 0,
    profile_json TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
)
"""


def init_db() -> None:
    """Create schema tables if they don't exist. Safe to call multiple times."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text(METADATA_DDL))
        conn.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def data_table_name(dataset_id: str) -> str:
    """Return the SQLite table name for a given dataset id."""
    return f"data_{dataset_id.replace('-', '_')}"
