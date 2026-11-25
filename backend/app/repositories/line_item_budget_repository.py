from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Dict
from backend.app.models.line_item_budget import LineItemBudget
from backend.app.models.split_allocation import SplitAllocation

class LineItemBudgetRepository:
    """
    Data access repository for LineItemBudget entities.
    Enforces project-scoped queries and computes spent allocations.
    """
    @staticmethod
    def get_by_id(db: Session, item_id: int) -> LineItemBudget | None:
        return db.get(LineItemBudget, item_id)

    @staticmethod
    def get_by_project_and_id(db: Session, project_id: int, item_id: int) -> LineItemBudget | None:
        stmt = select(LineItemBudget).where(
            LineItemBudget.project_id == project_id,
            LineItemBudget.id == item_id
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_project_and_code(db: Session, project_id: int, item_code: str) -> LineItemBudget | None:
        stmt = select(LineItemBudget).where(
            LineItemBudget.project_id == project_id,
            func.lower(LineItemBudget.item_code) == item_code.lower().strip()
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_all_by_project(db: Session, project_id: int) -> List[LineItemBudget]:
        stmt = (
            select(LineItemBudget)
            .where(LineItemBudget.project_id == project_id)
            .order_by(LineItemBudget.id)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_spent_amounts(db: Session, line_item_id: int) -> Dict[str, Decimal]:
        """
        Aggregate spent amounts from split_allocations charged to this line item.
        Returns dict with spent_dost and spent_citu.
        """
        stmt_dost = select(func.coalesce(func.sum(SplitAllocation.allocated_amount), 0)).where(
            SplitAllocation.line_item_id == line_item_id,
            SplitAllocation.funding_source == "DOST_REIMBURSABLE"
        )
        spent_dost = Decimal(str(db.execute(stmt_dost).scalar()))

        stmt_citu = select(func.coalesce(func.sum(SplitAllocation.allocated_amount), 0)).where(
            SplitAllocation.line_item_id == line_item_id,
            SplitAllocation.funding_source == "CITU_COUNTERPART"
        )
        spent_citu = Decimal(str(db.execute(stmt_citu).scalar()))

        return {
            "spent_dost": spent_dost,
            "spent_citu": spent_citu
        }

    @staticmethod
    def create(db: Session, item: LineItemBudget) -> LineItemBudget:
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def update(db: Session, item: LineItemBudget) -> LineItemBudget:
        db.commit()
        db.refresh(item)
        return item
