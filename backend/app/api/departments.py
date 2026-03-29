from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models import Department, User
from app.schemas.department import DepartmentCreateRequest, DepartmentOut, DepartmentUpdateRequest

router = APIRouter(prefix="/departments", tags=["departments"])


def _get_department_for_company_or_404(db: Session, company_id: int, department_id: int) -> Department:
    department = db.scalar(
        select(Department).where(
            Department.id == department_id,
            Department.company_id == company_id,
        )
    )
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return department


@router.get("", response_model=list[DepartmentOut])
def list_departments(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    departments = db.scalars(
        select(Department)
        .where(Department.company_id == admin_user.company_id)
        .order_by(Department.name.asc())
    ).all()
    return departments


@router.post("", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    name = payload.name.strip()
    code = payload.code.strip().upper() if payload.code else None

    duplicate_query = select(Department).where(
        Department.company_id == admin_user.company_id,
        or_(Department.name == name, Department.code == code if code else False),
    )
    existing = db.scalar(duplicate_query)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department already exists")

    department = Department(company_id=admin_user.company_id, name=name, code=code)
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


@router.patch("/{department_id}", response_model=DepartmentOut)
def update_department(
    department_id: int,
    payload: DepartmentUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    department = _get_department_for_company_or_404(db, admin_user.company_id, department_id)

    if payload.name is not None:
        next_name = payload.name.strip()
        duplicate_name = db.scalar(
            select(Department).where(
                Department.company_id == admin_user.company_id,
                Department.name == next_name,
                Department.id != department.id,
            )
        )
        if duplicate_name is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department name already exists")
        department.name = next_name

    if payload.code is not None:
        next_code = payload.code.strip().upper() if payload.code else None
        if next_code is not None:
            duplicate_code = db.scalar(
                select(Department).where(
                    Department.company_id == admin_user.company_id,
                    Department.code == next_code,
                    Department.id != department.id,
                )
            )
            if duplicate_code is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Department code already exists",
                )
        department.code = next_code

    db.commit()
    db.refresh(department)
    return department
