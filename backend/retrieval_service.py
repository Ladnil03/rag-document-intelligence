"""Question embedding, ChromaDB retrieval, and relevance filtering."""

import logging
from dataclasses import dataclass
from typing import List, Optional, Sequence

import config
import embedding_service
import vector_store

logger = logging.getLogger(__name__)


class RetrievalError(RuntimeError):
    """Raised when query embedding or vector retrieval cannot be completed."""


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    document_id: int
    filename: str
    chunk_index: int
    similarity: float
    page_number: Optional[int] = None


def retrieve_relevant_chunks(
    question: str,
    document_ids: Optional[Sequence[int]] = None,
) -> List[RetrievedChunk]:
    """Retrieve top candidates and retain only chunks meeting the threshold."""
    try:
        if not vector_store.has_indexed_chunks():
            logger.info("[Retrieval] No indexed document chunks are available.")
            return []
        logger.info("[Retrieval] Generating embedding for a question (%d characters).", len(question))
        query_embedding = embedding_service.embed_text(question)
        candidates = vector_store.search_chunks(
            query_embedding=query_embedding,
            top_k=config.TOP_K,
            document_ids=document_ids,
        )
    except Exception as exc:
        logger.error("[Retrieval] Query embedding or ChromaDB search failed: %s", exc)
        raise RetrievalError("Unable to retrieve relevant document context.") from exc

    relevant = [
        RetrievedChunk(
            text=candidate.text,
            document_id=candidate.document_id,
            filename=candidate.filename,
            chunk_index=candidate.chunk_index,
            # ChromaDB returns cosine distance for this collection. Lower is
            # closer, so ``1 - distance`` is the comparable similarity score.
            similarity=1.0 - candidate.distance,
            page_number=candidate.page_number,
        )
        for candidate in candidates
        if 1.0 - candidate.distance >= config.SIMILARITY_THRESHOLD
    ]
    logger.info(
        "[Retrieval] %d/%d chunks met similarity threshold %.2f.",
        len(relevant),
        len(candidates),
        config.SIMILARITY_THRESHOLD,
    )
    return relevant
