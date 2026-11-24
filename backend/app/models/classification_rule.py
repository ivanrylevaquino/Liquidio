from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base

class ClassificationRule(Base):
    """
    Institutional rule for suggesting funding classification (Module 3).
    Maps merchant/category keywords to DOST_REIMBURSABLE or CITU_COUNTERPART.
    """
    __tablename__ = "classification_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    keyword_or_category: Mapped[str] = mapped_column(String(100), nullable=False)
    funding_source: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
