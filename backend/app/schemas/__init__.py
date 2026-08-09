"""Pydantic request/response schemas.

Re-exports every schema so both ``from app.schemas import DocumentCreate``
and the legacy ``from schemas import DocumentCreate`` (via the
``backend/schemas.py`` shim) resolve to the same class.
"""

from app.schemas.auth import (
    CredentialsBase,
    TokenResponse,
    UserLogin,
    UserRegistration,
    UserResponse,
)
from app.schemas.chat import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    QueryRequest,
    QueryResponse,
    QuerySource,
)
from app.schemas.documents import (
    DocumentBase,
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
)
from app.schemas.shared import MessageRole, ProcessingStatus

__all__ = [
    "CredentialsBase",
    "TokenResponse",
    "UserLogin",
    "UserRegistration",
    "UserResponse",
    "ConversationCreate",
    "ConversationDetailResponse",
    "ConversationResponse",
    "MessageCreate",
    "MessageResponse",
    "QueryRequest",
    "QueryResponse",
    "QuerySource",
    "DocumentBase",
    "DocumentCreate",
    "DocumentResponse",
    "DocumentUpdate",
    "MessageRole",
    "ProcessingStatus",
]
