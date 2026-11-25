from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal
from pydantic import BaseModel, ConfigDict, Field

FundingSourceType = Literal["DOST_REIMBURSABLE", "CITU_COUNTERPART"]
PayorType = Literal["INSTITUTION", "BLANK", "PERSONAL"]


class ManualExpenseCreate(BaseModel):
    """Request payload for UC-1.2 Manual Expense Entry (single 100% funding allocation)."""
    project_id: int
    line_item_id: int
    funding_source: FundingSourceType
    expense_date: date
    vendor_name: str = Field(default="", max_length=150)
    vendor_tin: str | None = Field(default=None, max_length=30)
    vendor_address: str | None = Field(default=None, max_length=255)
    payor_name: str = Field(default="", max_length=100)
    payor_type: PayorType = "INSTITUTION"
    total_amount: Decimal = Field(..., gt=Decimal("0"), description="Expense amount must be strictly positive")
    description: str | None = Field(default=None)


class ExpenseRead(BaseModel):
    """Serialized Expense record."""
    id: int
    project_id: int
    encoded_by_id: int
    line_item_id: int | None
    expense_date: date
    vendor_name: str
    vendor_tin: str | None
    vendor_address: str | None
    payor_name: str
    payor_type: str
    total_amount: Decimal
    description: str | None
    is_valid_receipt: bool
    status: str
    created_at: datetime
    funding_source: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ExpenseValidationResult(BaseModel):
    """Validation flags returned for a saved manual expense."""
    is_valid_receipt: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ManualExpenseResponse(BaseModel):
    """Response returned after saving a manual expense with validation flags."""
    expense: ExpenseRead
    validation: ExpenseValidationResult


class ProjectExpensesListResponse(BaseModel):
    """Project-scoped list of recorded expenses."""
    project_id: int
    items: List[ExpenseRead]
    total_count: int
