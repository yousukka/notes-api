from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional


class NoteBase(SQLModel):
    title: str
    content: str


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str

    notes: list["Note"] = Relationship(back_populates="user")


class Note(NoteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    user: Optional[User] = Relationship(back_populates="notes")


class NoteCreate(NoteBase):
    pass
class UserCreate(SQLModel):
    email: str
    password: str