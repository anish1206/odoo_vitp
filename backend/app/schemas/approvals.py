from datetime import date, datetime

from pydantic import BaseModel, Field


class ApprovalTaskSummaryOut(BaseModel):
    task_id: int
    claim_id: int
    claim_title: str
    employee_name: str
    category_name: str
    original_currency: str
    original_amount: float
    submitted_at: datetime | None
    sequence_order: int
    status: str
    is_actionable: bool


class ApprovalActionLogOut(BaseModel):
    id: int
    action_type: str
    actor_name: str | None
    description: str | None
    created_at: datetime


class ApprovalTaskClaimDetailOut(BaseModel):
    task_id: int
    claim_id: int
    employee_name: str
    claim_title: str
    claim_description: str | None
    category_name: str
    expense_date: date
    original_currency: str
    original_amount: float
    status: str
    current_approval_step: int | None
    logs: list[ApprovalActionLogOut]


class ApprovalTaskListResponse(BaseModel):
    tasks: list[ApprovalTaskSummaryOut]


class ApprovalDecisionRequest(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)


class ApprovalDecisionResponse(BaseModel):
    task_id: int
    task_status: str
    claim_id: int
    claim_status: str
