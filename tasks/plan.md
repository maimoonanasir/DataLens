# Implementation Plan
*Plan version: 1.0 | Last updated: 2026-05-12*

---

## Plan Summary

DataLens is built in seven thin vertical slices. Each slice delivers a shippable increment — the app runs and the new capability is demonstrable before the next slice begins. We start with the smallest possible end-to-end flow (upload → display something) and layer capabilities on top. Week 1 is entirely spec and plan work. Week 2 delivers a working app. Week 3 polishes, documents, and prepares the demo. Total estimate: ~35 atomic tasks across 21 days.

---

## Major Phases and Milestones

### Phase 1: Foundation (Days 1–7, Week 1)

**Goal:** Repo exists, skills are discoverable, spec is solid, plan and tasks are complete. No application code yet.

- [x] Clone starter template, rename repo, push to GitHub
- [x] Verify six skills are in `.agent/skills/` and discoverable
- [x] Dataset exploration: download Online Retail II, inspect columns, identify quirks
- [x] Complete SPEC.md (all 10 sections, testable success criteria)
- [x] Complete plan.md (this document) and todo.md

**Checkpoint:** `uv sync` and `npm install` succeed. Empty pytest and vitest pass. Skills folder committed.

---

### Phase 2: CSV Upload + SQLite Persistence (Day 8)

**Goal:** User uploads a CSV; it is stored in SQLite; upload ID returned.

- FastAPI app bootstrapped (main.py, CORS, lifespan)
- SQLite engine, metadata table created on startup
- `POST /api/upload` endpoint: validate size (≤50 MB), validate CSV format, parse with Pandas, store in dynamic SQLite table, return dataset ID
- Pydantic models: `UploadResponse`, `DatasetMeta`
- Frontend: `UploadZone` component — drag-and-drop + click, calls upload API, shows success/error
- Tests: 4 upload tests (valid, non-CSV, too large, empty)

**Checkpoint:** Upload the Online Retail II CSV; see a dataset ID returned; confirm SQLite file contains the data table.

---

### Phase 3: Data Profiling Display (Day 9)

**Goal:** After upload, profiling results appear on screen.

- `profiler.py` service: detect column types (numeric/categorical/datetime/text), count nulls, compute basic stats
- `GET /api/datasets/{id}/profile` endpoint
- Frontend: `DataProfile` component — renders column cards with type badge, null %, and stat summary
- Tests: profiling accuracy on sample data, null count correctness

**Checkpoint:** Upload CSV → see column type badges and statistics in the UI.

---

### Phase 4: Dashboard Visualizations (Days 10–11)

**Goal:** Dashboard with ≥ 4 auto-generated visualizations renders from uploaded data.

- `chart_selector.py`: given a profile, return 4–6 `ChartSpec` objects (chart_type, title, x/y columns)
- `POST /api/datasets/{id}/charts` endpoint: accepts filter state, returns data arrays for each ChartSpec
- Frontend: `Dashboard` + `ChartCard` — renders Recharts bar/line/histogram/scatter based on spec type
- Tests: auto-selection logic, chart data endpoint shape

**Checkpoint:** Upload CSV → dashboard shows ≥ 4 meaningful charts with real data.

---

### Phase 5: Global Filters (Day 12)

**Goal:** Dropdown/date/slider filters update all charts simultaneously.

- `GET /api/datasets/{id}/filter-options` — returns unique values for categorical columns, min/max for numeric/datetime
- `FilterPanel` component — renders appropriate control per filter type; emits filter state object
- Dashboard re-fetches chart data when filter state changes
- `query_engine.py` applies WHERE clauses from filter state to every chart query
- Tests: filter application test (country filter reduces row count)

**Checkpoint:** Select "United Kingdom" in Country filter → all charts update to UK-only data.

---

### Phase 6: LLM Chat Interface (Day 13)

**Goal:** User asks a natural language question; LLM uses tool-calling to answer with data.

- `llm.py`: Anthropic client, four tool definitions (`query_data`, `get_statistics`, `get_column_values`, `filter_data`)
- `POST /api/datasets/{id}/chat` endpoint: accepts message history, runs tool-calling loop, returns answer
- `ChatPanel` component — message list, input field, loading state
- Tests: tool function unit tests (mock LLM, verify tools return correct shapes)

**Checkpoint:** Ask "which country has the highest total revenue?" → get correct country name with a numeric value.

---

### Phase 7: Executive Summary (Day 15)

**Goal:** One-click LLM-generated narrative summary referencing actual data patterns.

- `POST /api/datasets/{id}/summary` — uses LLM to generate a business-analyst-style memo
- Prompt engineering: pass top stats from profile, sample chart data, instruct "write like a senior BA"
- `ExecutiveSummary` component — "Generate Summary" button, loading skeleton, formatted output
- Tests: summary endpoint returns non-empty string; references dataset-specific terms

**Checkpoint:** Click "Generate Executive Summary" → readable narrative appears within 30 seconds.

---

### Phase 8: Polish, Documentation, Demo Prep (Days 15–21)

**Goal:** Demo-ready app with complete documentation and passing clean-install verification.

- Bug fixes from mid-project video review
- UI polish: loading states, error messages, empty state illustrations
- Write README.md (complete, clean-install verified)
- Write three ADRs (LLM provider, SQLite schema, chart auto-selection)
- Write docs/report.md reflection
- Mid-project video recording (Day 14)
- Dry-run clean install (Day 20)
- Demo preparation (Day 21)

---

## Risks and Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Online Retail II CSV has mixed datetime formats causing parse errors | High | Use `pd.to_datetime(..., infer_datetime_format=True, errors='coerce')` — tested in Phase 3 |
| Anthropic API rate limits during heavy testing | Medium | Use claude-haiku-4-5 (cheap); add exponential backoff; cache summary results |
| Loading 1M rows into SQLite is slow | Medium | Use chunked Pandas `to_sql` with `chunksize=10000`; report progress via SSE if needed |
| LLM tool-calling returns wrong column names (hallucination) | Medium | Pass actual column names in every tool schema; validate tool args against profile before executing |
| Frontend chart library mismatch with data shape | Low | Define and test data shape contracts in `test_charts.py` before building ChartCard |
| Agent skips writing tests | Medium (known failure mode) | Explicitly request tests before implementation for each task; enforce in Boundaries |

---

## Parallel Work Opportunities

- Phase 3 profiler backend can be built in parallel with Phase 2 frontend UploadZone, since they share only the dataset ID interface.
- Phase 6 LLM tool definitions can be written in parallel with Phase 5 filter UI, since they use the same query_engine.

---

## Dependency Notes

- `chart_selector.py` depends on the `ColumnProfile` model output from `profiler.py`
- `query_engine.py` must be in place before LLM tools can use it
- Frontend `FilterPanel` depends on `GET /api/datasets/{id}/filter-options` response shape
- `ExecutiveSummary` depends on `llm.py` being stable from Phase 6

---

## Verification Checkpoints (Between Every Phase)

1. `uv run pytest backend/tests/ -v` — all tests pass
2. `cd frontend && npm run test` — all tests pass
3. App runs without errors (no red console output)
4. Git log shows atomic commits for this phase's work
5. No `[TODO]` or `pass` placeholders in committed code

---

*Plan version: 1.0 | Last updated: 2026-05-12*
