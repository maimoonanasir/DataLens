# SPEC: DataLens
*Spec version: 1.0 | Last updated: 2026-05-12*

---

## 1. Objective

**What is DataLens?**
DataLens is a generic data analytics web application that allows any user to upload a CSV file and immediately receive an auto-generated interactive dashboard — with visualizations, global filters, an LLM-powered chat interface, and an executive summary — without writing a single line of code or possessing any technical knowledge.

**Who is the target user?**
A business analyst at a mid-size retail or e-commerce firm who regularly receives raw CSV exports from internal systems (sales data, CRM extracts, inventory reports) and needs rapid exploratory insight — currently done manually in Excel — before handing off findings to leadership. They are comfortable using web apps but have no programming background.

**What does success look like?**
A business analyst can upload the Online Retail II CSV (~1 million rows), explore the data through a dashboard with at least 4 auto-generated visualizations, apply global filters (e.g., filter by Country = "United Kingdom"), ask the chat interface "which country has the highest total revenue?" and receive a correct data-grounded answer, and generate an executive summary — all within 90 seconds of the page loading.

### User Stories

- As a business analyst, I want to upload any CSV file and have the app automatically detect column types and compute statistics, so that I can understand my dataset immediately without manual inspection.
- As a business analyst, I want to see 4–6 visualizations auto-generated from my data, so that I can quickly identify patterns and trends.
- As a business analyst, I want to apply filters (dropdown, date range, slider) that update all charts at once, so that I can drill down into segments without losing context.
- As a business analyst, I want to ask plain-English questions about my data and receive accurate, data-grounded answers, so that I can explore hypotheses conversationally.
- As a business analyst, I want a one-click executive summary that reads like a business analyst's memo, not a technical printout, so that I can share findings with stakeholders immediately.
- As a business analyst, I want my uploaded dataset to persist after I refresh the page, so that I do not have to re-upload every time.
- As a business analyst, I want to upload a different CSV and have the app work seamlessly with the new data, so that I can use DataLens for any dataset I receive.

### Assumptions

1. The app runs locally on the analyst's laptop (macOS, Linux, or Windows) — not deployed to a cloud environment.
2. The assigned test dataset (Online Retail II, UK gift retailer 2009–2011, ~1 million rows) has columns: InvoiceNo, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country.
3. CSVs are well-structured (single header row, comma-delimited) — malformed files are rejected with user-facing error messages.
4. The LLM provider is Anthropic Claude (claude-haiku-4-5) — selected for cost efficiency and strong tool-calling support.
5. Users will have their own Anthropic API key — the app does not bundle or proxy an API key.
6. CSV files up to 50 MB are supported; files beyond this limit are rejected.
7. The app is single-user; no authentication or concurrent session management is required.
8. For very wide CSVs (100+ columns), the profiler will show all columns but auto-select charts from the top-10 most interesting columns only.
9. InvoiceDate in the Online Retail II dataset requires datetime parsing with mixed formats — the profiler handles this gracefully.
10. "Quantity" can be negative (cancellation orders) — visualizations and chat answers treat these as-is unless the user asks to exclude them.

### Success Criteria (Specific and Testable)

| # | Criterion |
|---|-----------|
| SC-1 | CSV upload accepts files ≤ 50 MB and rejects > 50 MB with HTTP 413 |
| SC-2 | CSV upload rejects non-CSV files with HTTP 400 and a human-readable error |
| SC-3 | Data profiling completes within 10 seconds for the Online Retail II file |
| SC-4 | Profile correctly identifies: InvoiceDate as datetime, Country as categorical, Quantity/Price as numeric, Description as text |
| SC-5 | Dashboard renders ≥ 4 visualizations within 3 seconds of profiling completion |
| SC-6 | Global filters (Country dropdown, date range, Quantity slider) update all charts within 1 second |
| SC-7 | Chat interface returns a data-grounded answer to "which country has the highest total revenue?" within 15 seconds |
| SC-8 | Chat interface correctly answers all 5 sample dataset-specific questions from the hidden grading rubric |
| SC-9 | Executive summary generates within 30 seconds and references ≥ 3 specific data patterns from the dataset |
| SC-10 | Uploading a second CSV replaces the dataset; charts and chat update to reflect the new data |
| SC-11 | Data persists after page refresh — the last uploaded dataset is restored from SQLite without re-upload |
| SC-12 | Backend returns HTTP 200 on all chart data endpoints with no console errors in the browser |

