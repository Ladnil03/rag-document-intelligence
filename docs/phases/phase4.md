# Phase 4 — RAG Question Answering

## Status

Completed

## Objective

Add grounded question answering on top of Phase 3’s indexed document chunks.

## Implemented Features

- `POST /query` with Pydantic request and response schemas.
- Question embedding through the existing Phase 3 embedding service.
- Top-K ChromaDB retrieval with cosine-distance relevance filtering.
- Bounded source-labelled context and a dedicated grounding prompt.
- Configurable OpenAI Responses API LLM service.
- Source metadata returned only for chunks included in context.
- Safe no-context behavior that skips LLM generation.

## Query Endpoint

`POST /query`

```json
{"question":"What does the document say about chunking?"}
```

```json
{
  "answer":"...",
  "sources":[{"document_id":1,"filename":"guide.pdf","chunk_index":0,"similarity":0.73}],
  "has_relevant_context":true
}
```

`page_number` appears only if actual vector metadata contains it.

## Retrieval

`retrieval_service.py` embeds the question with `all-MiniLM-L6-v2`, requests `TOP_K` chunks from ChromaDB, converts cosine distance to `similarity = 1 - distance`, and keeps chunks meeting `SIMILARITY_THRESHOLD`. Its optional internal document-ID argument keeps future filtering possible without implementing user isolation now.

## Embedding Model

The query uses the existing configurable `all-MiniLM-L6-v2` model in the same 384-dimensional space used at ingestion.

## Top-K and Relevance Threshold

Defaults: `TOP_K=4`; `SIMILARITY_THRESHOLD=0.35`. ChromaDB’s cosine distance is lower for closer vectors; it is converted to similarity before comparison. Both are baseline settings to evaluate later.

## Context Construction

`context_builder.py` retains highest-ranked chunks in order until adding another would exceed `MAX_CONTEXT_LENGTH=6000`. It labels each included source; only included chunks are returned to the client.

## LLM and Prompt

Provider: OpenAI Responses API, through `llm_service.py`.

Default model: `gpt-4.1-mini` (`LLM_MODEL`).

The prompt requires the model to answer only from supplied context, avoid unsupported facts, acknowledge insufficient evidence, be concise, and use source labels where useful.

## Sources

Responses return `document_id`, `filename`, `chunk_index`, and similarity; no raw vectors or fabricated page numbers are returned.

## Error Handling

- Empty/invalid question: validation error (`422`).
- No indexed or sufficiently relevant chunks: grounded insufficiency response (`200`) and no LLM call.
- Embedding/ChromaDB failure: `503`.
- Missing/invalid LLM configuration: `503`.
- LLM generation failure: `502`.

## Dependencies Added

- `openai` 2.53.0 (installed in `backend/env/`)

## Environment Variables

```text
TOP_K=4
SIMILARITY_THRESHOLD=0.35
MAX_CONTEXT_LENGTH=6000
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1-mini
OPENAI_API_KEY=your_openai_api_key_here
```

## Files Changed

- `backend/config.py`, `embedding_service.py`, `vector_store.py`, `schemas.py`, `main.py`
- `backend/retrieval_service.py`, `context_builder.py`, `prompt_builder.py`, `llm_service.py`, `query_service.py`
- `backend/.env.example`
- `docs/understanding.md`, `system_architecture.md`, `workflow.md`, `decisions.md`, `phases/phase4.md`

## Known Limitations

- No authentication, user isolation, document filter API, chat history, or streaming.
- No evaluation framework or automated relevance tuning.
- The default threshold/context values are initial baselines.
- The OpenAI API call requires a developer-supplied key and functional verification.

## What Was Not Implemented

Phase 5+ registration, login, JWT, user accounts, authorization, multi-user document filtering, agents, MCP, queues, Docker, and deployment.

## Next Phase

```text
Phase 5 — Authentication and User Isolation
```
