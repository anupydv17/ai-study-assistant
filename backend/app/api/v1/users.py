"""User endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud import document as document_crud
from app.crud import user as user_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import PasswordChange, UserRead, UserUpdate
from app.services import storage

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get the currently logged-in user",
)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserRead:
    """Return the profile of whoever owns the access token.

    The single Depends() above is what makes this endpoint private. No token,
    no response.
    """
    return current_user


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update your profile",
)
def update_current_user(
    updates: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """Update the logged-in user's editable fields."""
    return user_crud.update_user(db, current_user, full_name=updates.full_name)


@router.post(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change your password",
)
def change_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Change the logged-in user's password.

    The current password is required even though the request is already
    authenticated. A valid token proves the request came from a logged-in
    session — not that the session belongs to the real account owner. Without
    this check, anyone who stole a token could lock the owner out permanently.
    """
    if not user_crud.authenticate(
        db, email=current_user.email, password=payload.current_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your current password is incorrect.",
        )

    if payload.new_password == payload.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The new password must be different from the current one.",
        )

    user_crud.change_password(db, current_user, new_password=payload.new_password)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete your account and all of your data",
)
def delete_current_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Permanently delete the account, its documents, and its files."""
    # Collect the filenames before the rows disappear, then remove the files
    # once the database delete has succeeded.
    documents = document_crud.list_for_owner(db, owner_id=current_user.id)
    stored_filenames = [document.stored_filename for document in documents]

    user_crud.delete_user(db, current_user)

    for stored_filename in stored_filenames:
        storage.delete_file(stored_filename)
