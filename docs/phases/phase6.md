# Phase 6 - Persistent Chat Experience and Streaming

## Status

Completed (Implementation Complete; developer functional testing pending)

## Objective

Turn authenticated, user-isolated question answering into persistent conversations with bounded follow-up context and streamed assistant responses.

## Database Changes

`Conversation` has `id`, non-null `user_id` foreign key, `title`, `created_at`, and `updated_at`. `Message` has `id`, non-null `conversation_id` foreign key, constrained `role` (`user` or `assistant`), `content`, and `created_at`. A user has many conversations; a conversation has many messages. ORM and database cascade configuration delete messages with a conversation.

## API Endpoints

Protected with the existing Bearer JWT dependency:

- `POST /conversations` - create an empty conversation; optional title.
- `GET /conversations` - list only the caller's conversations.
- `GET /conversations/{conversation_id}` - return an owned conversation and its persisted messages.
- `DELETE /conversations/{conversation_id}` - delete an owned conversation and cascade its messages.
- `POST /conversations/{conversation_id}/messages` - persist a user message and return an SSE stream.

## Authentication and Ownership

Every route loads the current user from the Phase 5 JWT dependency. Conversation lookups constrain both conversation ID and `user_id`; message creation uses only an already owner-verified conversation. Cross-user IDs return `404`.

## Message Flow

The message route validates ownership, saves the user message, derives the default title from that first message, loads bounded prior history, retrieves relevant chunks, and constructs the conversational prompt. It streams the real provider deltas and accumulates them. Only a completed generation is inserted as the assistant message.

## RAG Integration and History Strategy

Conversation history and retrieved document context are separate prompt sections. The system retrieves again for every user question using the authenticated user ID, so chat history never bypasses ChromaDB isolation. `CHAT_HISTORY_MESSAGE_LIMIT=10` retains the newest ten messages in chronological order as a simple configurable initial limit. It is a character/token-unaware baseline, not a universal optimum.

## Streaming

The endpoint returns `text/event-stream` SSE. It emits actual OpenAI Responses `response.output_text.delta` values as `token` events with JSON `{ "text": "..." }`. It never generates a full LLM answer and artificially splits it into chunks.

## Persistence and Failures

The complete accumulated streamed answer is written to PostgreSQL before `sources` and `done` are emitted. If LLM generation or assistant-message persistence fails, the endpoint sends an SSE `error` event; no partial assistant message is saved. The already-valid user message remains as the record of the submitted request.

## Sources

After a successful assistant save, the SSE `sources` event provides only chunks that entered the prompt: `document_id`, `filename`, `chunk_index`, similarity, and page number only when available. It also includes `has_relevant_context`. No-context replies are persisted and sent as a single non-LLM token event with empty sources; this is a fallback response, not simulated LLM streaming.

## Dependencies Added

None. The existing OpenAI Python client is reused for Responses streaming.

## Environment Variables

- `CHAT_HISTORY_MESSAGE_LIMIT=10`
- Existing RAG, OpenAI, database, and JWT environment variables remain required.

## Files Changed

- `backend/models.py`, `crud.py`, `schemas.py`, `config.py`, `main.py`, `.env.example`
- `backend/chat_service.py`, `conversation_routes.py`
- `backend/prompt_builder.py`, `llm_service.py`
- `docs/understanding.md`, `system_architecture.md`, `workflow.md`, `decisions.md`, this file

## Known Limitations

- No token-aware history truncation, title-generation LLM call, refresh tokens, Redis, background worker, retry queue, evaluation system, or production deployment.
- A client that disconnects during generation may receive partial text but no assistant message is persisted.
- PostgreSQL, ChromaDB, local files, and the LLM provider do not have one distributed transaction.
- Functional verification could not be performed by the coding agent because `backend/env/Scripts/python.exe` still cannot launch.

## What Was Not Implemented

No Phase 7 evaluation datasets, retrieval/answer metrics, faithfulness checks, automated evaluation pipeline, Docker, deployment, agents, MCP, or multi-agent behavior.

## Next Phase

```text
Phase 7 - RAG Evaluation and Quality
```
