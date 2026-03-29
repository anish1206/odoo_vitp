from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models import ExpenseCategory, User
from app.schemas.category import CategoryCreateRequest, CategoryOut, CategoryUpdateRequest

router = APIRouter(prefix="/categories", tags=["categories"])


def _get_category_for_company_or_404(db: Session, company_id: int, category_id: int) -> ExpenseCategory:
    category = db.scalar(
        select(ExpenseCategory).where(
            ExpenseCategory.id == category_id,
            ExpenseCategory.company_id == company_id,
        )
    )
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router.get("", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    categories = db.scalars(
        select(ExpenseCategory)
        .where(ExpenseCategory.company_id == admin_user.company_id)
        .order_by(ExpenseCategory.name.asc())
    ).all()
    return categories


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    name = payload.name.strip()
    code = payload.code.strip().upper() if payload.code else None
    description = payload.description.strip() if payload.description else None

    duplicate_query = select(ExpenseCategory).where(
        ExpenseCategory.company_id == admin_user.company_id,
        or_(ExpenseCategory.name == name, ExpenseCategory.code == code if code else False),
    )
    existing = db.scalar(duplicate_query)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category already exists")

    category = ExpenseCategory(
        company_id=admin_user.company_id,
        name=name,
        code=code,
        description=description,
        is_active=True,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    payload: CategoryUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    category = _get_category_for_company_or_404(db, admin_user.company_id, category_id)

    if payload.name is not None:
        next_name = payload.name.strip()
        duplicate_name = db.scalar(
            select(ExpenseCategory).where(
                ExpenseCategory.company_id == admin_user.company_id,
                ExpenseCategory.name == next_name,
                ExpenseCategory.id != category.id,
            )
        )
        if duplicate_name is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name already exists")
        category.name = next_name

    if payload.code is not None:
        next_code = payload.code.strip().upper() if payload.code else None
        if next_code is not None:
            duplicate_code = db.scalar(
                select(ExpenseCategory).where(
                    ExpenseCategory.company_id == admin_user.company_id,
                    ExpenseCategory.code == next_code,
                    ExpenseCategory.id != category.id,
                )
            )
            if duplicate_code is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category code already exists",
                )
        category.code = next_code

    if payload.description is not None:
        category.description = payload.description.strip() if payload.description else None

    if payload.is_active is not None:
        category.is_active = payload.is_active

    db.commit()
    db.refresh(category)
    return category
