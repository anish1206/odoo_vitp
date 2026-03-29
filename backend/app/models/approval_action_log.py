from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ApprovalActionType(str, Enum):
    SUBMITTED = "SUBMITTED"
    RESUBMITTED = "RESUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMMENTED = "COMMENTED"
    RULE_MATCHED = "RULE_MATCHED"
    FALLBACK_MANAGER_USED = "FALLBACK_MANAGER_USED"


class ApprovalActionLog(Base):
    __tablename__ = "approval_action_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("expense_claims.id"), index=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action_type: Mapped[ApprovalActionType] = mapped_column(SqlEnum(ApprovalActionType), nullable=False)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("approval_tasks.id"), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    claim = relationship("ExpenseClaim", back_populates="approval_logs")
    actor = relationship("User", foreign_keys=[actor_id], back_populates="approval_actions")
    task = relationship("ApprovalTask", back_populates="logs")