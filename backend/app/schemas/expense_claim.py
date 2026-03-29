from datetime import date, datetime
from enum import Enum

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
    original_currency: str = Field(min_length=3, max_length=3)
    original_amount: float = Field(gt=0)
    expense_date: date
    department_id: int | None = None


class ClaimUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    category_id: int | None = None
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
    original_currency: str
    original_amount: float
    base_currency: str
    converted_amount: float | None
    expense_date: date
    status: str
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime
    is_editable: bool


class ClaimListResponse(BaseModel):
    claims: list[ClaimOut]
