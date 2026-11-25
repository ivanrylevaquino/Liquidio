import pytest
import json
from backend.app.models.user import User
from backend.app.repositories.activity_log_repository import ActivityLogRepository
from backend.app.core.security import create_access_token

def test_login_success(client, db_session, create_user):
    create_user("alice", "USER", "password123")

    response = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "alice"
    assert data["user"]["role"] == "USER"
    # Ensure passwords and hashes are NEVER returned in response
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]

    # Verify audit log recorded LOGIN_SUCCESS
    logs = ActivityLogRepository.get_all(db_session)
    assert len(logs) == 1
    log = logs[0]
    assert log.action_type == "LOGIN_SUCCESS"
    assert log.entity_name == "users"
    details = json.loads(log.details_json)
    assert details["username"] == "alice"
    assert "password" not in details
    assert "password_hash" not in details

def test_login_failed_wrong_password(client, db_session, create_user):
    create_user("bob", "USER", "correctPassword123")

    response = client.post(
        "/api/auth/login",
        json={"username": "bob", "password": "wrongPassword123"}
    )
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]

    # Verify audit log recorded LOGIN_FAILED with NO password in details
    logs = ActivityLogRepository.get_all(db_session)
    assert len(logs) == 1
    log = logs[0]
    assert log.action_type == "LOGIN_FAILED"
    assert "wrongpassword" not in log.details_json.lower()
    details = json.loads(log.details_json)
    assert details["username"] == "bob"
    assert details["reason"] == "Invalid credentials"
    assert "password" not in details

def test_login_failed_nonexistent_user(client, db_session):
    response = client.post(
        "/api/auth/login",
        json={"username": "ghost_user", "password": "anyPassword123"}
    )
    assert response.status_code == 401

    # Verify audit log recorded LOGIN_FAILED with user_id=None
    logs = ActivityLogRepository.get_all(db_session)
    assert len(logs) == 1
    log = logs[0]
    assert log.user_id is None
    assert log.action_type == "LOGIN_FAILED"
    assert "anypassword" not in log.details_json.lower()
    details = json.loads(log.details_json)
    assert details["attempted_username"] == "ghost_user"
    assert "password" not in details

def test_no_token_returns_401(client):
    """Protected endpoints refuse requests without valid credentials."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_deactivated_user_refused(client, create_user, db_session):
    """Deactivated user cannot log in and token requests are refused."""
    user = create_user("charlie", "USER", "activePass123")
    user.is_active = False
    db_session.commit()

    # 1. Login attempt as deactivated user -> 403 Forbidden
    res_login = client.post(
        "/api/auth/login",
        json={"username": "charlie", "password": "activePass123"}
    )
    assert res_login.status_code == 403
    assert "deactivated" in res_login.json()["detail"].lower()

    # 2. Pre-existing valid token used for deactivated user -> 403 Forbidden
    token = create_access_token({"sub": str(user.id), "username": user.username, "role": user.role})
    res_me = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_me.status_code == 403
    assert "deactivated" in res_me.json()["detail"].lower()

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
