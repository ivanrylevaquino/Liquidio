from decimal import Decimal
from typing import List
from pydantic import BaseModel, ConfigDict, Field, model_validator

class LineItemBudgetBase(BaseModel):
    item_code: str = Field(..., min_length=1, max_length=30, description="Category code (e.g., PS, MOOE, CO)")
    category_name: str = Field(..., min_length=2, max_length=100, description="Descriptive category name")
    dost_allotment: Decimal = Field(default=Decimal("0.00"), ge=0, description="Approved DOST reimbursable budget")
    citu_allotment: Decimal = Field(default=Decimal("0.00"), ge=0, description="Approved CIT-U counterpart budget")

class LineItemBudgetCreate(LineItemBudgetBase):
    @model_validator(mode="after")
    def validate_non_negative(self) -> "LineItemBudgetCreate":
        if self.dost_allotment < 0 or self.citu_allotment < 0:
            raise ValueError("Allotments must be non-negative amounts.")
        return self

class LineItemBudgetUpdate(BaseModel):
    item_code: str | None = Field(default=None, min_length=1, max_length=30)
    category_name: str | None = Field(default=None, min_length=2, max_length=100)
    dost_allotment: Decimal = Field(..., ge=0, description="Updated approved DOST allotment")
    citu_allotment: Decimal = Field(..., ge=0, description="Updated approved CIT-U counterpart allotment")

    @model_validator(mode="after")
    def validate_non_negative(self) -> "LineItemBudgetUpdate":
        if self.dost_allotment < 0 or self.citu_allotment < 0:
            raise ValueError("Allotments must be non-negative amounts.")
        return self

class LineItemBudgetRead(LineItemBudgetBase):
    id: int
    project_id: int
    remaining_dost: Decimal
    remaining_citu: Decimal

    model_config = ConfigDict(from_attributes=True)

class LineItemBudgetResponse(BaseModel):
    line_item: LineItemBudgetRead
    warnings: List[str] = []

class ProjectLineItemsListResponse(BaseModel):
    project_id: int
    project_code: str
    total_dost_budget: Decimal
    total_citu_budget: Decimal
    sum_dost_allotment: Decimal
    sum_citu_allotment: Decimal
    items: List[LineItemBudgetRead]
    warnings: List[str] = []
