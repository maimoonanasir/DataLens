# Task Breakdown
*Task breakdown version: 1.0 | Last updated: 2026-05-12*

---

## Phase 1: Foundation

- [x] **T001:** Set up project repo and verify scaffolding
  - **Phase:** 1 — Foundation
  - **Description:** Rename starter, initialize git, push to GitHub, verify `uv sync` and `npm install` complete
  - **Acceptance:** Both package managers complete without errors; `pytest` and `vitest run` succeed with zero tests
  - **Verify:** Run both test commands locally
  - **Files:** pyproject.toml, frontend/package.json
  - **Dependencies:** None

- [x] **T002:** Complete SPEC.md
  - **Phase:** 1 — Foundation
  - **Description:** Fill all ten sections; testable success criteria; assumptions surfaced
  - **Acceptance:** No `[TODO]` blocks remain; all six core areas present
  - **Verify:** Peer review
  - **Files:** SPEC.md
  - **Dependencies:** T001

- [x] **T003:** Complete plan.md and todo.md
  - **Phase:** 1 — Foundation
  - **Description:** Phase plan with milestones and risks; atomic task list with acceptance criteria
  - **Acceptance:** Every task ≤ 5 files; every task has acceptance criteria and verify step
  - **Verify:** Peer review
  - **Files:** tasks/plan.md, tasks/todo.md
  - **Dependencies:** T002

---

## Phase 2: Upload + Persistence

- [x] **T010:** Bootstrap FastAPI app and SQLite schema
  - **Phase:** 2 — Upload + Persistence
  - **Description:** `main.py` with CORS, lifespan; `database.py` with engine + `datasets` metadata table creation on startup
  - **Acceptance:** `uv run uvicorn backend.app.main:app --reload` starts without errors; `datasets` table exists in `datalens.db`
  - **Verify:** `curl http://localhost:8000/api/health` returns `{"status": "ok"}`
  - **Files:** backend/app/main.py, backend/app/database.py, backend/app/models/dataset.py
  - **Dependencies:** T001

- [x] **T011:** Implement CSV upload endpoint with validation
  - **Phase:** 2 — Upload + Persistence
  - **Description:** `POST /api/upload` — validate size (≤50 MB), validate CSV format, parse with Pandas (chunked), store in dynamic SQLite table, return dataset ID
  - **Acceptance:** Valid CSV → 200 + dataset ID; non-CSV → 400; >50 MB → 413; empty file → 400
  - **Verify:** `pytest backend/tests/test_upload.py`
  - **Files:** backend/app/routers/upload.py, backend/app/services/importer.py, backend/tests/test_upload.py
  - **Dependencies:** T010

- [x] **T012:** Implement dataset listing endpoint
  - **Phase:** 2 — Upload + Persistence
  - **Description:** `GET /api/datasets` returns all datasets in the metadata table (id, name, row_count, created_at)
  - **Acceptance:** After upload, dataset appears in listing; persists after server restart
  - **Verify:** Upload → restart server → `GET /api/datasets` still shows dataset
  - **Files:** backend/app/routers/datasets.py
  - **Dependencies:** T011

- [x] **T013:** Build UploadZone frontend component
  - **Phase:** 2 — Upload + Persistence
  - **Description:** Drag-and-drop + click upload zone; shows file name, progress indicator, error messages; calls `POST /api/upload`
  - **Acceptance:** Valid CSV shows success state; wrong file type shows error; component renders in all states
  - **Verify:** `npm run test -- UploadZone`
  - **Files:** frontend/src/components/UploadZone.tsx, frontend/tests/UploadZone.test.tsx
  - **Dependencies:** T011

---

## Phase 3: Data Profiling

- [x] **T020:** Implement data profiling service
  - **Phase:** 3 — Profiling
  - **Description:** `profiler.py` — detect column types, count nulls, compute stats (min/max/mean/median for numeric; top 10 values for categorical; min/max date for datetime; character count for text)
  - **Acceptance:** On Online Retail II: InvoiceDate → datetime, Country → categorical, Quantity → numeric, Description → text
  - **Verify:** `pytest backend/tests/test_profiling.py`
  - **Files:** backend/app/services/profiler.py, backend/tests/test_profiling.py
  - **Dependencies:** T011

