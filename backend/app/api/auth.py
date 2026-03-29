from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.country_currency import get_base_currency
from app.core.default_data import DEFAULT_EXPENSE_CATEGORIES
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    decode_token,
)
from app.db.session import get_db
from app.models import Company, ExpenseCategory, User, UserRole
from app.schemas.auth import (
    AccessTokenResponse,
    AuthResponse,
    LoginRequest,
    RefreshTokenRequest,
    SignupRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def build_auth_response(user: User) -> AuthResponse:
    company = user.company
    access_token = create_access_token(
        user_id=user.id,
        company_id=user.company_id,
        role=user.role.value,
        is_approver=user.is_approver,
    )
    refresh_token = create_refresh_token(user_id=user.id)

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user,
        company=company,
    )


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    country_code = payload.country_code.upper().strip()

    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    existing_company = db.scalar(select(Company).where(Company.name == payload.company_name.strip()))
    if existing_company is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company name already exists",
        )

    base_currency = get_base_currency(country_code)
    if base_currency is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported country code for base currency",
        )

    company = Company(
        name=payload.company_name.strip(),
        country_code=country_code,
        base_currency=base_currency,
    )
    db.add(company)
    db.flush()

    for category in DEFAULT_EXPENSE_CATEGORIES:
        db.add(
            ExpenseCategory(
                company_id=company.id,
                name=category["name"],
                code=category["code"],
                description=category["description"],
            )
        )

    admin_user = User(
        company_id=company.id,
        email=email,
        hashed_password=get_password_hash(payload.password),
        first_name=payload.admin_first_name.strip(),
        last_name=payload.admin_last_name.strip(),
        role=UserRole.ADMIN,
        is_approver=True,
        is_active=True,
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    return build_auth_response(admin_user)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    user = db.scalar(select(User).where(User.email == email))

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return build_auth_response(user)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    token_payload = decode_token(payload.refresh_token)
    if token_payload is None or token_payload.get("token_type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = token_payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
        )

    user = db.get(User, int(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist or is inactive",
        )

    access_token = create_access_token(
        user_id=user.id,
        company_id=user.company_id,
        role=user.role.value,
        is_approver=user.is_approver,
    )
    return AccessTokenResponse(access_token=access_token)
