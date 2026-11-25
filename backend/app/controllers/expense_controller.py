from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas.expense import (
    ExpenseRead,
    ManualExpenseCreate,
    ManualExpenseResponse,
    ProjectExpensesListResponse,
)
from backend.app.services.expense_service import ExpenseService

router = APIRouter(tags=["Expenses"])


@router.post("/api/expenses/manual", response_model=ManualExpenseResponse, status_code=201)
def create_manual_expense(
    expense_in: ManualExpenseCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    UC-1.2: Record a manual expense with a single 100% funding allocation,
    deduct remaining line-item balance, run validation flags, and log EXPENSE_CREATED.
    """
    client_ip = request.client.host if request.client else None
    return ExpenseService.create_manual_expense(
        db=db,
        expense_in=expense_in,
        acting_user=current_user,
        client_ip=client_ip,
    )


@router.get("/api/projects/{project_id}/expenses", response_model=ProjectExpensesListResponse)
def list_project_expenses(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all expenses scoped to a specific project."""
    return ExpenseService.list_expenses_by_project(
        db=db,
        project_id=project_id,
        skip=skip,
        limit=limit,
    )


@router.get("/api/projects/{project_id}/expenses/{expense_id}", response_model=ExpenseRead)
def get_project_expense(
    project_id: int,
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve a single expense scoped to a specific project."""
    return ExpenseService.get_expense(
        db=db,
        project_id=project_id,
        expense_id=expense_id,
    )
