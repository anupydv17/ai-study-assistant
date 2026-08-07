"""Chat message database model.

One row per turn of conversation. Questions and answers are stored the same
way, distinguished by `role`, which is exactly how the AI provider expects a
conversation to be described.
"""

from datetime import datetime, timezone
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.document import Document


class MessageRole(StrEnum):
    """Who wrote a message.

    A StrEnum behaves like a string but only allows these two values, so a
    typo such as "assistent" fails immediately instead of silently creating a
    third kind of message.
    """

    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(Base):
    """A single question or answer in a document's conversation."""

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    role: Mapped[MessageRole] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    document: Mapped["Document"] = relationship(back_populates="chat_messages")

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id} role={self.role}>"
