from datetime import date, datetime
from typing import Any

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


class ApprovalReceiptContextOut(BaseModel):
    receipt_id: int
    original_filename: str
    file_mime_type: str
    file_size_bytes: int
    uploaded_at: datetime


class ApprovalOcrContextOut(BaseModel):
    extraction_id: int
    engine: str | None
    confidence: float | None
    parsed_fields: dict[str, Any] | None
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
    base_currency: str
    converted_amount: float | None
    exchange_rate: float | None
    exchange_rate_provider: str | None
    status: str
    current_approval_step: int | None
    pending_approver_names: list[str] = Field(default_factory=list)
    receipt: ApprovalReceiptContextOut | None = None
    ocr_extraction: ApprovalOcrContextOut | None = None
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
