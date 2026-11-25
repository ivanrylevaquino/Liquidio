from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.schemas.line_item_budget import (
    LineItemBudgetCreate,
    LineItemBudgetUpdate,
    LineItemBudgetRead,
    LineItemBudgetResponse,
    ProjectLineItemsListResponse
)
from backend.app.services.budget_service import BudgetService
from backend.app.models.user import User

router = APIRouter(prefix="/api/projects/{project_id}/line-items", tags=["Line Item Budgets"])

@router.post("", response_model=LineItemBudgetResponse, status_code=201)
def create_line_item(
    project_id: int,
    item_in: LineItemBudgetCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    UC-1.1: Add an approved line-item budget category to a project.
    Validates non-negative allotments and unique item_code per project.
    Initializes remaining_dost = dost_allotment and remaining_citu = citu_allotment.
    Logs BUDGET_LINE_CREATED in the tamper-resistant audit trail.
    """
    client_ip = request.client.host if request.client else None
    return BudgetService.create_line_item(
        db=db,
        project_id=project_id,
        item_in=item_in,
        acting_user=current_user,
        client_ip=client_ip
    )

@router.get("", response_model=ProjectLineItemsListResponse)
def list_line_items(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    UC-1.1: Retrieve all approved line-item budget categories for a project,
    along with aggregate allotment sums and any budget overrun warnings.
    """
    return BudgetService.list_line_items_by_project(db=db, project_id=project_id)

@router.get("/{item_id}", response_model=LineItemBudgetRead)
def get_line_item(
    project_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve an individual line item.
    Enforces project scoping (returns 404 if item belongs to another project).
    """
    return BudgetService.get_line_item(db=db, project_id=project_id, item_id=item_id)

@router.put("/{item_id}", response_model=LineItemBudgetResponse)
def update_line_item(
    project_id: int,
    item_id: int,
    item_in: LineItemBudgetUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    UC-1.1: Update an approved line-item budget category.
    Recomputes remaining balances based on spent allocations in split_allocations.
    Rejects any reduction below already spent amounts.
    Logs BUDGET_LINE_UPDATED with before and after allotment values in audit trail.
    """
    client_ip = request.client.host if request.client else None
    return BudgetService.update_line_item(
        db=db,
        project_id=project_id,
        item_id=item_id,
        item_in=item_in,
        acting_user=current_user,
        client_ip=client_ip
    )
