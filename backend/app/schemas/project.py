from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class ProjectBase(BaseModel):
    project_code: str = Field(..., min_length=2, max_length=50, description="Unique project code (e.g. DOST-CITU-2026-01)")
    title: str = Field(..., min_length=3, max_length=255, description="Full title of the research project")
    funding_agency: str = Field(default="DOST", max_length=50)
    start_date: date
    end_date: date
    total_dost_budget: Decimal = Field(default=Decimal("0.00"), ge=0, description="Aggregate approved DOST allotment")
    total_citu_budget: Decimal = Field(default=Decimal("0.00"), ge=0, description="Aggregate CIT-U counterpart allotment")

class ProjectCreate(ProjectBase):
    @model_validator(mode="after")
    def validate_dates_and_budgets(self) -> "ProjectCreate":
        if self.end_date < self.start_date:
            raise ValueError("Project end_date cannot be earlier than start_date.")
        if self.total_dost_budget < 0 or self.total_citu_budget < 0:
            raise ValueError("Budgets must be non-negative amounts.")
        return self

class ProjectRead(ProjectBase):
    id: int

    # Pydantic v2 from_attributes enables ORM conversion
    model_config = ConfigDict(from_attributes=True)
