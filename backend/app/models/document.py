"""Document database model.

The file itself lives on disk. This table stores everything *about* the file,
plus a pointer to where it was saved.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:  # imported only for type hints, never at runtime
    from app.models.chat import ChatMessage
    from app.models.study import StudyItem
    from app.models.user import User


class Document(Base):
    """A PDF uploaded by a user."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)

    # What the user called it — shown in the UI.
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)

    # What we called it on disk — a random name, so two users uploading
    # "notes.pdf" never collide and nobody can guess a path.
    stored_filename: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )

    file_size_bytes: Mapped[int] = mapped_column(nullable=False)

    # Filled in by Milestone 7, so they must be optional for now.
    page_count: Mapped[int | None] = mapped_column(default=None)
    extracted_text: Mapped[str | None] = mapped_column(Text, default=None)

    # The link back to the owner. This is what makes the document "yours".
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="documents")

    # Deleting a document deletes its conversation too.
    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )

    # Deleting a document deletes its saved study material too.
    study_items: Mapped[list["StudyItem"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="StudyItem.created_at.desc()",
    )

    @property
    def has_text(self) -> bool:
        """True when extraction found readable text (scanned PDFs give none)."""
        return bool(self.extracted_text and self.extracted_text.strip())

    def __repr__(self) -> str:
        return f"<Document id={self.id} name={self.original_filename!r}>"
