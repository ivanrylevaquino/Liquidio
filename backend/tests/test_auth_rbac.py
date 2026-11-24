import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import json

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.core.security import hash_password
from backend.app.models.user import User
from backend.app.models.activity_log import ActivityLog
from backend.app.repositories.user_repository import UserRepository
from backend.app.repositories.activity_log_repository import ActivityLogRepository
from backend.app.core.dependencies import require_role
from fastapi import HTTPException

# Isolated in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def create_test_user(username: str, role: str, raw_password: str = "password123") -> User:
    db = TestingSessionLocal()
    user = User(
        username=username,
        password_hash=hash_password(raw_password),
        full_name=f"Test {username.capitalize()}",
        role=role,
        email=f"{username}@cit.edu",
        is_active=True
    )
    user = UserRepository.create(db, user)
    db.close()
    return user

def test_login_success():
    create_test_user("admin_user", "ADMIN", "secretAdmin123")

    response = client.post(
        "/api/auth/login",
        json={"username": "admin_user", "password": "secretAdmin123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin_user"
    assert data["user"]["role"] == "ADMIN"
    # Ensure password hash is NEVER returned in response
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]

    # Verify audit log recorded LOGIN_SUCCESS
    db = TestingSessionLocal()
    logs = ActivityLogRepository.get_all(db)
    assert len(logs) == 1
    log = logs[0]
    assert log.action_type == "LOGIN_SUCCESS"
    assert log.entity_name == "users"
    details = json.loads(log.details_json)
    assert details["username"] == "admin_user"
    assert "password" not in details
    assert "password_hash" not in details
    db.close()

def test_login_failed_wrong_password():
    create_test_user("encoder_user", "ENCODER", "correctPassword")

    response = client.post(
        "/api/auth/login",
        json={"username": "encoder_user", "password": "wrongPassword"}
    )
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]

    # Verify audit log recorded LOGIN_FAILED with NO password or hash in details
    db = TestingSessionLocal()
    logs = ActivityLogRepository.get_all(db)
    assert len(logs) == 1
    log = logs[0]
    assert log.action_type == "LOGIN_FAILED"
    assert "wrongpassword" not in log.details_json.lower()
    assert "correctpassword" not in log.details_json.lower()
    details = json.loads(log.details_json)
    assert details["username"] == "encoder_user"
    assert details["reason"] == "Invalid credentials"
    assert "password" not in details
    db.close()

def test_login_failed_nonexistent_user():
    response = client.post(
        "/api/auth/login",
        json={"username": "ghost_user", "password": "anyPassword"}
    )
    assert response.status_code == 401

    # Verify audit log recorded LOGIN_FAILED with user_id=None
    db = TestingSessionLocal()
    logs = ActivityLogRepository.get_all(db)
    assert len(logs) == 1
    log = logs[0]
    assert log.user_id is None
    assert log.action_type == "LOGIN_FAILED"
    assert "anypassword" not in log.details_json.lower()
    details = json.loads(log.details_json)
    assert details["attempted_username"] == "ghost_user"
    assert "password" not in details
    db.close()

def test_rbac_endpoint_access():
    create_test_user("encoder_user", "ENCODER", "encoderPass")
    create_test_user("admin_user", "ADMIN", "adminPass")

    # 1. Login as ENCODER
    res_enc = client.post("/api/auth/login", json={"username": "encoder_user", "password": "encoderPass"})
    enc_token = res_enc.json()["access_token"]

    # Encoder accesses /api/auth/me -> 200 OK
    res_me_enc = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {enc_token}"}
    )
    assert res_me_enc.status_code == 200
    assert res_me_enc.json()["role"] == "ENCODER"

    # Encoder accesses /api/auth/admin-check (ADMIN only) -> 403 Forbidden
    res_forbidden = client.get(
        "/api/auth/admin-check",
        headers={"Authorization": f"Bearer {enc_token}"}
    )
    assert res_forbidden.status_code == 403
    assert "Access denied" in res_forbidden.json()["detail"]

    # 2. Login as ADMIN
    res_adm = client.post("/api/auth/login", json={"username": "admin_user", "password": "adminPass"})
    adm_token = res_adm.json()["access_token"]

    # Admin accesses /api/auth/admin-check -> 200 OK
    res_allowed = client.get(
        "/api/auth/admin-check",
        headers={"Authorization": f"Bearer {adm_token}"}
    )
    assert res_allowed.status_code == 200
    assert res_allowed.json()["role"] == "ADMIN"

def test_rbac_dependency_unit_level():
    """Unit test for require_role callable."""
    admin_checker = require_role("ADMIN")
    admin_user = User(id=1, username="admin", role="ADMIN", is_active=True, full_name="Admin", password_hash="x")
    encoder_user = User(id=2, username="encoder", role="ENCODER", is_active=True, full_name="Encoder", password_hash="x")

    # Allowed
    assert admin_checker(current_user=admin_user).role == "ADMIN"

    # Forbidden
    with pytest.raises(HTTPException) as exc_info:
        admin_checker(current_user=encoder_user)
    assert exc_info.value.status_code == 403
    assert "Access denied" in exc_info.value.detail

def test_activity_log_repository_immutability():
    """Verify that ActivityLogRepository only exposes insert and read methods."""
    methods = [m for m in dir(ActivityLogRepository) if not m.startswith("_")]
    assert "insert" in methods
    assert "get_all" in methods
    assert "get_by_user_id" in methods
    assert "get_by_entity" in methods

    # Verify NO update or delete methods exist on the repository
    assert not any("update" in m.lower() for m in methods), "Audit repository must not have update methods"
    assert not any("delete" in m.lower() for m in methods), "Audit repository must not have delete methods"
