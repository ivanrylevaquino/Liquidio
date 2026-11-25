import json
from decimal import Decimal
from sqlalchemy import select

from backend.app.models.expense import Expense
from backend.app.models.line_item_budget import LineItemBudget
from backend.app.models.split_allocation import SplitAllocation
from backend.app.repositories.activity_log_repository import ActivityLogRepository


def get_auth_header(client, username, password):
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def setup_project_and_item(client, headers, code="DOST-EXP-01"):
    proj_res = client.post(
        "/api/projects",
        headers=headers,
        json={
            "project_code": code,
            "title": "Expense Test Project",
            "funding_agency": "DOST",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "total_dost_budget": "100000.00",
            "total_citu_budget": "50000.00",
        },
    )
    assert proj_res.status_code == 201
    project = proj_res.json()

    item_res = client.post(
        f"/api/projects/{project['id']}/line-items",
        headers=headers,
        json={
            "item_code": "MOOE-01",
            "category_name": "Supplies and Materials",
            "dost_allotment": "10000.00",
            "citu_allotment": "5000.00",
        },
    )
    assert item_res.status_code == 201
    line_item = item_res.json()["line_item"]
    return project, line_item


def test_manual_expense_requires_auth(client):
    res = client.post(
        "/api/expenses/manual",
        json={
            "project_id": 1,
            "line_item_id": 1,
            "funding_source": "DOST_REIMBURSABLE",
            "expense_date": "2026-05-01",
            "total_amount": "100.00",
        },
    )
    assert res.status_code == 401


def test_create_manual_expense_success_and_deducts_balance(client, create_user, db_session):
    user = create_user("exp_user", "USER", "password123")
    headers = get_auth_header(client, "exp_user", "password123")
    project, line_item = setup_project_and_item(client, headers)

    res = client.post(
        "/api/expenses/manual",
        headers=headers,
        json={
            "project_id": project["id"],
            "line_item_id": line_item["id"],
            "funding_source": "DOST_REIMBURSABLE",
            "expense_date": "2026-05-15",
            "vendor_name": "National Book Store",
            "vendor_tin": "123-456-789-000",
            "vendor_address": "Cebu City",
            "payor_type": "INSTITUTION",
            "payor_name": "CIT-U",
            "total_amount": "2500.00",
            "description": "Bond paper and printer ink",
        },
    )
    assert res.status_code == 201
    data = res.json()
    expense = data["expense"]
    validation = data["validation"]

    assert expense["project_id"] == project["id"]
    assert expense["encoded_by_id"] == user.id
    assert expense["description"] == "Bond paper and printer ink"
    assert expense["funding_source"] == "DOST_REIMBURSABLE"
    assert expense["is_valid_receipt"] is True
    assert validation["is_valid_receipt"] is True
    assert validation["errors"] == []
    assert validation["warnings"] == []

    # Verify single 100% split allocation row
    splits = list(
        db_session.execute(
            select(SplitAllocation).where(SplitAllocation.expense_id == expense["id"])
        ).scalars().all()
    )
    assert len(splits) == 1
    assert splits[0].funding_source == "DOST_REIMBURSABLE"
    assert Decimal(str(splits[0].allocated_amount)) == Decimal("2500.00")

    # Verify remaining_dost deducted immediately; remaining_citu unchanged
    updated_item = db_session.get(LineItemBudget, line_item["id"])
    assert Decimal(str(updated_item.remaining_dost)) == Decimal("7500.00")
    assert Decimal(str(updated_item.remaining_citu)) == Decimal("5000.00")

    # Verify EXPENSE_CREATED audit log
    logs = ActivityLogRepository.get_by_entity(db_session, "expenses", expense["id"])
    assert len(logs) == 1
    assert logs[0].action_type == "EXPENSE_CREATED"
    assert logs[0].user_id == user.id
    details = json.loads(logs[0].details_json)
    assert details["total_amount"] == "2500.00"


def test_validation_flags_save_expense_without_rejecting(client, create_user, db_session):
    create_user("flag_user", "USER", "password123")
    headers = get_auth_header(client, "flag_user", "password123")
    project, line_item = setup_project_and_item(client, headers, code="DOST-EXP-FLAG")

    # Triggers: timeline error, blank vendor error, PERSONAL payor error,
    # missing TIN/address warnings, and over-budget warning (> 5000 CIT-U)
    res = client.post(
        "/api/expenses/manual",
        headers=headers,
        json={
            "project_id": project["id"],
            "line_item_id": line_item["id"],
            "funding_source": "CITU_COUNTERPART",
            "expense_date": "2025-12-01",
            "vendor_name": "   ",
            "payor_type": "PERSONAL",
            "payor_name": "Juan Dela Cruz",
            "total_amount": "6000.00",
        },
    )
    assert res.status_code == 201
    data = res.json()
    validation = data["validation"]

    assert data["expense"]["is_valid_receipt"] is False
    assert validation["is_valid_receipt"] is False
    assert any("timeline" in msg.lower() for msg in validation["errors"])
    assert any("blank" in msg.lower() for msg in validation["errors"])
    assert any("Ineligible for DOST reimbursement" in msg for msg in validation["errors"])
    assert any("tin" in msg.lower() for msg in validation["warnings"])
    assert any("address" in msg.lower() for msg in validation["warnings"])
    assert any("over-budget" in msg.lower() for msg in validation["warnings"])

    # Balance is still deducted immediately
    updated_item = db_session.get(LineItemBudget, line_item["id"])
    assert Decimal(str(updated_item.remaining_citu)) == Decimal("-1000.00")


