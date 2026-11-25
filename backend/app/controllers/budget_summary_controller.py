from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas.budget_summary import BudgetSummaryResponse
from backend.app.services.ledger_aggregation_service import LedgerAggregationService

router = APIRouter(tags=["Budget Summary"])


@router.get("/api/projects/{project_id}/budget-summary", response_model=BudgetSummaryResponse)
def get_project_budget_summary(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    UC-1.3: Read-only budget-vs-actual summary, receipt quality metrics,
    and burn-rate pace indicator for a specific project.
    """
    return LedgerAggregationService.get_budget_summary(db=db, project_id=project_id)
