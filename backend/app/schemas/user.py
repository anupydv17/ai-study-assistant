"""Pydantic schemas for user data.

Schemas describe the shape of data crossing the API boundary. They are kept
separate from the SQLAlchemy model on purpose: the database row holds a
hashed_password, and that must never appear in a response.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.security import MAX_PASSWORD_BYTES


class UserCreate(BaseModel):
    """What a client must send to register an account."""

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=MAX_PASSWORD_BYTES)


class UserUpdate(BaseModel):
    """Fields a user may change about themselves.

    Email is not here on purpose. Changing an email is an account-recovery
    path, so it needs a confirmation link sent to the new address — otherwise
    a stolen session could quietly take the account over. That is a feature of
    its own, not a form field.
    """

    full_name: str = Field(min_length=1, max_length=100)


class PasswordChange(BaseModel):
    """A password change request.

    current_password is required even though the user is already logged in.
    See the endpoint for why.
    """

    current_password: str = Field(min_length=1, max_length=MAX_PASSWORD_BYTES)
    new_password: str = Field(min_length=8, max_length=MAX_PASSWORD_BYTES)


class UserRead(BaseModel):
    """What we send back after registering.

    There is no password field of any kind here, so a password can never leak
    through this schema even if someone passes in a full database row.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    created_at: datetime