- [x] **T021:** Implement profiling endpoint
  - **Phase:** 3 — Profiling
  - **Description:** `GET /api/datasets/{id}/profile` — runs profiler on stored data, caches result in metadata table, returns JSON
  - **Acceptance:** Endpoint returns profile within 10 s for Online Retail II; subsequent calls return cached result instantly
  - **Verify:** Time the endpoint call; inspect JSON shape
  - **Files:** backend/app/routers/profile.py
  - **Dependencies:** T020

- [x] **T022:** Build DataProfile frontend component
  - **Phase:** 3 — Profiling
  - **Description:** Renders column cards grid — each card shows column name, type badge, null %, and key stats
  - **Acceptance:** Renders all columns; correct type badge colors; renders empty state for 0-null columns
  - **Verify:** `npm run test -- DataProfile`
  - **Files:** frontend/src/components/DataProfile.tsx, frontend/tests/DataProfile.test.tsx
  - **Dependencies:** T021

---

## Phase 4: Dashboard Visualizations

- [x] **T030:** Implement chart auto-selection service
  - **Phase:** 4 — Dashboard
  - **Description:** `chart_selector.py` — given profile, output 4–6 ChartSpec objects. Rules: categorical (≤20 unique) → bar; datetime → line/area; two numerics → scatter; single numeric → histogram; top-N categorical → horizontal bar
  - **Acceptance:** On Online Retail II profile: Country bar, InvoiceDate line, Quantity histogram, UnitPrice×Quantity scatter generated
  - **Verify:** `pytest backend/tests/test_chart_selector.py`
  - **Files:** backend/app/services/chart_selector.py, backend/app/models/chart.py, backend/tests/test_chart_selector.py
  - **Dependencies:** T020

- [x] **T031:** Implement chart data endpoint
  - **Phase:** 4 — Dashboard
  - **Description:** `POST /api/datasets/{id}/charts` — accepts active filters + ChartSpec list, queries SQLite, returns data arrays
  - **Acceptance:** Returns correct JSON shape `{charts: [{spec, data: [...]}]}`; no data for empty filter result handled gracefully
  - **Verify:** `pytest backend/tests/test_charts.py`
  - **Files:** backend/app/routers/charts.py, backend/app/services/query_engine.py, backend/tests/test_charts.py
  - **Dependencies:** T030

- [x] **T032:** Build ChartCard and Dashboard components
  - **Phase:** 4 — Dashboard
  - **Description:** `Dashboard.tsx` — responsive grid of `ChartCard.tsx` components; each ChartCard renders correct Recharts component based on spec type
  - **Acceptance:** 4–6 charts render; loading skeletons during fetch; no console errors
  - **Verify:** `npm run test -- Dashboard`
  - **Files:** frontend/src/components/Dashboard.tsx, frontend/src/components/ChartCard.tsx, frontend/tests/Dashboard.test.tsx
  - **Dependencies:** T031

---

## Phase 5: Global Filters

- [x] **T040:** Implement filter-options endpoint
  - **Phase:** 5 — Filters
  - **Description:** `GET /api/datasets/{id}/filter-options` — returns filter definitions: dropdowns for categoricals, date range for datetime, slider for numeric
  - **Acceptance:** Returns correct options for Online Retail II (37 countries, date min/max, quantity min/max)
  - **Verify:** Curl the endpoint; inspect JSON
  - **Files:** backend/app/routers/filters.py
  - **Dependencies:** T020

- [x] **T041:** Build FilterPanel frontend component
  - **Phase:** 5 — Filters
  - **Description:** `FilterPanel.tsx` — renders dynamic controls based on filter-options response; emits filter state object on every change
  - **Acceptance:** Dropdown, date inputs, and sliders render; onChange fires with correct filter object; Clear All button resets state
  - **Verify:** `npm run test -- FilterPanel`
  - **Files:** frontend/src/components/FilterPanel.tsx, frontend/src/hooks/useFilters.ts, frontend/tests/FilterPanel.test.tsx
  - **Dependencies:** T040

- [x] **T042:** Wire filters to dashboard (re-fetch on filter change)
  - **Phase:** 5 — Filters
  - **Description:** When filter state changes in FilterPanel, Dashboard re-fetches chart data with active filters; all charts update simultaneously
  - **Acceptance:** Selecting "United Kingdom" reduces all chart values to UK-only; clearing filter restores full data
  - **Verify:** Manual test — select country filter, observe all charts update
  - **Files:** frontend/src/App.tsx, frontend/src/hooks/useDataset.ts
  - **Dependencies:** T041

