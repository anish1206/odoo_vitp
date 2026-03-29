from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ClaimSubmitAction(str, Enum):
    SAVE_DRAFT = "SAVE_DRAFT"
    SUBMIT = "SUBMIT"


class ExpenseCategoryOut(BaseModel):
    id: int
    name: str
    code: str | None = None
    description: str | None = None


class ClaimCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    category_id: int
    receipt_file_id: int | None = None
    original_currency: str = Field(min_length=3, max_length=3)
    original_amount: float = Field(gt=0)
    expense_date: date
    department_id: int | None = None


class ClaimUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    category_id: int | None = None
    receipt_file_id: int | None = None
    original_currency: str | None = Field(default=None, min_length=3, max_length=3)
    original_amount: float | None = Field(default=None, gt=0)
    expense_date: date | None = None
    department_id: int | None = None


class ClaimOut(BaseModel):
    id: int
    title: str
    description: str | None
    category_id: int
    category_name: str
    receipt_file_id: int | None
    original_currency: str
    original_amount: float
    base_currency: str
    converted_amount: float | None
    exchange_rate_snapshot_id: int | None
    exchange_rate: float | None
    exchange_rate_provider: str | None
    exchange_rate_as_of: datetime | None
    expense_date: date
    status: str
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime
    is_editable: bool
    employee_id: int | None = None
    employee_name: str | None = None
    department_id: int | None = None
    department_name: str | None = None
    pending_approver_names: list[str] = Field(default_factory=list)


class ClaimApprovalTaskOut(BaseModel):
    task_id: int
    sequence_order: int
    status: str
    approver_id: int | None
    approver_name: str | None
    acted_at: datetime | None
    comment: str | None


class ClaimTimelineEventOut(BaseModel):
    id: int
    action_type: str
    actor_name: str | None
    description: str | None
    created_at: datetime


class ClaimReceiptContextOut(BaseModel):
    receipt_id: int
    original_filename: str
    file_mime_type: str
    file_size_bytes: int
    uploaded_at: datetime


class ClaimOcrContextOut(BaseModel):
    extraction_id: int
    engine: str | None
    confidence: float | None
    parsed_fields: dict[str, Any] | None
    created_at: datetime


class ClaimDetailOut(ClaimOut):
    rejection_reason: str | None
    current_approval_step: int | None
    final_approved_at: datetime | None
    approval_tasks: list[ClaimApprovalTaskOut] = Field(default_factory=list)
    approval_timeline: list[ClaimTimelineEventOut] = Field(default_factory=list)
    receipt: ClaimReceiptContextOut | None = None
    ocr_extraction: ClaimOcrContextOut | None = None


class ClaimListResponse(BaseModel):
    claims: list[ClaimOut]
