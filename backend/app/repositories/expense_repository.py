from typing import List
from sqlalchemy import select, desc
from sqlalchemy.orm import Session, joinedload

from backend.app.models.expense import Expense


class ExpenseRepository:
    """
    Data access repository for Expense entities.
    Every query is scoped by project_id.
    """
    @staticmethod
    def get_by_project_and_id(db: Session, project_id: int, expense_id: int) -> Expense | None:
        stmt = (
            select(Expense)
            .options(joinedload(Expense.splits))
            .where(
                Expense.project_id == project_id,
                Expense.id == expense_id
            )
        )
        return db.execute(stmt).unique().scalar_one_or_none()

    @staticmethod
    def get_all_by_project(
        db: Session,
        project_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Expense]:
        stmt = (
            select(Expense)
            .options(joinedload(Expense.splits))
            .where(Expense.project_id == project_id)
            .order_by(desc(Expense.expense_date), desc(Expense.id))
            .offset(skip)
            .limit(limit)
        )
        return list(db.execute(stmt).unique().scalars().all())
