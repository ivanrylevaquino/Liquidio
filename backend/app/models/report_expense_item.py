from decimal import Decimal
from sqlalchemy import Numeric, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.liquidation_report import LiquidationReport
    from backend.app.models.expense import Expense
    from backend.app.models.split_allocation import SplitAllocation

class ReportExpenseItem(Base):
    """
    Itemized line in DOST Form 3-A Liquidation Report (Module 4).
    Matches the SDD ERD: report_id, expense_id, split_allocation_id, claimed_amount, item_sequence_num.
    """
    __tablename__ = "report_expense_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("liquidation_reports.id"), nullable=False, index=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id"), nullable=False)
    split_allocation_id: Mapped[int] = mapped_column(ForeignKey("split_allocations.id"), nullable=False)
    claimed_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    item_sequence_num: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    report: Mapped["LiquidationReport"] = relationship("LiquidationReport", back_populates="items")
    expense: Mapped["Expense"] = relationship("Expense")
    split_allocation: Mapped["SplitAllocation"] = relationship("SplitAllocation")
