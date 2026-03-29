from uuid import uuid4


def _signup_payload() -> dict[str, str]:
    unique = uuid4().hex[:8]
    return {
        "company_name": f"Rules Co {unique}",
        "country_code": "IN",
        "admin_first_name": "Rules",
        "admin_last_name": "Owner",
        "email": f"rules.admin.{unique}@example.com",
        "password": "TestPass123!",
    }


def _login_headers(client, email: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def _create_department(client, admin_headers: dict[str, str], name: str, code: str) -> int:
    response = client.post(
        "/departments",
        headers=admin_headers,
        json={"name": name, "code": code},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_user(
    client,
    admin_headers: dict[str, str],
    *,
    email: str,
    first_name: str,
    last_name: str,
    role: str = "EMPLOYEE",
    is_approver: bool = False,
    department_id: int | None = None,
    manager_id: int | None = None,
    password: str = "TestPass123!",
) -> dict:
    response = client.post(
        "/users",
        headers=admin_headers,
        json={
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "role": role,
            "is_approver": is_approver,
            "department_id": department_id,
            "manager_id": manager_id,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_admin_can_crud_approval_rules(client):
    signup_response = client.post("/auth/signup", json=_signup_payload())
    assert signup_response.status_code == 201

    signup_data = signup_response.json()
    admin_headers = {"Authorization": f"Bearer {signup_data['access_token']}"}

    department_id = _create_department(client, admin_headers, "Finance", "fin")

    approver = _create_user(
        client,
        admin_headers,
        email=f"approver.{uuid4().hex[:8]}@example.com",
        first_name="Finance",
        last_name="Approver",
        is_approver=True,
        department_id=department_id,
    )

    categories_response = client.get("/claims/categories", headers=admin_headers)
    assert categories_response.status_code == 200
    category_id = categories_response.json()[0]["id"]

    create_rule_response = client.post(
        "/approval-rules",
        headers=admin_headers,
        json={
            "name": "Large Finance Spend",
            "description": "Finance claims above threshold",
            "min_amount": 1000,
            "max_amount": 10000,
            "category_id": category_id,
            "department_id": department_id,
            "strategy": "MIN_APPROVALS",
            "min_approval_percentage": 50,
            "is_active": True,
            "priority": 10,
            "steps": [
                {
                    "step_order": 1,
                    "name": "Finance Approver",
                    "approver_role": "SPECIFIC_USER",
                    "approver_user_id": approver["id"],
                },
                {
                    "step_order": 2,
                    "name": "Manager Check",
                    "approver_role": "MANAGER",
                },
            ],
        },
    )
    assert create_rule_response.status_code == 201
    rule = create_rule_response.json()
    assert rule["name"] == "Large Finance Spend"
    assert rule["strategy"] == "MIN_APPROVALS"
    assert rule["min_approval_percentage"] == 50
    assert len(rule["steps"]) == 2

    rule_id = rule["id"]

    list_response = client.get("/approval-rules", headers=admin_headers)
    assert list_response.status_code == 200
    listed_ids = [item["id"] for item in list_response.json()]
    assert rule_id in listed_ids

    update_response = client.patch(
        f"/approval-rules/{rule_id}",
        headers=admin_headers,
        json={
            "strategy": "SEQUENTIAL",
            "is_active": False,
            "priority": 7,
        },
    )
    assert update_response.status_code == 200
    updated_rule = update_response.json()
    assert updated_rule["strategy"] == "SEQUENTIAL"
    assert updated_rule["min_approval_percentage"] is None
    assert updated_rule["is_active"] is False
    assert updated_rule["priority"] == 7

    replace_steps_response = client.put(
        f"/approval-rules/{rule_id}/steps",
        headers=admin_headers,
        json={
            "steps": [
                {
                    "step_order": 1,
                    "name": "Department Head",
                    "approver_role": "DEPARTMENT_HEAD",
                    "approver_department_id": department_id,
                }
            ]
        },
    )
    assert replace_steps_response.status_code == 200
    replaced_rule = replace_steps_response.json()
    assert len(replaced_rule["steps"]) == 1
    assert replaced_rule["steps"][0]["approver_role"] == "DEPARTMENT_HEAD"


def test_non_admin_cannot_access_approval_rule_admin_endpoints(client):
    signup_response = client.post("/auth/signup", json=_signup_payload())
    assert signup_response.status_code == 201

    signup_data = signup_response.json()
    admin_headers = {"Authorization": f"Bearer {signup_data['access_token']}"}

    employee = _create_user(
        client,
        admin_headers,
        email=f"employee.{uuid4().hex[:8]}@example.com",
        first_name="Rule",
        last_name="Employee",
        is_approver=False,
    )

    employee_headers = _login_headers(client, employee["email"], "TestPass123!")

    list_response = client.get("/approval-rules", headers=employee_headers)
    assert list_response.status_code == 403
    assert list_response.json()["detail"] == "Admin access required"

    create_response = client.post(
        "/approval-rules",
        headers=employee_headers,
        json={
            "name": "Should fail",
            "strategy": "SEQUENTIAL",
            "is_active": True,
            "priority": 100,
            "steps": [
                {
                    "step_order": 1,
                    "name": "Manager",
                    "approver_role": "MANAGER",
                }
            ],
        },
    )
    assert create_response.status_code == 403
    assert create_response.json()["detail"] == "Admin access required"


def test_highest_priority_active_rule_is_selected(client):
    unique = uuid4().hex[:8]
    signup_response = client.post("/auth/signup", json=_signup_payload())
    assert signup_response.status_code == 201

    signup_data = signup_response.json()
    admin_headers = {"Authorization": f"Bearer {signup_data['access_token']}"}

    department_id = _create_department(client, admin_headers, "Engineering", "eng")

    low_priority_approver = _create_user(
        client,
        admin_headers,
        email=f"low.approver.{unique}@example.com",
        first_name="Low",
        last_name="Approver",
        is_approver=True,
        department_id=department_id,
    )
    high_priority_approver = _create_user(
        client,
        admin_headers,
        email=f"high.approver.{unique}@example.com",
        first_name="High",
        last_name="Approver",
        is_approver=True,
        department_id=department_id,
    )

    employee = _create_user(
        client,
        admin_headers,
        email=f"employee.{unique}@example.com",
        first_name="Claim",
        last_name="Employee",
        is_approver=False,
        department_id=department_id,
        manager_id=low_priority_approver["id"],
    )

    employee_headers = _login_headers(client, employee["email"], "TestPass123!")
    low_headers = _login_headers(client, low_priority_approver["email"], "TestPass123!")
    high_headers = _login_headers(client, high_priority_approver["email"], "TestPass123!")

    categories_response = client.get("/claims/categories", headers=employee_headers)
    assert categories_response.status_code == 200
    category_id = categories_response.json()[0]["id"]

    low_priority_rule_response = client.post(
        "/approval-rules",
        headers=admin_headers,
        json={
            "name": "Low Priority Rule",
            "category_id": category_id,
            "department_id": department_id,
            "strategy": "SEQUENTIAL",
            "is_active": True,
            "priority": 200,
            "steps": [
                {
                    "step_order": 1,
                    "name": "Low Approver",
                    "approver_role": "SPECIFIC_USER",
                    "approver_user_id": low_priority_approver["id"],
                }
            ],
        },
    )
    assert low_priority_rule_response.status_code == 201

    high_priority_rule_response = client.post(
        "/approval-rules",
        headers=admin_headers,
        json={
            "name": "High Priority Rule",
            "category_id": category_id,
            "department_id": department_id,
            "strategy": "SEQUENTIAL",
            "is_active": True,
            "priority": 10,
            "steps": [
                {
                    "step_order": 1,
                    "name": "High Approver",
                    "approver_role": "SPECIFIC_USER",
                    "approver_user_id": high_priority_approver["id"],
                }
            ],
        },
    )
    assert high_priority_rule_response.status_code == 201

    create_claim_response = client.post(
        "/claims",
        headers=employee_headers,
        json={
            "title": "Priority check claim",
            "description": "Should route to high-priority rule",
            "category_id": category_id,
            "department_id": department_id,
            "original_currency": "INR",
            "original_amount": 5000,
            "expense_date": "2026-03-29",
        },
    )
    assert create_claim_response.status_code == 201
    claim_id = create_claim_response.json()["id"]

    submit_response = client.post(f"/claims/{claim_id}/submit", headers=employee_headers)
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "IN_REVIEW"

    low_inbox = client.get("/approvals/tasks", headers=low_headers)
    assert low_inbox.status_code == 200
    assert len(low_inbox.json()["tasks"]) == 0

    high_inbox = client.get("/approvals/tasks", headers=high_headers)
    assert high_inbox.status_code == 200
    assert len(high_inbox.json()["tasks"]) == 1
    assert high_inbox.json()["tasks"][0]["claim_id"] == claim_id
