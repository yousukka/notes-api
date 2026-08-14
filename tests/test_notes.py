import os

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.engine import make_url

from main import app
from database import get_session
from models import User, Note


# Create a separate database engine for testing
DATABASE_URL = os.getenv("DATABASE_URL")

test_url = make_url(DATABASE_URL).set(database="notes_test")
test_engine = create_engine(test_url, echo=True)


@pytest.fixture
def client():
    # Create tables in the test database
    SQLModel.metadata.create_all(test_engine)

    # Use the test database session instead of notes_dev
    def get_test_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session

    with TestClient(app) as test_client:
        yield test_client

    # Remove test data/tables after the test
    SQLModel.metadata.drop_all(test_engine)

    # Remove the dependency override
    app.dependency_overrides.clear()


def create_test_user(client):
    response = client.post(
        "/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 200

    login_response = client.post(
        "/login",
        data={
            "username": "test@example.com",
            "password": "testpassword123"
        }
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_create_note(client):
    token = create_test_user(client)

    response = client.post(
        "/notes",
        json={
            "title": "Test Note",
            "content": "This note is created during testing."
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Test Note"
    assert data["content"] == "This note is created during testing."


def test_list_notes(client):
    token = create_test_user(client)

    client.post(
        "/notes",
        json={
            "title": "List Test",
            "content": "Testing list notes."
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    response = client.get(
        "/notes",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    notes = response.json()

    assert len(notes) == 1
    assert notes[0]["title"] == "List Test"


def test_delete_note(client):
    token = create_test_user(client)

    create_response = client.post(
        "/notes",
        json={
            "title": "Delete Test",
            "content": "This note will be deleted."
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert create_response.status_code == 200

    note_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/notes/{note_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert delete_response.status_code == 200

    list_response = client.get(
        "/notes",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert list_response.status_code == 200
    assert list_response.json() == []