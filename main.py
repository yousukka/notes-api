from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for request validation
class Note(BaseModel):
    title: str
    content: str

# Load notes from file
if os.path.exists("notes.json"):
    with open("notes.json", "r") as f:
        notes = json.load(f)
else:
    notes = []

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/notes")
def list_notes():
    return notes

@app.post("/notes")
def create_note(note: Note):
    notes.append(note.dict())

    with open("notes.json", "w") as f:
        json.dump(notes, f)

    return note

@app.put("/notes/{id}")
def update_note(id: int, note: Note):
    if id < 0 or id >= len(notes):
        return {"error": "Note not found"}

    notes[id] = note.dict()

    with open("notes.json", "w") as f:
        json.dump(notes, f)

    return {"message": "Note updated"}

@app.delete("/notes/{id}")
def delete_note(id: int):
    if id < 0 or id >= len(notes):
        return {"error": "Note not found"}

    notes.pop(id)

    with open("notes.json", "w") as f:
        json.dump(notes, f)

    return {"message": "Note deleted"}