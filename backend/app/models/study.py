"""Study item database model.

One table stores every kind of AI-generated material. The `kind` column says
what it is, and `content` holds the payload as JSON — which lets a quiz and a
summary live in the same table despite having nothing structurally in common.
"""

from datetime import datetime, timezone
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.document import Document


class StudyItemKind(StrEnum):
    """What kind of material an item holds."""

    SUMMARY = "summary"
    QUIZ = "quiz"
    FLASHCARDS = "flashcards"


class StudyItem(Base):
    """One piece of AI-generated study material, saved for later."""

    __tablename__ = "study_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    kind: Mapped[StudyItemKind] = mapped_column(String(20), index=True, nullable=False)

    # The generated payload. SQLAlchemy serialises this to JSON text on SQLite
    # and to a real JSON column on PostgreSQL — same Python code either way.
    content: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Which model produced it. Results from different models are not
    # comparable, so recording this makes the history honest.
    model: Mapped[str] = mapped_column(String(64), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), index=True, nullable=False
    )

    document: Mapped["Document"] = relationship(back_populates="study_items")

    def __repr__(self) -> str:
        return f"<StudyItem id={self.id} kind={self.kind}>"
