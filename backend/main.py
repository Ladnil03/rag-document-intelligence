"""
main.py — FastAPI application for the RAG Document Intelligence Platform.

Phase 3: The upload pipeline now includes:
  1. File validation
  2. Disk storage
  3. PostgreSQL metadata record (UPLOADED)
  4. Text extraction (pypdf / python-docx)
  5. Text chunking (chunker.py)
  6. Embedding + vector ingestion into ChromaDB (vector_store.py)
  7. Final status update  →  COMPLETED  (or FAILED on any error)

Document deletion also removes associated ChromaDB vectors.
"""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

import config
import crud
import database
import ingestion
import models
import llm_service
import query_service
import retrieval_service
import schemas
import vector_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure the storage directory exists
os.makedirs(config.STORAGE_DIR, exist_ok=True)


def init_db() -> None:
    """Create PostgreSQL tables if the database is reachable."""
    try:
        models.Base.metadata.create_all(bind=database.engine)
    except Exception as exc:
        logger.warning("Could not initialise database tables: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="RAG Document Intelligence Platform", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/")
def hello():
    return {"message": "RAG Document Intelligence API"}


# ---------------------------------------------------------------------------
# RAG question answering (Phase 4)
# ---------------------------------------------------------------------------

@app.post(
    "/query",
    response_model=schemas.QueryResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
def query_documents(request: schemas.QueryRequest):
    """Answer a question only when indexed documents provide relevant context."""
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question must not be empty.",
        )

    try:
        result = query_service.answer_question(question)
    except retrieval_service.RetrievalError as exc:
        logger.error("[Query] Retrieval failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document retrieval is temporarily unavailable.",
        ) from exc
    except llm_service.LLMConfigurationError as exc:
        logger.error("[Query] LLM configuration error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Answer generation is not configured.",
        ) from exc
    except llm_service.LLMGenerationError as exc:
        logger.error("[Query] LLM generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Answer generation failed. Please try again later.",
        ) from exc

    return schemas.QueryResponse(
        answer=result.answer,
        has_relevant_context=result.has_relevant_context,
        sources=[
            schemas.QuerySource(
                document_id=chunk.document_id,
                filename=chunk.filename,
                chunk_index=chunk.chunk_index,
                similarity=round(chunk.similarity, 4),
                page_number=chunk.page_number,
            )
            for chunk in result.chunks
        ],
    )


# ---------------------------------------------------------------------------
# Document Upload  (Phase 2 + Phase 3 pipeline)
# ---------------------------------------------------------------------------

@app.post(
    "/documents/upload",
    response_model=schemas.DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
):
    """
    Upload a PDF or DOCX file.

    Pipeline
    --------
    validate → store on disk → register in PostgreSQL (UPLOADED)
    → extract text → chunk → embed → ingest into ChromaDB → COMPLETED
    """
    # --- 1. Validate filename / extension ---
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename missing in request.",
        )

    _, ext = os.path.splitext(file.filename)
    ext_lower = ext.lower()

    if ext_lower not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{ext}'. Only PDF and DOCX files are allowed.",
        )

    # --- 2. Read bytes + size validation ---
    contents = await file.read()
    file_size = len(contents)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    if file_size > config.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size} bytes) exceeds the 10 MB limit.",
        )

    # --- 3. Save to disk with unique filename ---
    unique_id = str(uuid.uuid4())
    stored_filename = f"{unique_id}{ext_lower}"
    relative_storage_path = f"storage/{stored_filename}"
    absolute_storage_path = os.path.join(config.STORAGE_DIR, stored_filename)

    try:
        with open(absolute_storage_path, "wb") as f:
            f.write(contents)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file to storage.",
        ) from exc

    file_type = ext_lower.lstrip(".")

    # --- 4. Create PostgreSQL record (status = UPLOADED) ---
    db_document = crud.create_uploaded_document(
        db=db,
        name=file.filename,
        stored_file_path=relative_storage_path,
        file_type=file_type,
        file_size=file_size,
    )
    doc_id = db_document.id
    logger.info("[Upload] document_id=%d name='%s' saved to disk.", doc_id, file.filename)

    # --- 5. Processing (extraction → chunking → embedding → ChromaDB) ---
    crud.update_document_status(db=db, document_id=doc_id, status=schemas.ProcessingStatus.PROCESSING.value)

    try:
        # The ingestion component owns extraction -> chunking -> embedding ->
        # vector replacement.  A document is not marked complete until it
        # returns successfully.
        extracted_text = ingestion.index_document(
            document_id=doc_id,
            filename=file.filename,
            file_path=absolute_storage_path,
            file_type=file_type,
        )

        # Persist extracted text and mark COMPLETED only after vector storage.
        updated = crud.update_document_status(
            db=db,
            document_id=doc_id,
            status=schemas.ProcessingStatus.COMPLETED.value,
            extracted_text=extracted_text,
        )
        logger.info("[Upload] document_id=%d processing COMPLETED.", doc_id)
        return updated

    except Exception as exc:
        logger.error("[Upload] document_id=%d processing FAILED: %s", doc_id, exc)
        failed = crud.update_document_status(
            db=db,
            document_id=doc_id,
            status=schemas.ProcessingStatus.FAILED.value,
        )
        return failed


