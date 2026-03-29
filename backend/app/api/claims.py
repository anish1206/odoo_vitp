from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_admin, get_current_user
from app.db.session import get_db
from app.models import (
    ApprovalActionLog,
    ApprovalTask,
    ApprovalTaskStatus,
    ExchangeRateSnapshot,
    ExpenseCategory,
    ExpenseClaim,
    ExpenseClaimStatus,
    ReceiptFile,
    User,
    UserRole,
)
from app.services.approval_engine import generate_tasks_for_submitted_claim
from app.services.currency_service import preview_conversion
from app.schemas.expense_claim import (
    ClaimApprovalTaskOut,
    ClaimCreateRequest,
    ClaimDetailOut,
    ClaimListResponse,
    ClaimOcrContextOut,
    ClaimOut,
    ClaimReceiptContextOut,
    ClaimTimelineEventOut,
    ClaimUpdateRequest,
    ExpenseCategoryOut,
)

router = APIRouter(prefix="/claims", tags=["claims"])


def _display_name(user: User | None) -> str | None:
    if user is None:
        return None
    return f"{user.first_name} {user.last_name}".strip()


def _pending_approver_names(claim: ExpenseClaim) -> list[str]:
    pending_tasks = sorted(
        (task for task in claim.approval_tasks if task.status == ApprovalTaskStatus.PENDING),
        key=lambda item: item.sequence_order,
    )
    names: list[str] = []
    seen: set[str] = set()
    for task in pending_tasks:
        approver_name = _display_name(task.approver) or f"User #{task.approver_id}"
        if approver_name in seen:
            continue
        seen.add(approver_name)
        names.append(approver_name)
    return names


def _latest_ocr_extraction(claim: ExpenseClaim):
    if claim.receipt_file is None:
        return None

    if not claim.receipt_file.ocr_extractions:
        return None

    return max(
        claim.receipt_file.ocr_extractions,
        key=lambda extraction: (extraction.created_at, extraction.id),
    )


def _to_claim_out(claim: ExpenseClaim) -> ClaimOut:
    category_name = claim.category.name if claim.category is not None else "Unknown"
    exchange_snapshot = claim.exchange_rate_snapshot
    department_name = claim.department.name if claim.department is not None else None

    return ClaimOut(
        id=claim.id,
        title=claim.title,
        description=claim.description,
        category_id=claim.category_id,
        category_name=category_name,
        receipt_file_id=claim.receipt_file_id,
        original_currency=claim.original_currency,
        original_amount=float(claim.original_amount),
        base_currency=claim.base_currency,
        converted_amount=None
        if claim.converted_amount is None
        else float(claim.converted_amount),
        exchange_rate_snapshot_id=claim.exchange_rate_snapshot_id,
        exchange_rate=None if exchange_snapshot is None else float(exchange_snapshot.rate),
        exchange_rate_provider=None if exchange_snapshot is None else exchange_snapshot.provider,
        exchange_rate_as_of=None if exchange_snapshot is None else exchange_snapshot.as_of,
        expense_date=claim.expense_date,
        status=claim.status.value,
        submitted_at=claim.submitted_at,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
        is_editable=claim.status == ExpenseClaimStatus.DRAFT,
        employee_id=claim.employee_id,
        employee_name=_display_name(claim.employee),
        department_id=claim.department_id,
        department_name=department_name,
        pending_approver_names=_pending_approver_names(claim),
    )


