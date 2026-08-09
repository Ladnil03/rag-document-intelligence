from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProcessingStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentBase(BaseModel):
    name: str


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    name: str


class DocumentResponse(DocumentBase):
    id: int
    name: str
    stored_file_path: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime
    processing_status: str
    extracted_text: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


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
