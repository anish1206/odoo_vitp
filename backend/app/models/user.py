from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(120))
    last_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole), default=UserRole.EMPLOYEE)
    is_approver: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    company = relationship("Company", back_populates="users")
    department = relationship("Department", back_populates="users")
    manager = relationship("User", remote_side=[id], back_populates="reports")
    reports = relationship("User", back_populates="manager")

    employee_claims = relationship("ExpenseClaim", foreign_keys="ExpenseClaim.employee_id")
    uploaded_receipts = relationship("ReceiptFile", back_populates="employee")
    assigned_approval_tasks = relationship("ApprovalTask", foreign_keys="ApprovalTask.approver_id")
    approval_actions = relationship("ApprovalActionLog", foreign_keys="ApprovalActionLog.actor_id")
    audit_logs = relationship("AuditLog", back_populates="user")
