from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import (
    ApprovalActionLog,
    ApprovalTask,
    ApprovalTaskStatus,
    ExpenseClaim,
    ReceiptFile,
    User,
    UserRole,
)
from app.schemas.approvals import (
    ApprovalDecisionRequest,
    ApprovalDecisionResponse,
    ApprovalOcrContextOut,
    ApprovalReceiptContextOut,
    ApprovalTaskClaimDetailOut,
    ApprovalTaskListResponse,
    ApprovalTaskSummaryOut,
)
from app.services.approval_engine import apply_approval_decision, is_task_actionable

router = APIRouter(prefix="/approvals", tags=["approvals"])


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

    for pending_task in pending_tasks:
        approver_name = _display_name(pending_task.approver) or f"User #{pending_task.approver_id}"
        if approver_name in seen:
            continue
        seen.add(approver_name)
        names.append(approver_name)

    return names


def _get_current_approver_or_403(current_user: User) -> User:
    if current_user.is_approver or current_user.role == UserRole.ADMIN:
        return current_user

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Approver access required")


def _load_task_for_approver_or_404(db: Session, approver_id: int, task_id: int) -> ApprovalTask:
    task = db.scalar(
        select(ApprovalTask)
        .options(
            selectinload(ApprovalTask.claim).selectinload(ExpenseClaim.employee),
            selectinload(ApprovalTask.claim).selectinload(ExpenseClaim.category),
            selectinload(ApprovalTask.claim).selectinload(ExpenseClaim.exchange_rate_snapshot),
            selectinload(ApprovalTask.claim)
            .selectinload(ExpenseClaim.approval_tasks)
            .selectinload(ApprovalTask.approver),
            selectinload(ApprovalTask.claim)
            .selectinload(ExpenseClaim.approval_logs)
            .selectinload(ApprovalActionLog.actor),
            selectinload(ApprovalTask.claim)
            .selectinload(ExpenseClaim.receipt_file)
            .selectinload(ReceiptFile.ocr_extractions),
            selectinload(ApprovalTask.rule),
        )
        .where(ApprovalTask.id == task_id, ApprovalTask.approver_id == approver_id)
    )

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval task not found")

    return task


