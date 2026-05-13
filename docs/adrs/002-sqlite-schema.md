# ADR-002: SQLite Schema Design for Arbitrary CSV Storage

**Date:** 2026-05-02
**Status:** Accepted
**Deciders:** Haider Ahmad

---

## Context

DataLens must persist any CSV file a user uploads — without knowing in advance how many columns there are, what their names are, or what types they hold. The schema must support:

1. Storing the raw CSV data so charts can be re-generated after page refresh
2. Caching the column profile (type detection, stats) to avoid re-running the profiler on every request
3. Supporting arbitrary column names and types without schema migration

The spec mandates SQLite as the database and Pandas as the data processing library.

---

## Options Considered

**Option A — Single "wide" EAV (Entity-Attribute-Value) table**
Store every cell as a row in `(dataset_id, row_idx, column_name, value)`. This is schema-agnostic but queries are extremely slow (require self-joins or pivoting) and the table would have 1 billion rows for a 1M-row × 1K-column CSV.

**Option B — Store CSV as a BLOB (compressed bytes)**
Store the raw CSV bytes in a BLOB column. Load into Pandas on every request. Avoids dynamic tables but makes SQL queries impossible — the LLM tool `query_data` could not execute SQL against BLOBs, breaking the entire tool-calling architecture.

**Option C — Dynamic tables, one per dataset**
Create a new SQLite table for each uploaded dataset, named `data_<dataset_id>`. Column names come from the CSV header. Pandas `df.to_sql()` handles arbitrary column types. A separate `datasets` metadata table stores per-dataset information including the cached profile JSON.

**Option D — Parquet files on disk + SQLite metadata**
Store the CSV data as a Parquet file and use Pandas to query it. Faster than SQLite for columnar scans, but breaks the requirement to support SQL queries from the LLM tool layer without additional abstraction.

---

## Decision

We chose **Option C — Dynamic tables, one per dataset**.

Schema:

```sql
-- Metadata table (fixed schema)
CREATE TABLE IF NOT EXISTS datasets (
    id           TEXT PRIMARY KEY,    -- 16-char UUID fragment
    name         TEXT NOT NULL,       -- original filename
    row_count    INTEGER NOT NULL,
    col_count    INTEGER NOT NULL,
    file_size    INTEGER NOT NULL,
    profile_json TEXT,                -- JSON-serialised column profiles (cached)
    created_at   TEXT NOT NULL
);

-- Per-dataset table (dynamic, created by Pandas df.to_sql())
-- Example: data_abc123def456
-- Columns: whatever the CSV header contains
```

**Why this works:**

1. **SQL queries work natively.** The LLM `query_data` tool can execute `SELECT Country, SUM(Quantity) ... FROM data_abc123def456 GROUP BY Country` without any transformation layer.

2. **Pandas integration is trivial.** `df.to_sql(table_name, engine, if_exists='replace')` creates the table with correct column types inferred from the DataFrame dtypes. Loading back is `pd.read_sql_table(table_name, engine)`.

3. **Profile caching avoids re-running the profiler.** After the initial upload, the profile is stored as JSON in the `profile_json` column of the `datasets` table. Subsequent requests (charts, filters, chat, summary) read the cached profile — no re-scan of the data table needed.

4. **Multi-dataset support is natural.** Each dataset gets its own table. Uploading a new CSV creates a new table; the old table remains (supporting a dataset history feature in future).

---

## Trade-offs

**What we gave up:**
- Referential integrity (no foreign keys enforced between `datasets` and data tables)
- Schema validation at the DB level (SQLite is flexible but will accept any column name)
- Query plan optimisation (no indexes — added in future if large datasets are slow)

**What we accepted:**
- Table name sanitisation is critical: `data_table_name()` strips non-word characters from the dataset ID to prevent SQL injection via table name. Column names from CSV headers are double-quoted in all queries.
- SQLite's `check_same_thread=False` is required for FastAPI's async model — this is safe because SQLite uses file-level locking and we don't run concurrent writes.

**Security note:** All SQL in `query_engine.py` is parameterised for WHERE clause values. Table and column names are embedded directly as they come from internal state (dataset_id from UUID generation, column names from profile), not from user input.
