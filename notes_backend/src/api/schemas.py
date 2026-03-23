import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, constr


class Message(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    created_at: datetime


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email (must be unique).")
    username: constr(min_length=1, max_length=64) = Field(..., description="Display/handle username (unique).")
    password: constr(min_length=8, max_length=128) = Field(..., description="User password (min 8 characters).")


class LoginRequest(BaseModel):
    username: str = Field(..., description="Username or email.")
    password: str = Field(..., description="Password.")


class TagCreate(BaseModel):
    name: constr(min_length=1, max_length=64)


class TagUpdate(BaseModel):
    name: constr(min_length=1, max_length=64)


class TagOut(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime


class NoteCreate(BaseModel):
    title: constr(min_length=0, max_length=500) = ""
    content: str = ""


class NoteUpdate(BaseModel):
    title: Optional[constr(min_length=0, max_length=500)] = None
    content: Optional[str] = None
    is_archived: Optional[bool] = None


class NoteOut(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    is_archived: bool
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    tags: List[TagOut] = []
    is_favorite: bool = False


class NoteListOut(BaseModel):
    items: List[NoteOut]
    total: int


class AssignTagsRequest(BaseModel):
    tag_ids: List[uuid.UUID] = Field(default_factory=list, description="Set of tag IDs to assign to the note.")


class SearchResponse(BaseModel):
    items: List[NoteOut]
    total: int
