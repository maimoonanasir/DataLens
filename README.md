# DataLens — Generic Data Analytics Dashboard

DataLens is a full-stack web application that lets you upload any CSV file and immediately explore your data through an auto-generated interactive dashboard, global filters, an AI-powered chat interface, and an executive summary — no coding required.

**Dataset used for development and demo:** Online Retail II (UK Gift Retailer 2009–2011), ~1 million rows, available at [Kaggle](https://www.kaggle.com/datasets/mashlyn/online-retail-ii-uci).

---

## Prerequisites

Before running DataLens, ensure you have:

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11 or higher | [python.org](https://www.python.org/downloads/) |
| uv | latest | `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js | 18 or higher | [nodejs.org](https://nodejs.org/) |
| npm | 9 or higher | Comes with Node.js |
| Anthropic API Key | — | See below |

---

## Obtaining an Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign in or create a free account
3. Navigate to **API Keys** → **Create Key**
4. Copy the key (starts with `sk-ant-...`)
5. Paste it into your `.env` file (see Setup below)

The app uses `claude-haiku-4-5`, which is Anthropic's fastest and most cost-effective model. Typical usage for one project session costs less than $0.10.

---

## Setup Instructions

Follow these steps in order. Each step should take about 1 minute.

### Step 1 — Clone the repository

```bash
git clone <your-repo-url>
cd datalens
```

### Step 2 — Configure environment variables

```bash
cp .env.example .env
```

Open `.env` in any text editor and fill in your API key:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Leave the other variables at their defaults unless you need to change ports.

### Step 3 — Install backend dependencies

```bash
uv sync
```

This installs all Python dependencies listed in `pyproject.toml` into a virtual environment managed by `uv`. You do not need to activate the environment manually.

### Step 4 — Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### Step 5 — Start the application

**Option A — Single command (recommended):**

```bash
make dev
```

**Option B — Two terminals (if you don't have Make):**

Terminal 1 (backend):
```bash
uv run uvicorn backend.app.main:app --reload --port 8000
```

Terminal 2 (frontend):
```bash
cd frontend && npm run dev
```

### Step 6 — Open in browser

Navigate to **[http://localhost:5173](http://localhost:5173)**

You should see the DataLens upload screen. Drag and drop your CSV file to get started.

---

## Single Command to Start

```bash
make dev
```

This starts both the FastAPI backend (port 8000) and the React frontend (port 5173) simultaneously.

---

## Running Tests

**Backend tests (pytest):**

```bash
uv run pytest backend/tests/ -v
```

Expected output: 19+ tests passing.

**Frontend tests (Vitest):**

```bash
cd frontend && npm run test
```

Expected output: 20+ tests passing.

---

## Project Structure

```
datalens/
├── backend/app/          # FastAPI application
│   ├── main.py           # App entry point
│   ├── database.py       # SQLite engine
│   ├── models/           # Pydantic models
│   ├── routers/          # API endpoints
│   └── services/         # Business logic (profiler, charts, LLM)
├── frontend/src/         # React application
│   ├── App.tsx           # Root component
│   ├── components/       # UI components
│   └── lib/api.ts        # API client
├── docs/adrs/            # Architecture Decision Records
├── tasks/                # Implementation plan and task list
├── SPEC.md               # Full project specification
└── .env.example          # Environment variable template
```

---

## How to Use DataLens

1. **Upload** — Drag and drop any CSV file (up to 50 MB)
2. **Explore** — Browse 4–6 auto-generated charts on the Dashboard tab
3. **Filter** — Use the Global Filters panel to drill into segments
4. **Profile** — Switch to the Data Profile tab to see column statistics
5. **Chat** — Ask questions in plain English on the Chat tab
6. **Summarise** — Generate a one-click executive summary on the Summary tab

Your data persists in SQLite — refreshing the page restores the last dataset automatically.

---

## Troubleshooting

**"uv: command not found"**
Install uv: `pip install uv` or follow [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)

**"npm: command not found"**
Install Node.js from [nodejs.org](https://nodejs.org/). npm is included.

**Backend won't start — "ModuleNotFoundError: No module named 'backend'"**
Run the backend from the repo root (not from inside `backend/`):
```bash
cd datalens
uv run uvicorn backend.app.main:app --reload --port 8000
```

**"ANTHROPIC_API_KEY is not set" error in chat/summary**
Make sure `.env` exists (copy from `.env.example`) and contains your key. The file must be in the repo root, not inside `backend/`.

**Charts show "No data for current filters"**
Clear all filters using the "Clear all" button in the filter panel.

**File upload fails with "Could not parse CSV"**
Ensure your file is a valid CSV (comma-separated, UTF-8 or Latin-1 encoded) with at least 2 columns and 1 data row.

**Port 8000 or 5173 already in use**
Change the port in `.env` (BACKEND_PORT / FRONTEND_PORT) and update the `make dev` command accordingly.

---

## Team

- **Maimoona, Emaan and Abdullah** — Project lead, backend architecture, LLM integration, documentation

---

## License

Dataset: Online Retail II UCI — CC BY 4.0
Application code: MIT
