# RAG Document Intelligence — Understanding Summary

This is the condensed version of `understanding.md`. It keeps the important concepts, project-specific implementation details, architecture, key configurations, common mistakes, and interview points while removing repeated explanations.

> **Source of truth:** Actual source code and verified tests are authoritative. Documentation must describe what is actually implemented; future plans must not be presented as implemented.

---

# 1. Client–Server & HTTP Fundamentals

## Client vs Server
- **Client:** Browser, curl, Postman, or frontend that sends requests.
- **Server:** FastAPI application served by Uvicorn.
- Communication happens through HTTP; processes do not directly call each other's functions.
- The project follows a client → API server model.

## HTTP
- Application-level protocol used for request/response communication.
- Request contains method, path, headers and optionally a body.
- Response contains status code and body.
- HTTP is stateless: each request is independent.

## File Upload & Multipart/Form-Data
- Binary files are uploaded using `multipart/form-data`, not ordinary JSON.
- `POST /documents/upload` receives files through FastAPI `UploadFile`.
- `python-multipart` parses multipart requests.
- Example client form: `-F "file=@doc.pdf"`.

---

# 2. Document Management

## File Validation
The backend validates:
- Supported extensions: `.pdf`, `.docx`
- Non-empty files
- Maximum size: 10 MB
- File structure/text extraction

Typical failures:
- `400 Bad Request`
- `413 Payload Too Large`
- `415 Unsupported Media Type`

Server-side validation is required even if the frontend validates files.

## File Storage vs Metadata
Binary files are stored separately from relational metadata.

### File storage
- Files are saved under `backend/storage/`.
- UUID filenames prevent collisions and path-related security issues.

### PostgreSQL metadata
The `documents` table stores information such as:
- name
- stored file path
- file type
- file size
- creation time
- processing status
- extracted text

This keeps large binary payloads out of PostgreSQL.

## MIME/File Types
The project normalizes supported document types to `pdf` and `docx` and selects the corresponding extractor.

## PDF Extraction
- Uses `pypdf.PdfReader`.
- Iterates through pages and calls `extract_text()`.
- Image-only/scanned PDFs require OCR; normal extraction cannot magically read image text.

## DOCX Extraction
- Uses `python-docx`.
- Reads document paragraphs and joins non-empty text.
- DOCX is an OpenXML/ZIP-based format.

## Processing States
Documents move through:

`UPLOADED → PROCESSING → COMPLETED`

or:

`UPLOADED → PROCESSING → FAILED`

The database status makes multi-step processing observable.

## Processing Error Handling
- Upload validation uses HTTP exceptions.
- Extraction/processing failures mark the document `FAILED`.
- API responses should be sanitized; raw tracebacks and server paths must not be exposed.

## Synchronous Processing
Current document processing is synchronous:

`Upload → Validate → Store → Extract → Process → Respond`

This is simple and suitable for the learning/development stage. Heavy workloads can later be moved to background workers.

---

# 3. RAG Ingestion Pipeline

The core ingestion flow is:

```text
Upload
  ↓
Validate
  ↓
Store file
  ↓
PostgreSQL: UPLOADED
  ↓
Text extraction
  ↓
Chunking
  ↓
Embedding
  ↓
ChromaDB upsert
  ↓
PostgreSQL: COMPLETED
```

Any ingestion failure results in `FAILED`.

## Text Chunking
Long extracted text is split into smaller overlapping pieces.

Why:
- Embedding models have input limits.
- Smaller chunks improve retrieval granularity.
- Overlap preserves context across boundaries.

Current baseline:
- `CHUNK_SIZE = 1000` characters
- `CHUNK_OVERLAP = 200` characters

These are tunable starting values, not universal optimal values.

## Chunk Size
Controls how much text each chunk contains.

- Too small → insufficient context.
- Too large → weaker retrieval granularity and possible token-limit problems.

Characters are not the same as tokens.

## Chunk Overlap
Text shared between adjacent chunks.

- Prevents important sentences from being lost at chunk boundaries.
- Must be less than chunk size.

---

# 4. Embeddings & Vector Search

## Embeddings
An embedding is a fixed-length numeric vector representing text semantically.

Current default:
- Model: `all-MiniLM-L6-v2`
- Dimensions: `384`

