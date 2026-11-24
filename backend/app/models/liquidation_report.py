from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import String, Date, Numeric, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING
from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.project import Project
    from backend.app.models.user import User
    from backend.app.models.report_expense_item import ReportExpenseItem

class LiquidationReport(Base):
    """
    DOST Form 3-A Liquidation Report header record (Module 4).
    Aggregates disbursements across a reporting period.
    """
    __tablename__ = "liquidation_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    report_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    total_disbursed_dost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_citu_counterpart: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    generated_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="liquidation_reports")
    generated_by: Mapped["User"] = relationship("User")
    items: Mapped[List["ReportExpenseItem"]] = relationship("ReportExpenseItem", back_populates="report", cascade="all, delete-orphan")
