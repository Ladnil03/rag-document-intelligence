# Phase 8 — Productionization and Deployment Readiness

## Goal

Transform the existing RAG Document Intelligence Platform from a local development application into a reproducible, containerized, observable, and deployment-ready system without changing core RAG behavior or introducing enterprise overengineering (no Kubernetes, Kafka, Celery, microservices).

---

## What Was Built

### 1. Dependency Management
**File:** `backend/requirements.txt`

Locked all direct project dependencies with version bounds. Used by `pip install -r requirements.txt` in both local `env/` and Docker image builds.

### 2. Environment Configuration Centralization
**File:** `backend/config.py`

Added three new settings sourced from environment variables:
- `ENVIRONMENT` — (`development` / `production`) controls log verbosity
- `LOG_LEVEL` — configurable logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- `ALLOWED_ORIGINS` — comma-separated list of allowed CORS origins

**File:** `backend/.env.example`

Updated with all required environment variables, placeholder values, and inline comments explaining each.

### 3. Alembic Database Migrations
**Files:** `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/script.py.mako`, `backend/alembic/versions/001_initial_schema.py`

Set up Alembic with SQLAlchemy metadata for the project models. Initial migration script (`001_initial_schema.py`) defines `users`, `documents`, `conversations`, and `messages` tables with full foreign keys, cascades, and indices.

```bash
# Apply all pending migrations
cd backend/
.\env\Scripts\alembic.exe upgrade head
```

### 4. Database Connectivity Check
**File:** `backend/database.py`

Added `check_database_connection()` function executing `SELECT 1` against PostgreSQL and returning `(True, "ok")` or `(False, error_message)`. Used by health probes.

### 5. Health Probes
**File:** `backend/main.py`

Three health endpoints:

| Endpoint | Purpose | Success | Failure |
|---|---|---|---|
| `GET /health/liveness` | Process alive | `200 {"status":"alive"}` | Never fails |
| `GET /health/readiness` | DB connectivity | `200 {"status":"ready"}` | `503 {"detail":"..."}` |
| `GET /health` | DB + storage | `200 {"status":"healthy"}` | `503 {"status":"unhealthy"}` |

### 6. CORS Middleware
**File:** `backend/main.py`

`CORSMiddleware` reads `ALLOWED_ORIGINS` from config. Default value includes `localhost:3000` and `localhost:5173` for local frontend development.

### 7. Global Exception Handler
**File:** `backend/main.py`

`@app.exception_handler(Exception)` catches any unhandled server error, logs the full traceback with `exc_info=True` server-side, and returns a sanitized `500 Internal Server Error` JSON. Prevents raw stack traces leaking to API clients.

### 8. File Upload Security
**File:** `backend/main.py`

Upload filenames sanitized with `os.path.basename()` to prevent path traversal attacks (`../../etc/passwd`). Files are stored at `storage/<uuid>.<ext>` regardless of the client-provided name.

### 9. Structured Logging
**File:** `backend/main.py`

Initializes a `rag_platform` logger with `LOG_LEVEL` from config. Logs auth failures, ingestion status, query events, and errors with consistent format.

### 10. Containerization
**File:** `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y gcc libpq-dev curl
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p storage chroma_data evaluation/reports
EXPOSE 8000
HEALTHCHECK CMD curl -f http://localhost:8000/health/liveness || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**File:** `backend/.dockerignore`

Excludes: `env/`, `.env`, `.git`, `__pycache__`, `*.pyc`, `storage/*`, `chroma_data/*`, `.pytest_cache/`, `test.db`.

### 11. Docker Compose Orchestration
**File:** `docker-compose.yml` (project root)

Two services:
- **`web`** — FastAPI + Uvicorn (built from `backend/Dockerfile`), port `8000`
- **`db`** — PostgreSQL 16 Alpine, port `5432`

The `web` service uses `depends_on` with condition `service_healthy` so it waits for PostgreSQL to be ready before starting.

Four named volumes for data persistence:

| Volume | Mount | Purpose |
|---|---|---|
| `postgres_data` | `/var/lib/postgresql/data` | PostgreSQL database files |
| `chroma_data` | `/app/chroma_data` | ChromaDB vector embeddings |
| `storage_data` | `/app/storage` | Uploaded document files |
| `evaluation_reports` | `/app/evaluation/reports` | Evaluation JSON reports |

---

## Deployment Workflow

### Local Development (No Docker)
```bash
cd backend/
.\env\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env   # then fill in values
.\env\Scripts\alembic.exe upgrade head
.\env\Scripts\uvicorn.exe main:app --reload
```

### Docker Compose
```bash
# From project root
copy backend\.env.example backend\.env   # fill in secrets
docker-compose up --build
```

First-time startup: apply migrations inside the running container:
```bash
docker-compose exec web alembic upgrade head
```

---

## Tests Added

**File:** `backend/test_main.py`

Added three health probe tests:
- `test_health_liveness_always_returns_alive` — asserts 200/alive always
- `test_health_readiness_returns_valid_shape` — asserts 200 or 503 with correct response schema
- `test_health_full_endpoint_returns_valid_shape` — asserts 200/healthy or 503/unhealthy

Also fixed `Request` missing import in `main.py`.

**Final test result:** `14 passed, 3 warnings` in 8.5 s

---

## Files Modified / Created

| File | Action | Description |
|---|---|---|
| `backend/requirements.txt` | Created | Locked dependency list |
| `backend/config.py` | Modified | Added `ENVIRONMENT`, `LOG_LEVEL`, `ALLOWED_ORIGINS` |
| `backend/.env.example` | Modified | Updated with Phase 8 variables |
| `backend/alembic.ini` | Created | Alembic configuration |
| `backend/alembic/env.py` | Created | Alembic migration environment |
| `backend/alembic/script.py.mako` | Created | Revision template |
| `backend/alembic/versions/001_initial_schema.py` | Created | Initial schema migration |
| `backend/database.py` | Modified | Added `check_database_connection()` |
| `backend/main.py` | Modified | CORS, health endpoints, exception handler, structured logging, filename sanitization, Request import |
| `backend/Dockerfile` | Created | Production container image |
| `backend/.dockerignore` | Created | Build context exclusions |
| `docker-compose.yml` | Created | Multi-container orchestration |
| `backend/test_main.py` | Modified | Health probe tests |
| `docs/understanding.md` | Modified | Phase 8 concept entries |
| `docs/system_architecture.md` | Modified | Phase 8 architecture section and diagram |
| `docs/workflow.md` | Modified | Local dev and Docker deployment workflows |
| `docs/decisions.md` | Modified | ADRs 028-033 |
| `docs/phases/phase8.md` | Created | This document |

---

## Deployment Readiness Status

The platform is **deployment-ready**:
- Locked dependencies (`requirements.txt`)
- Environment-driven configuration (no hardcoded secrets)
- Alembic database migrations (`alembic upgrade head`)
- Health probes (`/health/liveness`, `/health/readiness`, `/health`)
- CORS allow-listing (`ALLOWED_ORIGINS`)
- Global exception masking (no raw tracebacks to clients)
- File upload security (path traversal prevention)
- Structured logging (`LOG_LEVEL`)
- Docker container image (`Dockerfile`)
- Docker Compose multi-service orchestration (`docker-compose.yml`)
- Persistent storage volumes (no data loss on container restart)
- All 14 unit tests pass

> Active cloud deployment is left to the operator. The platform does not self-deploy.