The same embedding space must be used for:
- document chunks
- user queries

The embedding model is loaded once and reused.

## Embedding Dimensions
All vectors inside a ChromaDB collection must have compatible dimensions.

Changing embedding models may require:
- a new collection
- complete re-indexing

## Semantic Similarity
Semantic similarity compares embeddings rather than exact keywords.

The project uses cosine space.

Important:
- High similarity does not prove factual correctness.
- Similarity is a retrieval signal, not a truth score.

## Vector Database
A vector database is optimized for high-dimensional vector search.

In this project:
- PostgreSQL → structured metadata
- ChromaDB → embeddings/vectors

They serve different purposes.

## ChromaDB
Uses a persistent client:

`chromadb.PersistentClient(...)`

Data persists across process restarts.

The project stores vectors in:

`backend/chroma_data/`

Collection:

`document_chunks`

## Vector Collection
A collection is a named namespace similar conceptually to a SQL table.

Each stored chunk contains:
- ID
- embedding
- document text
- metadata

One collection is used for document chunks so cross-document retrieval remains possible.

## Vector Metadata
Each chunk stores metadata such as:
- `document_id`
- `filename`
- `chunk_index`
- `user_id` for multi-user isolation

Metadata connects vector results back to application documents.

---

# 5. Re-indexing & Cleanup

## Re-indexing
Reprocessing replaces a document's complete vector set instead of creating duplicates.

The project uses deterministic IDs such as:

`doc_{document_id}_chunk_{index}`

Process:

```text
Embed new chunks
   ↓
Delete old chunks for document
   ↓
Insert new chunks
```

Embedding happens before deletion so an embedding failure does not destroy the old vectors.

## Vector Cleanup
Deleting a document must also delete its ChromaDB vectors.

Order is important because orphaned vectors can pollute future retrieval.

The project cleans ChromaDB before deleting the corresponding file/database record.

---

# 6. RAG Query Pipeline

RAG means **Retrieval-Augmented Generation**.

Instead of asking the LLM directly:

```text
Question → LLM
```

the project uses:

```text
Question
  ↓
Query Embedding
  ↓
Vector Retrieval
  ↓
Relevant Chunks
  ↓
Context Construction
  ↓
RAG Prompt
  ↓
LLM
  ↓
Answer + Sources
```

## Retrieval
Retrieval selects the most relevant chunks from ChromaDB.

Important:
- Retrieval is separate from generation.
- Results are filtered by authenticated `user_id`.
- The client cannot supply the user identity for retrieval.

## Query Embeddings
The user question is embedded using the same embedding model/space as document chunks.

Using different embedding models makes similarity comparisons unreliable.

## Similarity Search
ChromaDB returns cosine distance.

The application converts it to:

`similarity = 1 - distance`

Lower distance means closer vectors.

## Top-K
`TOP_K = 4`

Top-K limits how many candidate chunks are initially retrieved.

Higher K:
- may improve recall
- may introduce more noise/context

Lower K:
- reduces context
- may miss relevant evidence

## Relevance Threshold
`SIMILARITY_THRESHOLD = 0.35`

Only chunks meeting the threshold are treated as evidence.

If no chunk is relevant:
- RAG does not call the LLM
- the system returns an insufficiency/no-context response

Threshold values are corpus/model-specific baselines.

## Context Construction
Selected chunks are formatted into the prompt.

Current baseline:
- `MAX_CONTEXT_LENGTH = 6000`

Only chunks actually included in the LLM context are returned as sources.

## Prompt Construction
The prompt:
- provides retrieved context
- separates source information
- asks the model to answer from the supplied evidence
- requires acknowledgement when evidence is insufficient

The no-context behavior is enforced in application code, not just through prompting.

## LLM Generation
The LLM receives:
- instructions
- retrieved context
- user question

The project uses a configurable LLM provider/model through a small service boundary.

The API key is loaded from environment configuration and never exposed to clients.

## Grounding & Hallucination
Grounding means answers are supported by retrieved evidence.

The project reduces hallucination risk through:
1. similarity threshold
2. limited retrieved context
3. grounded prompt instructions
4. explicit no-context branch

A RAG system cannot guarantee zero hallucinations.

## Source Citations
Sources identify the chunks actually used as evidence.

Current source information includes:
- document ID
- filename
- chunk index
- similarity

