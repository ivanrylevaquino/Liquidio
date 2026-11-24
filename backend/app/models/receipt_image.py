from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.expense import Expense

class ReceiptImage(Base):
    """
    Receipt supporting document storage record.
    Supports local storage folder (Module 1) and Google Drive cloud archival (Module 2).
    """
    __tablename__ = "receipt_images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id"), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    gdrive_file_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gdrive_view_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    local_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ocr_raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    expense: Mapped["Expense"] = relationship("Expense", back_populates="receipt_images")