---

## 2. Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Frontend framework | React 18 with Vite 5 | Mandated by spec |
| Styling | Tailwind CSS v3 | Mandated by spec |
| UI Components | Headless Tailwind primitives | No heavy dependency, full control |
| Charts | Recharts 2 | Mandated choice; declarative, React-native |
| Frontend testing | Vitest + @testing-library/react | Mandated by spec |
| Backend framework | FastAPI | Mandated by spec |
| Data validation | Pydantic v2 | Mandated by spec |
| Python version | 3.11+ | Mandated by spec |
| Package manager | uv with pyproject.toml | Mandated by spec |
| Data processing | Pandas 2.x | Mandated by spec |
| ORM / DB access | SQLAlchemy 2.x (Core, not ORM) | Provides clean SQL abstraction over SQLite |
| Database | SQLite | Mandated by spec |
| LLM provider | Anthropic Claude (claude-haiku-4-5) | Best tool-calling support; cost-effective at scale; see ADR-001 |
| LLM pattern | Tool-use / function-calling | Mandated by spec |
| Backend testing | pytest | Mandated by spec |
| Coding agent | Claude (Cowork) | Available subscription |

---

## 3. Commands

```bash
# --- Setup (run once) ---
# Backend
cd datalens
uv sync

# Frontend
cd frontend
npm install

# --- Development (run both simultaneously) ---
# Start backend (from repo root)
uv run uvicorn backend.app.main:app --reload --port 8000

# Start frontend (in a second terminal, from repo root)
cd frontend && npm run dev

# --- Single-command start (using make) ---
make dev

# --- Tests ---
# Backend tests
uv run pytest backend/tests/ -v

# Frontend tests
cd frontend && npm run test

# --- Lint ---
uv run ruff check backend/
cd frontend && npm run lint

# --- Build (production frontend) ---
cd frontend && npm run build
```

---

## 4. Project Structure

```
datalens/
├── .agent/
│   └── skills/                    → Six mandatory Agent Skills (SKILL.md files)
│       ├── spec-driven-development/
│       ├── planning-and-task-breakdown/
│       ├── incremental-implementation/
│       ├── test-driven-development/
│       ├── documentation-and-adrs/
│       └── git-workflow-and-versioning/
├── docs/
│   ├── adrs/                      → Architecture Decision Records
│   │   ├── 001-llm-provider.md
│   │   ├── 002-sqlite-schema.md
│   │   └── 003-chart-auto-selection.md
│   └── report.md                  → Final reflection document
├── tasks/
│   ├── plan.md                    → Phase-by-phase implementation plan
│   └── todo.md                    → Atomic task breakdown
├── backend/
│   ├── app/
│   │   ├── main.py                → FastAPI app factory, CORS, lifespan
│   │   ├── database.py            → SQLite engine, session management
│   │   ├── models/
│   │   │   ├── dataset.py         → Pydantic models: DatasetMeta, ProfileResult
│   │   │   ├── chart.py           → ChartRequest, ChartData, ChartSpec
│   │   │   └── chat.py            → ChatMessage, ChatResponse, ToolCall
│   │   ├── routers/
│   │   │   ├── upload.py          → POST /api/upload — CSV ingestion
│   │   │   ├── datasets.py        → GET /api/datasets — list persisted datasets
│   │   │   ├── profile.py         → GET /api/datasets/{id}/profile
│   │   │   ├── charts.py          → POST /api/datasets/{id}/charts
│   │   │   ├── filters.py         → GET /api/datasets/{id}/filter-options
│   │   │   ├── chat.py            → POST /api/datasets/{id}/chat
│   │   │   └── summary.py         → POST /api/datasets/{id}/summary
│   │   └── services/
│   │       ├── profiler.py        → Column type detection, null counts, statistics
│   │       ├── chart_selector.py  → Auto-select 4-6 chart types from profile
│   │       ├── query_engine.py    → SQL-backed data querying helpers
│   │       └── llm.py             → Anthropic client, tool definitions, chat loop
│   └── tests/
│       ├── conftest.py            → Shared fixtures (test DB, test client)
│       ├── test_upload.py         → Upload validation tests
│       ├── test_profiling.py      → Profiling accuracy tests
│       ├── test_chart_selector.py → Auto-selection logic tests
│       ├── test_charts.py         → Chart data endpoint tests
│       └── test_chat_tools.py     → LLM tool function unit tests
├── frontend/
│   ├── src/
│   │   ├── main.tsx               → React entry point
│   │   ├── App.tsx                → Root component, dataset state
│   │   ├── components/
│   │   │   ├── UploadZone.tsx     → Drag-and-drop CSV upload
│   │   │   ├── DataProfile.tsx    → Column stats panel
│   │   │   ├── Dashboard.tsx      → Chart grid container
│   │   │   ├── ChartCard.tsx      → Single chart wrapper (Recharts)
│   │   │   ├── FilterPanel.tsx    → Global filter controls
│   │   │   ├── ChatPanel.tsx      → LLM chat interface
│   │   │   └── ExecutiveSummary.tsx → Summary display
│   │   ├── hooks/
│   │   │   ├── useDataset.ts      → Dataset state + API calls
│   │   │   └── useFilters.ts      → Filter state management
│   │   └── lib/
│   │       └── api.ts             → Typed API client (fetch wrappers)
│   ├── tests/
│   │   ├── UploadZone.test.tsx
│   │   ├── DataProfile.test.tsx
│   │   ├── FilterPanel.test.tsx
│   │   ├── ChatPanel.test.tsx
│   │   └── Dashboard.test.tsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
├── SPEC.md                        → This file
├── README.md                      → Setup + single-command startup
├── .env.example                   → Required environment variables
├── .gitignore
├── pyproject.toml                 → Python deps (uv)
└── Makefile                       → Convenience commands
```

