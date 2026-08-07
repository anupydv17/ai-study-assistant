"""Tests for registration, login and the current-user endpoint."""

from fastapi.testclient import TestClient

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
ME = "/api/v1/users/me"


def test_register_creates_a_user(client: TestClient) -> None:
    response = client.post(
        REGISTER,
        json={
            "email": "new@example.com",
            "full_name": "New Person",
            "password": "GoodPassword1",
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["full_name"] == "New Person"
    assert "id" in body


def test_register_never_returns_a_password(client: TestClient) -> None:
    """The response schema must not leak the password in any form."""
    response = client.post(
        REGISTER,
        json={
            "email": "leak@example.com",
            "full_name": "Leak Test",
            "password": "GoodPassword1",
        },
    )

    body = response.json()
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_rejects_a_duplicate_email(client: TestClient) -> None:
    payload = {
        "email": "taken@example.com",
        "full_name": "First",
        "password": "GoodPassword1",
    }
    client.post(REGISTER, json=payload)

    response = client.post(REGISTER, json={**payload, "full_name": "Second"})

    assert response.status_code == 409


def test_register_rejects_an_invalid_email(client: TestClient) -> None:
    response = client.post(
        REGISTER,
        json={
            "email": "not-an-email",
            "full_name": "Nobody",
            "password": "GoodPassword1",
        },
    )

    assert response.status_code == 422


def test_register_rejects_a_short_password(client: TestClient) -> None:
    response = client.post(
        REGISTER,
        json={"email": "short@example.com", "full_name": "Nobody", "password": "abc"},
    )

    assert response.status_code == 422


def test_login_returns_a_token(client: TestClient) -> None:
    client.post(
        REGISTER,
        json={
            "email": "login@example.com",
            "full_name": "Login Test",
            "password": "GoodPassword1",
        },
    )

    response = client.post(
        LOGIN, data={"username": "login@example.com", "password": "GoodPassword1"}
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_with_a_wrong_password_is_rejected(client: TestClient) -> None:
    client.post(
        REGISTER,
        json={
            "email": "wrong@example.com",
            "full_name": "Wrong Pass",
            "password": "GoodPassword1",
        },
    )

    response = client.post(
        LOGIN, data={"username": "wrong@example.com", "password": "NotThePassword"}
    )

    assert response.status_code == 401


def test_login_does_not_reveal_whether_an_account_exists(client: TestClient) -> None:
    """Wrong password and unknown account must be indistinguishable.

    If these messages differed, an attacker could discover which emails are
    registered.
    """
    client.post(
        REGISTER,
        json={
            "email": "real@example.com",
            "full_name": "Real",
            "password": "GoodPassword1",
        },
    )

    wrong_password = client.post(
        LOGIN, data={"username": "real@example.com", "password": "WrongPassword1"}
    )
    no_such_user = client.post(
        LOGIN, data={"username": "ghost@example.com", "password": "GoodPassword1"}
    )

    assert wrong_password.status_code == no_such_user.status_code == 401
    assert wrong_password.json() == no_such_user.json()


def test_me_requires_a_token(client: TestClient) -> None:
    assert client.get(ME).status_code == 401


def test_me_rejects_a_tampered_token(client: TestClient, auth_header: str) -> None:
    response = client.get(ME, headers={"Authorization": auth_header + "x"})

    assert response.status_code == 401


def test_me_returns_the_logged_in_user(client: TestClient, auth_header: str) -> None:
    response = client.get(ME, headers={"Authorization": auth_header})

    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.com"
