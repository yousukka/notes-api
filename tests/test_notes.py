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
        headers={
            "Authorization": f"Bearer {token}"
        }
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
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    response = client.get(
        "/notes",
        headers={
            "Authorization": f"Bearer {token}"
        }
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
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert create_response.status_code == 200

    note_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/notes/{note_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert delete_response.status_code == 200

    list_response = client.get(
        "/notes",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert list_response.status_code == 200
    assert list_response.json() == []


def test_register_and_login(client):
    email = "day3user@example.com"
    password = "password123"

    # Register a new user
    register_response = client.post(
        "/register",
        json={
            "email": email,
            "password": password
        }
    )

    assert register_response.status_code == 200
    assert "user_id" in register_response.json()

    # Duplicate email should be rejected
    duplicate_response = client.post(
        "/register",
        json={
            "email": email,
            "password": password
        }
    )

    assert duplicate_response.status_code == 400

    # Login with correct password
    login_response = client.post(
        "/login",
        data={
            "username": email,
            "password": password
        }
    )

    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

    # Login with wrong password
    wrong_login_response = client.post(
        "/login",
        data={
            "username": email,
            "password": "wrongpassword"
        }
    )

    assert wrong_login_response.status_code == 401


def test_protected_route_requires_auth(client):
    response = client.get("/notes")

    assert response.status_code == 401


def test_user_isolation(client):
    # Register User A
    user_a_email = "usera@example.com"
    user_a_password = "password123"

    register_a = client.post(
        "/register",
        json={
            "email": user_a_email,
            "password": user_a_password
        }
    )

    assert register_a.status_code == 200

    # Login User A
    login_a = client.post(
        "/login",
        data={
            "username": user_a_email,
            "password": user_a_password
        }
    )

    assert login_a.status_code == 200

    token_a = login_a.json()["access_token"]

    # User A creates a note
    create_response = client.post(
        "/notes",
        json={
            "title": "User A Note",
            "content": "This belongs to User A."
        },
        headers={
            "Authorization": f"Bearer {token_a}"
        }
    )

    assert create_response.status_code == 200

    note_id = create_response.json()["id"]

    # Register User B
    user_b_email = "userb@example.com"
    user_b_password = "password123"

    register_b = client.post(
        "/register",
        json={
            "email": user_b_email,
            "password": user_b_password
        }
    )

    assert register_b.status_code == 200

    # Login User B
    login_b = client.post(
        "/login",
        data={
            "username": user_b_email,
            "password": user_b_password
        }
    )

    assert login_b.status_code == 200

    token_b = login_b.json()["access_token"]

    # User B should see no notes
    list_response = client.get(
        "/notes",
        headers={
            "Authorization": f"Bearer {token_b}"
        }
    )

    assert list_response.status_code == 200
    assert list_response.json() == []

    # User B tries to access User A's note
    get_response = client.get(
        f"/notes/{note_id}",
        headers={
            "Authorization": f"Bearer {token_b}"
        }
    )

        

    # User B tries to delete User A's note
    delete_response = client.delete(
        f"/notes/{note_id}",
        headers={
            "Authorization": f"Bearer {token_b}"
        }
    )

    assert delete_response.status_code in [403, 404, 405]