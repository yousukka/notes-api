from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

notes = []

class Note(BaseModel):
    title: str
    content: str

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.post("/notes")
def create_note(note: Note):
    notes.append(note)
    return note

@app.get("/notes")
def list_notes():
    return notes