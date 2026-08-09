# RAG Document Intelligence Platform

A enterprise-grade, document-centric Retrieval-Augmented Generation (RAG) backend platform built with FastAPI, PostgreSQL, ChromaDB, Sentence-Transformers, and OpenAI Responses API.

The platform enables users to upload PDF/DOCX documents, index them into a persistent vector store with multi-tenant data isolation, perform grounded Q&A with source citations, participate in persistent streamed conversations over Server-Sent Events (SSE), evaluate RAG retrieval and answer generation quality via an off-line evaluation suite, and deploy as a fully containerized multi-service system via Docker Compose.

---

## System Architecture

```text
Documents (PDF/DOCX)
        ↓
Text Extraction (pypdf / python-docx)
        ↓
Chunking (Paragraph/Boundary aware)
        ↓
Embeddings (sentence-transformers / all-MiniLM-L6-v2)
        ↓
ChromaDB Vector Store (Persistent with user_id isolation)
        ↓
Retrieval (Cosine similarity filtering)
        ↓
Conversational History + Document Context Prompt
        ↓
LLM Generation (OpenAI Responses streaming via SSE)
        ↓
Phase 7 RAG Evaluation Suite (Recall@K, Precision@K, LLM-as-a-Judge)
        ↓
Phase 8 Production Layer (Docker, Alembic, Health Probes, CORS, Logging)
```

---

## Key Features

- **Document Processing**: Ingests PDF and DOCX documents with automated text extraction, character-boundary chunking (`CHUNK_SIZE=1000`, `CHUNK_OVERLAP=200`), and 384-dimensional vector embeddings.
- **Authentication & Multi-User Isolation**: JWT authentication with HS256 tokens and password hashing via `pwdlib`. Enforces strict tenant isolation in PostgreSQL and ChromaDB (`user_id` metadata filter).
- **Direct Grounded RAG Query (`POST /query`)**: Semantic search returning grounded answers with structured source citations. Automatically refuses to generate answers when no chunks meet `SIMILARITY_THRESHOLD`.
- **Persistent Streamed Chat (`POST /conversations/{id}/messages`)**: Persistent conversation sessions with chronologically bounded chat history (`CHAT_HISTORY_MESSAGE_LIMIT=10`) streamed via Server-Sent Events (`text/event-stream`).
- **RAG Evaluation Suite (Phase 7)**: Off-line benchmark evaluation suite (`evaluation/evaluate.py`) supporting Recall@K, Precision@K, Hit Rate@K, MRR@K, deterministic reference term scoring, unanswerable refusal safety, optional LLM-as-a-Judge (1-5 rubrics), report generation, failure analysis, and baseline comparison.
- **Production Readiness (Phase 8)**: Containerized via Docker and Docker Compose, Alembic database migrations, health probes, CORS middleware, global exception masking, structured logging, file upload security.
- **Frontend Foundation (Phase 9)**: React + TypeScript + Vite + Tailwind dark-theme three-column shell with reusable components, auth foundation, and environment-driven API access.
- **RAG Workspace (Phase 10)**: Real upload + status polling, conversation management, SSE-streamed chat with Markdown rendering and source citations, all wired to the live backend.
- **Production-Quality Frontend (Phase 11)**: Toasts, skeleton loaders, error boundary, friendly error mapping, 401 auto-logout, accessibility polish, smart chat auto-scroll, multi-stage Docker image served by nginx with `/api/*` reverse proxy.

---

## Directory Structure

