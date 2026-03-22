"""
Pytest configuration and fixtures for InternalKnowledgeHub tests.
"""

import os
import pytest
from typing import Generator
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Set test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-only"

from app.main import create_app
from app.core.database import Base, get_db
from app.models.models import User, Document, Chunk, QAHistory
from app.core.security import get_password_hash


# Test database engine
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def app() -> Generator[Flask, None, None]:
    """Create application for testing."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": TEST_DATABASE_URL,
        "WTF_CSRF_ENABLED": False,
    })
    yield app


@pytest.fixture(scope="function")
def db_session(app: Flask) -> Generator[Session, None, None]:
    """Create a new database session for a test."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(app: Flask, db_session: Session) -> Generator[FlaskClient, None, None]:
    """Create a test client with database session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Override dependency
    app.config["_test_db_session"] = db_session
    
    with app.test_client() as test_client:
        with app.app_context():
            yield test_client


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin(db_session: Session) -> User:
    """Create a test admin user."""
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        full_name="Admin User",
        is_active=True,
        role="admin"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def auth_headers(client: FlaskClient, test_user: User) -> dict:
    """Get authentication headers for test user."""
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"}
    )
    token = response.json.get("access_token")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(client: FlaskClient, test_admin: User) -> dict:
    """Get authentication headers for admin user."""
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "adminpassword123"}
    )
    token = response.json.get("access_token")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_document(db_session: Session, test_user: User) -> Document:
    """Create a test document."""
    document = Document(
        filename="test_document.pdf",
        original_filename="test_document.pdf",
        file_path="/tmp/test_document.pdf",
        file_size=1024,
        mime_type="application/pdf",
        status="completed",
        uploaded_by_id=test_user.id,
        chunk_count=5
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document


@pytest.fixture
def test_chunks(db_session: Session, test_document: Document) -> list[Chunk]:
    """Create test chunks for a document."""
    chunks = []
    for i in range(5):
        chunk = Chunk(
            document_id=test_document.id,
            content=f"This is test chunk {i} content for testing purposes.",
            chunk_index=i,
            start_char=i * 100,
            end_char=(i + 1) * 100,
            embedding=[0.1] * 384  # Mock embedding
        )
        chunks.append(chunk)
        db_session.add(chunk)
    
    db_session.commit()
    return chunks
