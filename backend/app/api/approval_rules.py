from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models import (
    ApprovalRule,
    ApprovalRuleStep,
    ApprovalRuleStrategy,
    ApproverRole,
    Department,
    ExpenseCategory,
    User,
    UserRole,
)
from app.schemas.approval_rule_admin import (
    ApprovalRuleCreateRequest,
    ApprovalRuleOut,
    ApprovalRuleStepCreateRequest,
    ApprovalRuleStepsReplaceRequest,
    ApprovalRuleUpdateRequest,
)

router = APIRouter(prefix="/approval-rules", tags=["approval-rules"])


def _get_rule_for_company_or_404(db: Session, company_id: int, rule_id: int) -> ApprovalRule:
    rule = db.scalar(
        select(ApprovalRule)
        .options(selectinload(ApprovalRule.steps))
        .where(ApprovalRule.id == rule_id, ApprovalRule.company_id == company_id)
    )
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval rule not found")
    return rule


def _validate_amount_range(min_amount: float | None, max_amount: float | None) -> None:
    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_amount cannot be greater than max_amount",
        )


def _validate_category_for_company(db: Session, company_id: int, category_id: int | None) -> None:
    if category_id is None:
        return

    category = db.scalar(
        select(ExpenseCategory).where(
            ExpenseCategory.id == category_id,
            ExpenseCategory.company_id == company_id,
        )
    )
    if category is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category for company")


def _validate_department_for_company(db: Session, company_id: int, department_id: int | None) -> None:
    if department_id is None:
        return

    department = db.scalar(
        select(Department).where(
            Department.id == department_id,
            Department.company_id == company_id,
        )
    )
    if department is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid department for company")


def _validate_approver_user_for_company(db: Session, company_id: int, user_id: int) -> User:
    user = db.scalar(
        select(User).where(
            User.id == user_id,
            User.company_id == company_id,
            User.is_active.is_(True),
        )
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid approver user for company")

    if not user.is_approver and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected approver user must be admin or marked approver",
        )

    return user


def _ensure_department_head_available(db: Session, company_id: int, department_id: int) -> None:
    candidates = db.scalars(
        select(User).where(
            User.company_id == company_id,
            User.department_id == department_id,
            User.is_active.is_(True),
        )
    ).all()

    has_head = any(candidate.role == UserRole.ADMIN or candidate.is_approver for candidate in candidates)
    if not has_head:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active admin/approver found in selected department",
        )


def _validate_rule_strategy(strategy: ApprovalRuleStrategy, min_approval_percentage: int | None) -> None:
    if strategy == ApprovalRuleStrategy.MIN_APPROVALS:
        if min_approval_percentage is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="min_approval_percentage is required for MIN_APPROVALS strategy",
            )
        return

    if min_approval_percentage is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_approval_percentage is only allowed for MIN_APPROVALS strategy",
        )


def _normalize_and_validate_steps(
    db: Session,
    company_id: int,
    steps: list[ApprovalRuleStepCreateRequest],
) -> list[ApprovalRuleStepCreateRequest]:
    seen_orders: set[int] = set()
    normalized: list[ApprovalRuleStepCreateRequest] = []

    for step in steps:
        if step.step_order in seen_orders:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate step_order: {step.step_order}",
            )
        seen_orders.add(step.step_order)

        approver_user_id = step.approver_user_id
        approver_department_id = step.approver_department_id

        if step.approver_role == ApproverRole.SPECIFIC_USER:
            if approver_user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Step {step.step_order}: approver_user_id is required for SPECIFIC_USER",
                )
            _validate_approver_user_for_company(db, company_id, approver_user_id)
            approver_department_id = None

        elif step.approver_role == ApproverRole.DEPARTMENT_HEAD:
            if approver_department_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Step {step.step_order}: approver_department_id is required for DEPARTMENT_HEAD",
                )
            _validate_department_for_company(db, company_id, approver_department_id)
            _ensure_department_head_available(db, company_id, approver_department_id)
            approver_user_id = None

        else:
            approver_user_id = None
            approver_department_id = None

        normalized.append(
            ApprovalRuleStepCreateRequest(
                step_order=step.step_order,
                name=step.name.strip(),
                approver_role=step.approver_role,
                approver_user_id=approver_user_id,
                approver_department_id=approver_department_id,
            )
        )

    return sorted(normalized, key=lambda current_step: current_step.step_order)


def _add_steps_to_rule(db: Session, rule_id: int, steps: list[ApprovalRuleStepCreateRequest]) -> None:
    for step in steps:
        db.add(
            ApprovalRuleStep(
                rule_id=rule_id,
                step_order=step.step_order,
                name=step.name,
                approver_role=step.approver_role,
                approver_user_id=step.approver_user_id,
                approver_department_id=step.approver_department_id,
            )
        )


