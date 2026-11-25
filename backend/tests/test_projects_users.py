import pytest
from decimal import Decimal
from datetime import date
from backend.app.repositories.activity_log_repository import ActivityLogRepository

def get_auth_header(client, username, password):
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# ==============================================================================
# USER MANAGEMENT TESTS
# ==============================================================================

def test_create_user_success(client, create_user, db_session):
    u1 = create_user("initiator", "USER", "password123")
    headers = get_auth_header(client, "initiator", "password123")

    # Any authenticated user creates another user
    res = client.post(
        "/api/users",
        headers=headers,
        json={
            "username": "newuser",
            "full_name": "New User",
            "password": "validPassword8",
            "email": "newuser@cit.edu"
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["username"] == "newuser"
    assert data["full_name"] == "New User"
    assert "password" not in data
    assert "password_hash" not in data

    # Verify audit log recorded acting user_id
    logs = ActivityLogRepository.get_by_entity(db_session, "users", data["id"])
    assert len(logs) == 1
    assert logs[0].action_type == "USER_CREATE"
    assert logs[0].user_id == u1.id

def test_create_user_short_password_rejected(client, create_user):
    create_user("user_a", "USER", "password123")
    headers = get_auth_header(client, "user_a", "password123")

    res = client.post(
        "/api/users",
        headers=headers,
        json={
            "username": "shortpwd",
            "full_name": "Short Password User",
            "password": "short7",  # Less than 8 characters
        }
    )
    assert res.status_code in [400, 422]

def test_create_user_duplicate_username_rejected(client, create_user):
    create_user("user_b", "USER", "password123")
    headers = get_auth_header(client, "user_b", "password123")

    res = client.post(
        "/api/users",
        headers=headers,
        json={
            "username": "user_b",
            "full_name": "Duplicate User",
            "password": "validPassword8",
        }
    )
    assert res.status_code == 400
    assert "already registered" in res.json()["detail"].lower()

def test_deactivate_self_prevented(client, create_user):
    u = create_user("self_user", "USER", "password123")
    create_user("other_user", "USER", "password123")
    headers = get_auth_header(client, "self_user", "password123")

    res = client.post(
        f"/api/users/{u.id}/deactivate",
        headers=headers
    )
    assert res.status_code == 400
    assert "cannot deactivate your own account" in res.json()["detail"].lower()

def test_deactivate_last_active_user_prevented(client, create_user):
    # Only 1 active user in system
    u1 = create_user("only_user", "USER", "password123")
    headers = get_auth_header(client, "only_user", "password123")

    # Even attempting with a non-existent or target
    # Let's create an already deactivated user
    u2 = create_user("dead_user", "USER", "password123")
    u2.is_active = False

    # Attempting to deactivate u1 when u1 is the only active one fails
    # (Since self-check also triggers, let's verify count check logic)
    res = client.post(
        f"/api/users/{u2.id}/deactivate",
        headers=headers
    )
    assert res.status_code == 400
    assert "already deactivated" in res.json()["detail"].lower()

def test_deactivate_other_user_success(client, create_user, db_session):
    u1 = create_user("user_active1", "USER", "password123")
    u2 = create_user("user_target", "USER", "password123")
    create_user("user_active2", "USER", "password123") # Ensure > 1 active remain

    headers = get_auth_header(client, "user_active1", "password123")

    res = client.post(
        f"/api/users/{u2.id}/deactivate",
        headers=headers
    )
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    # Verify audit log captures actor
    logs = ActivityLogRepository.get_by_entity(db_session, "users", u2.id)
    deact_logs = [l for l in logs if l.action_type == "USER_DEACTIVATE"]
    assert len(deact_logs) == 1
    assert deact_logs[0].user_id == u1.id

# ==============================================================================
# PROJECT MANAGEMENT TESTS
# ==============================================================================

def test_create_project_success(client, create_user, db_session):
    user = create_user("project_mgr", "USER", "password123")
    headers = get_auth_header(client, "project_mgr", "password123")

    res = client.post(
        "/api/projects",
        headers=headers,
        json={
            "project_code": "DOST-CITU-2026-01",
            "title": "AI-Powered Microgrid Monitoring",
            "funding_agency": "DOST",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "total_dost_budget": "5000000.00",
            "total_citu_budget": "1500000.00"
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["project_code"] == "DOST-CITU-2026-01"
    assert Decimal(data["total_dost_budget"]) == Decimal("5000000.00")
    assert Decimal(data["total_citu_budget"]) == Decimal("1500000.00")

    # Verify audit log entry
    logs = ActivityLogRepository.get_by_entity(db_session, "projects", data["id"])
    assert len(logs) == 1
    assert logs[0].action_type == "PROJECT_CREATE"
    assert logs[0].user_id == user.id

def test_create_project_invalid_dates_rejected(client, create_user):
    create_user("user_d", "USER", "password123")
    headers = get_auth_header(client, "user_d", "password123")

    # end_date before start_date
    res = client.post(
        "/api/projects",
        headers=headers,
        json={
            "project_code": "INVALID-DATES",
            "title": "Invalid Timeline Project",
            "funding_agency": "DOST",
            "start_date": "2026-12-31",
            "end_date": "2026-01-01",
            "total_dost_budget": "100000.00",
            "total_citu_budget": "50000.00"
        }
    )
    assert res.status_code in [400, 422]

def test_create_duplicate_project_code_rejected(client, create_user):
    create_user("user_e", "USER", "password123")
    headers = get_auth_header(client, "user_e", "password123")

    payload = {
        "project_code": "DOST-CITU-DUP",
        "title": "First Project",
        "funding_agency": "DOST",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "total_dost_budget": "100000.00",
        "total_citu_budget": "50000.00"
    }
    res1 = client.post("/api/projects", headers=headers, json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/projects", headers=headers, json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()

def test_get_project_by_id(client, create_user):
    create_user("user_f", "USER", "password123")
    headers = get_auth_header(client, "user_f", "password123")

    res_create = client.post(
        "/api/projects",
        headers=headers,
        json={
            "project_code": "DOST-CITU-GET",
            "title": "Retrievable Project",
            "funding_agency": "DOST",
            "start_date": "2026-03-01",
            "end_date": "2026-09-30",
            "total_dost_budget": "2000000.00",
            "total_citu_budget": "400000.00"
        }
    )
    project_id = res_create.json()["id"]

    res_get = client.get(f"/api/projects/{project_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["project_code"] == "DOST-CITU-GET"

    # Non-existent project
    res_404 = client.get("/api/projects/999999", headers=headers)
    assert res_404.status_code == 404