Page numbers are not invented when the extraction pipeline does not provide page-to-chunk information.

## Retrieval vs Generation Failure

### Retrieval failure
Infrastructure/search failure.

Returns a safe `503` rather than pretending no evidence exists.

### Generation failure
LLM/provider failure.

Returns an appropriate provider/API error rather than fabricating an answer.

No secrets or provider stack traces are exposed.

---

# 7. Phase 5 — Authentication & Multi-User Isolation

## Authentication
Authentication establishes **who** made a request.

- Login verifies credentials.
- JWT is issued.
- Protected endpoints validate the Bearer token.

## Authorization
Authorization establishes **what the authenticated user is allowed to access**.

Authentication alone is not enough.

The backend uses ownership conditions such as:

`Document.user_id == current_user.id`

## Password Hashing
Passwords are never stored as plaintext.

The project uses `pwdlib.PasswordHash.recommended()` for hashing and verification.

Fast general-purpose hashes such as SHA-256 should not be used directly for password storage.

## JWT
JWT contains signed claims.

The project keeps claims minimal:
- `sub` → user ID
- `exp` → expiration

JWT payloads are readable, so sensitive secrets must never be stored inside them.

## Bearer Authentication
Requests use:

```text
Authorization: Bearer <token>
```

FastAPI dependencies centralize token extraction and validation.

## User → Document Relationship
A user can own many documents.

PostgreSQL uses:
- foreign keys
- SQLAlchemy relationships

## Server-Side Isolation
The backend is the security boundary.

Do not:
- trust a client-supplied user ID
- rely only on frontend filtering
- retrieve another user's resource and then check ownership afterward

Use owner-qualified queries.

## ChromaDB Isolation
Vector data also requires ownership filtering.

Every chunk stores `user_id`, and retrieval applies the authenticated user's filter before results are used.

---

# 8. Phase 6 — Conversations & Streaming

## Conversation & Message
A conversation is a persistent container.

A message is an individual:
- user message
- assistant message

Conversation metadata and message content are stored separately.

## Ownership Chain

```text
User
 ↓
Conversation
 ↓
Message
```

Every conversation lookup must be scoped to the authenticated user.

Deleting a conversation can cascade to its messages.

## Conversational RAG
Two kinds of context are kept separate:

1. **Conversation history** — previous chat messages
2. **Knowledge context** — newly retrieved document chunks

History does not replace retrieval.

Follow-up questions still need document retrieval.

## History Limit
Current baseline:

`CHAT_HISTORY_MESSAGE_LIMIT = 10`

Only recent messages are included to avoid consuming too much context.

This is count-based rather than token-aware.

## Streaming / SSE
Server-Sent Events allow the server to send generated text incrementally.

The project streams:
- `token`
- `sources`
- `done`
- `error`

The frontend progressively builds the assistant response.

Do not fake streaming by splitting a completed response.

## Streaming Persistence
During streaming:
- user message is stored
- assistant deltas are accumulated
- one complete assistant message is stored only after successful completion

A failed stream does not create a fake/incomplete assistant message.

---

# 9. Phase 7 — RAG Evaluation

RAG needs evaluation beyond normal software tests because a pipeline can technically run while producing poor retrieval or hallucinated answers.

## Evaluation Pipeline

```text
Benchmark Dataset
      ↓
Retrieval
      ↓
Generation
      ↓
Metrics
      ↓
Failure Analysis
      ↓
Improvement
```

The evaluation code reuses production retrieval/generation services.

## Retrieval Metrics

### Recall@K
Measures how many expected relevant sources were retrieved.

```text
Recall@K =
relevant retrieved sources / total expected relevant sources
```

High recall means important evidence is less likely to be missed.

### Precision@K
Measures how much of the retrieved top-K is actually relevant.

```text
Precision@K =
relevant retrieved sources / K
```

High precision means less irrelevant context.

### Hit Rate@K
Binary metric:
- `1` if at least one relevant source is retrieved
- `0` otherwise

A perfect hit rate does not guarantee all required evidence was retrieved.

### MRR@K
Measures how highly ranked the first relevant result is.

- rank 1 → `1.0`
- rank 2 → `0.5`
- not found → `0`

## Generation Metrics

