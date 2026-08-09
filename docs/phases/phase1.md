# Phase 1 — PostgreSQL Backend Foundation

## Status

Completed

## Objective

Replace in-memory document storage (`documents = []`) with persistent PostgreSQL database storage using SQLAlchemy ORM and FastAPI.

## Implemented Features

- Persistent relational storage using PostgreSQL and SQLAlchemy ORM.
- Request-scoped database session management using FastAPI `Depends(get_db)`.
- Separate SQLAlchemy database model (`Document`) and Pydantic validation schemas (`DocumentCreate`, `DocumentUpdate`, `DocumentResponse`).
- Complete RESTful CRUD API endpoints (`POST`, `GET` list, `GET` item, `PATCH`, `DELETE`).
- Proper HTTP status codes (`201 Created`, `200 OK`, `404 Not Found`, `422 Unprocessable Entity`).
- Automated pytest test suite covering all CRUD routes and restart persistence verification.
- Completely removed `documents = []` in-memory list as source of truth.

## API Endpoints

- `GET /` — Health check endpoint returning status message (`200 OK`).
- `POST /documents` — Creates a document in PostgreSQL (`201 Created`).
- `GET /documents` — Retrieves all documents stored in PostgreSQL (`200 OK`).
- `GET /documents/{document_id}` — Retrieves a single document by ID (`200 OK` or `404 Not Found`).
- `PATCH /documents/{document_id}` — Updates a document name by ID (`200 OK` or `404 Not Found`).
- `DELETE /documents/{document_id}` — Deletes a document by ID (`200 OK` or `404 Not Found`).

## Database Schema

### `documents` Table
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIMEZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## Files Changed / Created

- `backend/.env.example` — Template for database environment configuration.
- `backend/.env` — Environment file for database configuration.
- `backend/database.py` — Database engine, `SessionLocal`, and `get_db()` dependency.
- `backend/models.py` — SQLAlchemy `Document` table model.
- `backend/schemas.py` — Pydantic schemas for request/response validation.
- `backend/crud.py` — Database helper query functions.
- `backend/main.py` — Updated FastAPI endpoints with database session injection.
- `backend/test_main.py` — Comprehensive pytest suite.
- `backend/.gitignore` — Configured to exclude `.env`, `env`, and `test.db`.

## Dependencies Added

Installed into `backend/env/`:
- `sqlalchemy` (v2.0.51) — ORM library
- `psycopg` (v3.3.4) & `psycopg-binary` — PostgreSQL driver
- `python-dotenv` (v1.2.2) — Environment variable management
- `pytest` (v9.1.1) — Automated testing framework
- `httpx` (v0.28.1) — HTTP test client dependency

## Environment Variables

Defined in `backend/.env` (and `.env.example`):
- `DATABASE_URL` — Connection string (Format: `postgresql+psycopg://username:password@host:port/database_name`).

## Tests Performed

Ran automated pytest suite in `backend/env/`:
1. `test_1_create_document`: Creates document record, expects `201 Created` — **PASSED**.
2. `test_2_get_all_documents`: Retrieves list of documents, expects `200 OK` — **PASSED**.
3. `test_3_get_one_document`: Retrieves existing document by ID, expects `200 OK` — **PASSED**.
4. `test_4_update_document`: Updates document name via PATCH, expects `200 OK` — **PASSED**.
5. `test_5_verify_update`: Re-retrieves document and verifies updated name — **PASSED**.
6. `test_6_delete_document`: Deletes document by ID, expects `200 OK` — **PASSED**.
7. `test_7_missing_document`: Queries non-existent ID, expects `404 Not Found` — **PASSED**.
8. `test_8_persistence_verification`: Creates record, closes database session context, re-queries database — **PASSED**.

Result: **8 passed in 1.07s**.

## Persistence Verification

Explicitly verified in `test_8_persistence_verification`. Data written to the database persists across session closes and server process reloads, confirming PostgreSQL has replaced RAM as the single source of truth.

## Known Limitations

- No authentication or user isolation (`user_id`).
- No physical file upload or document parsing (PDF, DOCX, TXT).
- No text chunking or vector embeddings.
- No ChromaDB or vector search integration.
- No LLM integration or RAG query engine.

## What Was NOT Implemented

Strictly adhered to Phase 1 boundaries. Did NOT implement:
- Authentication / JWT / User accounts
- File uploads / File storage
- PDF / DOCX processing
- Text extraction / Chunking
- Embeddings / ChromaDB / Vector search
- RAG / LLM integration / Agents / MCP
- Redis / Celery / Background workers
- Docker / Deployment

## Next Phase

```text
Phase 2 — Document Upload and Processing
```