@router.get("/tasks", response_model=ApprovalTaskListResponse)
def list_approval_tasks(
    status_filter: ApprovalTaskStatus = Query(default=ApprovalTaskStatus.PENDING, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    approver = _get_current_approver_or_403(current_user)

    tasks = db.scalars(
        select(ApprovalTask)
        .options(
            selectinload(ApprovalTask.claim).selectinload(ExpenseClaim.employee),
            selectinload(ApprovalTask.claim).selectinload(ExpenseClaim.category),
            selectinload(ApprovalTask.claim)
            .selectinload(ExpenseClaim.approval_tasks)
            .selectinload(ApprovalTask.approver),
        )
        .where(
            ApprovalTask.approver_id == approver.id,
            ApprovalTask.status == status_filter,
        )
        .order_by(ApprovalTask.created_at.asc())
    ).all()

    response_items: list[ApprovalTaskSummaryOut] = []

    for task in tasks:
        claim = task.claim
        actionable = is_task_actionable(task)

        if status_filter == ApprovalTaskStatus.PENDING and not actionable:
            continue

        response_items.append(
            ApprovalTaskSummaryOut(
                task_id=task.id,
                claim_id=claim.id,
                claim_title=claim.title,
                employee_name=f"{claim.employee.first_name} {claim.employee.last_name}".strip(),
                category_name=claim.category.name if claim.category is not None else "Unknown",
                original_currency=claim.original_currency,
                original_amount=float(claim.original_amount),
                submitted_at=claim.submitted_at,
                sequence_order=task.sequence_order,
                status=task.status.value,
                is_actionable=actionable,
            )
        )

    return ApprovalTaskListResponse(tasks=response_items)


@router.get("/tasks/{task_id}", response_model=ApprovalTaskClaimDetailOut)
def get_approval_task_detail(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    approver = _get_current_approver_or_403(current_user)
    task = _load_task_for_approver_or_404(db, approver.id, task_id)

    claim = task.claim
    logs = sorted(claim.approval_logs, key=lambda item: item.created_at)
    latest_ocr = None
    if claim.receipt_file is not None and claim.receipt_file.ocr_extractions:
        latest_ocr = max(
            claim.receipt_file.ocr_extractions,
            key=lambda extraction: (extraction.created_at, extraction.id),
        )

    receipt_context = None
    if claim.receipt_file is not None:
        receipt_context = ApprovalReceiptContextOut(
            receipt_id=claim.receipt_file.id,
            original_filename=claim.receipt_file.original_filename,
            file_mime_type=claim.receipt_file.file_mime_type,
            file_size_bytes=claim.receipt_file.file_size_bytes,
            uploaded_at=claim.receipt_file.uploaded_at,
        )

    ocr_context = None
    if latest_ocr is not None:
        ocr_context = ApprovalOcrContextOut(
            extraction_id=latest_ocr.id,
            engine=latest_ocr.engine,
            confidence=latest_ocr.confidence,
            parsed_fields=latest_ocr.parsed_fields,
            created_at=latest_ocr.created_at,
        )

    return ApprovalTaskClaimDetailOut(
        task_id=task.id,
        claim_id=claim.id,
        employee_name=_display_name(claim.employee) or "Unknown",
        claim_title=claim.title,
        claim_description=claim.description,
        category_name=claim.category.name if claim.category is not None else "Unknown",
        expense_date=claim.expense_date,
        original_currency=claim.original_currency,
        original_amount=float(claim.original_amount),
        base_currency=claim.base_currency,
        converted_amount=None if claim.converted_amount is None else float(claim.converted_amount),
        exchange_rate=None
        if claim.exchange_rate_snapshot is None
        else float(claim.exchange_rate_snapshot.rate),
        exchange_rate_provider=None
        if claim.exchange_rate_snapshot is None
        else claim.exchange_rate_snapshot.provider,
        status=claim.status.value,
        current_approval_step=claim.current_approval_step,
        pending_approver_names=_pending_approver_names(claim),
        receipt=receipt_context,
        ocr_extraction=ocr_context,
        logs=[
            {
                "id": log.id,
                "action_type": log.action_type.value,
                "actor_name": _display_name(log.actor),
                "description": log.description,
                "created_at": log.created_at,
            }
            for log in logs
        ],
    )


@router.post("/tasks/{task_id}/approve", response_model=ApprovalDecisionResponse)
def approve_task(
    task_id: int,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    approver = _get_current_approver_or_403(current_user)
    task = _load_task_for_approver_or_404(db, approver.id, task_id)

    try:
        claim = apply_approval_decision(
            db=db,
            task=task,
            actor=approver,
            approve=True,
            comment=payload.comment.strip() if payload.comment else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(task)
    db.refresh(claim)

    return ApprovalDecisionResponse(
        task_id=task.id,
        task_status=task.status.value,
        claim_id=claim.id,
        claim_status=claim.status.value,
    )


@router.post("/tasks/{task_id}/reject", response_model=ApprovalDecisionResponse)
def reject_task(
    task_id: int,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    approver = _get_current_approver_or_403(current_user)
    task = _load_task_for_approver_or_404(db, approver.id, task_id)

    if payload.comment is None or not payload.comment.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection comment is required",
        )

    try:
        claim = apply_approval_decision(
            db=db,
            task=task,
            actor=approver,
            approve=False,
            comment=payload.comment.strip(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(task)
    db.refresh(claim)

    return ApprovalDecisionResponse(
        task_id=task.id,
        task_status=task.status.value,
        claim_id=claim.id,
        claim_status=claim.status.value,
    )
