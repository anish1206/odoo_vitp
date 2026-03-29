from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import ApprovalRuleStrategy, ApproverRole


class ApprovalRuleStepCreateRequest(BaseModel):
    step_order: int = Field(ge=1, le=99)
    name: str = Field(min_length=1, max_length=150)
    approver_role: ApproverRole = ApproverRole.MANAGER
    approver_user_id: int | None = None
    approver_department_id: int | None = None


class ApprovalRuleCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    min_amount: float | None = Field(default=None, ge=0)
    max_amount: float | None = Field(default=None, ge=0)
    category_id: int | None = None
    department_id: int | None = None
    strategy: ApprovalRuleStrategy = ApprovalRuleStrategy.SEQUENTIAL
    min_approval_percentage: int | None = Field(default=None, ge=1, le=100)
    is_active: bool = True
    priority: int = Field(default=100, ge=1, le=9999)
    steps: list[ApprovalRuleStepCreateRequest] = Field(min_length=1)


class ApprovalRuleUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    min_amount: float | None = Field(default=None, ge=0)
    max_amount: float | None = Field(default=None, ge=0)
    category_id: int | None = None
    department_id: int | None = None
    strategy: ApprovalRuleStrategy | None = None
    min_approval_percentage: int | None = Field(default=None, ge=1, le=100)
    is_active: bool | None = None
    priority: int | None = Field(default=None, ge=1, le=9999)


class ApprovalRuleStepsReplaceRequest(BaseModel):
    steps: list[ApprovalRuleStepCreateRequest] = Field(min_length=1)


class ApprovalRuleStepOut(BaseModel):
    id: int
    rule_id: int
    step_order: int
    name: str
    approver_role: str
    approver_user_id: int | None
    approver_department_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalRuleOut(BaseModel):
    id: int
    company_id: int
    name: str
    description: str | None
    min_amount: float | None
    max_amount: float | None
    category_id: int | None
    department_id: int | None
    strategy: str
    min_approval_percentage: int | None
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime
    steps: list[ApprovalRuleStepOut]

    model_config = ConfigDict(from_attributes=True)
