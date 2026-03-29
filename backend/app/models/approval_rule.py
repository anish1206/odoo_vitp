from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ApprovalRuleStrategy(str, Enum):
    SEQUENTIAL = "SEQUENTIAL"
    MIN_APPROVALS = "MIN_APPROVALS"


class ApprovalRule(Base):
    __tablename__ = "approval_rules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    min_amount: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    max_amount: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("expense_categories.id"), nullable=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    strategy: Mapped[ApprovalRuleStrategy] = mapped_column(
        SqlEnum(ApprovalRuleStrategy), default=ApprovalRuleStrategy.SEQUENTIAL, nullable=False
    )
    min_approval_percentage: Mapped[int | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(default=100, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    company = relationship("Company", back_populates="approval_rules")
    category = relationship("ExpenseCategory", back_populates="approval_rules")
    department = relationship("Department", back_populates="approval_rules")
    steps = relationship("ApprovalRuleStep", back_populates="rule")
    tasks = relationship("ApprovalTask", back_populates="rule")