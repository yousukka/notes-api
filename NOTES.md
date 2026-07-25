# Notes App Audit

## Current Storage
- Notes are stored in a JSON file (notes.json).

## API Endpoints

### GET /notes
Returns all notes.

### POST /notes
Creates a new note.

### DELETE /notes/{id}
Deletes a note.

### POST /summarize/{id}
Summarizes a note using the Gemini API.

## Note Structure

Each note contains:

- id
- title
- content

## Frontend

The frontend sends requests to the FastAPI backend.

## Backend

FastAPI reads and writes data to notes.json.

## Goal

Replace notes.json with PostgreSQL using SQLAlchemy.
## Week 1 Plan

### Tables
- User
- Note

### Relationship
- One User can have many Notes.
- Each Note belongs to one User.

### Endpoints to Update
- GET /notes
- POST /notes
- DELETE /notes/{id}
- POST /summarize/{id}

These endpoints will use PostgreSQL instead of notes.json.

### Why PostgreSQL?
- Better data management
- Supports multiple users
- Scalable
- Same database used in production