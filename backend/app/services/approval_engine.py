from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import ceil

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    ApprovalActionLog,
    ApprovalActionType,
    ApprovalRule,
    ApprovalRuleStrategy,
    ApprovalTask,
    ApprovalTaskStatus,
    ApproverRole,
    ExpenseClaim,
    ExpenseClaimStatus,
    User,
    UserRole,
)


@dataclass
class ApprovalRoutingResult:
    matched_rule: ApprovalRule | None
    used_fallback: bool
    created_tasks: list[ApprovalTask]


def _rule_matches_claim(rule: ApprovalRule, claim: ExpenseClaim) -> bool:
    amount = float(claim.original_amount)

    if rule.min_amount is not None and amount < float(rule.min_amount):
        return False

    if rule.max_amount is not None and amount > float(rule.max_amount):
        return False

    if rule.category_id is not None and rule.category_id != claim.category_id:
        return False

    if rule.department_id is not None and rule.department_id != claim.department_id:
        return False

    return True


def _get_manager_chain(db: Session, claim: ExpenseClaim) -> list[User]:
    chain: list[User] = []
    seen_ids: set[int] = set()
    manager_id = claim.employee.manager_id

    while manager_id is not None:
        if manager_id in seen_ids:
            break

        seen_ids.add(manager_id)
        manager = db.get(User, manager_id)
        if manager is None:
            break

        if manager.company_id != claim.company_id:
            break

        if manager.is_active:
            chain.append(manager)

        manager_id = manager.manager_id

    return chain


def _resolve_fallback_approvers(db: Session, claim: ExpenseClaim) -> list[User]:
    manager_chain = _get_manager_chain(db, claim)
    if manager_chain:
        return manager_chain

    company_approvers = db.scalars(
        select(User)
        .where(
            User.company_id == claim.company_id,
            User.is_active.is_(True),
            User.id != claim.employee_id,
        )
        .order_by(User.role.desc(), User.id.asc())
    ).all()

    for candidate in company_approvers:
        if candidate.is_approver or candidate.role == UserRole.ADMIN:
            return [candidate]

    if claim.employee.is_active and (
        claim.employee.is_approver or claim.employee.role == UserRole.ADMIN
    ):
        return [claim.employee]

    return []


def _resolve_step_approver_id(
    db: Session,
    step_approver_role: ApproverRole,
    step_approver_user_id: int | None,
    step_approver_department_id: int | None,
    claim: ExpenseClaim,
    manager_level: int = 1,
) -> int | None:
    if step_approver_user_id is not None:
        approver = db.get(User, step_approver_user_id)
        if approver is None or not approver.is_active or approver.company_id != claim.company_id:
            return None
        return approver.id

    if step_approver_role == ApproverRole.MANAGER:
        manager_chain = _get_manager_chain(db, claim)
        manager_index = manager_level - 1
        if manager_index < 0 or manager_index >= len(manager_chain):
            return None

        return manager_chain[manager_index].id

    if step_approver_role == ApproverRole.DEPARTMENT_HEAD:
        if step_approver_department_id is None:
            return None

        candidates = db.scalars(
            select(User).where(
                User.company_id == claim.company_id,
                User.department_id == step_approver_department_id,
                User.is_active.is_(True),
            )
        ).all()

        for candidate in candidates:
            if candidate.role == UserRole.ADMIN:
                return candidate.id

        for candidate in candidates:
            if candidate.is_approver:
                return candidate.id

    return None


