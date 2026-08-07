"""Database operations for chat messages.

Every function takes a document_id. Callers are expected to have already
confirmed the user owns that document — the guard in the API layer does this
once, so it cannot be forgotten per-endpoint.
"""

from sqlalchemy.orm import Session

from app.models.chat import ChatMessage, MessageRole


def add_message(
    db: Session,
    *,
    document_id: int,
    role: MessageRole,
    content: str,
    commit: bool = True,
) -> ChatMessage:
    """Append one message to a document's conversation."""
    message = ChatMessage(document_id=document_id, role=role, content=content)
    db.add(message)

    if commit:
        db.commit()
        db.refresh(message)

    return message


def list_messages(db: Session, document_id: int) -> list[ChatMessage]:
    """Return the whole conversation, oldest first."""
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.document_id == document_id)
        .order_by(ChatMessage.created_at, ChatMessage.id)
        .all()
    )


def recent_messages(db: Session, document_id: int, limit: int) -> list[ChatMessage]:
    """Return the last `limit` messages, oldest first.

    We ask the database for the newest rows, then reverse them, so the AI
    receives the conversation in chronological order.
    """
    newest_first = (
        db.query(ChatMessage)
        .filter(ChatMessage.document_id == document_id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(limit)
        .all()
    )

    return list(reversed(newest_first))


def clear_messages(db: Session, document_id: int) -> int:
    """Delete a document's whole conversation. Returns how many were removed."""
    deleted = (
        db.query(ChatMessage)
        .filter(ChatMessage.document_id == document_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted
