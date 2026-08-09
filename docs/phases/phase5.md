# Phase 5 - Authentication and User Isolation

## Status

Completed (Implementation Complete; developer functional testing pending)

## Objective

Add secure local user registration/login and ensure a user can access only their own PostgreSQL documents, files, and RAG chunks.

## User Model

`users`: `id` (primary key), `email` (unique, indexed, non-null), `password_hash` (non-null), and `created_at`. `User.documents` and `Document.owner` form a one-to-many relationship. `documents.user_id` is an indexed, nullable transitional foreign key to `users.id`.

## Authentication

`POST /auth/register` validates a JSON email/password request, normalizes email, rejects duplicates with `409`, hashes the password, and returns `UserResponse` only. `POST /auth/login` verifies the submitted password and returns a JSON Bearer access token. Invalid credentials return the same `401` response regardless of whether the email or password was incorrect.

## Password Security

`pwdlib.PasswordHash.recommended()` creates the password hash; `pwdlib` verifies it at login. The application never stores or returns plaintext passwords or password hashes.

## JWT

`auth_service.py` signs tokens using `JWT_SECRET_KEY`, `JWT_ALGORITHM` (default `HS256`), and `ACCESS_TOKEN_EXPIRE_MINUTES` (default `60`). Payload claims are only string `sub` (user ID) and `exp`. No tokens are stored permanently.

## Authorization

The reusable `get_current_user` FastAPI dependency validates `Authorization: Bearer <access_token>`, validates required claims/signature/expiration, and loads the user from PostgreSQL. It protects `/query` and every `/documents` operation. Missing, invalid, malformed, expired, or deleted-user credentials return `401`; absent JWT configuration returns `503`.

## Document Ownership

`POST /documents`, `GET /documents`, `GET/PATCH/DELETE /documents/{document_id}`, and `POST /documents/upload` use the authenticated user ID as the ownership source. List, read, update, and delete database operations all constrain their queries by both document ID (where relevant) and `user_id`. Cross-user document IDs return `404` and do not disclose ownership or content.

## RAG Isolation

New ingestion writes `user_id`, `document_id`, `filename`, and `chunk_index` to every ChromaDB chunk. `/query` sends the authenticated user ID through `query_service` and `retrieval_service`; ChromaDB search uses a required `user_id` metadata filter. Other users' chunks cannot become context or sources.

## Existing Data Migration

At startup, `Base.metadata.create_all()` creates the `users` table and `database.migrate_phase5_schema()` adds `documents.user_id` plus its index if a local legacy schema lacks it. Existing rows are intentionally left `NULL`; their existing unscoped chunks have no `user_id` and are also excluded by retrieval. They are inaccessible until the developer deliberately resets/re-uploads data or performs a known-owner assignment and re-index. No old resource is silently assigned to an arbitrary account.

## API Endpoints

Public:

- `POST /auth/register`
- `POST /auth/login`
- `GET /`

Protected with Bearer authentication:

- `POST /documents`
- `GET /documents`
- `GET /documents/{document_id}`
- `PATCH /documents/{document_id}`
- `DELETE /documents/{document_id}`
- `POST /documents/upload`
- `POST /query`

## Dependencies Added

None during this implementation. The existing required `backend/env/` already contains `pwdlib 0.3.0` and `PyJWT 2.13.0`.

## Environment Variables

- `JWT_SECRET_KEY`
- `JWT_ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=60`

`.env.example` contains placeholders only. Generate a local secret with `backend/env/Scripts/python -c "import secrets; print(secrets.token_urlsafe(32))"` once the project environment interpreter is repaired.

## Files Changed

- `backend/auth_routes.py`, `auth_service.py`, `schemas.py`, `models.py`, `crud.py`, `database.py`, `main.py`
- `backend/ingestion.py`, `vector_store.py`, `retrieval_service.py`, `query_service.py`, `.env.example`
- `docs/understanding.md`, `docs/system_architecture.md`, `docs/workflow.md`, `docs/decisions.md`, this file

## Known Limitations

- No refresh tokens, logout/revocation list, OAuth, or MFA.
- Local PostgreSQL, filesystem, and ChromaDB remain separate stores without distributed transactions.
- Legacy unowned local data requires deliberate developer action.
- Functional testing has not been performed by the coding agent because `backend/env/Scripts/python.exe` cannot currently launch.

## What Was Not Implemented

No persistent chat sessions/messages, conversation memory, streaming responses, Redis, Celery, background workers, agents, MCP, Docker, deployment, or advanced RAG evaluation.

## Next Phase

```text
Phase 6 - Chat Experience
```
