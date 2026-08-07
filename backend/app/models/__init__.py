"""Database models.

Importing every model here guarantees they are registered on Base.metadata
before create_all() runs. A model that is never imported is invisible to
SQLAlchemy, and its table silently never gets created.
"""

from app.models.chat import ChatMessage, MessageRole
from app.models.document import Document
from app.models.study import StudyItem, StudyItemKind
from app.models.user import User

__all__ = [
    "ChatMessage",
    "Document",
    "MessageRole",
    "StudyItem",
    "StudyItemKind",
    "User",
]
