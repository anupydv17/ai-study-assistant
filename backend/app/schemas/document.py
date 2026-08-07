"""Pydantic schemas for documents."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    """A document as returned by the API.

    Note what is missing: stored_filename and owner_id. Clients have no
    business knowing where the file sits on our disk.

    The full extracted text is missing too — it can be hundreds of thousands
    of characters, and a document list would be enormous. It has its own
    endpoint instead.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    file_size_bytes: int
    page_count: int | None
    has_text: bool
    created_at: datetime


class DocumentTextRead(BaseModel):
    """The extracted text of a single document."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    page_count: int | None
    character_count: int
    extracted_text: str