def _to_claim_detail_out(claim: ExpenseClaim) -> ClaimDetailOut:
    base_claim = _to_claim_out(claim)
    latest_ocr = _latest_ocr_extraction(claim)

    tasks = sorted(claim.approval_tasks, key=lambda task: (task.sequence_order, task.id))
    logs = sorted(claim.approval_logs, key=lambda log: (log.created_at, log.id))

    receipt_context = None
    if claim.receipt_file is not None:
        receipt_context = ClaimReceiptContextOut(
            receipt_id=claim.receipt_file.id,
            original_filename=claim.receipt_file.original_filename,
            file_mime_type=claim.receipt_file.file_mime_type,
            file_size_bytes=claim.receipt_file.file_size_bytes,
            uploaded_at=claim.receipt_file.uploaded_at,
        )

    ocr_context = None
    if latest_ocr is not None:
        ocr_context = ClaimOcrContextOut(
            extraction_id=latest_ocr.id,
            engine=latest_ocr.engine,
            confidence=latest_ocr.confidence,
            parsed_fields=latest_ocr.parsed_fields,
            created_at=latest_ocr.created_at,
        )

    return ClaimDetailOut(
        **base_claim.model_dump(),
        rejection_reason=claim.rejection_reason,
        current_approval_step=claim.current_approval_step,
        final_approved_at=claim.final_approved_at,
        approval_tasks=[
            ClaimApprovalTaskOut(
                task_id=task.id,
                sequence_order=task.sequence_order,
                status=task.status.value,
                approver_id=task.approver_id,
                approver_name=_display_name(task.approver),
                acted_at=task.acted_at,
                comment=task.comment,
            )
            for task in tasks
        ],
        approval_timeline=[
            ClaimTimelineEventOut(
                id=log.id,
                action_type=log.action_type.value,
                actor_name=_display_name(log.actor),
                description=log.description,
                created_at=log.created_at,
            )
            for log in logs
        ],
        receipt=receipt_context,
        ocr_extraction=ocr_context,
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
        .options(
            selectinload(ExpenseClaim.category),
            selectinload(ExpenseClaim.department),
            selectinload(ExpenseClaim.employee),
            selectinload(ExpenseClaim.exchange_rate_snapshot),
            selectinload(ExpenseClaim.approval_tasks).selectinload(ApprovalTask.approver),
            selectinload(ExpenseClaim.approval_logs).selectinload(ApprovalActionLog.actor),
            selectinload(ExpenseClaim.receipt_file).selectinload(ReceiptFile.ocr_extractions),
        )
        .where(
            ExpenseClaim.id == claim_id,
            ExpenseClaim.company_id == current_user.company_id,
            ExpenseClaim.employee_id == current_user.id,
        )
    )
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return claim


def _get_claim_for_company_or_404(db: Session, company_id: int, claim_id: int) -> ExpenseClaim:
    claim = db.scalar(
        select(ExpenseClaim)
        .options(
            selectinload(ExpenseClaim.category),
            selectinload(ExpenseClaim.department),
            selectinload(ExpenseClaim.employee),
            selectinload(ExpenseClaim.exchange_rate_snapshot),
            selectinload(ExpenseClaim.approval_tasks).selectinload(ApprovalTask.approver),
            selectinload(ExpenseClaim.approval_logs).selectinload(ApprovalActionLog.actor),
            selectinload(ExpenseClaim.receipt_file).selectinload(ReceiptFile.ocr_extractions),
        )
        .where(
            ExpenseClaim.id == claim_id,
            ExpenseClaim.company_id == company_id,
        )
    )
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return claim


def _assert_can_view_claim(current_user: User, claim: ExpenseClaim) -> None:
    if claim.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    if current_user.role == UserRole.ADMIN or claim.employee_id == current_user.id:
        return

    if current_user.is_approver and any(task.approver_id == current_user.id for task in claim.approval_tasks):
        return

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view this claim")


def _get_receipt_for_user_or_400(db: Session, current_user: User, receipt_file_id: int) -> ReceiptFile:
    receipt = db.scalar(
        select(ReceiptFile).where(
            ReceiptFile.id == receipt_file_id,
            ReceiptFile.company_id == current_user.company_id,
            ReceiptFile.employee_id == current_user.id,
        )
    )
    if receipt is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid receipt for current employee",
        )

    return receipt


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
        receipt_file_id=payload.receipt_file_id,
        original_currency=original_currency,
        original_amount=payload.original_amount,
        base_currency=base_currency,
        converted_amount=payload.original_amount if original_currency == base_currency else None,
        expense_date=payload.expense_date,
        status=ExpenseClaimStatus.DRAFT,
    )

    if payload.receipt_file_id is not None:
        _get_receipt_for_user_or_400(db, current_user, payload.receipt_file_id)

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
        .options(
            selectinload(ExpenseClaim.category),
            selectinload(ExpenseClaim.department),
            selectinload(ExpenseClaim.employee),
            selectinload(ExpenseClaim.exchange_rate_snapshot),
            selectinload(ExpenseClaim.approval_tasks).selectinload(ApprovalTask.approver),
        )
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


