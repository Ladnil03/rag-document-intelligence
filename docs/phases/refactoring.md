# Codebase Refactoring Phase Document

## Objective

Refactor and modularize the RAG Document Intelligence codebase to maximize maintainability, testability, clarity, and architectural cleanliness while strictly preserving 100% of existing application behavior, API contracts, RAG pipeline parameters, database schemas, and frontend UI design.

## Problems Identified

1. **Root-level Shim Clutter**: 18 backward-compatibility shim files at `backend/` root created structural ambiguity.
2. **Ambiguous Test Imports**: Unit tests imported from root shims rather than canonical `app.*` packages.
3. **Logging Format String Bug**: `app/main.py` contained invalid format specifiers (`%(name__)` and `%(message__)`).
4. **Service Coupling**: `chat_service.py` re-exported a helper function from `conversation_service.py`.

## Architecture Before vs After

### Before
- Multi-layered package structure in `backend/app/` with 18 root-level shim files pointing to submodules.
- Mixed import styles across tests and entry points.

### After
- Unified `backend/app/` package structure with clear separation of concerns:
  - `app/api/routes/` for HTTP endpoints
  - `app/services/` for business logic orchestration
  - `app/rag/` for document ingestion, embeddings, storage, retrieval, and LLM inference
  - `app/crud/` for SQL query encapsulation
  - `app/models/` for ORM schemas
  - `app/schemas/` for Pydantic contracts
  - `app/core/` for configuration, security, and storage primitives
- Clean root directory containing only `main.py` (uvicorn shim) and `config.py` (alembic shim).

## Backend Changes

1. Removed 18 top-level Python shim files from `backend/`.
2. Updated `backend/test_main.py` to import directly from `app.core`, `app.db.base`, and `app.main`.
3. Fixed logging format string in `app/main.py` (`format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"`).
4. Fixed `Base` import in `app/main.py` (`from app.db.base import Base, engine`).
5. Removed redundant `history_turns` wrapper from `app/services/chat_service.py` and updated `app/api/routes/chat.py` to call `conversation_service.history_turns` directly.

## Frontend Changes

- None required (frontend `src/` directory was already cleanly modularized into `components/`, `context/`, `hooks/`, `pages/`, `services/`, `types/`, and `utils/`).
- Verified production build (`npm run build`) compiles cleanly without TypeScript or Vite errors.

## RAG Changes

- No algorithmic or configuration changes. Embedding model (`all-MiniLM-L6-v2`), chunk size, overlap, similarity threshold, and Groq LLM streaming remain identical.

## Configuration Changes

- Centralized configuration in `app.core.config` remains unchanged.
- Backward-compatibility shim `backend/config.py` retained for Alembic and evaluation tools.

## Files Changed

- `backend/app/main.py`
- `backend/app/api/routes/chat.py`
- `backend/app/services/chat_service.py`
- `backend/test_main.py`
- `docs/understanding.md`
- `docs/system_architecture.md`
- `docs/decisions.md`

## Files Created

- `docs/refactoring.md`
- `docs/phases/refactoring.md`

## Files Removed

1. `backend/auth_routes.py`
2. `backend/auth_service.py`
3. `backend/chat_service.py`
4. `backend/chunker.py`
5. `backend/context_builder.py`
6. `backend/conversation_routes.py`
7. `backend/crud.py`
8. `backend/database.py`
9. `backend/embedding_service.py`
10. `backend/extractor.py`
11. `backend/ingestion.py`
12. `backend/llm_service.py`
13. `backend/models.py`
14. `backend/prompt_builder.py`
15. `backend/query_service.py`
16. `backend/retrieval_service.py`
17. `backend/schemas.py`
18. `backend/vector_store.py`

## Behavior Preservation

- All API contracts, response models, HTTP status codes, status transitions, SSE event formats, database schemas, and frontend page layouts remain functionally identical.

## Known Limitations

- `backend/config.py` and `backend/main.py` remain at root to serve as top-level entry points for Alembic, evaluation scripts, and uvicorn command invocations (`uvicorn main:app`).

## Testing Checklist

- [x] Backend test suite passes (`pytest test_main.py`)
- [x] Evaluation test suite passes (`pytest test_evaluation.py`)
- [x] Frontend production build compiles (`npm run build`)
