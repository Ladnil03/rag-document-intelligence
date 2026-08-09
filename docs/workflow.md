# Workflow

## Create Conversation

```text
Authenticated user -> POST /conversations -> PostgreSQL conversation -> response
```

The optional supplied title is used; otherwise it starts as `New conversation` and the first user message derives a simple 80-character title without an LLM call.

## Send Message

```text
Authenticated user -> ownership check -> persist user message
                   -> load newest CHAT_HISTORY_MESSAGE_LIMIT messages
                   -> user-filtered document retrieval
                   -> separate history + document-context prompt
                   -> OpenAI Responses stream
                   -> SSE token events
                   -> persist complete assistant message
                   -> SSE sources event -> SSE done event
```

The SSE response content type is `text/event-stream`. Event payloads are JSON: `token` has `{ "text": "..." }`; `sources` has the Phase 4 source objects and `has_relevant_context`; `done` is `{}`. If generation or final persistence fails, an `error` event is sent and the partial assistant text is not stored.

## Follow-Up Questions

```text
New question + bounded previous messages + newly retrieved document chunks
    -> conversational LLM prompt -> streamed answer
```

Previous assistant messages supply conversational continuity; they do not replace document retrieval. The current user ID remains mandatory for every ChromaDB retrieval.

## Delete Conversation

```text
Authenticated user -> ownership-qualified conversation lookup
                   -> delete conversation -> cascade delete messages
```

Cross-user or nonexistent conversation IDs return `404` without exposing data.

## Existing Document and Direct Query Workflows

Document CRUD/upload and `POST /query` remain protected by the existing Bearer dependency. Direct query remains a non-streamed single-question endpoint; conversational streaming is provided by `POST /conversations/{conversation_id}/messages`.

## Evaluation Workflow

```text
Evaluation Dataset
        ↓
Run Retrieval
        ↓
Measure Retrieval (Recall@K, Precision@K, Hit Rate@K, MRR@K)
        ↓
Run RAG (query_service)
        ↓
Evaluate Answer (Relevance, Groundedness, LLM Judge)
        ↓
Analyze Failures
        ↓
Identify Improvement
        ↓
Modify System (Single variable: chunk size, top-K, similarity threshold)
        ↓
Evaluate Again & Compare Deltas
```

The evaluation suite reuses project services to load the benchmark dataset, execute vector search and RAG generation for an authenticated user, compute quantitative metrics, and generate structured reports.

## Failure Analysis

```text
Failed Example
        ↓
Identify Failure Type
        ↓
Find Root Cause
        ↓
Modify Retrieval / Generation Strategy
        ↓
Re-evaluate
```

For each failed evaluation test case, `evaluation/evaluate.py` assigns an explicit failure category (`wrong_retrieval_or_missing_source`, `insufficient_context_retrieval`, `poor_answer_or_reference_mismatch`, or `hallucination_on_unanswerable`), logs the likely cause, and suggests a potential targeted fix.

## Local Development Setup

```text
1. cd backend/
2. python -m venv env
3. .\env\Scripts\python.exe -m pip install -r requirements.txt
4. Copy .env.example → .env and fill in values
5. .\env\Scripts\python.exe -m alembic upgrade head
6. .\env\Scripts\uvicorn.exe main:app --reload
```

## Docker Compose Deployment

```text
1. cd <project-root>/
2. Copy backend/.env.example → backend/.env and fill in secrets
3. docker-compose up --build
```

The `db` container starts first; the `web` container waits until `db` passes its health check (`pg_isready`). Both containers mount named volumes: `postgres_data` for PostgreSQL, `chroma_data` for ChromaDB, and `storage_data` for uploaded files.

## Database Migration Workflow

```text
# Apply all pending migrations (development or production)
cd backend/
.\env\Scripts\alembic.exe upgrade head

# Generate a new migration after changing SQLAlchemy models
.\env\Scripts\alembic.exe revision --autogenerate -m "describe_the_change"

# Downgrade one revision
.\env\Scripts\alembic.exe downgrade -1
```

## Health Probe Workflow

