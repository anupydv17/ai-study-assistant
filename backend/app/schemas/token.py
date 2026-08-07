"""Schemas for authentication tokens."""

from pydantic import BaseModel


class Token(BaseModel):
    """The response returned by a successful login.

    `token_type` is part of the OAuth2 standard. Clients send the token back
    as the header:  Authorization: Bearer <access_token>
    """

    access_token: str
    token_type: str = "bearer"
