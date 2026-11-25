from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import String, Date, Numeric, Boolean, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING
from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.project import Project
    from backend.app.models.user import User
    from backend.app.models.line_item_budget import LineItemBudget
    from backend.app.models.split_allocation import SplitAllocation
    from backend.app.models.receipt_image import ReceiptImage

class Expense(Base):
    """
    Expense transaction record for a project.
    Status values: PENDING_REVIEW, APPROVED, REJECTED, LIQUIDATED.
    Payor types: INSTITUTION, BLANK, PERSONAL.
    """
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    encoded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    line_item_id: Mapped[int | None] = mapped_column(ForeignKey("line_item_budgets.id"), nullable=True)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    vendor_name: Mapped[str] = mapped_column(String(150), nullable=False)
    vendor_tin: Mapped[str | None] = mapped_column(String(30), nullable=True)
    vendor_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payor_name: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    payor_type: Mapped[str] = mapped_column(String(20), default="INSTITUTION", nullable=False) # INSTITUTION, BLANK, PERSONAL
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_valid_receipt: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING_REVIEW", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Future-proofing columns for Module 4 review/approval
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    invalid_override_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    invalid_override_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="expenses")
    encoded_by: Mapped["User"] = relationship("User", foreign_keys=[encoded_by_id])
    approved_by: Mapped["User | None"] = relationship("User", foreign_keys=[approved_by_id])
    line_item: Mapped["LineItemBudget | None"] = relationship("LineItemBudget", back_populates="expenses")
    splits: Mapped[List["SplitAllocation"]] = relationship("SplitAllocation", back_populates="expense", cascade="all, delete-orphan")
    receipt_images: Mapped[List["ReceiptImage"]] = relationship("ReceiptImage", back_populates="expense", cascade="all, delete-orphan")
