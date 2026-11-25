from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.repositories.budget_summary_repository import BudgetSummaryRepository
from backend.app.repositories.line_item_budget_repository import LineItemBudgetRepository
from backend.app.repositories.project_repository import ProjectRepository
from backend.app.schemas.budget_summary import (
    BudgetSummaryResponse,
    BurnRateSummary,
    LineItemBudgetSummary,
    ProjectBudgetTotals,
    ReceiptQualitySummary,
)

# Burn-rate pace threshold: flag "ahead of pace" when overall spent % exceeds
# timeline elapsed % by more than 10 percentage points.
BURN_RATE_AHEAD_THRESHOLD_POINTS = Decimal("10.00")
_TWO_PLACES = Decimal("0.01")
_ZERO = Decimal("0.00")
_HUNDRED = Decimal("100.00")


def _q2(value: Decimal) -> Decimal:
    return Decimal(str(value)).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


def _percent(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        return _ZERO
    return ((numerator / denominator) * _HUNDRED).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


class LedgerAggregationService:
    """
    Read-only aggregation service for UC-1.3: Budget vs. Actual Dashboard.
    Performs no database writes and emits no audit log entries.
    """
    @staticmethod
    def get_budget_summary(
        db: Session,
        project_id: int,
        as_of_date: date | None = None
    ) -> BudgetSummaryResponse:
        project = ProjectRepository.get_by_id(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} does not exist."
            )

        items = LineItemBudgetRepository.get_all_by_project(db, project_id)
        spent_map = BudgetSummaryRepository.get_spent_by_line_item(db, project_id)
        receipt_stats = BudgetSummaryRepository.get_receipt_quality_stats(db, project_id)

        line_item_summaries: List[LineItemBudgetSummary] = []
        total_dost_allotment = _ZERO
        total_citu_allotment = _ZERO
        total_dost_spent = _ZERO
        total_citu_spent = _ZERO
        total_dost_remaining = _ZERO
        total_citu_remaining = _ZERO

        for item in items:
            item_spent = spent_map.get(item.id, {})
            dost_spent = _q2(item_spent.get("DOST_REIMBURSABLE", _ZERO))
            citu_spent = _q2(item_spent.get("CITU_COUNTERPART", _ZERO))
            dost_allot = _q2(item.dost_allotment)
            citu_allot = _q2(item.citu_allotment)
            rem_dost = _q2(item.remaining_dost)
            rem_citu = _q2(item.remaining_citu)

            data_mismatch = (
                (dost_allot - rem_dost) != dost_spent
                or (citu_allot - rem_citu) != citu_spent
            )

            line_item_summaries.append(
                LineItemBudgetSummary(
                    line_item_id=item.id,
                    item_code=item.item_code,
                    category_name=item.category_name,
                    dost_allotment=dost_allot,
                    citu_allotment=citu_allot,
                    dost_spent=dost_spent,
                    citu_spent=citu_spent,
                    remaining_dost=rem_dost,
                    remaining_citu=rem_citu,
                    percent_spent_dost=_percent(dost_spent, dost_allot),
                    percent_spent_citu=_percent(citu_spent, citu_allot),
                    is_over_budget_dost=dost_spent > dost_allot,
                    is_over_budget_citu=citu_spent > citu_allot,
                    data_mismatch=data_mismatch,
                )
            )

            total_dost_allotment += dost_allot
            total_citu_allotment += citu_allot
            total_dost_spent += dost_spent
            total_citu_spent += citu_spent
            total_dost_remaining += rem_dost
            total_citu_remaining += rem_citu

        totals = ProjectBudgetTotals(
            total_dost_budget=_q2(project.total_dost_budget),
            total_citu_budget=_q2(project.total_citu_budget),
            total_dost_allotment=_q2(total_dost_allotment),
            total_citu_allotment=_q2(total_citu_allotment),
            total_dost_spent=_q2(total_dost_spent),
            total_citu_spent=_q2(total_citu_spent),
            total_dost_remaining=_q2(total_dost_remaining),
            total_citu_remaining=_q2(total_citu_remaining),
        )

        receipt_quality = ReceiptQualitySummary(
            invalid_receipt_count=int(receipt_stats["invalid_receipt_count"]),
            invalid_receipt_total_amount=_q2(receipt_stats["invalid_receipt_total_amount"]),
            pending_review_count=int(receipt_stats["pending_review_count"]),
        )

        overall_allotment = totals.total_dost_allotment + totals.total_citu_allotment
        overall_spent = totals.total_dost_spent + totals.total_citu_spent
        overall_spent_percent = _percent(overall_spent, overall_allotment)

        today = as_of_date or date.today()
        if not project.start_date or not project.end_date or project.end_date <= project.start_date:
            timeline_elapsed_percent = _ZERO
            pace_status = "no timeline data"
        else:
            total_days = Decimal((project.end_date - project.start_date).days)
            elapsed_days = Decimal((today - project.start_date).days)
            raw_elapsed = (elapsed_days / total_days) * _HUNDRED
            clamped_elapsed = max(_ZERO, min(_HUNDRED, raw_elapsed))
            timeline_elapsed_percent = clamped_elapsed.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

            if overall_spent_percent > (timeline_elapsed_percent + BURN_RATE_AHEAD_THRESHOLD_POINTS):
                pace_status = "ahead of pace"
            else:
                pace_status = "on track"

        burn_rate = BurnRateSummary(
            timeline_elapsed_percent=timeline_elapsed_percent,
            overall_spent_percent=overall_spent_percent,
            pace_status=pace_status,
        )

        return BudgetSummaryResponse(
            project_id=project.id,
            project_code=project.project_code,
            project_title=project.title,
            start_date=project.start_date,
            end_date=project.end_date,
            totals=totals,
            line_items=line_item_summaries,
            receipt_quality=receipt_quality,
            burn_rate=burn_rate,
        )
