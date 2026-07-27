from sqlmodel import SQLModel, Field
from datetime import datetime


class NoteBase(SQLModel):
    title: str
    content: str


class Note(NoteBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None


class NoteCreate(NoteBase):
    pass