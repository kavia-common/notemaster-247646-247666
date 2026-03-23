import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api.core.jwt import get_current_user
from src.api.db.models import Tag, User
from src.api.db.session import get_db
from src.api.schemas import TagCreate, TagOut, TagUpdate

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get(
    "",
    response_model=List[TagOut],
    summary="List tags",
)
def list_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[TagOut]:
    rows = db.execute(select(Tag).where(Tag.user_id == current_user.id).order_by(func.lower(Tag.name))).scalars().all()
    return [TagOut(id=t.id, name=t.name, created_at=t.created_at) for t in rows]


@router.post(
    "",
    response_model=TagOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create tag",
)
def create_tag(
    payload: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TagOut:
    tag = Tag(user_id=current_user.id, name=payload.name)
    db.add(tag)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Tag already exists")
    db.refresh(tag)
    return TagOut(id=tag.id, name=tag.name, created_at=tag.created_at)


@router.patch(
    "/{tag_id}",
    response_model=TagOut,
    summary="Update tag",
)
def update_tag(
    tag_id: uuid.UUID,
    payload: TagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TagOut:
    tag = db.scalar(select(Tag).where(and_(Tag.id == tag_id, Tag.user_id == current_user.id)))
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    tag.name = payload.name
    db.add(tag)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Tag already exists")
    db.refresh(tag)
    return TagOut(id=tag.id, name=tag.name, created_at=tag.created_at)


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tag",
)
def delete_tag(
    tag_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    res = db.execute(delete(Tag).where(and_(Tag.id == tag_id, Tag.user_id == current_user.id)))
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.commit()
    return None
