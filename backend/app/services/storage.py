"""Saving uploaded PDFs to disk.

This module knows about files and nothing about HTTP. It raises plain Python
exceptions; the API layer decides which status code each one deserves.
"""

import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

# Every real PDF file begins with these five bytes, whatever it is named.
PDF_MAGIC = b"%PDF-"

# Stream the upload in 1 MB pieces so a large file never sits in memory whole.
CHUNK_SIZE = 1024 * 1024


class NotAPDFError(Exception):
    """The upload is not a PDF, regardless of its filename."""


class FileTooLargeError(Exception):
    """The upload exceeded MAX_UPLOAD_SIZE_MB."""


@dataclass(frozen=True)
class StoredFile:
    """The result of saving an upload."""

    stored_filename: str
    size_bytes: int


def upload_dir() -> Path:
    """Return the upload folder, creating it if this is the first run."""
    directory = Path(settings.UPLOAD_DIR)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def path_for(stored_filename: str) -> Path:
    """Return the full path of a stored file."""
    return upload_dir() / stored_filename


async def save_pdf(upload: UploadFile) -> StoredFile:
    """Validate an uploaded PDF and stream it to disk.

    Raises NotAPDFError or FileTooLargeError. On any failure the partial file
    is removed, so a rejected upload never leaves rubbish behind.
    """
    # Check the file's actual contents, not the name the browser sent.
    header = await upload.read(len(PDF_MAGIC))
    if header != PDF_MAGIC:
        raise NotAPDFError("File contents are not a PDF.")

    # A random name: no collisions between users, and nothing guessable.
    stored_filename = f"{uuid.uuid4().hex}.pdf"
    destination = path_for(stored_filename)

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    size = len(header)

    try:
        with destination.open("wb") as out:
            out.write(header)

            while chunk := await upload.read(CHUNK_SIZE):
                size += len(chunk)
                if size > max_bytes:
                    raise FileTooLargeError(
                        f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit."
                    )
                out.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise

    return StoredFile(stored_filename=stored_filename, size_bytes=size)


def delete_file(stored_filename: str) -> None:
    """Remove a stored file, ignoring the case where it is already gone."""
    path_for(stored_filename).unlink(missing_ok=True)
