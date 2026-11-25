from datetime import date
from decimal import Decimal

from backend.app.models.line_item_budget import LineItemBudget
from backend.app.models.project import Project
from backend.app.repositories.activity_log_repository import ActivityLogRepository
from backend.app.repositories.project_repository import ProjectRepository
from backend.app.services.ledger_aggregation_service import (
    BURN_RATE_AHEAD_THRESHOLD_POINTS,
    LedgerAggregationService,
)


def get_auth_header(client, username, password):
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def create_project_record(
    db_session,
    code="DOST-SUM-01",
    start_date=date(2026, 1, 1),
    end_date=date(2026, 12, 31),
    dost_budget="100000.00",
    citu_budget="50000.00",
):
    project = Project(
        project_code=code,
        title=f"Project {code}",
        funding_agency="DOST",
        start_date=start_date,
        end_date=end_date,
        total_dost_budget=Decimal(dost_budget),
        total_citu_budget=Decimal(citu_budget),
    )
    return ProjectRepository.create(db_session, project)


def test_budget_summary_requires_auth(client):
    res = client.get("/api/projects/1/budget-summary")
    assert res.status_code == 401


def test_budget_summary_unknown_project_returns_404(client, create_user):
    create_user("sum_404", "USER", "password123")
    headers = get_auth_header(client, "sum_404", "password123")

    res = client.get("/api/projects/999999/budget-summary", headers=headers)
    assert res.status_code == 404