---

## 5. Code Style

### Python (Backend)

```python
# backend/app/services/profiler.py — representative style

from __future__ import annotations

import pandas as pd
from pydantic import BaseModel


class ColumnProfile(BaseModel):
    name: str
    dtype: str  # "numeric" | "categorical" | "datetime" | "text"
    null_count: int
    null_pct: float
    unique_count: int
    stats: dict[str, float | str | None]  # min/max/mean/median or top_values


def profile_dataframe(df: pd.DataFrame) -> list[ColumnProfile]:
    """Return a profile for every column in *df*.

    Args:
        df: The raw dataframe loaded from the uploaded CSV.

    Returns:
        A list of ColumnProfile objects, one per column.
    """
    profiles: list[ColumnProfile] = []
    for col in df.columns:
        series = df[col]
        dtype = _detect_dtype(series)
        profiles.append(
            ColumnProfile(
                name=col,
                dtype=dtype,
                null_count=int(series.isna().sum()),
                null_pct=round(series.isna().mean() * 100, 2),
                unique_count=int(series.nunique()),
                stats=_compute_stats(series, dtype),
            )
        )
    return profiles
```

**Key conventions:**
- `snake_case` for all Python identifiers
- Type hints on every function signature (enforced by ruff)
- Pydantic models for every API request/response boundary
- `ruff` for linting and formatting (line length 100)
- Docstrings on all public functions using Google style
- No bare `except` — always catch specific exceptions

### TypeScript / React (Frontend)

```tsx
// frontend/src/components/ChartCard.tsx — representative style

import { type FC } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import type { ChartSpec } from "../lib/api";

interface ChartCardProps {
  spec: ChartSpec;
  data: Record<string, unknown>[];
  loading?: boolean;
}

const ChartCard: FC<ChartCardProps> = ({ spec, data, loading = false }) => {
  if (loading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg" />;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">{spec.title}</h3>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data}>
          <XAxis dataKey={spec.xKey} tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey={spec.yKey} fill="#6366f1" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ChartCard;
```

**Key conventions:**
- `camelCase` for variables and functions; `PascalCase` for components and types
- TypeScript strict mode enabled
- Functional components with explicit `FC<Props>` type
- Props interfaces defined inline above each component
- Tailwind utility classes only — no custom CSS files
- All API calls go through `lib/api.ts` — no raw `fetch` in components

