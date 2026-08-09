"""Chat service.

Owns the streaming orchestration that used to live inside the
``POST /conversations/{id}/messages`` route. The route only translates
errors into HTTP responses and wraps the SSE iterator in a
``StreamingResponse``.

Two public surfaces:

- ``prepare_chat_reply``: builds the prompt + sources payload.
- ``stream_assistant_answer``: yields SSE events for the streamed reply,
  optionally persisting the assistant message via a callback supplied
  by the route (so the chat service owns the protocol but the route
  owns the DB session).
"""

import json
from dataclasses import dataclass
from typing import Callable, Iterator, Sequence

from app.rag import context, llm, prompts, retrieval
from app.rag.retrieval import RetrievedChunk


@dataclass(frozen=True)
class PreparedChatReply:
    prompt: str
    chunks: list[RetrievedChunk]
    has_relevant_context: bool


class RetrievalUnavailable(Exception):
    """Raised when the retrieval step cannot complete."""


def prepare_chat_reply(
    question: str,
    user_id: int,
    history: Sequence[tuple[str, str]],
) -> PreparedChatReply:
    """Retrieve document evidence and compose the prompt with chat history."""
    try:
        chunks = retrieval.retrieve_relevant_chunks(question, user_id)
        context_result = context.build_context(chunks)
    except retrieval.RetrievalError as exc:
        raise RetrievalUnavailable() from exc

    prompt = prompts.build_conversational_rag_prompt(
        list(history), context_result.context, question
    )
    return PreparedChatReply(
        prompt=prompt,
        chunks=context_result.chunks,
        has_relevant_context=bool(context_result.chunks),
    )


NO_CONTEXT_ANSWER = (
    "I could not find sufficiently relevant information in your documents or "
    "prior assistant messages to answer that question."
)


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def _sources_payload(prepared: PreparedChatReply) -> dict:
    return {
        "sources": [
            {
                "document_id": chunk.document_id,
                "filename": chunk.filename,
                "chunk_index": chunk.chunk_index,
                "similarity": round(chunk.similarity, 4),
                **(
                    {"page_number": chunk.page_number}
                    if chunk.page_number is not None
                    else {}
                ),
            }
            for chunk in prepared.chunks
        ],
        "has_relevant_context": prepared.has_relevant_context,
    }


def no_context_events(prepared: PreparedChatReply) -> Iterator[str]:
    """SSE iterator for the synchronous no-context reply path."""
    yield _sse("token", {"text": NO_CONTEXT_ANSWER})
    yield _sse("sources", _sources_payload(prepared))
    yield _sse("done", {})


def stream_assistant_answer(
    prepared: PreparedChatReply,
    persist_assistant: Callable[[str], None],
) -> Iterator[str]:
    """Yield SSE events for the streamed assistant answer.

    The assistant message is persisted only if the stream completes
    successfully. On generation failure an ``error`` event is emitted
    and the partial answer is NOT written to the database.
    """
    parts: list[str] = []
    try:
        for delta in llm.stream_chat_answer(prepared.prompt):
            parts.append(delta)
            yield _sse("token", {"text": delta})
    except (llm.LLMConfigurationError, llm.LLMGenerationError):
        yield _sse("error", {"message": "Assistant response generation failed."})
        return

    answer = "".join(parts).strip()
    if not answer:
        # Mirrors the original behaviour: an empty completion is treated as
        # a generation failure rather than a silent success.
        yield _sse("error", {"message": "Assistant response generation failed."})
        return

    try:
        persist_assistant(answer)
    except Exception:
        yield _sse("error", {"message": "Assistant response could not be saved."})
        return

    yield _sse("sources", _sources_payload(prepared))
    yield _sse("done", {})
