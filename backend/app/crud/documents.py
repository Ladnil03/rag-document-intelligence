"""Document CRUD helpers.

The two creation paths (``create_document`` for metadata-only and
``create_uploaded_document`` for ingestion entries) coexist because the
backend still exposes both ``POST /documents`` and ``POST /documents/upload``.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.shared import ProcessingStatus
from app.schemas.documents import DocumentCreate, DocumentUpdate


def get_document_for_user(
    db: Session, document_id: int, user_id: int
) -> Optional[Document]:
    """Retrieve a document only if it is owned by the authenticated user."""
    return (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == user_id)
        .first()
    )


def get_documents_for_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> List[Document]:
    """Retrieve only the authenticated user's documents."""
    return (
        db.query(Document)
        .filter(Document.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_document(db: Session, document: DocumentCreate, user_id: int) -> Document:
    """Create a metadata-only document for the authenticated owner."""
    db_document = Document(
        name=document.name,
        processing_status=ProcessingStatus.COMPLETED.value,
        user_id=user_id,
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
    file_size: int,
    user_id: int,
) -> Document:
    """Create a new document record for an uploaded file with initial UPLOADED status."""
    db_document = Document(
        name=name,
        stored_file_path=stored_file_path,
        file_type=file_type,
        file_size=file_size,
        processing_status=ProcessingStatus.UPLOADED.value,
        user_id=user_id,
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


def update_document_status(
    db: Session,
    document_id: int,
    status: str,
    extracted_text: Optional[str] = None,
) -> Optional[Document]:
    """Update document processing status and set extracted text content."""
    db_document = (
        db.query(Document).filter(Document.id == document_id).first()
    )
    if not db_document:
        return None

    db_document.processing_status = status
    if extracted_text is not None:
        db_document.extracted_text = extracted_text

    db.commit()
    db.refresh(db_document)
    return db_document


def update_document_for_user(
    db: Session, document_id: int, user_id: int, document_update: DocumentUpdate
) -> Optional[Document]:
    """Update a document only when it is owned by the authenticated user."""
    db_document = get_document_for_user(db, document_id, user_id)
    if not db_document:
        return None

    db_document.name = document_update.name
    db.commit()
    db.refresh(db_document)
    return db_document


def delete_document_for_user(db: Session, document_id: int, user_id: int) -> bool:
    """Delete a document only when it is owned by the authenticated user."""
    db_document = get_document_for_user(db, document_id, user_id)
    if not db_document:
        return False

    db.delete(db_document)
    db.commit()
    return True
