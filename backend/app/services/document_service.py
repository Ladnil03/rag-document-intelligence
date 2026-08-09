"""Document service.

Owns the upload + delete orchestration so the routes stay thin.
The actual byte persistence and ingestion steps are delegated to
``app.core.storage`` and ``app.rag.ingestion`` respectively.
"""

import logging
import os
import uuid
from typing import List

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core import config
from app.core.storage import save_upload_bytes, remove_file
from app.crud.documents import (
    create_document,
    create_uploaded_document,
    delete_document_for_user,
    get_document_for_user,
    get_documents_for_user,
    update_document_status,
)
from app.models.document import Document
from app.rag import ingestion as rag_ingestion
from app.rag.vector_store import delete_document_chunks
from app.schemas.documents import DocumentCreate, DocumentUpdate
from app.schemas.shared import ProcessingStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def list_documents(db: Session, user_id: int) -> List[Document]:
    return get_documents_for_user(db=db, user_id=user_id)


def get_document(db: Session, user_id: int, document_id: int) -> Document | None:
    return get_document_for_user(db=db, document_id=document_id, user_id=user_id)


# ---------------------------------------------------------------------------
# Create (metadata-only)
# ---------------------------------------------------------------------------

def create_metadata_document(
    db: Session, user_id: int, payload: DocumentCreate
) -> Document:
    return create_document(db=db, document=payload, user_id=user_id)


# ---------------------------------------------------------------------------
# Upload (file bytes -> ingestion -> COMPLETED/FAILED)
# ---------------------------------------------------------------------------

async def upload_document(db: Session, user_id: int, file: UploadFile) -> Document:
    """Persist, ingest, and return the resulting ``Document`` row."""
    if not file.filename:
        raise ValueError("Filename missing in request.")

    safe_filename = os.path.basename(file.filename)
    _, ext = os.path.splitext(safe_filename)
    ext_lower = ext.lower()

    if ext_lower not in config.ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{ext}'. Only PDF and DOCX files are allowed.")

    contents = await file.read()
    file_size = len(contents)

    if file_size == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")
    if file_size > config.MAX_FILE_SIZE:
        raise ValueError(f"File size ({file_size} bytes) exceeds the 10 MB limit.")

    unique_id = str(uuid.uuid4())
    stored_filename = f"{unique_id}{ext_lower}"
    relative_storage_path = f"storage/{stored_filename}"
    absolute_storage_path = os.path.join(config.STORAGE_DIR, stored_filename)

    save_upload_bytes(absolute_storage_path, contents)

    file_type = ext_lower.lstrip(".")

    db_document = create_uploaded_document(
        db=db,
        name=file.filename,
        stored_file_path=relative_storage_path,
        file_type=file_type,
        file_size=file_size,
        user_id=user_id,
    )
    doc_id = db_document.id
    logger.info("[Upload] document_id=%d name='%s' saved to disk.", doc_id, file.filename)

    update_document_status(db=db, document_id=doc_id, status=ProcessingStatus.PROCESSING.value)
    try:
        extracted_text = rag_ingestion.index_document(
            document_id=doc_id,
            filename=file.filename,
            file_path=absolute_storage_path,
            file_type=file_type,
            user_id=user_id,
        )
        updated = update_document_status(
            db=db,
            document_id=doc_id,
            status=ProcessingStatus.COMPLETED.value,
            extracted_text=extracted_text,
        )
        logger.info("[Upload] document_id=%d processing COMPLETED.", doc_id)
        return updated
    except Exception as exc:
        logger.error("[Upload] document_id=%d processing FAILED: %s", doc_id, exc)
        return update_document_status(
            db=db,
            document_id=doc_id,
            status=ProcessingStatus.FAILED.value,
        )


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

def rename_document(
    db: Session, user_id: int, document_id: int, payload: DocumentUpdate
) -> Document | None:
    document = get_document_for_user(db=db, document_id=document_id, user_id=user_id)
    if not document:
        return None
    document.name = payload.name
    db.commit()
    db.refresh(document)
    return document


# ---------------------------------------------------------------------------
# Delete (ordered: vectors -> file -> DB row)
# ---------------------------------------------------------------------------

class VectorStoreUnavailable(Exception):
    """Raised when ChromaDB vector deletion fails; no document data was deleted."""


class FileDeletionFailed(Exception):
    """Raised when filesystem cleanup fails after vectors were removed."""


class MetadataDeletionFailed(Exception):
    """Raised when PostgreSQL cleanup fails after vectors + file were removed."""


def delete_document(db: Session, user_id: int, document_id: int) -> int:
    """Delete a document with the documented safety ordering.

    1. Verify the document exists.
    2. Remove ChromaDB vectors; if this fails, abort so the data is intact.
    3. Remove the binary file. On failure, attempt to restore vectors and
       surface a 500; the metadata row is preserved.
    4. Delete the PostgreSQL row.
    """
    db_document = get_document_for_user(
        db=db, document_id=document_id, user_id=user_id
    )
    if not db_document:
        return -1

    try:
        delete_document_chunks(document_id)
    except Exception as exc:
        logger.error(
            "[Delete] ChromaDB vector deletion failed for document_id=%d: %s. "
            "No document data was deleted.",
            document_id,
            exc,
        )
        raise VectorStoreUnavailable() from exc

    if db_document.stored_file_path:
        # __file__ = backend/app/services/document_service.py -> backend/
        backend_root = os.path.dirname(
            os.path.dirname(os.path.dirname(__file__))
        )
        abs_path = os.path.join(backend_root, db_document.stored_file_path)
        if os.path.exists(abs_path):
            try:
                remove_file(abs_path)
            except Exception as exc:
                logger.error(
                    "[Delete] Failed to remove file %s for document_id=%d: %s. "
                    "Attempting vector restoration.",
                    abs_path,
                    document_id,
                    exc,
                )
                try:
                    rag_ingestion.index_document(
                        document_id=document_id,
                        filename=db_document.name,
                        file_path=abs_path,
                        file_type=db_document.file_type,
                        user_id=user_id,
                    )
                except Exception as restore_exc:
                    logger.error(
                        "[Delete] Vector restoration also failed for document_id=%d: %s",
                        document_id,
                        restore_exc,
                    )
                    update_document_status(
                        db, document_id, ProcessingStatus.FAILED.value
                    )
                raise FileDeletionFailed() from exc

    try:
        delete_document_for_user(
            db=db, document_id=document_id, user_id=user_id
        )
    except Exception as exc:
        logger.error(
            "[Delete] PostgreSQL deletion failed for document_id=%d after "
            "file/vector cleanup: %s",
            document_id,
            exc,
        )
        raise MetadataDeletionFailed() from exc

    logger.info("[Delete] document_id=%d fully deleted.", document_id)
    return document_id
