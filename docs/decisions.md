# Architectural Decisions

## ADR-001 — Phase-wise Development

**Decision:** Build the application incrementally and implement only the current phase boundary.

**Status:** Accepted.

## ADR-002 — PostgreSQL for Application Metadata

**Decision:** PostgreSQL, SQLAlchemy, and request-scoped sessions hold document metadata and processing state.

**Reason:** Relational metadata, status transitions, and file references belong in the application database. Raw files and vectors have different access patterns.

**Status:** Accepted (Phase 1).

## ADR-003 — Local Files and Synchronous Extraction

**Decision:** Store PDF/DOCX files under `backend/storage/` and extract them synchronously with `pypdf` and `python-docx`.

**Reason:** This keeps Phase 2 small and observable before adding queues or external file services.

**Status:** Accepted (Phase 2).

## ADR-004 — Persistent ChromaDB for Document Chunks

**Decision:** Use `chromadb.PersistentClient` with `backend/chroma_data/` by default and one configurable `document_chunks` collection.

**Reason:** ChromaDB is a lightweight local vector database appropriate for development. Persistence means indexed data survives FastAPI restarts without putting high-dimensional vectors in PostgreSQL.

**Status:** Accepted (Phase 3).

## ADR-005 — Local `all-MiniLM-L6-v2` Embeddings

**Decision:** Use configurable `sentence-transformers` model `all-MiniLM-L6-v2`, expected to produce 384-dimensional embeddings.

**Reason:** It is free, compact, suitable for CPU development, and requires no API key. The model runs locally after first-use model download/cache. `EMBEDDING_DIMENSIONS` verifies that the configured model is compatible with the selected collection strategy.

**Status:** Accepted (Phase 3).

## ADR-006 — Boundary-aware Character Chunking

**Decision:** Start with a configurable character target of 1000 and overlap of 200, preferring paragraph, sentence, and word boundaries.

**Reason:** This provides meaningful passages without a heavyweight tokenizer or framework. The values are baselines, not universal optima; retrieval evaluation should tune them later.

**Status:** Accepted (Phase 3).

## ADR-007 — Explicit Embeddings and Direct Libraries

**Decision:** `embedding_service.py` generates embeddings explicitly, and `vector_store.py` passes them to ChromaDB. LangChain/LangGraph are not used.

**Reason:** The ingestion flow is small enough to be understandable with direct libraries. Explicit vectors make model loading, dimensions, logging, and replacement behavior visible.

**Status:** Accepted (Phase 3).

## ADR-008 — Complete Per-document Vector Replacement

**Decision:** Embed new chunks first, then remove all existing vectors for that document, then upsert the complete new set with deterministic IDs.

**Reason:** This avoids duplicate records and stale chunks when reprocessing produces a different number of chunks. If storage fails after deletion, the document is marked `FAILED` rather than falsely remaining complete.

**Status:** Accepted (Phase 3).

## ADR-009 — Conservative Cross-store Deletion

**Decision:** Delete vectors before the file and PostgreSQL record; abort with an error if vector deletion fails.

**Reason:** A vector cleanup failure must not be silently hidden by deleting the metadata first. There is no distributed transaction across ChromaDB, filesystem, and PostgreSQL; an error after the first successful external mutation may require restoration or manual reconciliation, which the code logs and reports.

**Status:** Accepted (Phase 3).

## ADR-010 — RAG Before LLM Generation

**Decision:** Retrieve semantically relevant document chunks before asking the LLM to answer.

**Reason:** The LLM does not independently know this application's uploaded documents. Bounded retrieved context makes answers grounded in the indexed corpus and allows sources to be returned.

**Status:** Accepted (Phase 4).

## ADR-011 — Reuse the Phase 3 Embedding Model

**Decision:** Questions use the same `all-MiniLM-L6-v2` embedding service and 384-dimensional vector space as document chunks.

**Reason:** Similarity is meaningful only when questions and documents are represented in the same vector space. The cached embedding service also avoids loading the model for each request.

**Status:** Accepted (Phase 4).

## ADR-012 — Configurable Top-K, Similarity Threshold, and Context Limit

**Decision:** Retrieve `TOP_K=4` candidates, retain chunks with cosine similarity at least `0.35`, and cap context at 6000 characters by default.

**Reason:** ChromaDB returns cosine distance for the collection, which is converted as `similarity = 1 - distance`. The baseline rejects low-relevance chunks while keeping a small amount of evidence. These are initial values to evaluate, not universal retrieval settings.

**Status:** Accepted (Phase 4).

## ADR-013 — OpenAI Responses API Behind a Small Service

**Decision:** Use configurable OpenAI Responses API generation through `llm_service.py`, with model default `gpt-4.1-mini` and `OPENAI_API_KEY` only in environment configuration.

**Reason:** The official Python client provides a direct implementation while the service boundary keeps the RAG pipeline independent of a future provider replacement. LangChain/LangGraph are not introduced because this phase needs only retrieval, a prompt, and one generation call.

**Status:** Accepted (Phase 4).

## ADR-014 — Skip Generation Without Grounded Context

**Decision:** When no retrieved chunk meets the threshold, return a clear insufficiency answer with no sources and do not call the LLM.

**Reason:** This makes grounding enforceable in application logic rather than relying only on prompt wording and avoids fabricating an answer from unrelated documents.

**Status:** Accepted (Phase 4).
