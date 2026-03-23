from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from src.api.core.jwt import get_current_user
from src.api.db.models import Note, User
from src.api.db.session import get_db
from src.api.routers.notes import _note_to_out
from src.api.schemas import SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.get(
    "",
    response_model=SearchResponse,
    summary="Search notes",
    description="Search notes by substring in title/content (case-insensitive).",
)
def search_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    q: str = Query(..., min_length=1, description="Search query."),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    archived: Optional[bool] = Query(default=None, description="Filter by archived status."),
) -> SearchResponse:
    pattern = f"%{q}%"
    base = select(Note).where(
        and_(
            Note.user_id == current_user.id,
            or_(Note.title.ilike(pattern), Note.content.ilike(pattern)),  # type: ignore[name-defined]
        )
    )
    if archived is not None:
        base = base.where(Note.is_archived == archived)

    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.execute(base.order_by(Note.updated_at.desc()).limit(limit).offset(offset)).scalars().all()
    return SearchResponse(items=[_note_to_out(db, n, current_user.id) for n in rows], total=total)
