"""Database engine and session management.

The engine is the connection pool to the database — created once, shared by
the whole application. Sessions are short-lived workspaces created per
request and closed as soon as the request finishes.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# SQLite refuses to share a connection between threads by default, but FastAPI
# handles requests on multiple threads. This flag relaxes that check.
# PostgreSQL does not need it, so we only apply it for SQLite.
connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,  # print every SQL statement while developing
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """Provide a database session to a request, then always close it.

    FastAPI calls this for any endpoint that declares `db: Session =
    Depends(get_db)`. The code after `yield` runs once the response has been
    sent, so connections are never leaked — even if the endpoint raises.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
