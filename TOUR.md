# Notes API Tour

## Project Overview

This is a FastAPI Notes API with user authentication, CRUD operations, note searching, and AI-powered note summarization.

## main.py

### Authentication

- `create_access_token()` creates a JWT access token for an authenticated user.
- `get_current_user()` validates the JWT token and identifies the current user.

### User APIs

- `POST /register` — Creates a new user account and securely hashes the password.
- `POST /login` — Checks the user's email and password and returns a JWT access token.

### Notes APIs

- `GET /notes` — Returns notes belonging to the currently authenticated user.
- `GET /notes/search/{keyword}` — Searches the current user's notes by title.
- `POST /notes` — Creates a new note for the authenticated user.
- `PUT /notes/{id}` — Updates an existing note owned by the authenticated user.
- `DELETE /notes/{id}` — Deletes an existing note owned by the authenticated user.

### AI Feature

- `POST /notes/{id}/summarize` — Uses Gemini AI to analyze a note and return a summary, key points, and sentiment.

## Database

The application uses SQLModel and a database session to store users and notes.

## Security

Passwords are hashed using bcrypt. JWT bearer tokens are used to protect the Notes API endpoints.

## CORS

CORS middleware is enabled so the frontend can communicate with the API.