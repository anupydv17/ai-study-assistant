"""Database operations for saved study material.

Study items belong to a document, and documents belong to a user. Every read
here joins through documents so ownership is enforced in the query itself,
exactly as it is for documents.
"""

from typing import Any

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.study import StudyItem, StudyItemKind


def create_item(
    db: Session,
    *,
    document_id: int,
    kind: StudyItemKind,
    content: dict[str, Any],
    model: str,
) -> StudyItem:
    """Save one piece of generated material."""
    item = StudyItem(
        document_id=document_id,
        kind=kind,
        content=content,
        model=model,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


def list_for_owner(
    db: Session,
    *,
    owner_id: int,
    kind: StudyItemKind | None = None,
    limit: int = 50,
) -> list[StudyItem]:
    """Return a user's saved material across all their documents, newest first.

    The join to Document is what scopes this to one user. Without it, this
    would return every study item in the system.
    """
    query = (
        db.query(StudyItem)
        .join(Document, StudyItem.document_id == Document.id)
        .filter(Document.owner_id == owner_id)
    )

    if kind is not None:
        query = query.filter(StudyItem.kind == kind)

    return query.order_by(StudyItem.created_at.desc(), StudyItem.id.desc()).limit(limit).all()


def list_for_document(
    db: Session,
    *,
    document_id: int,
    kind: StudyItemKind | None = None,
) -> list[StudyItem]:
    """Return saved material for one document, newest first.

    Callers must already have confirmed the user owns that document.
    """
    query = db.query(StudyItem).filter(StudyItem.document_id == document_id)

    if kind is not None:
        query = query.filter(StudyItem.kind == kind)

    return query.order_by(StudyItem.created_at.desc(), StudyItem.id.desc()).all()


def get_for_owner(db: Session, *, item_id: int, owner_id: int) -> StudyItem | None:
    """Return one saved item, but only if this user owns its document."""
    return (
        db.query(StudyItem)
        .join(Document, StudyItem.document_id == Document.id)
        .filter(StudyItem.id == item_id, Document.owner_id == owner_id)
        .first()
    )


def delete_item(db: Session, item: StudyItem) -> None:
    """Remove one saved item."""
    db.delete(item)
    db.commit()
