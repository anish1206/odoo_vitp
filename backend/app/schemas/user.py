from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import UserRole
from app.schemas.company import CompanyOut


class UserOut(BaseModel):
    id: int
    company_id: int
    email: str
    first_name: str
    last_name: str
    role: str
    is_approver: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CurrentUserResponse(BaseModel):
    user: UserOut
    company: CompanyOut


class UserAdminOut(BaseModel):
    id: int
    company_id: int
    email: str
    first_name: str
    last_name: str
    role: str
    is_approver: bool
    is_active: bool
    department_id: int | None
    manager_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    role: UserRole = UserRole.EMPLOYEE
    is_approver: bool = False
    department_id: int | None = None
    manager_id: int | None = None


class UserUpdateRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    last_name: str | None = Field(default=None, min_length=1, max_length=120)
    role: UserRole | None = None
    is_approver: bool | None = None
    is_active: bool | None = None
    department_id: int | None = None
    manager_id: int | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
