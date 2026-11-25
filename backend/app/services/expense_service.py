from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.expense import Expense
from backend.app.models.split_allocation import SplitAllocation
from backend.app.models.user import User
from backend.app.repositories.activity_log_repository import ActivityLogRepository
from backend.app.repositories.expense_repository import ExpenseRepository
from backend.app.repositories.line_item_budget_repository import LineItemBudgetRepository
from backend.app.repositories.project_repository import ProjectRepository
from backend.app.schemas.expense import (
    ExpenseRead,
    ManualExpenseCreate,
    ManualExpenseResponse,
    ProjectExpensesListResponse,
)
from backend.app.services.expense_validation_service import ExpenseValidationService


def _serialize_expense(expense: Expense) -> ExpenseRead:
    funding_source = expense.splits[0].funding_source if expense.splits else None
    data = ExpenseRead.model_validate(expense)
    data.funding_source = funding_source
    return data


class ExpenseService:
    """
    Business service encapsulating UC-1.2: Manual Expense Entry.
    Executes expense creation, single 100% split allocation, immediate balance deduction,
    and EXPENSE_CREATED audit logging inside a single atomic database transaction.
    """
    @staticmethod
    def create_manual_expense(
        db: Session,
        expense_in: ManualExpenseCreate,
        acting_user: User,
        client_ip: str | None = None
    ) -> ManualExpenseResponse:
        if expense_in.total_amount <= Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expense total_amount must be greater than zero."
            )

        project = ProjectRepository.get_by_id(db, expense_in.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {expense_in.project_id} does not exist."
            )

        line_item = LineItemBudgetRepository.get_by_project_and_id(
            db, expense_in.project_id, expense_in.line_item_id
        )
        if not line_item:
            other_item = LineItemBudgetRepository.get_by_id(db, expense_in.line_item_id)
            if other_item is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Line item does not belong to the specified project."
                )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Line item with ID {expense_in.line_item_id} does not exist."
            )

        # Compute validation flags prior to deducting remaining balance
        validation = ExpenseValidationService.validate(
            project=project,
            line_item=line_item,
            funding_source=expense_in.funding_source,
            expense_date=expense_in.expense_date,
            vendor_name=expense_in.vendor_name,
            vendor_tin=expense_in.vendor_tin,
            vendor_address=expense_in.vendor_address,
            payor_type=expense_in.payor_type,
            total_amount=expense_in.total_amount,
        )

        # Single atomic transaction: expense + split row + balance deduction + audit log
        try:
            new_expense = Expense(
                project_id=project.id,
                encoded_by_id=acting_user.id,
                line_item_id=line_item.id,
                expense_date=expense_in.expense_date,
                vendor_name=expense_in.vendor_name.strip(),
                vendor_tin=expense_in.vendor_tin.strip() if expense_in.vendor_tin else None,
                vendor_address=expense_in.vendor_address.strip() if expense_in.vendor_address else None,
                payor_name=expense_in.payor_name.strip(),
                payor_type=expense_in.payor_type,
                total_amount=expense_in.total_amount,
                description=expense_in.description.strip() if expense_in.description else None,
                is_valid_receipt=validation.is_valid_receipt,
                status="PENDING_REVIEW",
            )
            db.add(new_expense)
            db.flush()

            split_row = SplitAllocation(
                expense_id=new_expense.id,
                line_item_id=line_item.id,
                funding_source=expense_in.funding_source,
                allocated_amount=expense_in.total_amount,
                is_overridden=False,
            )
            db.add(split_row)

            if expense_in.funding_source == "DOST_REIMBURSABLE":
                line_item.remaining_dost = Decimal(str(line_item.remaining_dost)) - expense_in.total_amount
            else:
                line_item.remaining_citu = Decimal(str(line_item.remaining_citu)) - expense_in.total_amount

            ActivityLogRepository.insert(
                db=db,
                action_type="EXPENSE_CREATED",
                entity_name="expenses",
                entity_id=new_expense.id,
                user_id=acting_user.id,
                details={
                    "project_id": project.id,
                    "line_item_id": line_item.id,
                    "funding_source": expense_in.funding_source,
                    "total_amount": str(expense_in.total_amount),
                    "vendor_name": new_expense.vendor_name,
                    "payor_type": new_expense.payor_type,
                    "is_valid_receipt": validation.is_valid_receipt,
                    "validation_errors": validation.errors,
                    "validation_warnings": validation.warnings,
                },
                ip_address=client_ip,
                commit=False,
            )

            db.commit()
            db.refresh(new_expense)
        except Exception:
            db.rollback()
            raise

        serialized = ExpenseRead.model_validate(new_expense)
        serialized.funding_source = expense_in.funding_source

        return ManualExpenseResponse(
            expense=serialized,
            validation=validation,
        )

    @staticmethod
    def list_expenses_by_project(
        db: Session,
        project_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> ProjectExpensesListResponse:
        project = ProjectRepository.get_by_id(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} does not exist."
            )

        items = ExpenseRepository.get_all_by_project(db, project_id, skip=skip, limit=limit)
        return ProjectExpensesListResponse(
            project_id=project_id,
            items=[_serialize_expense(e) for e in items],
            total_count=len(items),
        )

    @staticmethod
    def get_expense(
        db: Session,
        project_id: int,
        expense_id: int
    ) -> ExpenseRead:
        expense = ExpenseRepository.get_by_project_and_id(db, project_id, expense_id)
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expense with ID {expense_id} not found in project {project_id}."
            )
        return _serialize_expense(expense)
