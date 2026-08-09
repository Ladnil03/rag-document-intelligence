"""Message CRUD helpers."""

from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message


def create_message(
    db: Session, conversation: Conversation, role: str, content: str
) -> Message:
    """Persist one user/assistant message and advance its conversation timestamp."""
    message = Message(
        conversation_id=conversation.id,
        role=role,
        content=content,
    )
    conversation.updated_at = datetime.now(timezone.utc)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_recent_messages(
    db: Session, conversation_id: int, limit: int
) -> List[Message]:
    """Return only the newest bounded history, in chronological prompt order."""
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(messages))