@router.get("/company", response_model=ClaimListResponse)
def list_company_claims(
    status_filter: ExpenseClaimStatus | None = Query(default=None, alias="status"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    employee_id: int | None = Query(default=None),
    department_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    query = (
        select(ExpenseClaim)
        .options(
            selectinload(ExpenseClaim.category),
            selectinload(ExpenseClaim.department),
            selectinload(ExpenseClaim.employee),
            selectinload(ExpenseClaim.exchange_rate_snapshot),
            selectinload(ExpenseClaim.approval_tasks).selectinload(ApprovalTask.approver),
        )
        .where(ExpenseClaim.company_id == admin_user.company_id)
        .order_by(ExpenseClaim.created_at.desc())
    )

    if status_filter is not None:
        query = query.where(ExpenseClaim.status == status_filter)

    if date_from is not None:
        query = query.where(ExpenseClaim.expense_date >= date_from)

    if date_to is not None:
        query = query.where(ExpenseClaim.expense_date <= date_to)

    if employee_id is not None:
        query = query.where(ExpenseClaim.employee_id == employee_id)

    if department_id is not None:
        query = query.where(ExpenseClaim.department_id == department_id)

    claims = db.scalars(query).all()
    return ClaimListResponse(claims=[_to_claim_out(claim) for claim in claims])


@router.get("/company/{claim_id}", response_model=ClaimDetailOut)
def get_company_claim_detail(
    claim_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    claim = _get_claim_for_company_or_404(db, admin_user.company_id, claim_id)
    return _to_claim_detail_out(claim)


@router.get("/{claim_id}", response_model=ClaimDetailOut)
def get_claim_detail(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    claim = _get_claim_for_company_or_404(db, current_user.company_id, claim_id)
    _assert_can_view_claim(current_user, claim)
    return _to_claim_detail_out(claim)


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

    if "receipt_file_id" in payload.model_fields_set:
        if payload.receipt_file_id is not None:
            _get_receipt_for_user_or_400(db, current_user, payload.receipt_file_id)
        claim.receipt_file_id = payload.receipt_file_id

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

    if "department_id" in payload.model_fields_set:
        claim.department_id = payload.department_id

    if claim.original_currency == claim.base_currency:
        claim.converted_amount = claim.original_amount
        claim.exchange_rate_snapshot_id = None
    else:
        claim.converted_amount = None
        claim.exchange_rate_snapshot_id = None

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

    if claim.original_currency == claim.base_currency:
        claim.converted_amount = claim.original_amount
        claim.exchange_rate_snapshot_id = None
    else:
        try:
            preview = preview_conversion(
                base_currency=claim.base_currency,
                foreign_currency=claim.original_currency,
                amount=float(claim.original_amount),
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        snapshot = ExchangeRateSnapshot(
            base_currency=preview.base_currency,
            foreign_currency=preview.foreign_currency,
            rate=preview.rate,
            provider=preview.provider,
            as_of=preview.as_of,
        )
        db.add(snapshot)
        db.flush()

        claim.exchange_rate_snapshot_id = snapshot.id
        claim.converted_amount = preview.converted_amount

    claim.status = ExpenseClaimStatus.SUBMITTED
    claim.submitted_at = datetime.now(timezone.utc)

    try:
        generate_tasks_for_submitted_claim(
            db=db,
            claim=claim,
            actor_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(claim)
    claim = _get_claim_for_user_or_404(db, current_user, claim.id)

    return _to_claim_out(claim)
