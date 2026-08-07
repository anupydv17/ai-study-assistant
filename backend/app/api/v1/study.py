"""AI study-tool endpoints: summary, and later quiz, flashcards and chat.

These share the /documents prefix because they all act on one document, but
they live apart from documents.py, which handles storage rather than AI.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.crud import chat as chat_crud
from app.crud import document as document_crud
from app.crud import study as study_crud
from app.db.session import get_db
from app.models.chat import MessageRole
from app.models.document import Document
from app.models.study import StudyItemKind
from app.models.user import User
from app.schemas.study import (
    ChatAnswer,
    ChatMessageRead,
    ChatRequest,
    FlashcardsRead,
    QuizRead,
    StudyItemListRead,
    SummaryRead,
)
from app.services import ai

router = APIRouter(prefix="/documents", tags=["Study Tools"])


def _get_document_with_text(
    document_id: int, db: Session, current_user: User
) -> Document:
    """Fetch a document the user owns, and confirm it has usable text.

    Shared by every AI endpoint, so the ownership check can never be
    forgotten on a new one.
    """
    document = document_crud.get_for_owner(
        db, document_id=document_id, owner_id=current_user.id
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    if not document.has_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "This PDF contains no readable text, so it cannot be "
                "processed by the AI."
            ),
        )

    return document


# Deliberately `def`, not `async def`. The Gemini call blocks for several
# seconds; FastAPI runs sync endpoints in a threadpool, so other requests keep
# being served. An `async def` calling blocking code would freeze the server.
@router.post(
    "/{document_id}/summary",
    response_model=SummaryRead,
    summary="Generate a summary of one of your PDFs",
)
def create_summary(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SummaryRead:
    """Summarise a document with Gemini."""
    document = _get_document_with_text(document_id, db, current_user)

    try:
        summary = ai.generate_summary(document.extracted_text or "")
    except ai.AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc

    study_crud.create_item(
        db,
        document_id=document.id,
        kind=StudyItemKind.SUMMARY,
        content={"summary": summary},
        model=settings.GEMINI_MODEL,
    )

    return SummaryRead(
        document_id=document.id,
        model=settings.GEMINI_MODEL,
        summary=summary,
    )


@router.post(
    "/{document_id}/quiz",
    response_model=QuizRead,
    summary="Generate a multiple-choice quiz from one of your PDFs",
)
def create_quiz(
    document_id: int,
    count: int = Query(default=5, ge=1, le=20, description="How many questions"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizRead:
    """Generate a quiz with Gemini."""
    document = _get_document_with_text(document_id, db, current_user)

    try:
        questions = ai.generate_quiz(document.extracted_text or "", count=count)
    except ai.AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc

    study_crud.create_item(
        db,
        document_id=document.id,
        kind=StudyItemKind.QUIZ,
        # model_dump() turns Pydantic objects into plain dicts, which is what
        # a JSON column can store.
        content={"questions": [q.model_dump() for q in questions]},
        model=settings.GEMINI_MODEL,
    )

    return QuizRead(
        document_id=document.id,
        model=settings.GEMINI_MODEL,
        questions=questions,
    )


@router.post(
    "/{document_id}/flashcards",
    response_model=FlashcardsRead,
    summary="Generate flashcards from one of your PDFs",
)
def create_flashcards(
    document_id: int,
    count: int = Query(default=10, ge=1, le=30, description="How many cards"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FlashcardsRead:
    """Generate a flashcard deck with Gemini."""
    document = _get_document_with_text(document_id, db, current_user)

    try:
        cards = ai.generate_flashcards(document.extracted_text or "", count=count)
    except ai.AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc

    study_crud.create_item(
        db,
        document_id=document.id,
        kind=StudyItemKind.FLASHCARDS,
        content={"flashcards": [c.model_dump() for c in cards]},
        model=settings.GEMINI_MODEL,
    )

    return FlashcardsRead(
        document_id=document.id,
        model=settings.GEMINI_MODEL,
        flashcards=cards,
    )


@router.post(
    "/{document_id}/chat",
    response_model=ChatAnswer,
    summary="Ask a question about one of your PDFs",
)
def ask_question(
    document_id: int,
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatAnswer:
    """Answer a question in the context of the document's conversation."""
    document = _get_document_with_text(document_id, db, current_user)

    # Read history BEFORE saving the new question, or the question would be
    # replayed to the model as if it had already been asked.
    history = chat_crud.recent_messages(
        db, document_id=document.id, limit=settings.CHAT_HISTORY_LIMIT
    )

    try:
        answer_text = ai.answer_question(
            document_text=document.extracted_text or "",
            history=history,
            question=request.question,
        )
    except ai.AIServiceError as exc:
        # Nothing is saved on failure, so the user can simply retry.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc

    # Save both messages in one transaction: never store a question whose
    # answer failed to save.
    question_message = chat_crud.add_message(
        db,
        document_id=document.id,
        role=MessageRole.USER,
        content=request.question,
        commit=False,
    )
    answer_message = chat_crud.add_message(
        db,
        document_id=document.id,
        role=MessageRole.ASSISTANT,
        content=answer_text,
        commit=False,
    )
    db.commit()
    db.refresh(question_message)
    db.refresh(answer_message)

    return ChatAnswer(
        document_id=document.id,
        model=settings.GEMINI_MODEL,
        question=ChatMessageRead.model_validate(question_message),
        answer=ChatMessageRead.model_validate(answer_message),
    )


@router.get(
    "/{document_id}/chat",
    response_model=list[ChatMessageRead],
    summary="Get the conversation history for one of your PDFs",
)
def get_chat_history(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatMessageRead]:
    """Return every message exchanged about this document, oldest first."""
    document = document_crud.get_for_owner(
        db, document_id=document_id, owner_id=current_user.id
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    return chat_crud.list_messages(db, document_id=document.id)


@router.delete(
    "/{document_id}/chat",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear the conversation for one of your PDFs",
)
def clear_chat_history(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete the whole conversation for a document."""
    document = document_crud.get_for_owner(
        db, document_id=document_id, owner_id=current_user.id
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    chat_crud.clear_messages(db, document_id=document.id)


@router.get(
    "/{document_id}/history",
    response_model=list[StudyItemListRead],
    summary="List saved study material for one of your PDFs",
)
def list_document_history(
    document_id: int,
    kind: StudyItemKind | None = Query(default=None, description="Filter by kind"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[StudyItemListRead]:
    """Return everything the AI has generated for this document."""
    document = document_crud.get_for_owner(
        db, document_id=document_id, owner_id=current_user.id
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    return study_crud.list_for_document(db, document_id=document.id, kind=kind)
