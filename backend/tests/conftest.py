"""Shared test fixtures.

pytest finds this file automatically. Anything defined here is available to
every test without importing it.

Two rules drive the whole setup:
  1. Tests must never touch the real database or the real uploads folder.
  2. Tests must never call Gemini — that costs money and would make results
     depend on a network connection.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# `from app import models` (not `import app.models`) is deliberate: the latter
# would rebind the name `app` to the package and clobber the FastAPI instance
# imported below. Importing models registers every table on Base.metadata.
from app import models  # noqa: F401
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """A fresh, empty, in-memory database for one test.

    "sqlite://" with no path means in-memory. StaticPool keeps a single
    connection alive so the tables survive between calls — without it, each
    connection would get its own blank database.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with TestingSessionLocal() as session:
        yield session

    Base.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(
    session: Session, tmp_path, monkeypatch
) -> Generator[TestClient, None, None]:
    """A test client wired to the throwaway database and a temp upload folder.

    dependency_overrides is FastAPI's built-in seam for exactly this: swap a
    dependency for a test version without changing any application code.
    """

    def get_db_override():
        return session

    app.dependency_overrides[get_db] = get_db_override

    # Uploads land in a per-test temp directory, so tests never write into
    # backend/uploads and never see each other's files.
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

    # Note: TestClient is NOT used as a context manager here, so the lifespan
    # handler does not run and create_tables() never touches the real engine.
    yield TestClient(app)

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def register_and_login(client: TestClient, email: str, password: str = "TestPass123") -> str:
    """Create a user and return an Authorization header value."""
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": password},
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    return f"Bearer {response.json()['access_token']}"


@pytest.fixture(name="auth_header")
def auth_header_fixture(client: TestClient) -> str:
    """A logged-in user, as an Authorization header."""
    return register_and_login(client, "alice@example.com")


@pytest.fixture(name="other_auth_header")
def other_auth_header_fixture(client: TestClient) -> str:
    """A second, unrelated logged-in user — used to test isolation."""
    return register_and_login(client, "mallory@example.com")


@pytest.fixture(name="pdf_bytes")
def pdf_bytes_fixture() -> bytes:
    """A small but genuinely valid PDF containing readable text."""
    import pymupdf

    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((60, 80), "The Calvin cycle takes place in the stroma.", fontsize=12)
    data = document.tobytes()
    document.close()
    return data
