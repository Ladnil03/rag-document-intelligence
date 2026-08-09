"""CRUD helpers grouped by entity.

``from app.crud import create_user`` is the canonical form. The legacy
flat-module import path (``import crud; crud.create_user(...)``) keeps
working through the ``backend/crud.py`` shim.
"""

from app.crud.conversations import (
    create_conversation,
    delete_conversation_for_user,
    get_conversation_for_user,
    get_conversations_for_user,
    set_conversation_title_if_default,
)
from app.crud.documents import (
    create_document,
    create_uploaded_document,
    delete_document_for_user,
    get_document_for_user,
    get_documents_for_user,
    update_document_for_user,
    update_document_status,
)
from app.crud.messages import create_message, get_recent_messages
from app.crud.users import create_user, get_user_by_email, get_user_by_id

__all__ = [
    "create_conversation",
    "delete_conversation_for_user",
    "get_conversation_for_user",
    "get_conversations_for_user",
    "set_conversation_title_if_default",
    "create_document",
    "create_uploaded_document",
    "delete_document_for_user",
    "get_document_for_user",
    "get_documents_for_user",
    "update_document_for_user",
    "update_document_status",
    "create_message",
    "get_recent_messages",
    "create_user",
    "get_user_by_email",
    "get_user_by_id",
]
