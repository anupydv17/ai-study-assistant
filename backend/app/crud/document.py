"""Database operations for documents.

Every read here takes an owner_id and filters by it. That is deliberate: it
makes it impossible to fetch a document by id alone and accidentally hand one
user another user's file.
"""

from sqlalchemy.orm import Session

from app.models.document import Document


def create_document(
    db: Session,
    *,
    owner_id: int,
    original_filename: str,
    stored_filename: str,
    size_bytes: int,
    extracted_text: str,
    page_count: int,
) -> Document:
    """Insert a row describing a newly uploaded file."""
    document = Document(
        owner_id=owner_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_size_bytes=size_bytes,
        extracted_text=extracted_text,
        page_count=page_count,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def list_for_owner(db: Session, owner_id: int) -> list[Document]:
    """Return every document belonging to one user, newest first."""
    return (
        db.query(Document)
        .filter(Document.owner_id == owner_id)
        .order_by(Document.created_at.desc())
        .all()
    )


def delete_document(db: Session, document: Document) -> None:
    """Delete a document row.

    Cascades remove its chat messages and study items automatically. The file
    on disk is the caller's responsibility — the database knows nothing about
    the filesystem.
    """
    db.delete(document)
    db.commit()


def get_for_owner(db: Session, document_id: int, owner_id: int) -> Document | None:
    """Return one document, but only if this user owns it.

    Filtering on owner_id as well as id is the whole defence against one user
    reading another's documents.
    """
    return (
        db.query(Document)
        .filter(Document.id == document_id, Document.owner_id == owner_id)
        .first()
    )
