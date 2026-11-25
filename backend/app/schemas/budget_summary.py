from datetime import date
from decimal import Decimal
from typing import List, Literal
from pydantic import BaseModel


class LineItemBudgetSummary(BaseModel):
    """Per-line-item budget vs. actual aggregation."""
    line_item_id: int
    item_code: str
    category_name: str
    dost_allotment: Decimal
    citu_allotment: Decimal
    dost_spent: Decimal
    citu_spent: Decimal
    remaining_dost: Decimal
    remaining_citu: Decimal
    percent_spent_dost: Decimal
    percent_spent_citu: Decimal
    is_over_budget_dost: bool
    is_over_budget_citu: bool
    data_mismatch: bool


class ProjectBudgetTotals(BaseModel):
    """Project-level budget totals for DOST and CIT-U."""
    total_dost_budget: Decimal
    total_citu_budget: Decimal
    total_dost_allotment: Decimal
    total_citu_allotment: Decimal
    total_dost_spent: Decimal
    total_citu_spent: Decimal
    total_dost_remaining: Decimal
    total_citu_remaining: Decimal


class ReceiptQualitySummary(BaseModel):
    """Receipt compliance and review queue counts."""
    invalid_receipt_count: int
    invalid_receipt_total_amount: Decimal
    pending_review_count: int


class BurnRateSummary(BaseModel):
    """Timeline elapsed vs. overall budget spent pace indicator."""
    timeline_elapsed_percent: Decimal
    overall_spent_percent: Decimal
    pace_status: Literal["on track", "ahead of pace", "no timeline data"]


class BudgetSummaryResponse(BaseModel):
    """Full UC-1.3 Budget vs. Actual dashboard summary for a project."""
    project_id: int
    project_code: str
    project_title: str
    start_date: date
    end_date: date
    totals: ProjectBudgetTotals
    line_items: List[LineItemBudgetSummary]
    receipt_quality: ReceiptQualitySummary
    burn_rate: BurnRateSummary
