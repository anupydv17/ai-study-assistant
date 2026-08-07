"""Tests for the AI study tools.

Gemini is never called. Every test replaces the AI service with a fake, so the
suite is free, fast, offline and deterministic. What we are testing is *our*
code around the AI — the ownership checks, the error translation, the saving —
not whether Google's model works.
"""

import pytest
from fastapi.testclient import TestClient

from app.services import ai

DOCUMENTS = "/api/v1/documents"


@pytest.fixture(name="document_id")
def document_id_fixture(client: TestClient, auth_header: str, pdf_bytes: bytes) -> int:
    response = client.post(
        f"{DOCUMENTS}/upload",
        headers={"Authorization": auth_header},
        files={"file": ("notes.pdf", pdf_bytes, "application/pdf")},
    )
    return response.json()["id"]


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def test_summary_returns_generated_text(
    client: TestClient, auth_header: str, document_id: int, monkeypatch
) -> None:
    monkeypatch.setattr(ai, "generate_summary", lambda text: "A fake summary.")

    response = client.post(
        f"{DOCUMENTS}/{document_id}/summary", headers={"Authorization": auth_header}
    )

    assert response.status_code == 200
    assert response.json()["summary"] == "A fake summary."


def test_summary_is_saved_to_history(
    client: TestClient, auth_header: str, document_id: int, monkeypatch
) -> None:
    monkeypatch.setattr(ai, "generate_summary", lambda text: "A fake summary.")

    client.post(
        f"{DOCUMENTS}/{document_id}/summary", headers={"Authorization": auth_header}
    )

    history = client.get(
        "/api/v1/history", headers={"Authorization": auth_header}
    ).json()

    assert len(history) == 1
    assert history[0]["kind"] == "summary"


def test_summary_reports_ai_failure_as_502(
    client: TestClient, auth_header: str, document_id: int, monkeypatch
) -> None:
    """A provider outage is our upstream's fault, not a 500 on our side."""

    def explode(text: str) -> str:
        raise ai.AIServiceError("The AI service is unavailable right now.")

    monkeypatch.setattr(ai, "generate_summary", explode)

    response = client.post(
        f"{DOCUMENTS}/{document_id}/summary", headers={"Authorization": auth_header}
    )

    assert response.status_code == 502


def test_summary_of_another_users_document_is_refused(
    client: TestClient, other_auth_header: str, document_id: int, monkeypatch
) -> None:
    """The ownership check must run BEFORE any AI call."""
    calls: list[str] = []
    monkeypatch.setattr(ai, "generate_summary", lambda text: calls.append(text) or "x")

    response = client.post(
        f"{DOCUMENTS}/{document_id}/summary",
        headers={"Authorization": other_auth_header},
    )

    assert response.status_code == 404
    assert calls == []  # we must not have paid for a generation


# ---------------------------------------------------------------------------
# Quiz
# ---------------------------------------------------------------------------


def test_quiz_returns_questions(
    client: TestClient, auth_header: str, document_id: int, monkeypatch
) -> None:
    from app.schemas.study import QuizQuestion

    fake = [
        QuizQuestion(
            question="Where does the Calvin cycle happen?",
            options=["Stroma", "Thylakoid", "Nucleus", "Ribosome"],
            correct_index=0,
            explanation="The notes say the stroma.",
        )
    ]
    monkeypatch.setattr(ai, "generate_quiz", lambda text, *, count: fake)

    response = client.post(
        f"{DOCUMENTS}/{document_id}/quiz?count=1", headers={"Authorization": auth_header}
    )

    assert response.status_code == 200
    assert response.json()["questions"][0]["correct_index"] == 0


@pytest.mark.parametrize("count", [0, 21, -1])
def test_quiz_rejects_an_out_of_range_count(
    client: TestClient, auth_header: str, document_id: int, count: int
) -> None:
    """One test body, three inputs. No AI mock needed — validation runs first."""
    response = client.post(
        f"{DOCUMENTS}/{document_id}/quiz?count={count}",
        headers={"Authorization": auth_header},
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------


def test_chat_saves_both_messages(
    client: TestClient, auth_header: str, document_id: int, monkeypatch
) -> None:
    monkeypatch.setattr(
        ai, "answer_question", lambda **kwargs: "It happens in the stroma."
    )

    client.post(
        f"{DOCUMENTS}/{document_id}/chat",
        headers={"Authorization": auth_header},
        json={"question": "Where does it happen?"},
    )

    history = client.get(
        f"{DOCUMENTS}/{document_id}/chat", headers={"Authorization": auth_header}
    ).json()

    assert [message["role"] for message in history] == ["user", "assistant"]


def test_chat_saves_nothing_when_the_ai_fails(
    client: TestClient, auth_header: str, document_id: int, monkeypatch
) -> None:
    """A failed question must not leave a dangling message in the history."""

    def explode(**kwargs):
        raise ai.AIServiceError("down")

    monkeypatch.setattr(ai, "answer_question", explode)

    client.post(
        f"{DOCUMENTS}/{document_id}/chat",
        headers={"Authorization": auth_header},
        json={"question": "Where does it happen?"},
    )

    history = client.get(
        f"{DOCUMENTS}/{document_id}/chat", headers={"Authorization": auth_header}
    ).json()

    assert history == []


def test_chat_rejects_an_empty_question(
    client: TestClient, auth_header: str, document_id: int
) -> None:
    response = client.post(
        f"{DOCUMENTS}/{document_id}/chat",
        headers={"Authorization": auth_header},
        json={"question": ""},
    )

    assert response.status_code == 422