---

## Phase 6: LLM Chat Interface

- [x] **T050:** Define LLM tool functions and Anthropic client
  - **Phase:** 6 — Chat
  - **Description:** `llm.py` — Anthropic client setup; define four tool schemas: `query_data`, `get_statistics`, `get_column_values`, `filter_data`; implement Python handlers for each tool
  - **Acceptance:** Tool handlers return correct shapes on unit tests; `query_data(dataset_id, "SELECT Country, SUM(Quantity) FROM ... GROUP BY Country ORDER BY 2 DESC LIMIT 5")` returns 5-row result
  - **Verify:** `pytest backend/tests/test_chat_tools.py`
  - **Files:** backend/app/services/llm.py, backend/tests/test_chat_tools.py
  - **Dependencies:** T031

- [x] **T051:** Implement chat endpoint
  - **Phase:** 6 — Chat
  - **Description:** `POST /api/datasets/{id}/chat` — accepts `{messages: [...], filters: {...}}`; runs Anthropic tool-calling loop (max 5 turns); returns final answer text
  - **Acceptance:** Endpoint returns answer to "which country has the highest total revenue?" with correct country name; handles LLM errors gracefully
  - **Verify:** Curl endpoint with test question; observe answer
  - **Files:** backend/app/routers/chat.py, backend/app/models/chat.py
  - **Dependencies:** T050

- [x] **T052:** Build ChatPanel frontend component
  - **Phase:** 6 — Chat
  - **Description:** `ChatPanel.tsx` — message list, input field, send button, loading dots; renders user and assistant messages; handles error state
  - **Acceptance:** Input → send → loading dots → answer appears; handles enter key; empty input blocked
  - **Verify:** `npm run test -- ChatPanel`
  - **Files:** frontend/src/components/ChatPanel.tsx, frontend/tests/ChatPanel.test.tsx
  - **Dependencies:** T051

---

## Phase 7: Executive Summary

- [x] **T060:** Implement summary endpoint
  - **Phase:** 7 — Summary
  - **Description:** `POST /api/datasets/{id}/summary` — collects profile stats + sample chart data, sends to LLM with business-analyst prompt, returns narrative text
  - **Acceptance:** Returns non-empty text ≥ 200 words; references at least 3 dataset-specific facts (e.g., UK dominance, seasonal patterns, top product)
  - **Verify:** Call endpoint; read output; spot-check facts against data
  - **Files:** backend/app/routers/summary.py
  - **Dependencies:** T050

- [x] **T061:** Build ExecutiveSummary frontend component
  - **Phase:** 7 — Summary
  - **Description:** `ExecutiveSummary.tsx` — "Generate Summary" button; loading skeleton; formatted text display; copy-to-clipboard button
  - **Acceptance:** Button triggers API call; skeleton shown during loading; text renders on success; error message on failure
  - **Verify:** Manual test — generate summary, verify rendering
  - **Files:** frontend/src/components/ExecutiveSummary.tsx
  - **Dependencies:** T060

---

## Phase 8: Polish and Documentation

- [x] **T070:** Write README.md (complete, verified)
  - **Files:** README.md
  - **Dependencies:** All implementation tasks

- [x] **T071:** Write ADR-001: LLM Provider Selection
  - **Files:** docs/adrs/001-llm-provider.md
  - **Dependencies:** T050

- [x] **T072:** Write ADR-002: SQLite Schema for Arbitrary CSVs
  - **Files:** docs/adrs/002-sqlite-schema.md
  - **Dependencies:** T011

- [x] **T073:** Write ADR-003: Chart Auto-Selection Algorithm
  - **Files:** docs/adrs/003-chart-auto-selection.md
  - **Dependencies:** T030

- [x] **T074:** Write docs/report.md (final reflection)
  - **Files:** docs/report.md
  - **Dependencies:** All tasks

- [x] **T075:** Write .env.example and .gitignore
  - **Files:** .env.example, .gitignore
  - **Dependencies:** None

- [x] **T076:** Write pyproject.toml with all dependencies
  - **Files:** pyproject.toml
  - **Dependencies:** All backend tasks

- [x] **T077:** Write Makefile for single-command startup
  - **Files:** Makefile
  - **Dependencies:** T070

---

*Task breakdown version: 1.0 | Last updated: 2026-05-12*