def test_budget_summary_empty_project_returns_zeros(client, create_user, db_session):
    create_user("sum_empty", "USER", "password123")
    headers = get_auth_header(client, "sum_empty", "password123")
    project = create_project_record(db_session, code="DOST-EMPTY")

    res = client.get(f"/api/projects/{project.id}/budget-summary", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["line_items"] == []
    assert Decimal(data["totals"]["total_dost_allotment"]) == Decimal("0.00")
    assert Decimal(data["totals"]["total_citu_allotment"]) == Decimal("0.00")
    assert Decimal(data["totals"]["total_dost_spent"]) == Decimal("0.00")
    assert Decimal(data["totals"]["total_citu_spent"]) == Decimal("0.00")
    assert Decimal(data["totals"]["total_dost_remaining"]) == Decimal("0.00")
    assert Decimal(data["totals"]["total_citu_remaining"]) == Decimal("0.00")
    assert Decimal(data["totals"]["total_dost_budget"]) == Decimal("100000.00")
    assert Decimal(data["totals"]["total_citu_budget"]) == Decimal("50000.00")
    assert data["receipt_quality"]["invalid_receipt_count"] == 0
    assert Decimal(data["receipt_quality"]["invalid_receipt_total_amount"]) == Decimal("0.00")
    assert data["receipt_quality"]["pending_review_count"] == 0
    assert Decimal(data["burn_rate"]["overall_spent_percent"]) == Decimal("0.00")


def test_budget_summary_aggregation_over_budget_and_receipt_quality(
    client, create_user, db_session
):
    create_user("sum_agg", "USER", "password123")
    headers = get_auth_header(client, "sum_agg", "password123")
    project = create_project_record(db_session, code="DOST-AGG-01")

    # Line item 1: DOST 10,000, CIT-U 5,000
    item1 = client.post(
        f"/api/projects/{project.id}/line-items",
        headers=headers,
        json={
            "item_code": "MOOE-1",
            "category_name": "Supplies",
            "dost_allotment": "10000.00",
            "citu_allotment": "5000.00",
        },
    ).json()["line_item"]

    # Line item 2: DOST 0.00 (tests zero-division), CIT-U 2,000
    item2 = client.post(
        f"/api/projects/{project.id}/line-items",
        headers=headers,
        json={
            "item_code": "EQ-2",
            "category_name": "Equipment",
            "dost_allotment": "0.00",
            "citu_allotment": "2000.00",
        },
    ).json()["line_item"]

    # Record valid DOST expense on item1 (4,000)
    r1 = client.post(
        "/api/expenses/manual",
        headers=headers,
        json={
            "project_id": project.id,
            "line_item_id": item1["id"],
            "funding_source": "DOST_REIMBURSABLE",
            "expense_date": "2026-03-01",
            "vendor_name": "Vendor A",
            "vendor_tin": "111-222",
            "vendor_address": "Cebu",
            "payor_type": "INSTITUTION",
            "total_amount": "4000.00",
        },
    )
    assert r1.status_code == 201

    # Record invalid/flagged CIT-U expense exceeding item1 CIT-U allotment (6,000 > 5,000)
    r2 = client.post(
        "/api/expenses/manual",
        headers=headers,
        json={
            "project_id": project.id,
            "line_item_id": item1["id"],
            "funding_source": "CITU_COUNTERPART",
            "expense_date": "2026-03-10",
            "vendor_name": "",
            "payor_type": "PERSONAL",
            "total_amount": "6000.00",
        },
    )
    assert r2.status_code == 201

    # Record valid CIT-U expense on item2 (500)
    r3 = client.post(
        "/api/expenses/manual",
        headers=headers,
        json={
            "project_id": project.id,
            "line_item_id": item2["id"],
            "funding_source": "CITU_COUNTERPART",
            "expense_date": "2026-03-15",
            "vendor_name": "Vendor B",
            "payor_type": "INSTITUTION",
            "total_amount": "500.00",
        },
    )
    assert r3.status_code == 201

    logs_before = len(ActivityLogRepository.get_all(db_session))
    res = client.get(f"/api/projects/{project.id}/budget-summary", headers=headers)
    assert res.status_code == 200
    logs_after = len(ActivityLogRepository.get_all(db_session))
    # Read-only endpoint must not emit audit logs
    assert logs_after == logs_before

    data = res.json()
    assert Decimal(data["totals"]["total_dost_allotment"]) == Decimal("10000.00")
    assert Decimal(data["totals"]["total_citu_allotment"]) == Decimal("7000.00")
    assert Decimal(data["totals"]["total_dost_spent"]) == Decimal("4000.00")
    assert Decimal(data["totals"]["total_citu_spent"]) == Decimal("6500.00")
    assert Decimal(data["totals"]["total_dost_remaining"]) == Decimal("6000.00")
    assert Decimal(data["totals"]["total_citu_remaining"]) == Decimal("500.00")

    by_code = {li["item_code"]: li for li in data["line_items"]}
    assert Decimal(by_code["MOOE-1"]["percent_spent_dost"]) == Decimal("40.00")
    assert Decimal(by_code["MOOE-1"]["percent_spent_citu"]) == Decimal("120.00")
    assert by_code["MOOE-1"]["is_over_budget_dost"] is False
    assert by_code["MOOE-1"]["is_over_budget_citu"] is True
    assert by_code["MOOE-1"]["data_mismatch"] is False

    # Zero-division handled cleanly
    assert Decimal(by_code["EQ-2"]["percent_spent_dost"]) == Decimal("0.00")
    assert Decimal(by_code["EQ-2"]["percent_spent_citu"]) == Decimal("25.00")

    # Receipt quality summary
    assert data["receipt_quality"]["invalid_receipt_count"] == 1
    assert Decimal(data["receipt_quality"]["invalid_receipt_total_amount"]) == Decimal("6000.00")
    assert data["receipt_quality"]["pending_review_count"] == 3


def test_budget_summary_data_mismatch_flag(client, create_user, db_session):
    create_user("sum_mismatch", "USER", "password123")
    headers = get_auth_header(client, "sum_mismatch", "password123")
    project = create_project_record(db_session, code="DOST-MISMATCH")

    item = client.post(
        f"/api/projects/{project.id}/line-items",
        headers=headers,
        json={
            "item_code": "MISM-1",
            "category_name": "Mismatch Item",
            "dost_allotment": "1000.00",
            "citu_allotment": "0.00",
        },
    ).json()["line_item"]

    # Corrupt remaining_dost directly to simulate drift from split_allocations
    row = db_session.get(LineItemBudget, item["id"])
    row.remaining_dost = Decimal("500.00")
    db_session.commit()

    res = client.get(f"/api/projects/{project.id}/budget-summary", headers=headers)
    assert res.status_code == 200
    assert res.json()["line_items"][0]["data_mismatch"] is True


def test_budget_summary_cross_project_isolation(client, create_user, db_session):
    create_user("sum_iso", "USER", "password123")
    headers = get_auth_header(client, "sum_iso", "password123")
    proj_a = create_project_record(db_session, code="DOST-ISO-A")
    proj_b = create_project_record(db_session, code="DOST-ISO-B")

    item_b = client.post(
        f"/api/projects/{proj_b.id}/line-items",
        headers=headers,
        json={
            "item_code": "ISO-B",
            "category_name": "Project B Item",
            "dost_allotment": "5000.00",
            "citu_allotment": "0.00",
        },
    ).json()["line_item"]

    client.post(
        "/api/expenses/manual",
        headers=headers,
        json={
            "project_id": proj_b.id,
            "line_item_id": item_b["id"],
            "funding_source": "DOST_REIMBURSABLE",
            "expense_date": "2026-04-01",
            "vendor_name": "",
            "payor_type": "PERSONAL",
            "total_amount": "2000.00",
        },
    )

    res_a = client.get(f"/api/projects/{proj_a.id}/budget-summary", headers=headers)
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["line_items"] == []
    assert Decimal(data_a["totals"]["total_dost_spent"]) == Decimal("0.00")
    assert data_a["receipt_quality"]["invalid_receipt_count"] == 0
    assert data_a["receipt_quality"]["pending_review_count"] == 0


def test_burn_rate_pace_thresholds(client, create_user, db_session):
    assert BURN_RATE_AHEAD_THRESHOLD_POINTS == Decimal("10.00")
    create_user("burn_user", "USER", "password123")
    headers = get_auth_header(client, "burn_user", "password123")

    # 100-day project: 2026-01-01 to 2026-04-11
    project = create_project_record(
        db_session,
        code="DOST-BURN",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 4, 11),
    )
    item = client.post(
        f"/api/projects/{project.id}/line-items",
        headers=headers,
        json={
            "item_code": "BURN-1",
            "category_name": "Burn Item",
            "dost_allotment": "10000.00",
            "citu_allotment": "0.00",
        },
    ).json()["line_item"]

    # Spend 50% (5,000 / 10,000)
    client.post(
        "/api/expenses/manual",
        headers=headers,
        json={
            "project_id": project.id,
            "line_item_id": item["id"],
            "funding_source": "DOST_REIMBURSABLE",
            "expense_date": "2026-01-15",
            "vendor_name": "Vendor Burn",
            "payor_type": "INSTITUTION",
            "total_amount": "5000.00",
        },
    )

    # At day 20 (20% elapsed) vs 50% spent -> +30 pts -> "ahead of pace"
    ahead = LedgerAggregationService.get_budget_summary(
        db_session, project.id, as_of_date=date(2026, 1, 21)
    )
    assert ahead.burn_rate.timeline_elapsed_percent == Decimal("20.00")
    assert ahead.burn_rate.overall_spent_percent == Decimal("50.00")
    assert ahead.burn_rate.pace_status == "ahead of pace"

    # At day 45 (45% elapsed) vs 50% spent -> +5 pts <= 10 -> "on track"
    ontrack = LedgerAggregationService.get_budget_summary(
        db_session, project.id, as_of_date=date(2026, 2, 15)
    )
    assert ontrack.burn_rate.timeline_elapsed_percent == Decimal("45.00")
    assert ontrack.burn_rate.pace_status == "on track"

    # Clamped at 0% before start and 100% after end
    before_start = LedgerAggregationService.get_budget_summary(
        db_session, project.id, as_of_date=date(2025, 12, 1)
    )
    assert before_start.burn_rate.timeline_elapsed_percent == Decimal("0.00")

    after_end = LedgerAggregationService.get_budget_summary(
        db_session, project.id, as_of_date=date(2026, 12, 1)
    )
    assert after_end.burn_rate.timeline_elapsed_percent == Decimal("100.00")

    # Invalid timeline (end_date == start_date) -> "no timeline data"
    bad_proj = create_project_record(
        db_session,
        code="DOST-NOTIME",
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 1),
    )
    no_time = LedgerAggregationService.get_budget_summary(db_session, bad_proj.id)
    assert no_time.burn_rate.timeline_elapsed_percent == Decimal("0.00")
    assert no_time.burn_rate.pace_status == "no timeline data"
