import pytest
from decimal import Decimal
from datetime import date
import json

from backend.app.models.project import Project
from backend.app.models.expense import Expense
from backend.app.models.split_allocation import SplitAllocation
from backend.app.repositories.activity_log_repository import ActivityLogRepository
from backend.app.repositories.project_repository import ProjectRepository

def get_auth_header(client, username, password):
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_project(db_session):
    p = Project(
        project_code="DOST-TEST-01",
        title="Test Line Item Project",
        funding_agency="DOST",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        total_dost_budget=Decimal("500000.00"),
        total_citu_budget=Decimal("150000.00")
    )
    return ProjectRepository.create(db_session, p)

def test_create_line_item_success_and_initial_balances(client, create_user, test_project, db_session):
    u = create_user("budget_mgr", "USER", "password123")
    headers = get_auth_header(client, "budget_mgr", "password123")

    res = client.post(
        f"/api/projects/{test_project.id}/line-items",
        headers=headers,
        json={
            "item_code": "PS",
            "category_name": "Personnel Services",
            "dost_allotment": "200000.00",
            "citu_allotment": "50000.00"
        }
    )
    assert res.status_code == 201
    data = res.json()["line_item"]
    assert data["item_code"] == "PS"
    assert Decimal(data["dost_allotment"]) == Decimal("200000.00")
    assert Decimal(data["citu_allotment"]) == Decimal("50000.00")
    # Rule: on create, remaining = allotment
    assert Decimal(data["remaining_dost"]) == Decimal("200000.00")
    assert Decimal(data["remaining_citu"]) == Decimal("50000.00")

    # Verify audit log recorded BUDGET_LINE_CREATED with before/after
    logs = ActivityLogRepository.get_by_entity(db_session, "line_item_budgets", data["id"])
    assert len(logs) == 1
    log = logs[0]
    assert log.action_type == "BUDGET_LINE_CREATED"
    assert log.user_id == u.id
    details = json.loads(log.details_json)
    assert details["before"]["dost_allotment"] == "0.00"
    assert details["after"]["dost_allotment"] == "200000.00"

def test_negative_allotment_rejected(client, create_user, test_project):
    create_user("budget_mgr", "USER", "password123")
    headers = get_auth_header(client, "budget_mgr", "password123")

    res = client.post(
        f"/api/projects/{test_project.id}/line-items",
        headers=headers,
        json={
            "item_code": "MOOE",
            "category_name": "Maintenance & Other",
            "dost_allotment": "-500.00",
            "citu_allotment": "100.00"
        }
    )
    assert res.status_code in [400, 422]

