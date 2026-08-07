"""Database operations for users.

This layer talks to the database and nothing else — no HTTP, no status codes,
no knowledge that a web request exists. That keeps it reusable and easy to
test in isolation.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


def get_user_by_email(db: Session, email: str) -> User | None:
    """Return the user with this email, or None if there isn't one."""
    return db.query(User).filter(User.email == email).first()


def update_user(db: Session, user: User, *, full_name: str) -> User:
    """Update a user's editable profile fields."""
    user.full_name = full_name

    db.commit()
    db.refresh(user)

    return user


def change_password(db: Session, user: User, *, new_password: str) -> User:
    """Set a new password and invalidate every token issued before now."""
    user.hashed_password = hash_password(new_password)
    user.password_changed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(user)

    return user


def delete_user(db: Session, user: User) -> None:
    """Delete a user. Cascades remove their documents, chats and study items."""
    db.delete(user)
    db.commit()


def authenticate(db: Session, email: str, password: str) -> User | None:
    """Return the user if the email exists and the password matches.

    Returns None for both "no such user" and "wrong password" on purpose. The
    caller must not reveal which one failed — see the login endpoint.
    """
    user = get_user_by_email(db, email)
    if user is None:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def create_user(db: Session, user_in: UserCreate) -> User:
    """Insert a new user, storing only the hashed password."""
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hash_password(user_in.password),
    )

    db.add(user)      # stage the row
    db.commit()       # write it permanently
    db.refresh(user)  # reload it so id and created_at are populated

    return user
