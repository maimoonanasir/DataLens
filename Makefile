.PHONY: dev backend frontend test test-backend test-frontend lint install

# Start both backend and frontend concurrently
dev:
	@echo "Starting DataLens (backend on :8000, frontend on :5173)..."
	@trap 'kill 0' EXIT; \
	uv run uvicorn backend.app.main:app --reload --port 8000 & \
	(cd frontend && npm run dev) & \
	wait

# Backend only
backend:
	uv run uvicorn backend.app.main:app --reload --port 8000

# Frontend only
frontend:
	cd frontend && npm run dev

# Install all dependencies
install:
	uv sync
	cd frontend && npm install

# Run all tests
test: test-backend test-frontend

# Backend tests
test-backend:
	uv run pytest backend/tests/ -v

# Frontend tests
test-frontend:
	cd frontend && npm run test

# Lint
lint:
	uv run ruff check backend/
	cd frontend && npm run lint
