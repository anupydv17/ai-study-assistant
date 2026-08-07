"""User database model."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:  # imported only for type hints, never at runtime
    from app.models.document import Document


class User(Base):
    """A registered user of the application."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Lets an account be disabled without deleting it and losing their notes.
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Never store the raw password. The name makes the intent impossible to
    # misread when someone reads this model six months from now.
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # When the password was last changed. Any token issued before this moment
    # is refused, which is how a password change logs out stolen sessions.
    # Null for accounts that have never changed their password.
    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    # Deleting a user deletes their documents too — no orphaned rows.
    documents: Mapped[list["Document"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
