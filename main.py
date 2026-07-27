from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Session, select
from google import genai
from dotenv import load_dotenv
import os
import uvicorn

from database import engine, get_session
from models import Note, NoteCreate

load_dotenv()

app = FastAPI()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.get("/notes")
def list_notes(session: Session = Depends(get_session)):
    return session.exec(select(Note)).all()


@app.get("/notes/search/{keyword}")
def search_notes(keyword: str, session: Session = Depends(get_session)):
    notes = session.exec(select(Note)).all()

    results = [
        note for note in notes
        if keyword.lower() in note.title.lower()
    ]

    return results


@app.post("/notes")
def create_note(note: NoteCreate, session: Session = Depends(get_session)):
    db_note = Note(
        title=note.title,
        content=note.content
    )

    session.add(db_note)
    session.commit()
    session.refresh(db_note)

    return db_note


@app.put("/notes/{id}")
def update_note(id: int, updated_note: NoteCreate, session: Session = Depends(get_session)):
    note = session.get(Note, id)

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.title = updated_note.title
    note.content = updated_note.content

    session.add(note)
    session.commit()
    session.refresh(note)

    return note


@app.delete("/notes/{id}")
def delete_note(id: int, session: Session = Depends(get_session)):
    note = session.get(Note, id)

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    session.delete(note)
    session.commit()

    return {"message": "Note deleted"}


@app.post("/notes/{id}/summarize")
def summarize_note(id: int, session: Session = Depends(get_session)):
    note = session.get(Note, id)

    if not note:
        return {"summary": "Note not found"}

    if not note.content.strip():
        return {"summary": "Note content is empty"}

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Summarize this note in two sentences: {note.content}"
        )

        return {"summary": response.text}

    except Exception as e:
        return {"summary": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)