# Phase 2 — Document Upload and Processing

## Status

Completed (Implementation & Code Verification)

## Objective

Allow users to upload actual PDF and DOCX documents via `multipart/form-data`, validate file payloads, store raw binary files in local disk storage, track processing status in PostgreSQL, and extract clean plain text for downstream processing.

## Implemented Features

- File upload endpoint (`POST /documents/upload`) accepting `multipart/form-data`.
- Strict file validation:
  - Allowed extensions: `.pdf` and `.docx` (`415 Unsupported Media Type`)
  - Non-empty payload check (>0 bytes) (`400 Bad Request`)
  - Maximum size limit check (10MB / 10,485,760 bytes) (`413 Payload Too Large`)
  - Missing file / empty filename check (`400 Bad Request`)
- Unique UUID filename generation (e.g. `storage/a1b2c3d4.pdf`) preventing path collisions and security risks.
- Local binary file storage in `backend/storage/`.
- Text extraction engine (`backend/extractor.py`):
  - PDF text extraction page-by-page using `pypdf`
  - DOCX text extraction paragraph-by-paragraph using `python-docx`
- Document processing state management (`UPLOADED`, `PROCESSING`, `COMPLETED`, `FAILED`).
- Extended SQLAlchemy `Document` model and Pydantic schemas with metadata and extracted text.
- File cleanup on deletion (`DELETE /documents/{id}` removes binary file from `storage/`).

## API Endpoints

- `POST /documents/upload` — Uploads PDF/DOCX, validates file, saves binary to `storage/`, inserts PostgreSQL metadata, extracts text, updates status, returns `DocumentResponse` (`201 Created`).
- `GET /documents` — Retrieves all stored documents with metadata and processing status (`200 OK`).
- `GET /documents/{document_id}` — Retrieves single document by ID including `extracted_text` (`200 OK` or `404 Not Found`).
- `PATCH /documents/{document_id}` — Updates document title by ID (`200 OK` or `404 Not Found`).
- `DELETE /documents/{document_id}` — Deletes document record from PostgreSQL and removes associated file from `storage/` (`200 OK` or `404 Not Found`).

## Database Schema Changes

Updated `documents` table in PostgreSQL:
- `id` (INTEGER, PRIMARY KEY)
- `name` (VARCHAR — Original filename)
- `stored_file_path` (VARCHAR — Relative path in `storage/`)
- `file_type` (VARCHAR — `'pdf'` or `'docx'`)
- `file_size` (INTEGER — Size in bytes)
- `created_at` (TIMESTAMP WITH TIMEZONE)
- `processing_status` (VARCHAR — `'UPLOADED'`, `'PROCESSING'`, `'COMPLETED'`, `'FAILED'`)
- `extracted_text` (TEXT — Extracted plain text string content)

## File Storage

Binary files are saved to:
```text
backend/storage/
```
Stored using unique filenames generated via `uuid.uuid4()` + lowercased extension.

## Text Extraction

- **PDF**: Handled by `pypdf.PdfReader`
- **DOCX**: Handled by `docx.Document`
- Corrupt/unreadable files set status to `FAILED` without crashing the application.

## Processing Statuses Implemented

- `UPLOADED`: Initial file upload and disk write complete.
- `PROCESSING`: Text extraction in progress.
- `COMPLETED`: Text extracted successfully and persisted to PostgreSQL.
- `FAILED`: Text extraction failed due to corrupt document or unreadable format.

## Files Changed / Created

- `backend/storage/` — Local storage directory for binary document files.
- `backend/extractor.py` — Text extraction engine for PDF and DOCX formats.
- `backend/models.py` — Updated `Document` SQLAlchemy model with file fields.
- `backend/schemas.py` — Updated Pydantic schemas and `ProcessingStatus` Enum.
- `backend/crud.py` — Added file upload and status/text updating functions.
- `backend/main.py` — Implemented `POST /documents/upload` endpoint and file deletion cleanup.
- `backend/.gitignore` — Configured to ignore `storage/*` contents while retaining `.gitkeep`.

## Dependencies Added

Installed into `backend/env/`:
- `pypdf` (v6.15.0) — PDF parsing and text extraction library
- `python-docx` (v1.2.0) — Microsoft Word (`.docx`) document parsing library
- `lxml` (v6.1.1) — XML parser for `python-docx`
- `python-multipart` (v0.0.32) — FastAPI form data parsing library

## Environment Variables

- `DATABASE_URL` — Connection string in `backend/.env`. Driver normalized in `database.py`.

## Functional Testing Notice (Per Section 24)

- **Backend Code Verification**: Python import check verified cleanly using `backend/env/`. Database schema connection verified against local PostgreSQL database.
- **Developer Manual Testing**: Per Section 24 of the user prompt, full manual functional testing of the upload endpoint (`POST /documents/upload`) with sample PDF and DOCX files will be performed manually by the developer.

## Known Limitations

- No user authentication or user accounts.
- Local disk storage only (no cloud object storage).
- Synchronous processing (no background task queues).
- Plain text extraction only (no text chunking, embeddings, vector database, RAG, or LLM).

## What Was NOT Implemented

Strictly adhered to Phase 2 boundaries. Did NOT implement:
- Text chunking / overlapping windows
- Embeddings / Vectorization
- ChromaDB / Vector search
- RAG query pipeline / LLM integration
- Authentication / JWT / User accounts
- Background workers (Celery, Redis, RabbitMQ)
- Docker / Cloud deployment

## Next Phase

```text
Phase 3 — RAG Ingestion Pipeline
```
