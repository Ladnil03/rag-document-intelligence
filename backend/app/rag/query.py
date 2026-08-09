"""End-to-end RAG query orchestration, separate from HTTP and persistence concerns."""

import logging
from dataclasses import dataclass
from typing import List

from app.rag import context, llm, prompts, retrieval

logger = logging.getLogger(__name__)

NO_RELEVANT_CONTEXT_ANSWER = (
    "I could not find sufficiently relevant information in the indexed documents "
    "to answer that question."
)


@dataclass(frozen=True)
class QueryResult:
    answer: str
    chunks: List[retrieval.RetrievedChunk]
    has_relevant_context: bool


def answer_question(question: str, user_id: int, top_k: int | None = None) -> QueryResult:
    """Retrieve grounded context and generate an answer, or decline safely."""
    logger.info("[Query] Received question (%d characters).", len(question))
    chunks = retrieval.retrieve_relevant_chunks(question, user_id, top_k=top_k)
    if not chunks:
        logger.info("[Query] No sufficiently relevant context found; skipping LLM.")
        return QueryResult(NO_RELEVANT_CONTEXT_ANSWER, [], False)

    context_result = context.build_context(chunks)
    if not context_result.chunks:
        logger.info("[Query] Relevant chunks exceeded context cap; skipping LLM.")
        return QueryResult(NO_RELEVANT_CONTEXT_ANSWER, [], False)

    prompt = prompts.build_rag_prompt(question, context_result.context)
    answer = llm.generate_answer(prompt)
    return QueryResult(answer, context_result.chunks, True)
