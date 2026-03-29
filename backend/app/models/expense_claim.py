from datetime import date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, Enum as SqlEnum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExpenseClaimStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class ExpenseClaim(Base):
    __tablename__ = "expense_claims"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("expense_categories.id"), index=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    receipt_file_id: Mapped[int | None] = mapped_column(ForeignKey("receipt_files.id"), nullable=True)
    original_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    original_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    converted_amount: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    exchange_rate_snapshot_id: Mapped[int | None] = mapped_column(
        ForeignKey("exchange_rate_snapshots.id"), nullable=True
    )
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    final_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[ExpenseClaimStatus] = mapped_column(
        SqlEnum(ExpenseClaimStatus), default=ExpenseClaimStatus.DRAFT, nullable=False
    )
    current_approval_step: Mapped[int | None] = mapped_column(nullable=True)
    is_resubmission: Mapped[bool] = mapped_column(default=False, nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    company = relationship("Company", back_populates="claims")
    employee = relationship("User", foreign_keys=[employee_id], back_populates="employee_claims")
    category = relationship("ExpenseCategory", back_populates="claims")
    department = relationship("Department", back_populates="claims")
    receipt_file = relationship("ReceiptFile", back_populates="claim")
    exchange_rate_snapshot = relationship("ExchangeRateSnapshot", back_populates="claims")
    approval_tasks = relationship("ApprovalTask", back_populates="claim")
    approval_logs = relationship("ApprovalActionLog", back_populates="claim")