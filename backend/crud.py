from typing import List, Optional
from sqlalchemy.orm import Session
import models
import schemas


def get_document(db: Session, document_id: int) -> Optional[models.Document]:
    """Retrieve a single document by its ID."""
    return db.query(models.Document).filter(models.Document.id == document_id).first()


def get_documents(db: Session, skip: int = 0, limit: int = 100) -> List[models.Document]:
    """Retrieve all stored documents."""
    return db.query(models.Document).offset(skip).limit(limit).all()


def create_document(db: Session, document: schemas.DocumentCreate) -> models.Document:
    """Create a metadata-only document in PostgreSQL (Phase 1 legacy compatibility)."""
    db_document = models.Document(
        name=document.name,
        processing_status=schemas.ProcessingStatus.COMPLETED.value
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


def create_uploaded_document(
    db: Session,
    name: str,
    stored_file_path: str,
    file_type: str,
    file_size: int
) -> models.Document:
    """Create a new document record for an uploaded file with initial UPLOADED status."""
    db_document = models.Document(
        name=name,
        stored_file_path=stored_file_path,
        file_type=file_type,
        file_size=file_size,
        processing_status=schemas.ProcessingStatus.UPLOADED.value
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


def update_document_status(
    db: Session,
    document_id: int,
    status: str,
    extracted_text: Optional[str] = None
) -> Optional[models.Document]:
    """Update document processing status and set extracted text content."""
    db_document = get_document(db, document_id=document_id)
    if not db_document:
        return None
        
    db_document.processing_status = status
    if extracted_text is not None:
        db_document.extracted_text = extracted_text
        
    db.commit()
    db.refresh(db_document)
    return db_document


def update_document(
    db: Session, document_id: int, document_update: schemas.DocumentUpdate
) -> Optional[models.Document]:
    """Update an existing document's name in PostgreSQL."""
    db_document = get_document(db, document_id=document_id)
    if not db_document:
        return None
        
    db_document.name = document_update.name
    db.commit()
    db.refresh(db_document)
    return db_document


def delete_document(db: Session, document_id: int) -> bool:
    """Delete a document by ID from PostgreSQL."""
    db_document = get_document(db, document_id=document_id)
    if not db_document:
        return False
        
    db.delete(db_document)
    db.commit()
    return True
