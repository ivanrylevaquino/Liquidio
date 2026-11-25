from decimal import Decimal
from typing import Dict
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from backend.app.models.expense import Expense
from backend.app.models.line_item_budget import LineItemBudget
from backend.app.models.split_allocation import SplitAllocation


class BudgetSummaryRepository:
    """
    Read-only aggregation repository for UC-1.3 budget-vs-actual summaries.
    All queries are strictly scoped by project_id.
    """
    @staticmethod
    def get_spent_by_line_item(db: Session, project_id: int) -> Dict[int, Dict[str, Decimal]]:
        """
        Aggregate spent amounts from split_allocations grouped by line_item_id and funding_source,
        scoped to the given project_id.
        """
        stmt = (
            select(
                SplitAllocation.line_item_id,
                SplitAllocation.funding_source,
                func.coalesce(func.sum(SplitAllocation.allocated_amount), 0),
            )
            .join(LineItemBudget, SplitAllocation.line_item_id == LineItemBudget.id)
            .join(Expense, SplitAllocation.expense_id == Expense.id)
            .where(
                LineItemBudget.project_id == project_id,
                Expense.project_id == project_id,
            )
            .group_by(SplitAllocation.line_item_id, SplitAllocation.funding_source)
        )

        result: Dict[int, Dict[str, Decimal]] = {}
        for line_item_id, funding_source, total in db.execute(stmt).all():
            if line_item_id not in result:
                result[line_item_id] = {}
            result[line_item_id][funding_source] = Decimal(str(total))
        return result

    @staticmethod
    def get_receipt_quality_stats(db: Session, project_id: int) -> Dict[str, int | Decimal]:
        """
        Aggregate invalid receipt count/amount and pending review count for a project.
        """
        stmt = (
            select(
                func.coalesce(
                    func.sum(case((Expense.is_valid_receipt.is_(False), 1), else_=0)),
                    0,
                ),
                func.coalesce(
                    func.sum(case((Expense.is_valid_receipt.is_(False), Expense.total_amount), else_=0)),
                    0,
                ),
                func.coalesce(
                    func.sum(case((Expense.status == "PENDING_REVIEW", 1), else_=0)),
                    0,
                ),
            )
            .where(Expense.project_id == project_id)
        )
        invalid_count, invalid_amount, pending_count = db.execute(stmt).one()
        return {
            "invalid_receipt_count": int(invalid_count or 0),
            "invalid_receipt_total_amount": Decimal(str(invalid_amount or 0)),
            "pending_review_count": int(pending_count or 0),
        }
