import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    notes: Mapped[list["Note"]] = relationship(back_populates="user")
    tags: Mapped[list["Tag"]] = relationship(back_populates="user")


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="notes")
    tags: Mapped[list["NoteTag"]] = relationship(back_populates="note")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="note")


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("user_id", "name", name="tags_user_name_unique"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="tags")
    notes: Mapped[list["NoteTag"]] = relationship(back_populates="tag")


class NoteTag(Base):
    __tablename__ = "note_tags"

    note_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("notes.id"), primary_key=True)
    tag_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tags.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    note: Mapped["Note"] = relationship(back_populates="tags")
    tag: Mapped["Tag"] = relationship(back_populates="notes")


class Favorite(Base):
    __tablename__ = "favorites"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    note_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("notes.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    note: Mapped["Note"] = relationship(back_populates="favorites")
