from decimal import Decimal
from datetime import date
from sqlalchemy import String, Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING
from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.line_item_budget import LineItemBudget
    from backend.app.models.expense import Expense
    from backend.app.models.liquidation_report import LiquidationReport

class Project(Base):
    """
    Research Project domain entity (e.g., DOST-funded grant at CIT-U).
    Per-project isolation ensures strict scoping for all budgets and expenses.
    """
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    funding_agency: Mapped[str] = mapped_column(String(50), default="DOST", nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_dost_budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_citu_budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)

    # Relationships
    line_items: Mapped[List["LineItemBudget"]] = relationship("LineItemBudget", back_populates="project", cascade="all, delete-orphan")
    expenses: Mapped[List["Expense"]] = relationship("Expense", back_populates="project")
    liquidation_reports: Mapped[List["LiquidationReport"]] = relationship("LiquidationReport", back_populates="project")