def test_manual_expense_4xx_rejections(client, create_user):
    create_user("err_user", "USER", "password123")
    headers = get_auth_header(client, "err_user", "password123")
    project_a, _ = setup_project_and_item(client, headers, code="DOST-EXP-A")
    _, item_b = setup_project_and_item(client, headers, code="DOST-EXP-B")

    # 1. Amount <= 0
    res_zero = client.post(
        "/api/expenses/manual",
        headers=headers,
        json={
            "project_id": project_a["id"],
            "line_item_id": item_b["id"],
            "funding_source": "DOST_REIMBURSABLE",
            "expense_date": "2026-05-01",
            "total_amount": "0.00",
        },
    )
    assert res_zero.status_code == 422

    # 2. Unknown project
    res_no_proj = client.post(
        "/api/expenses/manual",
        headers=headers,
        json={
            "project_id": 999999,
            "line_item_id": item_b["id"],
            "funding_source": "DOST_REIMBURSABLE",
            "expense_date": "2026-05-01",
            "total_amount": "100.00",
        },
    )
    assert res_no_proj.status_code == 404

    # 3. Line item belonging to another project
    res_cross = client.post(
        "/api/expenses/manual",
        headers=headers,
        json={
            "project_id": project_a["id"],
            "line_item_id": item_b["id"],
            "funding_source": "DOST_REIMBURSABLE",
            "expense_date": "2026-05-01",
            "total_amount": "100.00",
        },
    )
    assert res_cross.status_code == 400
    assert "does not belong" in res_cross.json()["detail"].lower()


def test_list_and_get_expenses_scoped_by_project(client, create_user):
    create_user("scope_user", "USER", "password123")
    headers = get_auth_header(client, "scope_user", "password123")
    project_a, item_a = setup_project_and_item(client, headers, code="DOST-SCOPE-A")
    project_b, _ = setup_project_and_item(client, headers, code="DOST-SCOPE-B")

    create_res = client.post(
        "/api/expenses/manual",
        headers=headers,
        json={
            "project_id": project_a["id"],
            "line_item_id": item_a["id"],
            "funding_source": "DOST_REIMBURSABLE",
            "expense_date": "2026-04-10",
            "vendor_name": "Acme Corp",
            "total_amount": "500.00",
        },
    )
    assert create_res.status_code == 201
    exp_id = create_res.json()["expense"]["id"]

    list_a = client.get(f"/api/projects/{project_a['id']}/expenses", headers=headers)
    assert list_a.status_code == 200
    assert list_a.json()["total_count"] == 1

    list_b = client.get(f"/api/projects/{project_b['id']}/expenses", headers=headers)
    assert list_b.status_code == 200
    assert list_b.json()["total_count"] == 0

    get_a = client.get(f"/api/projects/{project_a['id']}/expenses/{exp_id}", headers=headers)
    assert get_a.status_code == 200
    assert get_a.json()["id"] == exp_id

    get_b = client.get(f"/api/projects/{project_b['id']}/expenses/{exp_id}", headers=headers)
    assert get_b.status_code == 404


def test_manual_expense_rolls_back_on_audit_failure(client, create_user, db_session, monkeypatch):
    create_user("rb_user", "USER", "password123")
    headers = get_auth_header(client, "rb_user", "password123")
    project, line_item = setup_project_and_item(client, headers, code="DOST-ROLLBACK")

    def boom(*args, **kwargs):
        raise RuntimeError("Simulated audit log failure")

    monkeypatch.setattr(ActivityLogRepository, "insert", boom)

    try:
        client.post(
            "/api/expenses/manual",
            headers=headers,
            json={
                "project_id": project["id"],
                "line_item_id": line_item["id"],
                "funding_source": "DOST_REIMBURSABLE",
                "expense_date": "2026-06-01",
                "vendor_name": "Rollback Vendor",
                "total_amount": "1500.00",
            },
        )
    except RuntimeError:
        pass

    db_session.expire_all()
    expenses = list(
        db_session.execute(select(Expense).where(Expense.project_id == project["id"])).scalars().all()
    )
    splits = list(db_session.execute(select(SplitAllocation)).scalars().all())
    item_after = db_session.get(LineItemBudget, line_item["id"])

    assert len(expenses) == 0
    assert len(splits) == 0
    assert Decimal(str(item_after.remaining_dost)) == Decimal("10000.00")
