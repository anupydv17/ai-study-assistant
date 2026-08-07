"""Password hashing and access tokens.

We never store a password. We store a bcrypt hash, which is a one-way
transformation: you can check whether a guess matches it, but you cannot turn
it back into the original password.

Access tokens are JWTs. They are *signed*, not encrypted — anyone can read the
contents, but nobody can change them without the SECRET_KEY.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings

# bcrypt only reads the first 72 bytes of input. Schemas enforce this limit so
# two different long passwords can never collide into the same hash.
MAX_PASSWORD_BYTES = 72


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password for storage."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain-text password against a stored hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(subject: str) -> str:
    """Create a signed token identifying `subject` (we use the user's email)."""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": subject,   # "subject" — who this token belongs to
        "iat": now,       # "issued at"
        "exp": expires_at,  # "expires" — PyJWT rejects the token after this
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@dataclass(frozen=True)
class TokenData:
    """The trustworthy contents of a verified access token."""

    subject: str
    issued_at: datetime


def decode_access_token(token: str) -> TokenData | None:
    """Return a verified token's contents, or None if it cannot be trusted.

    Returns None for a forged signature, an expired token, or malformed input.
    The caller decides what that means in HTTP terms.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except jwt.PyJWTError:
        return None

    subject = payload.get("sub")
    issued_at = payload.get("iat")

    if not subject or not issued_at:
        return None

    return TokenData(
        subject=subject,
        issued_at=datetime.fromtimestamp(issued_at, tz=timezone.utc),
    )
