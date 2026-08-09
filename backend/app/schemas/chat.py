"""Conversation, message, query, and streaming-related schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.shared import MessageRole


class ConversationCreate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def reject_blank_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Message content must not be empty.")
        return normalized


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: MessageRole
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse]


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)


class QuerySource(BaseModel):
    document_id: int
    filename: str
    chunk_index: int
    similarity: float
    page_number: Optional[int] = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[QuerySource]
    has_relevant_context: bool