# ---------------------------------------------------------------------------
# Document metadata CRUD  (Phase 1 / Phase 2 preserved)
# ---------------------------------------------------------------------------

@app.post(
    "/documents",
    response_model=schemas.DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_document(
    document: schemas.DocumentCreate,
    db: Session = Depends(database.get_db),
):
    """Create a metadata-only document (Phase 1 legacy endpoint)."""
    return crud.create_document(db=db, document=document)


@app.get(
    "/documents",
    response_model=List[schemas.DocumentResponse],
    status_code=status.HTTP_200_OK,
)
def get_documents(db: Session = Depends(database.get_db)):
    """Retrieve all documents from PostgreSQL."""
    return crud.get_documents(db=db)


@app.get(
    "/documents/{document_id}",
    response_model=schemas.DocumentResponse,
    status_code=status.HTTP_200_OK,
)
def get_document(document_id: int, db: Session = Depends(database.get_db)):
    """Retrieve a single document by ID."""
    db_document = crud.get_document(db=db, document_id=document_id)
    if not db_document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return db_document


@app.patch(
    "/documents/{document_id}",
    response_model=schemas.DocumentResponse,
    status_code=status.HTTP_200_OK,
)
def update_document(
    document_id: int,
    document_update: schemas.DocumentUpdate,
    db: Session = Depends(database.get_db),
):
    """Update a document's name."""
    updated = crud.update_document(db=db, document_id=document_id, document_update=document_update)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return updated


@app.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_200_OK,
)
def delete_document(document_id: int, db: Session = Depends(database.get_db)):
    """
    Delete a document.

    Deletion order
    --------------
    1. Verify document exists in PostgreSQL.
    2. Remove associated ChromaDB vectors. If this fails, abort before
       changing PostgreSQL or the file store so orphan vectors are not hidden.
    3. Remove binary file from storage/.
    4. Delete PostgreSQL row.
    """
    db_document = crud.get_document(db=db, document_id=document_id)
    if not db_document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # 2. Delete ChromaDB vectors first. There is no distributed transaction,
    # but a vector-store failure is a safe precondition failure: the document
    # record and binary file are still intact and the caller can retry.
    try:
        vector_store.delete_document_chunks(document_id)
    except Exception as exc:
        logger.error(
            "[Delete] ChromaDB vector deletion failed for document_id=%d: %s. No document data was deleted.",
            document_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to delete document vectors. No document data was deleted; retry the request.",
        ) from exc

    # 3. Delete file from storage
    if db_document.stored_file_path:
        abs_path = os.path.join(os.path.dirname(__file__), db_document.stored_file_path)
        if os.path.exists(abs_path):
            try:
                os.remove(abs_path)
            except Exception as exc:
                logger.error(
                    "[Delete] Failed to remove file %s for document_id=%d: %s. Attempting vector restoration.",
                    abs_path,
                    document_id,
                    exc,
                )
                try:
                    ingestion.index_document(
                        document_id=document_id,
                        filename=db_document.name,
                        file_path=abs_path,
                        file_type=db_document.file_type,
                    )
                except Exception as restore_exc:
                    logger.error(
                        "[Delete] Vector restoration also failed for document_id=%d: %s",
                        document_id,
                        restore_exc,
                    )
                    crud.update_document_status(
                        db, document_id, schemas.ProcessingStatus.FAILED.value
                    )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Document file could not be deleted. The document metadata was retained.",
                ) from exc

    # 4. Delete PostgreSQL row
    try:
        crud.delete_document(db=db, document_id=document_id)
    except Exception as exc:
        logger.error(
            "[Delete] PostgreSQL deletion failed for document_id=%d after file/vector cleanup: %s",
            document_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document metadata deletion failed after cleanup; manual reconciliation is required.",
        ) from exc
    logger.info("[Delete] document_id=%d fully deleted.", document_id)

    return {"message": "Document deleted successfully", "id": document_id}