```text
rag-document-intelligence/
├── backend/
│   ├── env/                      # ONLY Python virtual environment
│   ├── alembic/                  # Database migration scripts (Alembic)
│   │   ├── env.py                # Alembic SQLAlchemy environment
│   │   ├── script.py.mako        # Revision template
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   ├── evaluation/               # Phase 7 RAG Evaluation Subsystem
│   │   ├── dataset.json          # Benchmark dataset (10 test cases)
│   │   ├── metrics.py            # Retrieval & Generation metrics
│   │   ├── judge.py              # LLM-as-a-Judge module
│   │   ├── evaluate.py           # CLI evaluation runner
│   │   ├── README.md             # Evaluation guide & documentation
│   │   └── reports/              # JSON evaluation reports
│   ├── documents/                # Sample evaluation PDF documents
│   ├── storage/                  # Uploaded document storage
│   ├── chroma_data/              # ChromaDB vector store directory
│   ├── auth_routes.py            # Registration & login routes
│   ├── auth_service.py           # JWT generation & verification
│   ├── chat_service.py           # Conversational RAG logic
│   ├── chunker.py                # Character boundary chunker
│   ├── config.py                 # Central configuration (env-driven)
│   ├── context_builder.py        # LLM context formatter
│   ├── conversation_routes.py    # Conversation CRUD & streaming API
│   ├── crud.py                   # Database queries & ownership rules
│   ├── database.py               # SQLAlchemy engine, sessions, health check
│   ├── embedding_service.py      # Local Sentence-Transformers embeddings
│   ├── extractor.py              # PDF/DOCX text extractors
│   ├── ingestion.py              # Document processing & indexing pipeline
│   ├── llm_service.py            # OpenAI Responses streaming client
│   ├── main.py                   # FastAPI app (CORS, health, exception handler)
│   ├── models.py                 # SQLAlchemy ORM database models
│   ├── prompt_builder.py         # Grounded prompt construction
│   ├── query_service.py          # Direct RAG query service
│   ├── requirements.txt          # Locked dependency list
│   ├── retrieval_service.py      # ChromaDB retrieval service
│   ├── schemas.py                # Pydantic request/response schemas
│   ├── vector_store.py           # ChromaDB vector store client
│   ├── alembic.ini               # Alembic configuration
│   ├── .env.example              # Environment variable template
│   ├── .dockerignore             # Docker build context exclusions
│   ├── Dockerfile                # Production Docker image
│   ├── test_main.py              # API unit tests
│   └── test_evaluation.py        # Evaluation unit tests
├── frontend/                      # React + TypeScript SPA (Phases 9–11)
│   ├── src/                       # Components, hooks, services, pages
│   ├── Dockerfile                 # Multi-stage Node → nginx image
│   ├── nginx.conf                 # SPA static + /api/* reverse proxy
│   ├── .env.example               # Documents VITE_API_URL
│   └── package.json
├── docs/                         # Architecture, decisions, and phase documentation
│   ├── decisions.md              # Architectural Decision Records (ADRs 001-039)
│   ├── system_architecture.md    # Mermaid system architecture diagrams
│   ├── understanding.md          # Comprehensive concept documentation
│   ├── workflow.md               # User, evaluation, and deployment workflows
│   └── phases/                   # Phase specifications (Phase 1 to 11)
├── docker-compose.yml            # Multi-container orchestration (db, web, frontend)
└── README.md                     # Root project documentation
```

---

## Setup & Quickstart

### Option A: Local Development (No Docker)

#### 1. Prerequisites
- Python 3.11+
- PostgreSQL running locally

#### 2. Create Virtual Environment
```powershell
cd backend
python -m venv env
.\env\Scripts\python.exe -m pip install -r requirements.txt
```

#### 3. Environment Configuration
```powershell
copy .env.example .env
# Edit .env and fill in DATABASE_URL, OPENAI_API_KEY, JWT_SECRET_KEY
```

#### 4. Apply Database Migrations
```powershell
.\env\Scripts\alembic.exe upgrade head
```

#### 5. Run the Server
```powershell
.\env\Scripts\uvicorn.exe main:app --reload --port 8000
```

---

### Option B: Docker Compose (Recommended)

#### 1. Prerequisites
- Docker Desktop installed and running

#### 2. Environment Configuration
```powershell
copy backend\.env.example backend\.env
# Edit backend\.env — set OPENAI_API_KEY and JWT_SECRET_KEY at minimum
```

