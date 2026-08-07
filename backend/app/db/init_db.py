"""Table creation — no longer used by the application.

Alembic owns the schema now. Deploys run `alembic upgrade head`.

This is kept only as a convenience for throwaway scripts. Never call it
against a database that holds real data: it creates missing tables but can
never ALTER an existing one, so it silently leaves the schema wrong.
"""

from app.db.base import Base
from app.db.session import engine

# Importing the models package registers every model on Base.metadata.
# Without this import, create_all() would find nothing to create.
import app.models  # noqa: F401


def create_tables() -> None:
    """Create all tables that do not already exist."""
    Base.metadata.create_all(bind=engine)
