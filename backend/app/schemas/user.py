from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.schemas.company import CompanyOut


class UserOut(BaseModel):
    id: int
    company_id: int
    email: EmailStr
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
