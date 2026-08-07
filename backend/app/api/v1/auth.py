"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.crud import user as user_crud
from app.db.session import get_db
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    """Register a new user.

    Fails with 409 Conflict if the email is already taken.
    """
    if user_crud.get_user_by_email(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    return user_crud.create_user(db, user_in)


@router.post(
    "/login",
    response_model=Token,
    summary="Exchange email and password for an access token",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """Log in and receive a JWT access token.

    The OAuth2 standard names the field `username`; we put the email in it.
    """
    user = user_crud.authenticate(
        db,
        email=form_data.username,
        password=form_data.password,
    )

    if user is None:
        # Deliberately vague: saying "no such user" would let an attacker
        # discover which emails are registered.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(access_token=create_access_token(subject=user.email))
