"""Document endpoints (metadata CRUD + upload + delete)."""

from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.models.user import User
from app.schemas.documents import DocumentCreate, DocumentResponse, DocumentUpdate
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=List[DocumentResponse], status_code=status.HTTP_200_OK)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DocumentResponse]:
    """Retrieve only documents owned by the authenticated user."""
    items = document_service.list_documents(db=db, user_id=current_user.id)
    return [DocumentResponse.model_validate(item) for item in items]


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document_metadata(
    payload: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    """Create a metadata-only document for the authenticated user."""
    item = document_service.create_metadata_document(
        db=db, user_id=current_user.id, payload=payload
    )
    return DocumentResponse.model_validate(item)


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    item = document_service.get_document(
        db=db, user_id=current_user.id, document_id=document_id
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentResponse.model_validate(item)


@router.patch(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
)
def rename_document(
    document_id: int,
    payload: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    updated = document_service.rename_document(
        db=db, user_id=current_user.id, document_id=document_id, payload=payload
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentResponse.model_validate(updated)


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document using the documented safety ordering."""
    try:
        result = document_service.delete_document(
            db=db, user_id=current_user.id, document_id=document_id
        )
    except document_service.VectorStoreUnavailable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to delete document vectors. No document data was deleted; retry the request.",
        )
    except document_service.FileDeletionFailed:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document file could not be deleted. The document metadata was retained.",
        )
    except document_service.MetadataDeletionFailed:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document metadata deletion failed after cleanup; manual reconciliation is required.",
        )

    if result == -1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return {"message": "Document deleted successfully", "id": document_id}


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    """
    Upload a PDF or DOCX file.

    Pipeline
    --------
    validate → store on disk → register in PostgreSQL (UPLOADED)
    → extract text → chunk → embed → ingest into ChromaDB → COMPLETED
    """
    try:
        item = await document_service.upload_document(
            db=db, user_id=current_user.id, file=file
        )
    except ValueError as exc:
        # Validation errors (extension / size / missing filename). Map
        # by message prefix to the original status codes.
        message = str(exc)
        if "Unsupported file type" in message:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=message
            )
        if "exceeds the 10 MB limit" in message:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=message
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return DocumentResponse.model_validate(item)
