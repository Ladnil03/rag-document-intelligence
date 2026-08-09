import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app

# Setup isolated test database engine (SQLite file for standalone automated unit testing)
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    """Create fresh tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_1_create_document():
    """Test 1: Create a document and expect 201 Created."""
    response = client.post("/documents", json={"name": "example.pdf"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "example.pdf"
    assert "id" in data
    assert "created_at" in data


def test_2_get_all_documents():
    """Test 2: Retrieve all documents and expect 200 OK."""
    client.post("/documents", json={"name": "doc1.pdf"})
    client.post("/documents", json={"name": "doc2.pdf"})
    
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "doc1.pdf"
    assert data[1]["name"] == "doc2.pdf"


def test_3_get_one_document():
    """Test 3: Retrieve a single existing document and expect 200 OK."""
    create_res = client.post("/documents", json={"name": "contract.pdf"})
    doc_id = create_res.json()["id"]

    response = client.get(f"/documents/{doc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id
    assert data["name"] == "contract.pdf"


def test_4_update_document():
    """Test 4: Update document name and expect 200 OK."""
    create_res = client.post("/documents", json={"name": "old_title.pdf"})
    doc_id = create_res.json()["id"]

    response = client.patch(f"/documents/{doc_id}", json={"name": "new_title.pdf"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id
    assert data["name"] == "new_title.pdf"


def test_5_verify_update():
    """Test 5: Retrieve document again to verify updated name."""
    create_res = client.post("/documents", json={"name": "original.pdf"})
    doc_id = create_res.json()["id"]

    # Perform update
    client.patch(f"/documents/{doc_id}", json={"name": "updated.pdf"})

    # Verify retrieval
    get_res = client.get(f"/documents/{doc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "updated.pdf"


def test_6_delete_document():
    """Test 6: Delete a document and expect successful deletion response."""
    create_res = client.post("/documents", json={"name": "to_delete.pdf"})
    doc_id = create_res.json()["id"]

    del_res = client.delete(f"/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Document deleted successfully"

    # Confirm deletion
    get_res = client.get(f"/documents/{doc_id}")
    assert get_res.status_code == 404


def test_7_missing_document():
    """Test 7: Request a nonexistent document ID and expect 404 Not Found."""
    response = client.get("/documents/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


def test_8_persistence_verification():
    """Test 8: Mandatory persistence verification test.
    Create a document -> Close app context/session -> Re-query DB to confirm persistence.
    """
    create_res = client.post("/documents", json={"name": "persistent_doc.pdf"})
    doc_id = create_res.json()["id"]

    # Simulate app server shutdown/restart by creating a new session directly on the engine
    new_session = TestingSessionLocal()
    import models
    persisted_doc = new_session.query(models.Document).filter(models.Document.id == doc_id).first()
    new_session.close()

    assert persisted_doc is not None
    assert persisted_doc.id == doc_id
    assert persisted_doc.name == "persistent_doc.pdf"
