from pydantic import BaseModel, EmailStr, Field

from app.schemas.company import CompanyOut
from app.schemas.user import UserOut


class SignupRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=255)
    country_code: str = Field(min_length=2, max_length=2)
    admin_first_name: str = Field(min_length=1, max_length=120)
    admin_last_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthResponse(AccessTokenResponse):
    refresh_token: str
    user: UserOut
    company: CompanyOut
