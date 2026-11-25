import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings
from backend.app.core.database import Base, get_db
from backend.app.main import app
from backend.app.models.user import User
from backend.app.core.security import hash_password
from backend.app.repositories.user_repository import UserRepository

# Safeguard: Never allow tests to run against development liquidio.db
if settings.DATABASE_URL.endswith("liquidio.db"):
    test_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "liquidio_test_standalone.db"))
    settings.DATABASE_URL = f"sqlite:///{test_db_path}"

# Ensure a throwaway test secret is used
if not os.environ.get("JWT_SECRET") or os.environ.get("JWT_SECRET") == "supersecret-liquidio-dost-jwt-key-2026-citu":
    settings.JWT_SECRET = "test-throwaway-jwt-secret-liquidio-2026"

connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {"check_same_thread": False}

test_engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
    """Ensure schema is in place on test database."""
    Base.metadata.create_all(bind=test_engine)
    yield
    if "liquidio_test_standalone.db" in settings.DATABASE_URL:
        db_file = settings.DATABASE_URL.replace("sqlite:///", "")
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except OSError:
                pass

@pytest.fixture
def db_session():
    """Provides a fresh, isolated database session per test and cleans tables."""
    session = TestingSessionLocal()
    # Clean all records so each test executes in a clean slate
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()

    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db_session):
    """FastAPI TestClient with get_db dependency overridden to test db_session."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def create_user(db_session):
    """Helper fixture to create test users."""
    def _create(username: str, role: str, raw_password: str = "password123") -> User:
        user = User(
            username=username,
            password_hash=hash_password(raw_password),
            full_name=f"Test {username.capitalize()}",
            role=role,
            email=f"{username}@cit.edu",
            is_active=True
        )
        return UserRepository.create(db_session, user)
    return _create
