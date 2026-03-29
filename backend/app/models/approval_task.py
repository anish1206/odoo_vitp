from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ApprovalTaskStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SKIPPED = "SKIPPED"


class ApprovalTask(Base):
    __tablename__ = "approval_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("expense_claims.id"), index=True)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("approval_rules.id"), nullable=True)
    rule_step_id: Mapped[int | None] = mapped_column(ForeignKey("approval_rule_steps.id"), nullable=True)
    approver_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    sequence_order: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[ApprovalTaskStatus] = mapped_column(
        SqlEnum(ApprovalTaskStatus), default=ApprovalTaskStatus.PENDING, nullable=False
    )
    acted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    claim = relationship("ExpenseClaim", back_populates="approval_tasks")
    rule = relationship("ApprovalRule", back_populates="tasks")
    rule_step = relationship("ApprovalRuleStep", back_populates="tasks")
    approver = relationship("User", foreign_keys=[approver_id], back_populates="assigned_approval_tasks")
    actor = relationship("User", foreign_keys=[acted_by])
    logs = relationship("ApprovalActionLog", back_populates="task")