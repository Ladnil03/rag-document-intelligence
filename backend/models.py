from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text
from database import Base


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