@router.get("", response_model=list[ApprovalRuleOut])
def list_approval_rules(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    rules = db.scalars(
        select(ApprovalRule)
        .options(selectinload(ApprovalRule.steps))
        .where(ApprovalRule.company_id == admin_user.company_id)
        .order_by(ApprovalRule.priority.asc(), ApprovalRule.id.asc())
    ).all()
    return rules


@router.post("", response_model=ApprovalRuleOut, status_code=status.HTTP_201_CREATED)
def create_approval_rule(
    payload: ApprovalRuleCreateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    _validate_amount_range(payload.min_amount, payload.max_amount)
    _validate_category_for_company(db, admin_user.company_id, payload.category_id)
    _validate_department_for_company(db, admin_user.company_id, payload.department_id)
    _validate_rule_strategy(payload.strategy, payload.min_approval_percentage)
    normalized_steps = _normalize_and_validate_steps(db, admin_user.company_id, payload.steps)

    rule = ApprovalRule(
        company_id=admin_user.company_id,
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        min_amount=payload.min_amount,
        max_amount=payload.max_amount,
        category_id=payload.category_id,
        department_id=payload.department_id,
        strategy=payload.strategy,
        min_approval_percentage=payload.min_approval_percentage,
        is_active=payload.is_active,
        priority=payload.priority,
    )
    db.add(rule)
    db.flush()

    _add_steps_to_rule(db, rule.id, normalized_steps)

    db.commit()
    return _get_rule_for_company_or_404(db, admin_user.company_id, rule.id)


@router.patch("/{rule_id}", response_model=ApprovalRuleOut)
def update_approval_rule(
    rule_id: int,
    payload: ApprovalRuleUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    rule = _get_rule_for_company_or_404(db, admin_user.company_id, rule_id)

    min_amount = payload.min_amount if "min_amount" in payload.model_fields_set else float(rule.min_amount) if rule.min_amount is not None else None
    max_amount = payload.max_amount if "max_amount" in payload.model_fields_set else float(rule.max_amount) if rule.max_amount is not None else None
    strategy = payload.strategy if payload.strategy is not None else rule.strategy

    if "min_approval_percentage" in payload.model_fields_set:
        min_approval_percentage = payload.min_approval_percentage
    elif payload.strategy == ApprovalRuleStrategy.SEQUENTIAL:
        min_approval_percentage = None
    else:
        min_approval_percentage = rule.min_approval_percentage

    _validate_amount_range(min_amount, max_amount)
    if "category_id" in payload.model_fields_set:
        _validate_category_for_company(db, admin_user.company_id, payload.category_id)
    if "department_id" in payload.model_fields_set:
        _validate_department_for_company(db, admin_user.company_id, payload.department_id)
    _validate_rule_strategy(strategy, min_approval_percentage)

    if payload.name is not None:
        rule.name = payload.name.strip()

    if "description" in payload.model_fields_set:
        rule.description = payload.description.strip() if payload.description else None

    if "min_amount" in payload.model_fields_set:
        rule.min_amount = payload.min_amount

    if "max_amount" in payload.model_fields_set:
        rule.max_amount = payload.max_amount

    if "category_id" in payload.model_fields_set:
        rule.category_id = payload.category_id

    if "department_id" in payload.model_fields_set:
        rule.department_id = payload.department_id

    if payload.strategy is not None:
        rule.strategy = payload.strategy

    if "min_approval_percentage" in payload.model_fields_set or payload.strategy == ApprovalRuleStrategy.SEQUENTIAL:
        rule.min_approval_percentage = (
            min_approval_percentage if strategy == ApprovalRuleStrategy.MIN_APPROVALS else None
        )

    if payload.is_active is not None:
        rule.is_active = payload.is_active

    if payload.priority is not None:
        rule.priority = payload.priority

    db.commit()
    return _get_rule_for_company_or_404(db, admin_user.company_id, rule.id)


@router.put("/{rule_id}/steps", response_model=ApprovalRuleOut)
def replace_approval_rule_steps(
    rule_id: int,
    payload: ApprovalRuleStepsReplaceRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    rule = _get_rule_for_company_or_404(db, admin_user.company_id, rule_id)
    normalized_steps = _normalize_and_validate_steps(db, admin_user.company_id, payload.steps)

    db.execute(delete(ApprovalRuleStep).where(ApprovalRuleStep.rule_id == rule.id))
    _add_steps_to_rule(db, rule.id, normalized_steps)

    db.commit()
    return _get_rule_for_company_or_404(db, admin_user.company_id, rule.id)
