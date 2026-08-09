"""Conversation persistence and history helpers.

Routes call into this service so they stay thin and uniform.
"""

from typing import List, Optional, Sequence

from sqlalchemy.orm import Session

from app.core import config
from app.crud.conversations import (
    create_conversation,
    delete_conversation_for_user,
    get_conversation_for_user,
    get_conversations_for_user,
    set_conversation_title_if_default,
)
from app.crud.messages import create_message, get_recent_messages
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import ConversationCreate


def list_user_conversations(db: Session, user_id: int) -> List[Conversation]:
    return get_conversations_for_user(db=db, user_id=user_id)


def get_user_conversation(
    db: Session, user_id: int, conversation_id: int
) -> Optional[Conversation]:
    return get_conversation_for_user(
        db=db, conversation_id=conversation_id, user_id=user_id
    )


def create_user_conversation(
    db: Session, user_id: int, payload: ConversationCreate | None
) -> Conversation:
    return create_conversation(
        db=db,
        user_id=user_id,
        title=payload.title if payload else None,
    )


def delete_user_conversation(db: Session, user_id: int, conversation_id: int) -> bool:
    return delete_conversation_for_user(
        db=db, conversation_id=conversation_id, user_id=user_id
    )


def persist_user_message(
    db: Session, conversation: Conversation, content: str
) -> Message:
    """Persist a user message and set the default title if needed."""
    message = create_message(db, conversation, "user", content)
    set_conversation_title_if_default(db, conversation, content)
    return message


def persist_assistant_message(
    db: Session, conversation: Conversation, content: str
) -> Message:
    return create_message(db, conversation, "assistant", content)


def recent_messages_for_prompt(
    db: Session, conversation_id: int
) -> List[Message]:
    """Return the bounded recent history in chronological prompt order."""
    return get_recent_messages(
        db=db, conversation_id=conversation_id, limit=config.CHAT_HISTORY_MESSAGE_LIMIT
    )


def history_turns(
    records: Sequence[Message], exclude_message_id: int | None = None
) -> list[tuple[str, str]]:
    """Render messages as ``(role, content)`` tuples for the prompt builder."""
    return [
        (msg.role, msg.content)
        for msg in records
        if exclude_message_id is None or msg.id != exclude_message_id
    ]