```text
GET /health/liveness   →  200 {"status":"alive"}         (process alive)
GET /health/readiness  →  200 {"status":"ready"}         (DB connected)
                       or 503 {"detail":"..."}           (DB unavailable)
GET /health            →  200 {"status":"healthy"}       (DB + storage ok)
                       or 503 {"status":"unhealthy"}     (one check failed)
```

---

## Phase 9: Frontend Workflows

The frontend lives in `frontend/` and runs on Vite (default port 5173). All
backend URLs come from `VITE_API_URL`. The Groq API key is never sent to
the browser — it stays in `backend/.env`.

### Frontend Local Development

```text
1. cd frontend/
2. npm install
3. copy .env.example .env.local          # edit VITE_API_URL if needed
4. npm run dev                          # opens http://localhost:5173
```

### Register Workflow

```text
Browser
   → RegisterPage form (email, password)
   → AuthContext.register()
   → POST /auth/register (Bearer disabled)
   → 201 UserResponse → auto POST /auth/login
   → TokenResponse stored in localStorage
   → Navigate to /app (ProtectedRoute passes)
```

### Login Workflow

```text
Browser
   → LoginPage form (email, password)
   → AuthContext.login()
   → POST /auth/login
   → TokenResponse stored in localStorage
   → Navigate to the path captured by ProtectedRoute (state.from), or /app
```

### Protected Route Workflow

```text
Browser navigates to /app/...
   → ProtectedRoute checks localStorage["rag_auth_token"]
   → Missing → <Navigate to="/login" state={{from}} replace />
   → Present → render AppShell + matched child route
```

The `from` location is preserved so post-login redirect lands the user on
the page they originally requested.

### Authenticated API Request

```text
Page calls documents.list()
   → request() in services/api.ts
   → fetch(`${VITE_API_URL}/documents`,
          headers: Authorization: `Bearer ${token}`)
   → FastAPI get_current_user dependency verifies JWT
   → Owner-scoped SQL returned as JSON
```

### Logout Workflow

```text
User clicks Logout in sidebar UserFooter
   → AuthContext.logout()
   → localStorage.removeItem("rag_auth_token")
   → setUser(null)
   → Page rerenders; navigation to /login is handled by ProtectedRoute
     on the next route change (or by the user clicking a link)
```

### Chat UI Placeholder Workflow (Phase 9 only)

```text
User types a message in ChatInput
   → ChatPage onSend()
   → appends a user Message + a static "Phase 10 placeholder" assistant Message
```

No backend round-trip happens here yet. Phase 10 will replace this with a
real SSE stream against `POST /conversations/{conversation_id}/messages`,
including the `token`, `sources`, and `done` events.

---

## Phase 10: RAG Workspace Workflows

### Document Upload Workflow

```text
User drops / picks a file in KnowledgeBasePage
   → useDocuments.upload(file)
   → FormData(file) → POST /documents/upload (multipart/form-data)
   → FastAPI validates extension + size
   → Disk write → PostgreSQL UPLOADED → status PROCESSING
   → ingestion.index_document (extract → chunk → embed → upsert)
   → PostgreSQL COMPLETED (or FAILED on error)
Frontend useDocuments polls GET /documents every 2s while any row is
in UPLOADED/PROCESSING. Polling stops when every row is COMPLETED/FAILED.
```

### RAG Chat Workflow

```text
User types a question in ChatPage
   → useConversation.send(text)
   → optimistic user Message appended locally
   → POST /conversations/{id}/messages  (Bearer JWT, JSON body)
   → FastAPI persists user Message
   → chat_service.prepare_chat_reply → retrieval + history prompt
   → llm_service.stream_chat_answer → Groq chat.completions stream
   → accumulate tokens, persist assistant Message on completion
   → emit SSE: token*, sources, done
Frontend services/streaming.ts parses the SSE stream and grows the
in-progress assistant bubble. On `done`, useConversation refetches
GET /conversations/{id} so the local state matches what was persisted.
```

### Streaming Workflow

