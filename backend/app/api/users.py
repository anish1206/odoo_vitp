from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models import Department, User
from app.schemas.user import CurrentUserResponse, UserAdminOut, UserCreateRequest, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=CurrentUserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return CurrentUserResponse(user=current_user, company=current_user.company)


def _get_user_for_company_or_404(db: Session, company_id: int, user_id: int) -> User:
    user = db.scalar(select(User).where(User.company_id == company_id, User.id == user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def _validate_department_in_company(db: Session, company_id: int, department_id: int | None) -> None:
    if department_id is None:
        return

    department = db.scalar(
        select(Department).where(
            Department.company_id == company_id,
            Department.id == department_id,
        )
    )
    if department is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid department for company",
        )


def _validate_manager_in_company(db: Session, company_id: int, manager_id: int | None) -> None:
    if manager_id is None:
        return

    manager = db.scalar(
        select(User).where(
            User.company_id == company_id,
            User.id == manager_id,
            User.is_active.is_(True),
        )
    )
    if manager is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid manager for company",
        )


@router.get("", response_model=list[UserAdminOut])
def list_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    users = db.scalars(
        select(User)
        .where(User.company_id == admin_user.company_id)
        .order_by(User.created_at.asc())
    ).all()
    return users


@router.post("", response_model=UserAdminOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    email = payload.email.lower().strip()

    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User email already exists")

    _validate_department_in_company(db, admin_user.company_id, payload.department_id)
    _validate_manager_in_company(db, admin_user.company_id, payload.manager_id)

    user = User(
        company_id=admin_user.company_id,
        email=email,
        hashed_password=get_password_hash(payload.password),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        role=payload.role,
        is_approver=payload.is_approver,
        is_active=True,
        department_id=payload.department_id,
        manager_id=payload.manager_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserAdminOut)
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    user = _get_user_for_company_or_404(db, admin_user.company_id, user_id)

    if payload.first_name is not None:
        user.first_name = payload.first_name.strip()

    if payload.last_name is not None:
        user.last_name = payload.last_name.strip()

    if payload.role is not None:
        user.role = payload.role

    if payload.is_approver is not None:
        user.is_approver = payload.is_approver

    if payload.is_active is not None:
        if user.id == admin_user.id and payload.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate your own admin account",
            )
        user.is_active = payload.is_active

    if payload.password is not None:
        user.hashed_password = get_password_hash(payload.password)

    if "department_id" in payload.model_fields_set:
        _validate_department_in_company(db, admin_user.company_id, payload.department_id)
        user.department_id = payload.department_id

    if "manager_id" in payload.model_fields_set:
        if payload.manager_id is not None and payload.manager_id == user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User cannot be their own manager",
            )

        _validate_manager_in_company(db, admin_user.company_id, payload.manager_id)
        user.manager_id = payload.manager_id

    db.commit()
    db.refresh(user)
    return user