### Context Relevance
Does the retrieved context actually help answer the question?

### Answer Relevance
Does the generated answer directly address the question?

### Faithfulness / Groundedness
Are the answer's claims supported by the retrieved context?

A claim can be true in the real world but still be unfaithful if it is not supported by the retrieved project context.

### Unanswerable/Hallucination Safety
For questions with no relevant evidence:
- no relevant context should be returned
- the LLM should not be called
- the system should safely refuse/acknowledge insufficiency

## Evaluation Dataset
The project uses a version-controlled benchmark containing:
- questions
- expected sources
- expected terms/reference answers
- answerability flags

It contains 10 curated cases across:
- direct factual
- multi-step
- contextual
- unanswerable
- ambiguous

## Automated vs Manual Evaluation
Automated evaluation gives repeatable metrics.

Manual evaluation is still required to inspect:
- retrieval quality
- answer quality
- edge cases
- failure logs

Neither should completely replace the other.

## LLM-as-a-Judge
An LLM can score:
- context relevance
- answer relevance
- faithfulness

The project uses structured scoring and JSON output.

Known judge biases include:
- verbosity bias
- self-enhancement bias
- position bias

## Evaluation-Driven Improvement
Use:

```text
Baseline
 ↓
Analyze failures
 ↓
Change ONE parameter
 ↓
Evaluate again
 ↓
Compare metrics
```

Baseline configuration includes:

```text
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K=4
SIMILARITY_THRESHOLD=0.35
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

Only one variable should change per experiment.

## Failure Analysis
Failures are categorized, for example:
- wrong retrieval/missing source
- insufficient context retrieval
- poor answer/reference mismatch
- hallucination on unanswerable query

The goal is to identify **why** a test failed, not just that it failed.

---

# 10. Phase 8 — Productionization

Productionization makes the project reproducible, secure, observable and deployment-ready.

## Environment Configuration
Runtime settings are separated from source code.

Examples:
- database URL
- allowed origins
- log level
- JWT secret
- LLM key
- model/configuration values

Environment variables are loaded centrally.

## Dependency Management
Dependencies are pinned/managed so environments can be reproduced consistently.

## Docker
Docker packages the application into reproducible containers.

Important concepts:
- Dockerfile
- image
- container

## Docker Compose
Compose coordinates multiple services and their configuration.

## Database Migrations / Alembic
Alembic versions database schema changes.

Instead of manually changing the database, migrations provide a reproducible schema history.

## Health Checks
Health endpoints distinguish service availability/readiness from ordinary API behavior.

## Structured Logging
Production logs should be:
- structured
- searchable
- useful for debugging/observability

Never log:
- JWT secrets
- authorization headers
- API keys
- sensitive data

## CORS
CORS controls which browser origins can call the backend.

The project uses configured allowed origins rather than an unrestricted wildcard in production.

## File Upload Security
The backend protects against:
- path traversal
- oversized files
- unsupported extensions
- unsafe filenames

Controls include:
- 10 MB limit
- `.pdf` / `.docx` whitelist
- basename sanitization
- UUID storage paths

## Persistent Docker Storage
Named volumes preserve data across container restarts:

```text
PostgreSQL → postgres_data
ChromaDB   → chroma_data
Uploads    → storage_data
```

The project is described as **deployment-ready**, not necessarily already cloud-deployed.

---

# 11. Phase 9 — Frontend Foundation

## React
React builds the UI from reusable components.

## TypeScript
TypeScript provides static typing for frontend data and APIs.

## Components / Props / State
- **Component:** reusable UI unit
- **Props:** data passed into a component
- **State:** data that changes over time and triggers re-rendering

## Hooks
Hooks provide reusable stateful behavior.

Project examples include:
- `useAuth`
- `useDocuments`
- `useConversations`

Hooks must be called consistently at the top level, not inside conditions/loops.

## Routing
`react-router-dom` maps URLs to React components without full-page reloads.

## Protected Routes
Protected routes redirect unauthenticated users to login.

Authentication routing must be separated from protected application routes.

## Authentication Context
React Context shares authentication state across the component tree.

The project persists the JWT in `localStorage` so authentication survives refreshes.

## Centralized API Client
`services/api.ts` centralizes:
- base URL
- HTTP requests
- authentication headers
- response/error handling

Frontend API URL comes from:

`VITE_API_URL`

Secrets such as Groq API keys must remain backend-side.

## Frontend ↔ Backend

```text
React
 ↓
