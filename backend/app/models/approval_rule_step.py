from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ApproverRole(str, Enum):
    MANAGER = "MANAGER"
    SPECIFIC_USER = "SPECIFIC_USER"
    DEPARTMENT_HEAD = "DEPARTMENT_HEAD"


class ApprovalRuleStep(Base):
    __tablename__ = "approval_rule_steps"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("approval_rules.id"), index=True)
    step_order: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    approver_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approver_role: Mapped[ApproverRole] = mapped_column(
        SqlEnum(ApproverRole), default=ApproverRole.MANAGER, nullable=False
    )
    approver_department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    rule = relationship("ApprovalRule", back_populates="steps")
    approver_user = relationship("User")
    approver_department = relationship("Department", back_populates="rule_steps")
    tasks = relationship("ApprovalTask", back_populates="rule_step")