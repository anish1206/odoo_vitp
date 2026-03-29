from uuid import uuid4

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models import ApprovalTask, ApprovalTaskStatus, ExpenseClaim, ExpenseClaimStatus, User, UserRole


def _signup_payload() -> dict[str, str]:
    unique = uuid4().hex[:8]
    return {
        "company_name": f"Approve Co {unique}",
        "country_code": "IN",
        "admin_first_name": "Admin",
        "admin_last_name": "Owner",
        "email": f"admin.{unique}@example.com",
        "password": "TestPass123!",
    }


def _create_employee_and_manager(company_id: int, unique: str) -> tuple[User, User]:
    with SessionLocal() as db:
        manager = User(
            company_id=company_id,
            email=f"manager.{unique}@example.com",
            hashed_password=get_password_hash("TestPass123!"),
            first_name="Manager",
            last_name="User",
            role=UserRole.EMPLOYEE,
            is_approver=True,
            is_active=True,
        )
        db.add(manager)
        db.flush()

        employee = User(
            company_id=company_id,
            email=f"employee.{unique}@example.com",
            hashed_password=get_password_hash("TestPass123!"),
            first_name="Employee",
            last_name="User",
            role=UserRole.EMPLOYEE,
            is_approver=False,
            is_active=True,
            manager_id=manager.id,
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)
        db.refresh(manager)

        return employee, manager


def _auth_headers_for_login(client, email: str, password: str) -> dict[str, str]:
    login_response = client.post("/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_submission_creates_approval_task_and_approve_flow(client):
    unique = uuid4().hex[:8]
    signup_response = client.post("/auth/signup", json=_signup_payload())
    assert signup_response.status_code == 201

    company_id = signup_response.json()["company"]["id"]
    _, manager = _create_employee_and_manager(company_id=company_id, unique=unique)

    employee_headers = _auth_headers_for_login(client, f"employee.{unique}@example.com", "TestPass123!")
    manager_headers = _auth_headers_for_login(client, f"manager.{unique}@example.com", "TestPass123!")

    categories_response = client.get("/claims/categories", headers=employee_headers)
    assert categories_response.status_code == 200
    category_id = categories_response.json()[0]["id"]

    draft_response = client.post(
        "/claims",
        headers=employee_headers,
        json={
            "title": "Hotel booking",
            "description": "Client visit stay",
            "category_id": category_id,
            "original_currency": "INR",
            "original_amount": 4200,
            "expense_date": "2026-03-29",
        },
    )
    assert draft_response.status_code == 201
    claim_id = draft_response.json()["id"]

    submit_response = client.post(f"/claims/{claim_id}/submit", headers=employee_headers)
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "IN_REVIEW"

    inbox_response = client.get("/approvals/tasks", headers=manager_headers)
    assert inbox_response.status_code == 200
    tasks = inbox_response.json()["tasks"]
    assert len(tasks) == 1
    task_id = tasks[0]["task_id"]
    assert tasks[0]["is_actionable"] is True

    approve_response = client.post(
        f"/approvals/tasks/{task_id}/approve",
        headers=manager_headers,
        json={"comment": "Looks good"},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["task_status"] == "APPROVED"
    assert approve_response.json()["claim_status"] == "APPROVED"

    with SessionLocal() as db:
        claim = db.get(ExpenseClaim, claim_id)
        task = db.get(ApprovalTask, task_id)
        assert claim is not None
        assert task is not None
        assert claim.status == ExpenseClaimStatus.APPROVED
        assert task.status == ApprovalTaskStatus.APPROVED
        assert task.approver_id == manager.id


def test_reject_requires_comment_and_sets_claim_rejected(client):
    unique = uuid4().hex[:8]
    signup_response = client.post("/auth/signup", json=_signup_payload())
    assert signup_response.status_code == 201

    company_id = signup_response.json()["company"]["id"]
    _create_employee_and_manager(company_id=company_id, unique=unique)

    employee_headers = _auth_headers_for_login(client, f"employee.{unique}@example.com", "TestPass123!")
    manager_headers = _auth_headers_for_login(client, f"manager.{unique}@example.com", "TestPass123!")

    category_id = client.get("/claims/categories", headers=employee_headers).json()[0]["id"]

    claim_id = client.post(
        "/claims",
        headers=employee_headers,
        json={
            "title": "Meal expense",
            "description": "Dinner with client",
            "category_id": category_id,
            "original_currency": "INR",
            "original_amount": 1500,
            "expense_date": "2026-03-29",
        },
    ).json()["id"]

    client.post(f"/claims/{claim_id}/submit", headers=employee_headers)

    task_id = client.get("/approvals/tasks", headers=manager_headers).json()["tasks"][0]["task_id"]

    missing_comment_response = client.post(
        f"/approvals/tasks/{task_id}/reject",
        headers=manager_headers,
        json={"comment": ""},
    )
    assert missing_comment_response.status_code == 400
    assert missing_comment_response.json()["detail"] == "Rejection comment is required"

    reject_response = client.post(
        f"/approvals/tasks/{task_id}/reject",
        headers=manager_headers,
        json={"comment": "Missing required invoice details"},
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["task_status"] == "REJECTED"
    assert reject_response.json()["claim_status"] == "REJECTED"

    with SessionLocal() as db:
        claim = db.get(ExpenseClaim, claim_id)
        task = db.get(ApprovalTask, task_id)
        assert claim is not None
        assert task is not None
        assert claim.status == ExpenseClaimStatus.REJECTED
        assert claim.rejection_reason == "Missing required invoice details"
        assert task.status == ApprovalTaskStatus.REJECTED


def test_non_approver_cannot_access_approval_inbox(client):
    unique = uuid4().hex[:8]
    signup_response = client.post("/auth/signup", json=_signup_payload())
    assert signup_response.status_code == 201

    company_id = signup_response.json()["company"]["id"]

    with SessionLocal() as db:
        employee = User(
            company_id=company_id,
            email=f"simple.employee.{unique}@example.com",
            hashed_password=get_password_hash("TestPass123!"),
            first_name="Simple",
            last_name="Employee",
            role=UserRole.EMPLOYEE,
            is_approver=False,
            is_active=True,
        )
        db.add(employee)
        db.commit()

    employee_headers = _auth_headers_for_login(
        client,
        f"simple.employee.{unique}@example.com",
        "TestPass123!",
    )

    inbox_response = client.get("/approvals/tasks", headers=employee_headers)
    assert inbox_response.status_code == 403
    assert inbox_response.json()["detail"] == "Approver access required"