API Client
 ↓
HTTP + Bearer JWT
 ↓
FastAPI
 ↓
Authentication dependency
```

CORS must allow the frontend's origin.

---

# 12. Phase 10 — RAG Workspace

## Server State
Server state represents data owned by the backend:
- documents
- conversations
- messages
- processing status

Hooks encapsulate fetching/updating this data.

## Document Upload
Frontend sends documents using multipart/form-data to the backend.

## Document Processing Status
Frontend reflects backend processing states such as:
- uploaded
- processing
- completed
- failed

The UI must use real backend state rather than pretending processing succeeded.

## Conversations
Conversations are persisted by the backend and can be loaded after refresh.

## Chat State
The frontend maintains:
- selected conversation
- messages
- input
- loading state
- streaming state

## Streaming
The frontend consumes backend SSE and progressively renders assistant tokens.

## Markdown Rendering
Assistant messages can be rendered as Markdown.

Rendering must be safe; arbitrary HTML should not be injected unsafely.

## Source Citations
Frontend displays provenance returned by the backend.

Only actual sources returned by RAG should be shown.

## RAG Frontend Integration

```text
User Question
 ↓
React Chat
 ↓
API Client
 ↓
FastAPI
 ↓
Retrieval
 ↓
RAG
 ↓
SSE stream
 ↓
React progressively renders answer
 ↓
Sources displayed
```

## HTTP + SSE Error Handling
Frontend must distinguish:
- HTTP errors such as 401/403/404/500
- streaming errors that occur after an SSE connection has started

User-facing errors should be friendly and should not expose secrets/stack traces.

---

# 13. Phase 11 — Production-Quality Frontend

## Toast Notifications
Used for concise feedback such as:
- upload success
- delete success
- important errors

Avoid notification spam.

## Skeleton Loaders
Used while data is loading to avoid blank screens.

## Error Boundary
Catches unexpected React rendering errors and displays a safe fallback UI.

## Friendly Error Mapping
Convert backend/network errors into understandable messages instead of displaying raw technical errors.

## Accessibility
Important practices:
- keyboard navigation
- visible focus states
- semantic HTML
- labels
- ARIA where needed
- sufficient contrast
- status not communicated only through color

## Smart Auto-Scroll
Chat scrolls to new messages without aggressively forcing the user to the bottom when they are reading older messages.

## Reduced Motion
Respect users who prefer reduced motion.

## Frontend Production Build
The frontend must successfully build into production assets.

## Nginx Reverse Proxy
Nginx serves the React SPA and proxies API requests.

For SSE:
- buffering must be disabled
- read timeout must be long enough for streaming responses

## Multi-Stage Docker Build
Typical flow:

```text
Node build stage
      ↓
Vite production build
      ↓
nginx runtime stage
      ↓
Serve dist/
```

The final runtime image does not need the complete Node build environment.

---

# 14. Refactoring & Codebase Modularization

## Separation of Concerns
Each layer should have one clear responsibility.

### Backend

```text
API Routes
   ↓
Services
   ↓
RAG / CRUD / Database
```

Typical responsibilities:
- `api.routes` → HTTP layer
- `services` → business logic
- `rag` → RAG pipeline
- `crud` → database queries
- `models` → ORM entities
- `schemas` → API/Pydantic contracts

Routes should stay thin.

## Frontend

Use clear responsibilities for:
- layout
- chat
- documents
- reusable UI
- pages
- hooks
- API services

Avoid huge React components containing API calls, state, validation and presentation all together.

## Centralized API Services
Components should call service/hooks rather than constructing raw HTTP requests everywhere.

## Custom Hooks
Use hooks for reusable stateful logic.

Examples:
- `useAuth`
- `useDocuments`
- `useConversations`
- `useConversation`

## Clean Architecture Principles
Prefer:
- single responsibility
- separation of concerns
- clear dependency direction
- reuse without over-abstraction
- testable business logic

Avoid:
- unnecessary design patterns
- hundreds of tiny files
- duplicate entry points
- giant `utils` modules
- business logic inside UI/routes

---

# 15. Complete Project Architecture

## Document Ingestion

```text
User
 ↓
