from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import ExpenseCategory, ExpenseClaim, ExpenseClaimStatus, User
from app.schemas.expense_claim import (
    ClaimCreateRequest,
    ClaimListResponse,
    ClaimOut,
    ClaimUpdateRequest,
    ExpenseCategoryOut,
)

router = APIRouter(prefix="/claims", tags=["claims"])


def _to_claim_out(claim: ExpenseClaim) -> ClaimOut:
    category_name = claim.category.name if claim.category is not None else "Unknown"
    return ClaimOut(
        id=claim.id,
        title=claim.title,
        description=claim.description,
        category_id=claim.category_id,
        category_name=category_name,
        original_currency=claim.original_currency,
        original_amount=float(claim.original_amount),
        base_currency=claim.base_currency,
        converted_amount=None
        if claim.converted_amount is None
        else float(claim.converted_amount),
        expense_date=claim.expense_date,
        status=claim.status.value,
        submitted_at=claim.submitted_at,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
        is_editable=claim.status == ExpenseClaimStatus.DRAFT,
    )


def _get_active_category_or_400(db: Session, company_id: int, category_id: int) -> ExpenseCategory:
    category = db.scalar(
        select(ExpenseCategory).where(
            ExpenseCategory.id == category_id,
            ExpenseCategory.company_id == company_id,
            ExpenseCategory.is_active.is_(True),
        )
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid expense category",
        )
    return category


def _get_claim_for_user_or_404(db: Session, current_user: User, claim_id: int) -> ExpenseClaim:
    claim = db.scalar(
        select(ExpenseClaim)
        .options(selectinload(ExpenseClaim.category))
        .where(
            ExpenseClaim.id == claim_id,
            ExpenseClaim.company_id == current_user.company_id,
            ExpenseClaim.employee_id == current_user.id,
        )
    )
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return claim


@router.get("/categories", response_model=list[ExpenseCategoryOut])
def list_claim_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    categories = db.scalars(
        select(ExpenseCategory)
        .where(
            ExpenseCategory.company_id == current_user.company_id,
            ExpenseCategory.is_active.is_(True),
        )
        .order_by(ExpenseCategory.name.asc())
    ).all()

    return [
        ExpenseCategoryOut(
            id=category.id,
            name=category.name,
            code=category.code,
            description=category.description,
        )
        for category in categories
    ]


@router.post("", response_model=ClaimOut, status_code=status.HTTP_201_CREATED)
def create_claim(
    payload: ClaimCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = _get_active_category_or_400(db, current_user.company_id, payload.category_id)

    original_currency = payload.original_currency.upper().strip()
    base_currency = current_user.company.base_currency

    claim = ExpenseClaim(
        company_id=current_user.company_id,
        employee_id=current_user.id,
        category_id=category.id,
        department_id=payload.department_id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description is not None else None,
        original_currency=original_currency,
        original_amount=payload.original_amount,
        base_currency=base_currency,
        converted_amount=payload.original_amount if original_currency == base_currency else None,
        expense_date=payload.expense_date,
        status=ExpenseClaimStatus.DRAFT,
    )

    db.add(claim)
    db.commit()
    db.refresh(claim)
    claim = _get_claim_for_user_or_404(db, current_user, claim.id)

    return _to_claim_out(claim)


@router.get("/my", response_model=ClaimListResponse)
def list_my_claims(
    status_filter: ExpenseClaimStatus | None = Query(default=None, alias="status"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(ExpenseClaim)
        .options(selectinload(ExpenseClaim.category))
        .where(
            ExpenseClaim.company_id == current_user.company_id,
            ExpenseClaim.employee_id == current_user.id,
        )
        .order_by(ExpenseClaim.created_at.desc())
    )

    if status_filter is not None:
        query = query.where(ExpenseClaim.status == status_filter)

    if date_from is not None:
        query = query.where(ExpenseClaim.expense_date >= date_from)

    if date_to is not None:
        query = query.where(ExpenseClaim.expense_date <= date_to)

    claims = db.scalars(query).all()
    return ClaimListResponse(claims=[_to_claim_out(claim) for claim in claims])


@router.get("/{claim_id}", response_model=ClaimOut)
def get_claim_detail(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    claim = _get_claim_for_user_or_404(db, current_user, claim_id)
    return _to_claim_out(claim)


@router.patch("/{claim_id}", response_model=ClaimOut)
def update_draft_claim(
    claim_id: int,
    payload: ClaimUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    claim = _get_claim_for_user_or_404(db, current_user, claim_id)

    if claim.status != ExpenseClaimStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft claims can be edited",
        )

    if payload.category_id is not None:
        category = _get_active_category_or_400(db, current_user.company_id, payload.category_id)
        claim.category_id = category.id

    if payload.title is not None:
        claim.title = payload.title.strip()

    if payload.description is not None:
        claim.description = payload.description.strip() if payload.description else None

    if payload.original_currency is not None:
        claim.original_currency = payload.original_currency.upper().strip()

    if payload.original_amount is not None:
        claim.original_amount = payload.original_amount

    if payload.expense_date is not None:
        claim.expense_date = payload.expense_date

    claim.department_id = payload.department_id

    if claim.original_currency == claim.base_currency:
        claim.converted_amount = claim.original_amount
    else:
        claim.converted_amount = None

    db.commit()
    db.refresh(claim)
    claim = _get_claim_for_user_or_404(db, current_user, claim.id)

    return _to_claim_out(claim)


@router.post("/{claim_id}/submit", response_model=ClaimOut)
def submit_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    claim = _get_claim_for_user_or_404(db, current_user, claim_id)

    if claim.status != ExpenseClaimStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft claims can be submitted",
        )

    claim.status = ExpenseClaimStatus.SUBMITTED
    claim.submitted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(claim)
    claim = _get_claim_for_user_or_404(db, current_user, claim.id)

    return _to_claim_out(claim)