```text
SSE wire format (text/event-stream):

event: token
data: {"text":"Hello"}

event: token
data: {"text":", world"}

event: sources
data: {"sources":[{"document_id":1,"filename":"a.pdf","chunk_index":2,
                   "similarity":0.71}],"has_relevant_context":true}

event: done
data: {}

OR (on failure mid-stream):

event: error
data: {"message":"Assistant response generation failed."}
```

`services/streaming.ts` reads the response body with `ReadableStream`,
parses `event:` / `data:` frames (split on blank lines, multi-line
`data:` fields joined with `\n`), and routes each event to the matching
typed callback. `AbortController` lets the UI cancel the request.

### Source / Citation Workflow

```text
Backend chat_service returns chunks used for context.
conversation_routes._source_payload() ships them as the `sources`
SSE event payload: { sources, has_relevant_context }.
Frontend PendingAssistantMessage renders them in a "Sources" footer
below the streamed Markdown. Only chunks the assistant actually saw
are shown; page_number is omitted when not available (not invented).
```

### Conversation Workflow

```text
New chat   → POST /conversations               → id stored in
             localStorage ("rag_selected_conversation") and in useConversations.list
Switch     → useConversations.setSelectedId(id) → useConversation(id)
             loads GET /conversations/{id} → renders messages
Delete     → DELETE /conversations/{id}         → removed from list and
             from localStorage if it was active
Refresh    → Browser reload → AuthProvider reads JWT → useConversations
             reads selected id → useConversation loads messages from
             backend → state restored from server, not React memory.
```

---

## Phase 11: Production-Quality Frontend Workflows

### Toast Notification Workflow

```text
Page calls useToast().success("Uploaded 'a.pdf'.")
   → ToastProvider.toast({tone:"success", message, duration})
   → state update appends to a global queue
   → ToastViewport (aria-live polite) renders at bottom-right
   → Auto-dismisses after duration; user can also dismiss manually
```

Toasts are for transient feedback only. Anything that requires the user
to read or act lives inline (form errors, validation). Multiple toasts
queue and dismiss in order.

### 401 Auto-Logout Workflow

```text
Authenticated request returns 401
   → services/api.ts detects 401 on an authenticated call
   → authToken.clear()                 (removes from localStorage)
   → window.dispatchEvent("auth:unauthorized")
   → AuthProvider listener → setUser(null)
   → ProtectedRoute listener → forces Navigate to /login
   → AuthUnauthorizedToastBridge listener → "Session expired" toast
```

Three listeners react independently. Pages never have to handle 401
themselves — they just call API functions and read the thrown error.

### Error Boundary Workflow

```text
A component throws during render
   → ErrorBoundary.componentDidCatch(error, info)
   → Logged to console in dev only; never exposed to the user
   → Fallback UI rendered with "Try again" + "Reload page"
   → reset() clears state and re-renders children
```

Boundaries catch render-time exceptions only. Event-handler and async
errors are caught by the existing try/catch + friendlyError pipeline.

### Production Build Workflow

```text
npm run build
   → tsc -b (typecheck)
   → vite build (tree-shake, minify, emit hashed chunks to dist/)
   → dist/index.html + dist/assets/*.{js,css}

Docker (frontend/Dockerfile):
   → node:20-alpine installs deps + runs vite build
   → nginx:alpine serves /usr/share/nginx/html on port 80
   → /api/* reverse-proxied to the FastAPI web container
   → SPA fallback: unknown paths serve index.html so React Router works
```

`VITE_API_URL` is baked into the bundle at build time. In docker it is
`/api` so the browser only sees one origin.

### Frontend Docker Stack Workflow

```text
docker-compose up --build
   → db (postgres:16-alpine) starts + healthchecks
   → web (FastAPI + Uvicorn) waits for db, then starts (port 8000 internal)
   → frontend (nginx + static SPA) starts, depends on web
   → Browser hits http://localhost:8080 → nginx serves SPA
   → Browser fetches /api/* → nginx proxies to web:8000
   → Browser streams /api/conversations/{id}/messages → nginx → web
      (proxy_buffering off + long read_timeout so SSE works)
```
