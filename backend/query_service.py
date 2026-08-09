"""End-to-end RAG query orchestration, separate from the FastAPI route."""

import logging
from dataclasses import dataclass
from typing import List

import context_builder
import llm_service
import prompt_builder
import retrieval_service

logger = logging.getLogger(__name__)

NO_RELEVANT_CONTEXT_ANSWER = (
    "I could not find sufficiently relevant information in the indexed documents "
    "to answer that question."
)


@dataclass(frozen=True)
class QueryResult:
    answer: str
    chunks: List[retrieval_service.RetrievedChunk]
    has_relevant_context: bool


def answer_question(question: str) -> QueryResult:
    """Retrieve grounded context and generate an answer, or decline safely."""
    logger.info("[Query] Received question (%d characters).", len(question))
    chunks = retrieval_service.retrieve_relevant_chunks(question)
    if not chunks:
        logger.info("[Query] No sufficiently relevant context found; skipping LLM.")
        return QueryResult(NO_RELEVANT_CONTEXT_ANSWER, [], False)

    context_result = context_builder.build_context(chunks)
    if not context_result.chunks:
        logger.info("[Query] Relevant chunks exceeded context cap; skipping LLM.")
        return QueryResult(NO_RELEVANT_CONTEXT_ANSWER, [], False)

    prompt = prompt_builder.build_rag_prompt(question, context_result.context)
    answer = llm_service.generate_answer(prompt)
    return QueryResult(answer, context_result.chunks, True)
