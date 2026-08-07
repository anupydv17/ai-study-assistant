"""Pydantic schemas for AI-generated study material."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SummaryRead(BaseModel):
    """An AI-generated summary of one document."""

    document_id: int
    model: str
    summary: str


class QuizQuestion(BaseModel):
    """One multiple-choice question.

    This class is used twice: as the shape we demand from Gemini, and as the
    shape we return to the client. One definition, no chance of drift.
    """

    question: str
    options: list[str]
    correct_index: int
    explanation: str


class QuizRead(BaseModel):
    """A generated quiz for one document."""

    document_id: int
    model: str
    questions: list[QuizQuestion]


class Flashcard(BaseModel):
    """One flashcard: a prompt and its answer."""

    front: str
    back: str


class FlashcardsRead(BaseModel):
    """A generated flashcard deck for one document."""

    document_id: int
    model: str
    flashcards: list[Flashcard]


class StudyItemListRead(BaseModel):
    """A saved item as it appears in a history list.

    Deliberately without `content`: a history page shows what exists and when,
    and loading twenty full quizzes to render twenty rows would be wasteful.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    kind: str
    model: str
    created_at: datetime


class StudyItemRead(StudyItemListRead):
    """A single saved item, including its full generated content."""

    content: dict[str, Any]


class ChatRequest(BaseModel):
    """A question a student asks about their notes."""

    question: str = Field(min_length=1, max_length=2000)


class ChatMessageRead(BaseModel):
    """One stored message in a conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime


class ChatAnswer(BaseModel):
    """The result of asking a question: both messages that were saved."""

    document_id: int
    model: str
    question: ChatMessageRead
    answer: ChatMessageRead