def test_duplicate_item_code_in_same_project_rejected(client, create_user, test_project):
    create_user("budget_mgr", "USER", "password123")
    headers = get_auth_header(client, "budget_mgr", "password123")

    payload = {
        "item_code": "CO",
        "category_name": "Capital Outlay",
        "dost_allotment": "100000.00",
        "citu_allotment": "0.00"
    }
    res1 = client.post(f"/api/projects/{test_project.id}/line-items", headers=headers, json=payload)
    assert res1.status_code == 201

    # Same item code in same project rejected
    res2 = client.post(f"/api/projects/{test_project.id}/line-items", headers=headers, json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()

def test_cross_project_isolation(client, create_user, test_project, db_session):
    create_user("budget_mgr", "USER", "password123")
    headers = get_auth_header(client, "budget_mgr", "password123")

    # Create Line item in test_project
    res_item = client.post(
        f"/api/projects/{test_project.id}/line-items",
        headers=headers,
        json={
            "item_code": "PS",
            "category_name": "Personnel Services",
            "dost_allotment": "100000.00",
            "citu_allotment": "0.00"
        }
    )
    item_id = res_item.json()["line_item"]["id"]

    # Create Project B
    p_b = Project(
        project_code="PROJECT-B",
        title="Other Project",
        funding_agency="DOST",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        total_dost_budget=Decimal("100000.00"),
        total_citu_budget=Decimal("0.00")
    )
    p_b = ProjectRepository.create(db_session, p_b)

    # Attempting to access item_id through Project B returns 404
    res_cross = client.get(
        f"/api/projects/{p_b.id}/line-items/{item_id}",
        headers=headers
    )
    assert res_cross.status_code == 404

    # Attempting to update item_id through Project B returns 404
    res_cross_put = client.put(
        f"/api/projects/{p_b.id}/line-items/{item_id}",
        headers=headers,
        json={"dost_allotment": "120000.00", "citu_allotment": "0.00"}
    )
    assert res_cross_put.status_code == 404

def test_update_line_item_recomputes_remaining(client, create_user, test_project, db_session):
    u = create_user("budget_mgr", "USER", "password123")
    headers = get_auth_header(client, "budget_mgr", "password123")

    # 1. Create line item
    res = client.post(
        f"/api/projects/{test_project.id}/line-items",
        headers=headers,
        json={
            "item_code": "MOOE",
            "category_name": "Operating Expenses",
            "dost_allotment": "100000.00",
            "citu_allotment": "20000.00"
        }
    )
    item_id = res.json()["line_item"]["id"]

    # 2. Simulate an expense and split allocation spending 30,000 DOST and 5,000 CIT-U
    exp = Expense(
        project_id=test_project.id,
        encoded_by_id=u.id,
        line_item_id=item_id,
        expense_date=date(2026, 3, 1),
        vendor_name="National Bookstore",
        payor_name="CIT-U",
        payor_type="INSTITUTION",
        total_amount=Decimal("35000.00"),
        is_valid_receipt=True,
        status="PENDING_REVIEW"
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)

    split_dost = SplitAllocation(
        expense_id=exp.id,
        line_item_id=item_id,
        funding_source="DOST_REIMBURSABLE",
        allocated_amount=Decimal("30000.00")
    )
    split_citu = SplitAllocation(
        expense_id=exp.id,
        line_item_id=item_id,
        funding_source="CITU_COUNTERPART",
        allocated_amount=Decimal("5000.00")
    )
    db_session.add_all([split_dost, split_citu])
    db_session.commit()

    # 3. Update line item allotment to DOST 150,000 and CIT-U 30,000
    res_put = client.put(
        f"/api/projects/{test_project.id}/line-items/{item_id}",
        headers=headers,
        json={
            "dost_allotment": "150000.00",
            "citu_allotment": "30000.00",
            "category_name": "Operating Expenses Updated"
        }
    )
    assert res_put.status_code == 200
    updated = res_put.json()["line_item"]
    # Recomputed remaining = new allotment - spent
    assert Decimal(updated["dost_allotment"]) == Decimal("150000.00")
    assert Decimal(updated["citu_allotment"]) == Decimal("30000.00")
    assert Decimal(updated["remaining_dost"]) == Decimal("120000.00")  # 150,000 - 30,000
    assert Decimal(updated["remaining_citu"]) == Decimal("25000.00")   # 30,000 - 5,000

    # Verify audit log recorded BUDGET_LINE_UPDATED with before and after
    logs = ActivityLogRepository.get_by_entity(db_session, "line_item_budgets", item_id)
    update_logs = [l for l in logs if l.action_type == "BUDGET_LINE_UPDATED"]
    assert len(update_logs) == 1
    details = json.loads(update_logs[0].details_json)
    assert details["before"]["dost_allotment"] == "100000.00"
    assert details["after"]["dost_allotment"] == "150000.00"

def test_refuse_allotment_reduction_below_spent(client, create_user, test_project, db_session):
    u = create_user("budget_mgr", "USER", "password123")
    headers = get_auth_header(client, "budget_mgr", "password123")

    res = client.post(
        f"/api/projects/{test_project.id}/line-items",
        headers=headers,
        json={
            "item_code": "TRAVEL",
            "category_name": "Travel Expenses",
            "dost_allotment": "50000.00",
            "citu_allotment": "10000.00"
        }
    )
    item_id = res.json()["line_item"]["id"]

    # Allocate 40,000 to DOST
    exp = Expense(
        project_id=test_project.id,
        encoded_by_id=u.id,
        line_item_id=item_id,
        expense_date=date(2026, 3, 5),
        vendor_name="Cebu Pacific",
        payor_name="CIT-U",
        payor_type="INSTITUTION",
        total_amount=Decimal("40000.00"),
        is_valid_receipt=True,
        status="PENDING_REVIEW"
    )
    db_session.add(exp)
    db_session.commit()
    split = SplitAllocation(
        expense_id=exp.id,
        line_item_id=item_id,
        funding_source="DOST_REIMBURSABLE",
        allocated_amount=Decimal("40000.00")
    )
    db_session.add(split)
    db_session.commit()

    # Attempting to reduce allotment to 35,000 (< 40,000 spent) must be rejected
    res_bad_put = client.put(
        f"/api/projects/{test_project.id}/line-items/{item_id}",
        headers=headers,
        json={
            "dost_allotment": "35000.00",
            "citu_allotment": "10000.00"
        }
    )
    assert res_bad_put.status_code == 400
    assert "already been spent" in res_bad_put.json()["detail"].lower()

def test_project_total_overrun_warning(client, create_user, test_project):
    """
    If the sum of line items exceeds project totals, return a warning but still save.
    test_project has total_dost_budget = 500,000.00.
    """
    create_user("budget_mgr", "USER", "password123")
    headers = get_auth_header(client, "budget_mgr", "password123")

    res = client.post(
        f"/api/projects/{test_project.id}/line-items",
        headers=headers,
        json={
            "item_code": "OVERRUN_PS",
            "category_name": "Over Budget PS",
            "dost_allotment": "600000.00",  # Exceeds project total (500,000)
            "citu_allotment": "10000.00"
        }
    )
    assert res.status_code == 201
    assert len(res.json()["warnings"]) > 0
    assert "exceeds" in res.json()["warnings"][0].lower()
