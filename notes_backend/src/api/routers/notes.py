import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, delete, exists, func, insert, select
from sqlalchemy.orm import Session

from src.api.core.jwt import get_current_user
from src.api.db.models import Favorite, Note, NoteTag, Tag, User
from src.api.db.session import get_db
from src.api.schemas import (
    AssignTagsRequest,
    NoteCreate,
    NoteListOut,
    NoteOut,
    NoteUpdate,
    TagOut,
)

router = APIRouter(prefix="/notes", tags=["notes"])


def _note_to_out(db: Session, note: Note, user_id: uuid.UUID) -> NoteOut:
    tag_rows = db.execute(
        select(Tag).join(NoteTag, NoteTag.tag_id == Tag.id).where(NoteTag.note_id == note.id)
    ).scalars().all()

    is_favorite = db.scalar(
        select(exists().where(and_(Favorite.user_id == user_id, Favorite.note_id == note.id)))
    )

    return NoteOut(
        id=note.id,
        title=note.title,
        content=note.content,
        is_archived=note.is_archived,
        is_pinned=note.is_pinned,
        created_at=note.created_at,
        updated_at=note.updated_at,
        tags=[TagOut(id=t.id, name=t.name, created_at=t.created_at) for t in tag_rows],
        is_favorite=bool(is_favorite),
    )


@router.post(
    "",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a note",
)
def create_note(
    payload: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteOut:
    note = Note(
        user_id=current_user.id,
        title=payload.title,
        content=payload.content,
        is_archived=False,
        is_pinned=False,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return _note_to_out(db, note, current_user.id)


@router.get(
    "",
    response_model=NoteListOut,
    summary="List notes",
    description="Lists notes for current user with optional filters (archived, pinned, favorites, tag_id).",
)
def list_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    archived: Optional[bool] = Query(default=None),
    pinned: Optional[bool] = Query(default=None),
    favorite: Optional[bool] = Query(default=None),
    tag_id: Optional[uuid.UUID] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> NoteListOut:
    base = select(Note).where(Note.user_id == current_user.id)

    if archived is not None:
        base = base.where(Note.is_archived == archived)
    if pinned is not None:
        base = base.where(Note.is_pinned == pinned)
    if tag_id is not None:
        base = base.join(NoteTag, NoteTag.note_id == Note.id).where(NoteTag.tag_id == tag_id)
    if favorite:
        base = base.join(Favorite, Favorite.note_id == Note.id).where(Favorite.user_id == current_user.id)

    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.execute(base.order_by(Note.updated_at.desc()).limit(limit).offset(offset)).scalars().all()
    return NoteListOut(items=[_note_to_out(db, n, current_user.id) for n in rows], total=total)


@router.get(
    "/{note_id}",
    response_model=NoteOut,
    summary="Get note by id",
)
def get_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteOut:
    note = db.scalar(select(Note).where(and_(Note.id == note_id, Note.user_id == current_user.id)))
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return _note_to_out(db, note, current_user.id)


@router.patch(
    "/{note_id}",
    response_model=NoteOut,
    summary="Update a note",
)
def update_note(
    note_id: uuid.UUID,
    payload: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteOut:
    note = db.scalar(select(Note).where(and_(Note.id == note_id, Note.user_id == current_user.id)))
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(note, k, v)

    db.add(note)
    db.commit()
    db.refresh(note)
    return _note_to_out(db, note, current_user.id)


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a note",
)
def delete_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    res = db.execute(delete(Note).where(and_(Note.id == note_id, Note.user_id == current_user.id)))
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    db.commit()
    return None


@router.post(
    "/{note_id}/pin",
    response_model=NoteOut,
    summary="Pin a note",
)
def pin_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteOut:
    note = db.scalar(select(Note).where(and_(Note.id == note_id, Note.user_id == current_user.id)))
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.is_pinned = True
    db.add(note)
    db.commit()
    db.refresh(note)
    return _note_to_out(db, note, current_user.id)


@router.post(
    "/{note_id}/unpin",
    response_model=NoteOut,
    summary="Unpin a note",
)
def unpin_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteOut:
    note = db.scalar(select(Note).where(and_(Note.id == note_id, Note.user_id == current_user.id)))
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.is_pinned = False
    db.add(note)
    db.commit()
    db.refresh(note)
    return _note_to_out(db, note, current_user.id)


@router.post(
    "/{note_id}/favorite",
    response_model=NoteOut,
    summary="Favorite a note",
)
def favorite_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteOut:
    note = db.scalar(select(Note).where(and_(Note.id == note_id, Note.user_id == current_user.id)))
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Upsert-like: ignore if already exists due to PK (user_id, note_id).
    try:
        db.execute(
            insert(Favorite).values(user_id=current_user.id, note_id=note_id).prefix_with("ON CONFLICT DO NOTHING")
        )
    except Exception:
        # Some SQLAlchemy dialects may not support prefix_with; fallback:
        if not db.scalar(select(exists().where(and_(Favorite.user_id == current_user.id, Favorite.note_id == note_id)))):
            db.add(Favorite(user_id=current_user.id, note_id=note_id))
    db.commit()

    db.refresh(note)
    return _note_to_out(db, note, current_user.id)


@router.post(
    "/{note_id}/unfavorite",
    response_model=NoteOut,
    summary="Unfavorite a note",
)
def unfavorite_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteOut:
    note = db.scalar(select(Note).where(and_(Note.id == note_id, Note.user_id == current_user.id)))
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    db.execute(delete(Favorite).where(and_(Favorite.user_id == current_user.id, Favorite.note_id == note_id)))
    db.commit()

    db.refresh(note)
    return _note_to_out(db, note, current_user.id)


@router.put(
    "/{note_id}/tags",
    response_model=NoteOut,
    summary="Set tags on a note",
    description="Replaces note's tags with the provided tag_ids (must belong to current user).",
)
def set_note_tags(
    note_id: uuid.UUID,
    payload: AssignTagsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteOut:
    note = db.scalar(select(Note).where(and_(Note.id == note_id, Note.user_id == current_user.id)))
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    tag_ids = list(dict.fromkeys(payload.tag_ids))  # dedupe, preserve order
    if tag_ids:
        # Ensure tags belong to current user
        owned = db.execute(select(Tag.id).where(and_(Tag.user_id == current_user.id, Tag.id.in_(tag_ids)))).scalars().all()
        if set(owned) != set(tag_ids):
            raise HTTPException(status_code=400, detail="One or more tags are invalid")

    db.execute(delete(NoteTag).where(NoteTag.note_id == note_id))
    for tid in tag_ids:
        db.add(NoteTag(note_id=note_id, tag_id=tid))
    db.commit()
    db.refresh(note)
    return _note_to_out(db, note, current_user.id)
