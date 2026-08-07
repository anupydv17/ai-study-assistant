"""Reading text out of PDF files.

Like storage.py, this module knows nothing about HTTP. It raises plain Python
exceptions and the API layer decides what they mean to a client.
"""

from dataclasses import dataclass
from pathlib import Path

import pymupdf


class PDFExtractionError(Exception):
    """The PDF could not be opened or read."""


@dataclass(frozen=True)
class ExtractedContent:
    """The result of reading a PDF."""

    text: str
    page_count: int

    @property
    def is_empty(self) -> bool:
        """True when the PDF held no machine-readable text.

        Usually means the pages are scanned images rather than real text.
        """
        return not self.text.strip()


def extract_text(path: Path) -> ExtractedContent:
    """Read every page of a PDF and return its text and page count."""
    try:
        document = pymupdf.open(path)
    except Exception as exc:
        raise PDFExtractionError("The file could not be opened as a PDF.") from exc

    with document:
        if document.needs_pass:
            raise PDFExtractionError("The PDF is password protected.")

        pages = [page.get_text() for page in document]
        page_count = document.page_count

    # Two newlines between pages keeps paragraph boundaries readable, which
    # matters later when we feed this to a language model.
    return ExtractedContent(text="\n\n".join(pages).strip(), page_count=page_count)
