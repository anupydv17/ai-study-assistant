"""Tests for profile updates, password changes and account deletion."""

from fastapi.testclient import TestClient

ME = "/api/v1/users/me"
PASSWORD = "/api/v1/users/me/password"
LOGIN = "/api/v1/auth/login"


def test_update_changes_the_name(client: TestClient, auth_header: str) -> None:
    response = client.patch(
        ME, headers={"Authorization": auth_header}, json={"full_name": "Alice Updated"}
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Alice Updated"


def test_password_change_requires_the_current_password(
    client: TestClient, auth_header: str
) -> None:
    """Without this rule, a stolen token could lock the real owner out."""
    response = client.post(
        PASSWORD,
        headers={"Authorization": auth_header},
        json={"current_password": "TotallyWrong", "new_password": "BrandNewPass1"},
    )

    assert response.status_code == 400


def test_password_change_updates_the_password(
    client: TestClient, auth_header: str
) -> None:
    client.post(
        PASSWORD,
        headers={"Authorization": auth_header},
        json={"current_password": "TestPass123", "new_password": "BrandNewPass1"},
    )

    old = client.post(
        LOGIN, data={"username": "alice@example.com", "password": "TestPass123"}
    )
    new = client.post(
        LOGIN, data={"username": "alice@example.com", "password": "BrandNewPass1"}
    )

    assert old.status_code == 401
    assert new.status_code == 200


def test_password_change_invalidates_existing_tokens(
    client: TestClient, auth_header: str
) -> None:
    """The token that made the change must stop working afterwards.

    This is what logs a stolen session out.
    """
    assert client.get(ME, headers={"Authorization": auth_header}).status_code == 200

    client.post(
        PASSWORD,
        headers={"Authorization": auth_header},
        json={"current_password": "TestPass123", "new_password": "BrandNewPass1"},
    )

    assert client.get(ME, headers={"Authorization": auth_header}).status_code == 401


def test_delete_account_removes_the_user(client: TestClient, auth_header: str) -> None:
    assert (
        client.delete(ME, headers={"Authorization": auth_header}).status_code == 204
    )

    # The token is validly signed, but the account behind it is gone.
    assert client.get(ME, headers={"Authorization": auth_header}).status_code == 401


def test_delete_account_removes_the_users_documents(
    client: TestClient, auth_header: str, pdf_bytes: bytes, session
) -> None:
    from app.models import Document

    client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": auth_header},
        files={"file": ("notes.pdf", pdf_bytes, "application/pdf")},
    )
    assert session.query(Document).count() == 1

    client.delete(ME, headers={"Authorization": auth_header})

    assert session.query(Document).count() == 0
