from decimal import Decimal
from typing import List, Tuple, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.line_item_budget import LineItemBudget
from backend.app.models.project import Project
from backend.app.models.user import User
from backend.app.schemas.line_item_budget import (
    LineItemBudgetCreate,
    LineItemBudgetUpdate,
    LineItemBudgetRead,
    ProjectLineItemsListResponse,
    LineItemBudgetResponse
)
from backend.app.repositories.line_item_budget_repository import LineItemBudgetRepository
from backend.app.repositories.project_repository import ProjectRepository
from backend.app.repositories.activity_log_repository import ActivityLogRepository

class BudgetService:
    """
    Business service encapsulating UC-1.1: Approved Line-Item Budget setup.
    Validates non-negative allotments, unique item codes per project,
    cross-project isolation, and recomputes remaining balances on updates.
    """
    @staticmethod
    def _check_project_budget_overrun(
        project: Project,
        items: List[LineItemBudget]
    ) -> List[str]:
        """
        Compare the sum of line-item allotments with project-level approved totals.
        Returns warning messages if line items aggregate exceeds the project budget.
        """
        warnings = []
        total_dost_allotments = sum((Decimal(str(item.dost_allotment)) for item in items), Decimal("0.00"))
        total_citu_allotments = sum((Decimal(str(item.citu_allotment)) for item in items), Decimal("0.00"))

        if total_dost_allotments > project.total_dost_budget:
            warnings.append(
                f"Warning: Sum of DOST allotments (PHP {total_dost_allotments:,.2f}) exceeds the project's approved DOST budget (PHP {project.total_dost_budget:,.2f})."
            )
        if total_citu_allotments > project.total_citu_budget:
            warnings.append(
                f"Warning: Sum of CIT-U counterpart allotments (PHP {total_citu_allotments:,.2f}) exceeds the project's approved CIT-U budget (PHP {project.total_citu_budget:,.2f})."
            )
        return warnings

    @staticmethod
    def create_line_item(
        db: Session,
        project_id: int,
        item_in: LineItemBudgetCreate,
        acting_user: User,
        client_ip: str | None = None
    ) -> LineItemBudgetResponse:
        project = ProjectRepository.get_by_id(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} does not exist."
            )

        # Rule: item_code must be unique within a project
        existing = LineItemBudgetRepository.get_by_project_and_code(db, project_id, item_in.item_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item code '{item_in.item_code}' already exists in project '{project.project_code}'."
            )

        # Rule: Initial remaining balance = approved allotment
        new_item = LineItemBudget(
            project_id=project_id,
            item_code=item_in.item_code.strip().upper(),
            category_name=item_in.category_name.strip(),
            dost_allotment=item_in.dost_allotment,
            citu_allotment=item_in.citu_allotment,
            remaining_dost=item_in.dost_allotment,
            remaining_citu=item_in.citu_allotment,
        )
        created = LineItemBudgetRepository.create(db, new_item)

        # Audit Log: BUDGET_LINE_CREATED with before and after allotment values
        ActivityLogRepository.insert(
            db=db,
            action_type="BUDGET_LINE_CREATED",
            entity_name="line_item_budgets",
            entity_id=created.id,
            user_id=acting_user.id,
            details={
                "project_id": project_id,
                "item_code": created.item_code,
                "category_name": created.category_name,
                "before": {
                    "dost_allotment": "0.00",
                    "citu_allotment": "0.00",
                    "remaining_dost": "0.00",
                    "remaining_citu": "0.00"
                },
                "after": {
                    "dost_allotment": str(created.dost_allotment),
                    "citu_allotment": str(created.citu_allotment),
                    "remaining_dost": str(created.remaining_dost),
                    "remaining_citu": str(created.remaining_citu)
                }
            },
            ip_address=client_ip
        )

        # Check for project-level total allotment warnings
        all_items = LineItemBudgetRepository.get_all_by_project(db, project_id)
        warnings = BudgetService._check_project_budget_overrun(project, all_items)

        return LineItemBudgetResponse(
            line_item=LineItemBudgetRead.model_validate(created),
            warnings=warnings
        )

    @staticmethod
    def get_line_item(db: Session, project_id: int, item_id: int) -> LineItemBudgetRead:
        project = ProjectRepository.get_by_id(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found."
            )

        # Rule: A line item can only be accessed through its own project_id
        item = LineItemBudgetRepository.get_by_project_and_id(db, project_id, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Line item with ID {item_id} not found in project '{project.project_code}'."
            )
        return LineItemBudgetRead.model_validate(item)

    @staticmethod
    def list_line_items_by_project(db: Session, project_id: int) -> ProjectLineItemsListResponse:
        project = ProjectRepository.get_by_id(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found."
            )

        items = LineItemBudgetRepository.get_all_by_project(db, project_id)
        warnings = BudgetService._check_project_budget_overrun(project, items)

        sum_dost = sum((Decimal(str(item.dost_allotment)) for item in items), Decimal("0.00"))
        sum_citu = sum((Decimal(str(item.citu_allotment)) for item in items), Decimal("0.00"))

        return ProjectLineItemsListResponse(
            project_id=project.id,
            project_code=project.project_code,
            total_dost_budget=project.total_dost_budget,
            total_citu_budget=project.total_citu_budget,
            sum_dost_allotment=sum_dost,
            sum_citu_allotment=sum_citu,
            items=[LineItemBudgetRead.model_validate(item) for item in items],
            warnings=warnings
        )

    @staticmethod
    def update_line_item(
        db: Session,
        project_id: int,
        item_id: int,
        item_in: LineItemBudgetUpdate,
        acting_user: User,
        client_ip: str | None = None
    ) -> LineItemBudgetResponse:
        project = ProjectRepository.get_by_id(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found."
            )

        # Rule: A line item can only be accessed through its own project_id
        item = LineItemBudgetRepository.get_by_project_and_id(db, project_id, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Line item with ID {item_id} does not belong to project '{project.project_code}'."
            )

        # Check item_code uniqueness if changed
        if item_in.item_code and item_in.item_code.strip().upper() != item.item_code:
            existing = LineItemBudgetRepository.get_by_project_and_code(db, project_id, item_in.item_code)
            if existing and existing.id != item.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item code '{item_in.item_code}' is already used by another category in this project."
                )

        # Compute spent allocations for this line item
        spent = LineItemBudgetRepository.get_spent_amounts(db, item.id)
        spent_dost = spent["spent_dost"]
        spent_citu = spent["spent_citu"]

        # Rule: Reject any change that would make an allotment lower than what's already spent
        if item_in.dost_allotment < spent_dost:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reduce DOST allotment to PHP {item_in.dost_allotment:,.2f}. PHP {spent_dost:,.2f} has already been spent or allocated."
            )
        if item_in.citu_allotment < spent_citu:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reduce CIT-U counterpart allotment to PHP {item_in.citu_allotment:,.2f}. PHP {spent_citu:,.2f} has already been spent or allocated."
            )

        # Capture 'before' state for audit log
        before_state = {
            "dost_allotment": str(item.dost_allotment),
            "citu_allotment": str(item.citu_allotment),
            "remaining_dost": str(item.remaining_dost),
            "remaining_citu": str(item.remaining_citu)
        }

        # Rule on PUT: recompute remaining = new allotment minus amount already spent
        item.dost_allotment = item_in.dost_allotment
        item.citu_allotment = item_in.citu_allotment
        item.remaining_dost = item_in.dost_allotment - spent_dost
        item.remaining_citu = item_in.citu_allotment - spent_citu

        if item_in.category_name:
            item.category_name = item_in.category_name.strip()
        if item_in.item_code:
            item.item_code = item_in.item_code.strip().upper()

        updated = LineItemBudgetRepository.update(db, item)

        # Audit Log: BUDGET_LINE_UPDATED with before and after allotment values
        ActivityLogRepository.insert(
            db=db,
            action_type="BUDGET_LINE_UPDATED",
            entity_name="line_item_budgets",
            entity_id=updated.id,
            user_id=acting_user.id,
            details={
                "project_id": project_id,
                "item_code": updated.item_code,
                "category_name": updated.category_name,
                "before": before_state,
                "after": {
                    "dost_allotment": str(updated.dost_allotment),
                    "citu_allotment": str(updated.citu_allotment),
                    "remaining_dost": str(updated.remaining_dost),
                    "remaining_citu": str(updated.remaining_citu)
                }
            },
            ip_address=client_ip
        )

        all_items = LineItemBudgetRepository.get_all_by_project(db, project_id)
        warnings = BudgetService._check_project_budget_overrun(project, all_items)

        return LineItemBudgetResponse(
            line_item=LineItemBudgetRead.model_validate(updated),
            warnings=warnings
        )
