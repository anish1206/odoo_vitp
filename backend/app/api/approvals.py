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
    User,
    UserRole,
)
from app.schemas.approvals import (
    ApprovalDecisionRequest,
    ApprovalDecisionResponse,
    ApprovalTaskClaimDetailOut,
    ApprovalTaskListResponse,
    ApprovalTaskSummaryOut,
)
from app.services.approval_engine import apply_approval_decision, is_task_actionable

router = APIRouter(prefix="/approvals", tags=["approvals"])


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
            selectinload(ApprovalTask.claim).selectinload(ExpenseClaim.approval_tasks),
            selectinload(ApprovalTask.claim)
            .selectinload(ExpenseClaim.approval_logs)
            .selectinload(ApprovalActionLog.actor),
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
            selectinload(ApprovalTask.claim).selectinload(ExpenseClaim.approval_tasks),
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

    return ApprovalTaskClaimDetailOut(
        task_id=task.id,
        claim_id=claim.id,
        employee_name=f"{claim.employee.first_name} {claim.employee.last_name}".strip(),
        claim_title=claim.title,
        claim_description=claim.description,
        category_name=claim.category.name if claim.category is not None else "Unknown",
        expense_date=claim.expense_date,
        original_currency=claim.original_currency,
        original_amount=float(claim.original_amount),
        status=claim.status.value,
        current_approval_step=claim.current_approval_step,
        logs=[
            {
                "id": log.id,
                "action_type": log.action_type.value,
                "actor_name": None
                if log.actor is None
                else f"{log.actor.first_name} {log.actor.last_name}".strip(),
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
