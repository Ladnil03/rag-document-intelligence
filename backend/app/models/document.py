"""Document ORM model.

Single source of truth for the `documents` table.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Original filename or document title
    stored_file_path = Column(String, nullable=True)  # Relative path in storage/
    file_type = Column(String, nullable=True)  # 'pdf' or 'docx'
    file_size = Column(Integer, nullable=True)  # Size in bytes
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    processing_status = Column(String, nullable=False, default="UPLOADED")  # UPLOADED, PROCESSING, COMPLETED, FAILED
    extracted_text = Column(Text, nullable=True)  # Plain text extracted from PDF/DOCX
    # Nullable only for a controlled transition from pre-Phase-5 local data.
    # All new document creation paths require an authenticated owner.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    owner = relationship("User", back_populates="documents")