---

## 6. Testing Strategy

**Frameworks:** `pytest` (backend), `Vitest` + `@testing-library/react` (frontend)

**Test locations:** `backend/tests/`, `frontend/tests/`

### Backend Tests (minimum 10)

| Test file | What is tested |
|-----------|---------------|
| `test_upload.py` | Valid CSV accepted (200); non-CSV rejected (400); >50 MB rejected (413); empty file rejected (400) |
| `test_profiling.py` | Column type detection (numeric/categorical/datetime/text); null counts correct; stats accurate |
| `test_chart_selector.py` | Categorical column → bar chart; datetime column → line chart; two numerics → scatter; no datetime → no line |
| `test_charts.py` | Chart data endpoint returns correctly shaped JSON; filters applied correctly |
| `test_chat_tools.py` | `query_data` tool returns correct aggregated values; `get_statistics` returns profile data; `get_column_values` returns unique values |

### Frontend Tests (minimum 5)

| Test file | What is tested |
|-----------|---------------|
| `UploadZone.test.tsx` | Renders upload zone; shows error on invalid file type |
| `DataProfile.test.tsx` | Renders column cards from mock profile data |
| `FilterPanel.test.tsx` | Dropdown renders filter options; onChange fires callback |
| `ChatPanel.test.tsx` | Input renders; send button triggers callback; messages render |
| `Dashboard.test.tsx` | Renders correct number of chart cards from spec list |

**TDD Discipline:** Tests are written before or alongside the implementation of each feature, not added at the end. The git history will reflect this — each feature commit will contain both the implementation and its tests.

---

## 7. Boundaries

### Always Do

- Run `uv run pytest` and `npm run test` before every commit
- Use Pydantic for every API request/response boundary
- Validate uploaded CSV size and format before any processing
- Commit `.agent/skills/` folder as part of the repo
- Write an ADR when making a non-trivial architectural decision
- Wrap all LLM calls in try/except with graceful fallback error messages
- Use parameterized SQL queries (never string-interpolated SQL)
- Return HTTP 4xx with a JSON `{ "detail": "..." }` body for all user errors

### Ask First

- Adding new Python dependencies to `pyproject.toml`
- Adding new npm packages to `package.json`
- Changing the SQLite schema (may require data migration)
- Modifying the public API shape (affects frontend)
- Changing the LLM provider or model
- Adding new environment variables
- Changing the chart selection algorithm in ways that affect chart count

### Never Do

- Commit `.env` files (only `.env.example` is committed)
- Commit API keys or secrets of any kind
- Skip tests to ship faster
- Remove failing tests without team approval
- Deploy to a production environment (local laptop only)
- Edit files inside `.agent/skills/` (these come from Addy Osmani's repo)
- Use string-interpolated SQL (use parameterized queries)
- Make raw `fetch` calls inside React components (use `lib/api.ts`)

---

## 8. Success Criteria

See Section 1 (Success Criteria table, SC-1 through SC-12).

---

## 9. Out of Scope

- User authentication and multi-user accounts
- Production deployment to cloud infrastructure
- Mobile responsive design
- Custom machine learning or forecasting models
- Real-time collaborative editing
- Any feature requiring paid third-party services beyond the LLM API
- Handling multi-sheet Excel files (CSV only)
- Streaming LLM responses (request/response is sufficient)

---

## 10. Open Questions → Resolved

| Question | Resolution | ADR |
|----------|-----------|-----|
| Which chart library: Recharts or Plotly? | Recharts — lighter bundle, more React-native, sufficient for our chart types | ADR-003 |
| Which LLM provider? | Anthropic Claude (claude-haiku-4-5) — best tool-calling, reasonable cost | ADR-001 |
| How to store arbitrary CSVs in SQLite? | Dynamic table per dataset, metadata table for schema tracking | ADR-002 |
| Should the executive summary be editable? | No — read-only; regenerate button sufficient for MVP | Out of scope |
| How to handle very wide CSVs (100+ columns)? | Profile all columns; auto-select charts from top-10 by interest score | SPEC assumption 8 |
