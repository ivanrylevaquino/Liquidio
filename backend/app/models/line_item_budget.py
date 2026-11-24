from decimal import Decimal
from sqlalchemy import String, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING
from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.project import Project
    from backend.app.models.expense import Expense
    from backend.app.models.split_allocation import SplitAllocation

class LineItemBudget(Base):
    """
    Approved Line-Item Budget (LIB) category belonging to a project.
    Maintains separate DOST reimbursable allotments and CIT-U counterpart allotments.
    """
    __tablename__ = "line_item_budgets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    item_code: Mapped[str] = mapped_column(String(30), nullable=False)
    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dost_allotment: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    citu_allotment: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    remaining_dost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    remaining_citu: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="line_items")
    expenses: Mapped[List["Expense"]] = relationship("Expense", back_populates="line_item")
    split_allocations: Mapped[List["SplitAllocation"]] = relationship("SplitAllocation", back_populates="line_item")