#### 3. Start All Services
```powershell
docker-compose up --build
```

#### 4. Apply Database Migrations (first run only)
```powershell
docker-compose exec web alembic upgrade head
```

#### 5. Verify Health
```
Browser opens http://localhost:8080  → React SPA
GET http://localhost:8080/api/health/liveness  → {"status":"alive"}
GET http://localhost:8080/api/health/readiness → {"status":"ready"}
```

The frontend is served by an nginx container that reverse-proxies
`/api/*` to the FastAPI service. The browser only sees one origin in
production, so no CORS configuration is needed there.

---

## Health Probes

| Endpoint | Purpose | 200 Response | Failure |
|---|---|---|---|
| `GET /health/liveness` | Process alive | `{"status":"alive"}` | Never fails |
| `GET /health/readiness` | DB reachable | `{"status":"ready"}` | `503` |
| `GET /health` | DB + storage | `{"status":"healthy"}` | `503 {"status":"unhealthy"}` |

---

## API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | No | Register new user |
| `POST` | `/auth/login` | No | Login, receive JWT |
| `GET` | `/documents` | JWT | List user's documents |
| `POST` | `/documents` | JWT | Create document metadata |
| `GET` | `/documents/{id}` | JWT | Get document by ID |
| `PATCH` | `/documents/{id}` | JWT | Update document name |
| `DELETE` | `/documents/{id}` | JWT | Delete document + vectors |
| `POST` | `/documents/upload` | JWT | Upload and ingest document |
| `POST` | `/query` | JWT | Direct grounded RAG query |
| `GET` | `/conversations` | JWT | List conversations |
| `POST` | `/conversations` | JWT | Create conversation |
| `GET` | `/conversations/{id}` | JWT | Get conversation + messages |
| `DELETE` | `/conversations/{id}` | JWT | Delete conversation |
| `POST` | `/conversations/{id}/messages` | JWT | Send message (SSE stream) |
| `GET` | `/health` | No | Detailed health report |
| `GET` | `/health/liveness` | No | Liveness probe |
| `GET` | `/health/readiness` | No | Readiness probe |

---

## Phase 7 Evaluation Commands

All evaluation commands must be run from `backend/` using `backend/env/`:

```powershell
# 1. Run basic deterministic evaluation
.\env\Scripts\python.exe evaluation/evaluate.py --user-id <user_id>

# 2. Run evaluation with Top-K override and optional LLM-as-a-Judge scoring
.\env\Scripts\python.exe evaluation/evaluate.py --user-id <user_id> --top-k 5 --use-llm-judge

# 3. Compare evaluation report against a previous baseline report
.\env\Scripts\python.exe evaluation/evaluate.py --user-id <user_id> --top-k 5 --compare evaluation/reports/baseline.json
```

---

## Running Tests

From `backend/`:

```powershell
.\env\Scripts\python.exe -m pytest -v
```

Expected: **14 passed** (7 evaluation tests + 4 API tests + 3 health tests).

---

## Database Migrations (Alembic)

```powershell
# Apply all pending migrations
.\env\Scripts\alembic.exe upgrade head

# Generate a new migration after modifying models.py
.\env\Scripts\alembic.exe revision --autogenerate -m "describe_the_change"

# Downgrade one revision
.\env\Scripts\alembic.exe downgrade -1
```

---

## Documentation

- [System Architecture](docs/system_architecture.md)
- [Workflow Guide](docs/workflow.md)
- [Architectural Decisions](docs/decisions.md)
- [Conceptual Understanding](docs/understanding.md)
- [Phase 11 Specification](docs/phases/phase11.md)
- [Phase 10 Specification](docs/phases/phase10.md)
- [Phase 9 Specification](docs/phases/phase9.md)
- [Phase 8 Specification](docs/phases/phase8.md)
- [Phase 7 Specification](docs/phases/phase7.md)