Frontend Upload
 ↓
FastAPI
 ↓
Validation
 ↓
File Storage
 ↓
PostgreSQL Metadata
 ↓
Text Extraction
 ↓
Chunking
 ↓
Embedding Model
 ↓
ChromaDB
```

## RAG Query

```text
User Question
 ↓
Authentication
 ↓
Query Embedding
 ↓
ChromaDB user-scoped retrieval
 ↓
Top-K
 ↓
Similarity Threshold
 ↓
Context Construction
 ↓
Prompt
 ↓
LLM
 ↓
Answer + Sources
```

## Conversational RAG

```text
User
 ↓
Conversation
 ↓
Recent Message History
 +
Retrieved Document Context
 ↓
RAG Prompt
 ↓
LLM
 ↓
SSE Stream
 ↓
Persist completed assistant message
```

## Complete System

```text
React Frontend
      ↓
Nginx / API Client
      ↓
FastAPI
      ↓
Authentication
      ↓
Services
   ┌──┴───────────┐
   ↓              ↓
PostgreSQL      RAG Pipeline
                  ↓
             ChromaDB
                  ↓
                 LLM
```

---

# 16. Most Important Interview Topics

Be able to explain these without memorizing definitions:

### Backend
- HTTP and REST
- FastAPI routing
- Pydantic validation
- multipart/form-data
- file validation/storage
- PostgreSQL
- foreign keys and relationships
- authentication vs authorization
- JWT
- password hashing
- CORS
- Docker
- Alembic
- health checks
- structured logging

### RAG
- chunking
- chunk size
- overlap
- embeddings
- embedding dimensions
- cosine similarity/distance
- vector databases
- ChromaDB
- metadata filtering
- ingestion pipeline
- re-indexing
- retrieval
- top-K
- similarity threshold
- context construction
- prompt grounding
- hallucination
- citations
- conversational RAG

### Evaluation
- Recall@K
- Precision@K
- Hit Rate@K
- MRR
- context relevance
- answer relevance
- faithfulness
- unanswerable evaluation
- benchmark datasets
- LLM-as-a-Judge
- evaluation bias
- baseline comparison
- failure analysis

### Frontend
- React
- TypeScript
- components
- props/state
- hooks
- Context
- routing
- protected routes
- API client
- server state
- SSE
- Markdown rendering
- error boundaries
- accessibility
- production builds
- Nginx
- multi-stage Docker

### Architecture
- separation of concerns
- service layer
- API layer
- RAG layer
- database layer
- reusable frontend components
- custom hooks
- centralized API communication
- clean dependency direction

---

# 17. Core Configuration Baseline

```text
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSIONS=384

TOP_K=4
SIMILARITY_THRESHOLD=0.35
MAX_CONTEXT_LENGTH=6000

CHAT_HISTORY_MESSAGE_LIMIT=10

MAX_FILE_SIZE=10MB

```

These are project baselines and should be evaluated rather than treated as universally optimal.

---

# 18. Key Rules to Remember

1. Code and verified tests are the source of truth.
2. Never document planned functionality as implemented.
3. Never trust client-supplied user IDs for authorization.
4. Authentication and authorization are different.
5. Store files separately from relational metadata.
6. Use server-side file validation.
7. Use the same embedding space for documents and queries.
8. Do not mix embedding dimensions in one vector collection.
9. Use metadata filters for vector-level user isolation.
10. Do not call the LLM when retrieval finds no relevant evidence.
11. Retrieved evidence and conversation history are different contexts.
12. Do not fake streaming.
13. Persist one completed assistant message after successful streaming.
14. Evaluate retrieval separately from generation.
15. Change one evaluation parameter at a time.
16. Do not expose API keys or secrets to the frontend.
17. Keep API routes thin.
18. Keep React components focused.
19. Prefer simple modular architecture over unnecessary abstraction.
20. Do not confuse "deployment-ready" with "already deployed".

---

# 19. One-Line Mental Model

> **This project takes user documents, validates and extracts them, chunks and embeds their text, stores vectors in ChromaDB with ownership metadata, retrieves relevant evidence for authenticated questions, grounds an LLM response in that evidence, streams the answer to a React frontend, evaluates retrieval/generation quality, and packages the system for maintainable deployment.**
