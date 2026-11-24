from decimal import Decimal
from datetime import datetime
from sqlalchemy import String, Numeric, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.expense import Expense
    from backend.app.models.line_item_budget import LineItemBudget

class SplitAllocation(Base):
    """
    Portion allocation of an expense charged to a specific funding source.
    Funding sources: DOST_REIMBURSABLE or CITU_COUNTERPART.
    """
    __tablename__ = "split_allocations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id"), nullable=False, index=True)
    line_item_id: Mapped[int] = mapped_column(ForeignKey("line_item_budgets.id"), nullable=False)
    funding_source: Mapped[str] = mapped_column(String(30), nullable=False) # DOST_REIMBURSABLE or CITU_COUNTERPART
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_overridden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    override_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    expense: Mapped["Expense"] = relationship("Expense", back_populates="splits")
    line_item: Mapped["LineItemBudget"] = relationship("LineItemBudget", back_populates="split_allocations")
