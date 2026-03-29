from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    code: str | None = Field(default=None, max_length=40)


class DepartmentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    code: str | None = Field(default=None, max_length=40)


class DepartmentOut(BaseModel):
    id: int
    company_id: int
    name: str
    code: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
