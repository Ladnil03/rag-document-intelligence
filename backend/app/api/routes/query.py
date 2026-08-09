"""Direct RAG query endpoint (one-shot, non-streaming)."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.models.user import User
from app.rag import llm as rag_llm
from app.rag import retrieval as rag_retrieval
from app.rag.query import answer_question
from app.schemas.chat import QueryRequest, QueryResponse, QuerySource

logger = logging.getLogger(__name__)
router = APIRouter(tags=["query"])


@router.post(
    "/query",
    response_model=QueryResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
def query_documents(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
):
    """Answer a question only when indexed documents provide relevant context."""
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question must not be empty.",
        )

    try:
        result = answer_question(question, current_user.id)
    except rag_retrieval.RetrievalError as exc:
        logger.error("[Query] Retrieval failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document retrieval is temporarily unavailable.",
        ) from exc
    except rag_llm.LLMConfigurationError as exc:
        logger.error("[Query] LLM configuration error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Answer generation is not configured.",
        ) from exc
    except rag_llm.LLMGenerationError as exc:
        logger.error("[Query] LLM generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Answer generation failed. Please try again later.",
        ) from exc

    return QueryResponse(
        answer=result.answer,
        has_relevant_context=result.has_relevant_context,
        sources=[
            QuerySource(
                document_id=chunk.document_id,
                filename=chunk.filename,
                chunk_index=chunk.chunk_index,
                similarity=round(chunk.similarity, 4),
                page_number=chunk.page_number,
            )
            for chunk in result.chunks
        ],
    )
