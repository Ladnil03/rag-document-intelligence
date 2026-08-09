"""Chat endpoint: streamed assistant reply over SSE.

The route is intentionally thin. Persistence is owned by
``conversation_service`` and streaming protocol by ``chat_service``.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.models.user import User
from app.schemas.chat import MessageCreate
from app.schemas.shared import MessageRole
from app.services import chat_service, conversation_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversations", tags=["chat"])

NO_CONTEXT_HEADERS = {"Cache-Control": "no-cache"}
STREAM_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


@router.post(
    "/{conversation_id}/messages",
    response_class=StreamingResponse,
)
def send_message(
    conversation_id: int,
    request: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Persist a user message and stream/persist the corresponding assistant reply."""
    conversation = conversation_service.get_user_conversation(
        db=db, user_id=current_user.id, conversation_id=conversation_id
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )

    # 1. Persist the user message + title, load bounded history.
    try:
        user_message = conversation_service.persist_user_message(
            db, conversation, request.content
        )
        history_records = conversation_service.recent_messages_for_prompt(
            db, conversation_id
        )
    except Exception as exc:
        db.rollback()
        logger.error("[Chat] Could not persist/load message history: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save the message.",
        ) from exc

    prior_history = conversation_service.history_turns(
        history_records, exclude_message_id=user_message.id
    )
    has_prior_assistant = any(role == MessageRole.ASSISTANT.value for role, _ in prior_history)

    # 2. Build the prompt + sources payload.
    try:
        prepared = chat_service.prepare_chat_reply(
            request.content, current_user.id, prior_history
        )
    except chat_service.RetrievalUnavailable as exc:
        logger.error("[Chat] Retrieval failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document retrieval is temporarily unavailable.",
        ) from exc

    # 3. No-context branch: persist a synchronous reply and stream it back.
    if not prepared.has_relevant_context and not has_prior_assistant:
        try:
            conversation_service.persist_assistant_message(db, conversation, chat_service.NO_CONTEXT_ANSWER)
        except Exception as exc:
            db.rollback()
            logger.error("[Chat] Could not persist no-context reply: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to save the assistant response.",
            ) from exc

        return StreamingResponse(
            chat_service.no_context_events(prepared),
            media_type="text/event-stream",
            headers=NO_CONTEXT_HEADERS,
        )

    # 4. Real streaming branch. ``persist`` runs against the same DB session;
    #    chat_service handles the protocol, we handle persistence + errors.
    def persist(answer: str) -> None:
        # The session must still be alive when chat_service yields the
        # final ``done`` event. We commit synchronously here; on failure
        # the route returns an error SSE event via the chat_service catch.
        try:
            conversation_service.persist_assistant_message(db, conversation, answer)
        except Exception:
            db.rollback()
            raise

    return StreamingResponse(
        chat_service.stream_assistant_answer(prepared, persist),
        media_type="text/event-stream",
        headers=STREAM_HEADERS,
    )