def generate_tasks_for_submitted_claim(
    db: Session,
    claim: ExpenseClaim,
    actor_id: int,
) -> ApprovalRoutingResult:
    rules = db.scalars(
        select(ApprovalRule)
        .options(selectinload(ApprovalRule.steps))
        .where(
            ApprovalRule.company_id == claim.company_id,
            ApprovalRule.is_active.is_(True),
        )
        .order_by(ApprovalRule.priority.asc(), ApprovalRule.id.asc())
    ).all()

    matched_rule = next((rule for rule in rules if _rule_matches_claim(rule, claim)), None)

    created_tasks: list[ApprovalTask] = []
    used_fallback = False

    if matched_rule is not None:
        manager_step_count = 0
        for step in sorted(matched_rule.steps, key=lambda current_step: current_step.step_order):
            manager_level = 1
            if step.approver_role == ApproverRole.MANAGER:
                manager_step_count += 1
                manager_level = manager_step_count

            approver_id = _resolve_step_approver_id(
                db=db,
                step_approver_role=step.approver_role,
                step_approver_user_id=step.approver_user_id,
                step_approver_department_id=step.approver_department_id,
                claim=claim,
                manager_level=manager_level,
            )
            if approver_id is None:
                continue

            created_tasks.append(
                ApprovalTask(
                    claim_id=claim.id,
                    rule_id=matched_rule.id,
                    rule_step_id=step.id,
                    approver_id=approver_id,
                    sequence_order=step.step_order,
                    status=ApprovalTaskStatus.PENDING,
                )
            )

    if not created_tasks:
        fallback_approvers = _resolve_fallback_approvers(db, claim)
        if not fallback_approvers:
            raise ValueError("No approver available. Assign a manager or approver user first.")

        for index, fallback_approver in enumerate(fallback_approvers, start=1):
            created_tasks.append(
                ApprovalTask(
                    claim_id=claim.id,
                    rule_id=None,
                    rule_step_id=None,
                    approver_id=fallback_approver.id,
                    sequence_order=index,
                    status=ApprovalTaskStatus.PENDING,
                )
            )
        used_fallback = True

    for task in created_tasks:
        db.add(task)

    db.flush()

    claim.status = ExpenseClaimStatus.IN_REVIEW
    claim.current_approval_step = min(task.sequence_order for task in created_tasks)
    claim.rejection_reason = None
    claim.final_approved_at = None

    db.add(
        ApprovalActionLog(
            claim_id=claim.id,
            actor_id=actor_id,
            action_type=ApprovalActionType.SUBMITTED,
            description="Claim submitted for approval",
        )
    )

    if matched_rule is not None:
        db.add(
            ApprovalActionLog(
                claim_id=claim.id,
                actor_id=actor_id,
                action_type=ApprovalActionType.RULE_MATCHED,
                description=f"Matched approval rule: {matched_rule.name}",
            )
        )

    if used_fallback:
        db.add(
            ApprovalActionLog(
                claim_id=claim.id,
                actor_id=actor_id,
                action_type=ApprovalActionType.FALLBACK_MANAGER_USED,
                description="Fallback approver assignment used",
            )
        )

    return ApprovalRoutingResult(
        matched_rule=matched_rule,
        used_fallback=used_fallback,
        created_tasks=created_tasks,
    )


def is_task_actionable(task: ApprovalTask) -> bool:
    if task.status != ApprovalTaskStatus.PENDING:
        return False

    pending_orders = [
        claim_task.sequence_order
        for claim_task in task.claim.approval_tasks
        if claim_task.status == ApprovalTaskStatus.PENDING
    ]

    if not pending_orders:
        return False

    return task.sequence_order == min(pending_orders)


def apply_approval_decision(
    db: Session,
    task: ApprovalTask,
    actor: User,
    approve: bool,
    comment: str | None,
) -> ExpenseClaim:
    if task.status != ApprovalTaskStatus.PENDING:
        raise ValueError("Task is not pending")

    if not is_task_actionable(task):
        raise ValueError("Task is not actionable yet")

    now = datetime.now(timezone.utc)

    task.acted_at = now
    task.acted_by = actor.id
    task.comment = comment

    if approve:
        task.status = ApprovalTaskStatus.APPROVED
        action_type = ApprovalActionType.APPROVED

        rule = task.rule
        if rule is not None and rule.strategy == ApprovalRuleStrategy.MIN_APPROVALS:
            total_tasks = len(task.claim.approval_tasks)
            threshold = max(1, ceil(total_tasks * (rule.min_approval_percentage or 100) / 100))
            approved_count = sum(
                1
                for claim_task in task.claim.approval_tasks
                if claim_task.status == ApprovalTaskStatus.APPROVED
            )

            if approved_count >= threshold:
                for pending_task in task.claim.approval_tasks:
                    if pending_task.status == ApprovalTaskStatus.PENDING:
                        pending_task.status = ApprovalTaskStatus.SKIPPED

                task.claim.status = ExpenseClaimStatus.APPROVED
                task.claim.current_approval_step = None
                task.claim.final_approved_at = now
            else:
                task.claim.status = ExpenseClaimStatus.IN_REVIEW
                task.claim.final_approved_at = None
        else:
            pending_tasks = [
                claim_task
                for claim_task in task.claim.approval_tasks
                if claim_task.status == ApprovalTaskStatus.PENDING
            ]

            if not pending_tasks:
                task.claim.status = ExpenseClaimStatus.APPROVED
                task.claim.current_approval_step = None
                task.claim.final_approved_at = now
            else:
                task.claim.status = ExpenseClaimStatus.IN_REVIEW
                task.claim.current_approval_step = min(
                    pending_task.sequence_order for pending_task in pending_tasks
                )
                task.claim.final_approved_at = None

    else:
        task.status = ApprovalTaskStatus.REJECTED
        action_type = ApprovalActionType.REJECTED

        for pending_task in task.claim.approval_tasks:
            if pending_task.id != task.id and pending_task.status == ApprovalTaskStatus.PENDING:
                pending_task.status = ApprovalTaskStatus.SKIPPED

        task.claim.status = ExpenseClaimStatus.REJECTED
        task.claim.current_approval_step = None
        task.claim.rejection_reason = comment
        task.claim.final_approved_at = None

    db.add(
        ApprovalActionLog(
            claim_id=task.claim_id,
            actor_id=actor.id,
            task_id=task.id,
            action_type=action_type,
            description=comment,
        )
    )

    return task.claim
