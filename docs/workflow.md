# Workflow

## Document Ingestion

```text
Upload → Validate → Store file → Create metadata → PROCESSING
       → Extract → Chunk → Embed → Replace ChromaDB vectors → COMPLETED
```

Ingestion failures set the document status to `FAILED`. ChromaDB vector deletion occurs before file and PostgreSQL cleanup when a document is deleted.

## Query Workflow

```text
User question
  ↓
POST /query
  ↓
Validate a non-empty question
  ↓
Embed with all-MiniLM-L6-v2
  ↓
Search ChromaDB for TOP_K candidates
  ↓
Convert cosine distance to similarity and apply SIMILARITY_THRESHOLD
  ↓
Build bounded source-labelled context
  ↓
Build grounded RAG prompt
  ↓
OpenAI Responses API
  ↓
Answer + sources
```

`MAX_CONTEXT_LENGTH` prevents all retrieved text from being sent without a limit. Only chunks actually included in the context are returned as sources.

## No Relevant Context

```text
Question → retrieval → no indexed/relevant chunks
         → skip LLM
         → 200 response with a clear document-insufficiency answer and [] sources
```

## Failure Responses

```text
Question → embedding or ChromaDB failure → 503 retrieval unavailable
Question → missing/invalid LLM configuration → 503 generation not configured
Question → LLM provider failure → 502 generation failed
```

The API does not return credentials, raw stack traces, raw embeddings, or raw ChromaDB response structures.
