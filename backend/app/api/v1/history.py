"""Study history endpoints.

These span every document a user owns, which is why they sit under /history
rather than under a single document.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud import study as study_crud
from app.db.session import get_db
from app.models.study import StudyItemKind
from app.models.user import User
from app.schemas.study import StudyItemListRead, StudyItemRead

router = APIRouter(prefix="/history", tags=["Study History"])


@router.get(
    "",
    response_model=list[StudyItemListRead],
    summary="List everything the AI has generated for you",
)
def list_history(
    kind: StudyItemKind | None = Query(default=None, description="Filter by kind"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[StudyItemListRead]:
    """Return saved study material across all of the user's documents."""
    return study_crud.list_for_owner(
        db, owner_id=current_user.id, kind=kind, limit=limit
    )


@router.get(
    "/{item_id}",
    response_model=StudyItemRead,
    summary="Get one saved item, including its full content",
)
def get_history_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudyItemRead:
    """Return a saved quiz, summary or flashcard deck in full."""
    item = study_crud.get_for_owner(db, item_id=item_id, owner_id=current_user.id)

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Study item not found"
        )

    return item


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete one saved item",
)
def delete_history_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove a saved item from the user's history."""
    item = study_crud.get_for_owner(db, item_id=item_id, owner_id=current_user.id)

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Study item not found"
        )

    study_crud.delete_item(db, item)
