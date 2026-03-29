from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Department(Base):
    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("company_id", "name", name="uq_department_company_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    company = relationship("Company", back_populates="departments")
    users = relationship("User", back_populates="department")
    claims = relationship("ExpenseClaim", back_populates="department")
    approval_rules = relationship("ApprovalRule", back_populates="department")
    rule_steps = relationship("ApprovalRuleStep", back_populates="approver_department")