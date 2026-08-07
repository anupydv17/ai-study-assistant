"""Tests for uploading, listing, reading and deleting documents.

The isolation tests in here are the most valuable in the suite: they are what
stops an IDOR bug reaching production.
"""

from fastapi.testclient import TestClient

UPLOAD = "/api/v1/documents/upload"
DOCUMENTS = "/api/v1/documents"


def upload(client: TestClient, auth_header: str, pdf_bytes: bytes, name: str = "notes.pdf"):
    return client.post(
        UPLOAD,
        headers={"Authorization": auth_header},
        files={"file": (name, pdf_bytes, "application/pdf")},
    )


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------


def test_upload_stores_a_pdf(client: TestClient, auth_header: str, pdf_bytes: bytes) -> None:
    response = upload(client, auth_header, pdf_bytes)

    assert response.status_code == 201

    body = response.json()
    assert body["original_filename"] == "notes.pdf"
    assert body["page_count"] == 1
    assert body["has_text"] is True


def test_upload_never_exposes_the_path_on_disk(
    client: TestClient, auth_header: str, pdf_bytes: bytes
) -> None:
    body = upload(client, auth_header, pdf_bytes).json()

    assert "stored_filename" not in body
    assert "owner_id" not in body


def test_upload_rejects_a_file_that_is_not_really_a_pdf(
    client: TestClient, auth_header: str
) -> None:
    """A .pdf name is not enough — the contents are what count."""
    response = client.post(
        UPLOAD,
        headers={"Authorization": auth_header},
        files={"file": ("virus.pdf", b"MZ\x90\x00 not a pdf", "application/pdf")},
    )

    assert response.status_code == 400


def test_upload_requires_a_token(client: TestClient, pdf_bytes: bytes) -> None:
    response = client.post(
        UPLOAD, files={"file": ("notes.pdf", pdf_bytes, "application/pdf")}
    )

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Isolation between users
# ---------------------------------------------------------------------------


def test_list_shows_only_your_own_documents(
    client: TestClient, auth_header: str, other_auth_header: str, pdf_bytes: bytes
) -> None:
    upload(client, auth_header, pdf_bytes, "alice.pdf")

    alice = client.get(DOCUMENTS, headers={"Authorization": auth_header}).json()
    mallory = client.get(DOCUMENTS, headers={"Authorization": other_auth_header}).json()

    assert len(alice) == 1
    assert mallory == []


def test_another_user_cannot_read_your_document(
    client: TestClient, auth_header: str, other_auth_header: str, pdf_bytes: bytes
) -> None:
    """The IDOR test. If this fails, users can read each other's notes."""
    document_id = upload(client, auth_header, pdf_bytes).json()["id"]

    response = client.get(
        f"{DOCUMENTS}/{document_id}", headers={"Authorization": other_auth_header}
    )

    assert response.status_code == 404


def test_another_user_cannot_read_your_text(
    client: TestClient, auth_header: str, other_auth_header: str, pdf_bytes: bytes
) -> None:
    document_id = upload(client, auth_header, pdf_bytes).json()["id"]

    response = client.get(
        f"{DOCUMENTS}/{document_id}/text", headers={"Authorization": other_auth_header}
    )

    assert response.status_code == 404


def test_another_user_cannot_delete_your_document(
    client: TestClient, auth_header: str, other_auth_header: str, pdf_bytes: bytes
) -> None:
    document_id = upload(client, auth_header, pdf_bytes).json()["id"]

    response = client.delete(
        f"{DOCUMENTS}/{document_id}", headers={"Authorization": other_auth_header}
    )

    assert response.status_code == 404

    # And it really is still there.
    still_there = client.get(
        f"{DOCUMENTS}/{document_id}", headers={"Authorization": auth_header}
    )
    assert still_there.status_code == 200


def test_missing_document_returns_404_not_403(
    client: TestClient, auth_header: str
) -> None:
    """404 rather than 403 keeps us from confirming that a document exists."""
    response = client.get(f"{DOCUMENTS}/9999", headers={"Authorization": auth_header})

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------


def test_extracted_text_is_returned(
    client: TestClient, auth_header: str, pdf_bytes: bytes
) -> None:
    document_id = upload(client, auth_header, pdf_bytes).json()["id"]

    response = client.get(
        f"{DOCUMENTS}/{document_id}/text", headers={"Authorization": auth_header}
    )

    assert response.status_code == 200
    assert "Calvin cycle" in response.json()["extracted_text"]


def test_delete_removes_the_document(
    client: TestClient, auth_header: str, pdf_bytes: bytes
) -> None:
    document_id = upload(client, auth_header, pdf_bytes).json()["id"]

    assert (
        client.delete(
            f"{DOCUMENTS}/{document_id}", headers={"Authorization": auth_header}
        ).status_code
        == 204
    )
    assert (
        client.get(
            f"{DOCUMENTS}/{document_id}", headers={"Authorization": auth_header}
        ).status_code
        == 404
    )
