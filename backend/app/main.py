"""DataLens — FastAPI application entry point.

Registers all routers, sets up CORS for the React frontend (port 5173),
and initialises the SQLite database on startup.

Start with:
    uv run uvicorn backend.app.main:app --reload --port 8000
"""

from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.database import init_db
from backend.app.routers import upload, datasets, profile, charts, filters, chat, summary


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup and shutdown logic."""
    # Startup: initialise database schema
    init_db()
    yield
    # Shutdown: nothing to clean up for SQLite


app = FastAPI(
    title="DataLens API",
    description="Generic data analytics dashboard backend",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — allow the Vite dev server and production build
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(upload.router)
app.include_router(datasets.router)
app.include_router(profile.router)
app.include_router(charts.router)
app.include_router(filters.router)
app.include_router(chat.router)
app.include_router(summary.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/api/health", tags=["health"])
def health_check() -> dict:
    """Simple liveness probe."""
    return {"status": "ok", "service": "DataLens API", "version": "1.0.0"}
