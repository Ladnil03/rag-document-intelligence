"""Conversation CRUD helpers."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.schemas.chat import ConversationCreate


def create_conversation(
    db: Session, user_id: int, title: Optional[str] = None
) -> Conversation:
    conversation = Conversation(
        user_id=user_id,
        title=title.strip() if title else "New conversation",
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversations_for_user(
    db: Session, user_id: int, limit: int = 100
) -> List[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        .limit(limit)
        .all()
    )


def get_conversation_for_user(
    db: Session, conversation_id: int, user_id: int
) -> Optional[Conversation]:
    return (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
        .first()
    )


def delete_conversation_for_user(db: Session, conversation_id: int, user_id: int) -> bool:
    conversation = get_conversation_for_user(db, conversation_id, user_id)
    if not conversation:
        return False
    db.delete(conversation)
    db.commit()
    return True


def set_conversation_title_if_default(
    db: Session, conversation: Conversation, first_message: str
) -> None:
    """Use a predictable title without consuming an additional LLM call."""
    if conversation.title != "New conversation":
        return
    normalized = " ".join(first_message.split())
    conversation.title = normalized[:80] or "New conversation"
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()
