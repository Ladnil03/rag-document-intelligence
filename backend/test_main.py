"""Focused Phase 5 API checks; developer manual testing remains authoritative."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core import config
from app.db.base import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
config.JWT_SECRET_KEY = "test-only-jwt-secret"


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def register_and_login(email: str, password: str = "secure-password") -> dict[str, str]:
    registration = client.post("/auth/register", json={"email": email, "password": password})
    assert registration.status_code == 201
    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_registration_returns_only_safe_user_fields():
    response = client.post(
        "/auth/register", json={"email": "person@example.com", "password": "secure-password"}
    )
    assert response.status_code == 201
    assert response.json()["email"] == "person@example.com"
    assert "password" not in response.json()
    assert "password_hash" not in response.json()


def test_login_rejects_invalid_credentials_without_account_detail():
    client.post(
        "/auth/register", json={"email": "person@example.com", "password": "secure-password"}
    )
    response = client.post(
        "/auth/login", json={"email": "person@example.com", "password": "wrong-password"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password."


def test_document_routes_require_bearer_authentication():
    response = client.get("/documents")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_documents_are_isolated_by_authenticated_owner():
    first_headers = register_and_login("first@example.com")
    second_headers = register_and_login("second@example.com")

    first_document = client.post(
        "/documents", json={"name": "first.pdf"}, headers=first_headers
    )
    second_document = client.post(
        "/documents", json={"name": "second.pdf"}, headers=second_headers
    )
    assert first_document.status_code == 201
    assert second_document.status_code == 201

    first_list = client.get("/documents", headers=first_headers)
    assert first_list.status_code == 200
    assert [document["name"] for document in first_list.json()] == ["first.pdf"]

    other_id = second_document.json()["id"]
    assert client.get(f"/documents/{other_id}", headers=first_headers).status_code == 404
    assert client.patch(
        f"/documents/{other_id}", json={"name": "changed.pdf"}, headers=first_headers
    ).status_code == 404


def test_health_liveness_always_returns_alive():
    """Liveness probe must always return 200/alive regardless of DB availability."""
    liveness = client.get("/health/liveness")
    assert liveness.status_code == 200
    assert liveness.json()["status"] == "alive"


def test_health_readiness_returns_valid_shape():
    """Readiness probe checks Postgres which is unavailable in unit-test context.
    Accept either 200 (ready) or 503 (not ready); validate response shape in both cases."""
    readiness = client.get("/health/readiness")
    assert readiness.status_code in (200, 503)
    body = readiness.json()
    if readiness.status_code == 200:
        assert body["status"] == "ready"
    else:
        # HTTPException body has 'detail' key when DB is unreachable
        assert "detail" in body


def test_health_full_endpoint_returns_valid_shape():
    """/health aggregates component statuses; DB may be unavailable in unit tests."""
    health = client.get("/health")
    assert health.status_code in (200, 503)
    body = health.json()
    assert "status" in body
    assert body["status"] in ("healthy", "unhealthy")


