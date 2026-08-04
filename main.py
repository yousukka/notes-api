from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Session, select
from google import genai
from dotenv import load_dotenv
import os
import json
import uvicorn

from database import engine, get_session
from models import Note, NoteCreate, User, UserCreate

load_dotenv()


class Summary(BaseModel):
    summary: str
    key_points: list[str]
    sentiment: str


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
def create_access_token(user_id: int):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = session.get(User, int(user_id))

    if user is None:
        raise credentials_exception

    return user
@app.post("/register")
def register(user: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(
        select(User).where(User.email == user.email)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(user.password)

    db_user = User(
        email=user.email,
        hashed_password=hashed_password
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return {
        "message": "User registered successfully",
        "user_id": db_user.id
    }


@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    db_user = session.exec(
        select(User).where(User.email == form_data.username)
    ).first()

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not pwd_context.verify(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(db_user.id)

    return {
        "access_token": token,
        "token_type": "bearer"
    }
@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.get("/notes")
def list_notes(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return session.exec(
        select(Note).where(Note.user_id == current_user.id)
    ).all()

@app.get("/notes/search/{keyword}")
def search_notes(
    keyword: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    notes = session.exec(
        select(Note).where(Note.user_id == current_user.id)
    ).all()

    return [
        note for note in notes
        if keyword.lower() in note.title.lower()
    ]


@app.post("/notes")
def create_note(
    note: NoteCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    db_note = Note(
        title=note.title,
        content=note.content,
        user_id=current_user.id
    )

    session.add(db_note)
    session.commit()
    session.refresh(db_note)

    return db_note


@app.put("/notes/{id}")
def update_note(
    id: int,
    updated_note: NoteCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    note = session.get(Note, id)

    if not note or note.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Note not found")

    note.title = updated_note.title
    note.content = updated_note.content

    session.add(note)
    session.commit()
    session.refresh(note)

    return note


@app.delete("/notes/{id}")
def delete_note(
    id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    note = session.get(Note, id)

    if not note or note.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Note not found")

    session.delete(note)
    session.commit()

    return {"message": "Note deleted"}
@app.post("/notes/{id}/summarize")
def summarize_note(
    id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    note = session.get(Note, id)

    if not note or note.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Note not found")

    if not note.content.strip():
        return {
            "summary": "Note content is empty",
            "key_points": [],
            "sentiment": "neutral"
        }

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
            Analyze the following note.

            Return ONLY valid JSON in exactly this format:
            {{
                "summary": "short summary",
                "key_points": ["key point 1", "key point 2"],
                "sentiment": "positive, negative, or neutral"
            }}

            Note:
            {note.content}
            """
        )

        clean_text = response.text.strip()

        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]

        if clean_text.startswith("```"):
            clean_text = clean_text[3:]

        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]

        clean_text = clean_text.strip()

        data = json.loads(clean_text)
        result = Summary.model_validate(data)
        return result

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="The model returned an unexpected format"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)