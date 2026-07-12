from google import genai
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os

app = FastAPI()
load_dotenv()

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

# Day 5 Feature: Search notes by title
@app.get("/notes/search/{keyword}")
def search_notes(keyword: str):
    results = []

    for note in notes:
        if keyword.lower() in note["title"].lower():
            results.append(note)

    return results

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
@app.post("/notes/{id}/summarize")
def summarize_note(id: int):
    if id < 0 or id >= len(notes):
        return {"error": "Note not found"}

    note_text = notes[id]["content"]

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Summarize this note two sentences: {note_text}"
    )

    return {"summary": response.text}