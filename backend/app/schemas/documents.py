"""Document request / response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


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
