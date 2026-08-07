"""Document upload and listing endpoints."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud import document as document_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.document import DocumentRead, DocumentTextRead
from app.services import pdf, storage

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF",
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentRead:
    """Store a PDF and record it against the logged-in user."""
    try:
        stored = await storage.save_pdf(file)
    except storage.NotAPDFError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except storage.FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)
        ) from exc

    try:
        content = pdf.extract_text(storage.path_for(stored.stored_filename))
    except pdf.PDFExtractionError as exc:
        storage.delete_file(stored.stored_filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    try:
        return document_crud.create_document(
            db,
            owner_id=current_user.id,
            original_filename=file.filename or "untitled.pdf",
            stored_filename=stored.stored_filename,
            size_bytes=stored.size_bytes,
            extracted_text=content.text,
            page_count=content.page_count,
        )
    except Exception:
        # The file is on disk but the row failed. Remove the file so we never
        # accumulate uploads that nothing points at.
        storage.delete_file(stored.stored_filename)
        raise


@router.get(
    "",
    response_model=list[DocumentRead],
    summary="List your uploaded PDFs",
)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DocumentRead]:
    """Return every document belonging to the logged-in user."""
    return document_crud.list_for_owner(db, owner_id=current_user.id)


@router.get(
    "/{document_id}",
    response_model=DocumentRead,
    summary="Get one of your PDFs",
)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentRead:
    """Return a single document, provided the logged-in user owns it."""
    document = document_crud.get_for_owner(
        db, document_id=document_id, owner_id=current_user.id
    )

    if document is None:
        # 404 rather than 403: telling someone "this exists but is not yours"
        # confirms the document exists. Say nothing.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    return document


@router.get(
    "/{document_id}/text",
    response_model=DocumentTextRead,
    summary="Get the extracted text of one of your PDFs",
)
def get_document_text(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentTextRead:
    """Return the text extracted from a document at upload time."""
    document = document_crud.get_for_owner(
        db, document_id=document_id, owner_id=current_user.id
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    if not document.has_text:
        # The upload worked, but there is nothing to read — almost always a
        # scanned PDF. 422 says "understood the request, cannot fulfil it".
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "This PDF contains no readable text. It is most likely a "
                "scan, which would need OCR."
            ),
        )

    return DocumentTextRead(
        id=document.id,
        original_filename=document.original_filename,
        page_count=document.page_count,
        character_count=len(document.extracted_text or ""),
        extracted_text=document.extracted_text or "",
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete one of your PDFs",
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a document, its file on disk, and everything derived from it."""
    document = document_crud.get_for_owner(
        db, document_id=document_id, owner_id=current_user.id
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    stored_filename = document.stored_filename

    # Row first. If deleting the file failed after the row was already gone we
    # would have an orphan file; if the row delete fails we still have both,
    # which is the recoverable direction.
    document_crud.delete_document(db, document)
    storage.delete_file(stored_filename)
