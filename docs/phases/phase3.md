# Phase 3 — RAG Ingestion Pipeline

## Status

Completed

## Objective

Turn text extracted in Phase 2 into persistent, searchable vector representations while preserving the document source metadata needed by a later retrieval phase.

## Implemented Features

- Boundary-aware overlapping text chunker with configurable size and overlap.
- Configurable local sentence-transformer embedding service.
- Persistent ChromaDB vector store with explicit embeddings and cosine space.
- Upload integration that sets `COMPLETED` only after vector storage succeeds, or `FAILED` on any ingestion error.
- Deterministic chunk IDs and complete per-document vector replacement.
- ChromaDB cleanup integrated into document deletion, with vector-store failures preventing further deletion.

## Ingestion Pipeline

```text
Upload → Validate → Store file → Create metadata → PROCESSING
       → Extract text → Chunk text → Generate embeddings → Store vectors
       → Save text and COMPLETED
```

Any extraction, chunking, embedding, or ChromaDB failure sets the document to `FAILED`; it does not become `COMPLETED`.

## Chunking

`backend/chunker.py` uses a 1000-character default target (`CHUNK_SIZE`) with 200-character overlap (`CHUNK_OVERLAP`). It prefers paragraph, sentence, then word boundaries near that target. The settings are initial baselines to evaluate later; character counts are not token counts.

## Embedding Model

- Model: `all-MiniLM-L6-v2` by default (`EMBEDDING_MODEL`)
- Dimensions: 384 (`EMBEDDING_DIMENSIONS`)
- Runtime: local through `sentence-transformers`; no API key or hosted embedding service is used. The model may download to the local Hugging Face cache on first use if it is not already cached.

## ChromaDB

- Client: `chromadb.PersistentClient`
- Persistence directory: `backend/chroma_data/` by default (`CHROMA_PERSIST_DIRECTORY`)
- Collection: `document_chunks` (`CHROMA_COLLECTION_NAME`)
- Similarity configuration: cosine HNSW space
- Contents: deterministic ID, explicit embedding, chunk text, and metadata

## Metadata

Each vector has `document_id` (integer), `filename`, and `chunk_index`. The Phase 2 extractor does not preserve page-to-chunk mappings, so Phase 3 intentionally does not invent `page_number` metadata.

## Reprocessing

`replace_document_chunks()` generates all replacement embeddings before removing existing vectors for the document, then stores the new complete set. This prevents duplicate records and stale chunks with higher old indices. There is no public reprocessing endpoint in Phase 3.

## Deletion

The delete endpoint cleans vectors, then the stored file, then PostgreSQL metadata. If vector deletion fails, it returns `503` and retains the document/file. Cross-store work cannot be fully transactional; failures after a successful prior deletion are logged, reported, and may require the implemented restoration attempt or manual reconciliation.

## API Changes

No public API endpoints were added. `POST /documents/upload` now runs ingestion. `DELETE /documents/{document_id}` now cleans associated vectors and exposes cleanup failures rather than silently continuing.

## Dependencies Added

- `chromadb`
- `sentence-transformers`

Their transitive dependencies (including the local model runtime) are managed by pip in `backend/env/`.

## Environment Variables

```text
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSIONS=384
CHROMA_PERSIST_DIRECTORY=./chroma_data
CHROMA_COLLECTION_NAME=document_chunks
```

`DATABASE_URL` remains the existing PostgreSQL configuration. No embedding API key is used.

## Files Changed

- `backend/config.py`
- `backend/chunker.py`
- `backend/embedding_service.py`
- `backend/ingestion.py`
- `backend/vector_store.py`
- `backend/main.py`
- `backend/.env.example`
- `backend/.gitignore`
- `docs/understanding.md`
- `docs/system_architecture.md`
- `docs/workflow.md`
- `docs/decisions.md`

## Known Limitations

- No user-facing retrieval, query embedding, or similarity-search endpoint.
- No LLM generation, RAG answer generation, chat, source citations, authentication, agents, MCP, queues, Docker, or deployment work.
- Local ChromaDB and synchronous ingestion are development-oriented.
- Initial chunk configuration still needs retrieval-quality evaluation.
- PostgreSQL, local files, and ChromaDB do not share a distributed transaction.

## What Was Not Implemented

All Phase 4+ answering behavior, including `/chat`, `/query`, prompt construction, query retrieval, and LLM responses, remains unimplemented.

## Next Phase

```text
Phase 4 — RAG Question Answering
```
