"""Dependencies shared across API endpoints.

`get_current_user` is the gate: any endpoint that depends on it becomes
protected, and any endpoint that does not stays public.
"""

from datetime import timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.crud import user as user_crud
from app.db.session import get_db
from app.models.user import User

# Tells FastAPI where tokens come from. This is also what puts the
# "Authorize" button into the /docs page.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the Authorization header into a real User row.

    Raises 401 if the token is missing, forged, expired, or points at a user
    who no longer exists.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = decode_access_token(token)
    if token_data is None:
        raise credentials_error

    user = user_crud.get_user_by_email(db, token_data.subject)
    if user is None:
        # The token is validly signed, but the account was deleted since.
        raise credentials_error

    # A token issued before the last password change is no longer trusted.
    # This is what makes "change my password" actually log other sessions out.
    if user.password_changed_at is not None:
        changed_at = user.password_changed_at
        if changed_at.tzinfo is None:
            # SQLite returns naive datetimes; treat them as UTC.
            changed_at = changed_at.replace(tzinfo=timezone.utc)

        if token_data.issued_at < changed_at:
            raise credentials_error

    return user
