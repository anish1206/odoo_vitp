from uuid import uuid4


def _signup_payload() -> dict[str, str]:
    unique = uuid4().hex[:8]
    return {
        "company_name": f"Admin Co {unique}",
        "country_code": "IN",
        "admin_first_name": "Admin",
        "admin_last_name": "Owner",
        "email": f"admin.{unique}@example.com",
        "password": "TestPass123!",
    }


def _login_headers(client, email: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def test_admin_can_manage_departments_categories_and_users(client):
    signup_response = client.post("/auth/signup", json=_signup_payload())
    assert signup_response.status_code == 201

    signup_data = signup_response.json()
    admin_email = signup_data["user"]["email"]
    admin_headers = {"Authorization": f"Bearer {signup_data['access_token']}"}

    create_department_response = client.post(
        "/departments",
        headers=admin_headers,
        json={"name": "People Ops", "code": "hr"},
    )
    assert create_department_response.status_code == 201
    department = create_department_response.json()
    assert department["name"] == "People Ops"
    assert department["code"] == "HR"

    department_id = department["id"]

    update_department_response = client.patch(
        f"/departments/{department_id}",
        headers=admin_headers,
        json={"name": "HR Operations", "code": "hro"},
    )
    assert update_department_response.status_code == 200
    assert update_department_response.json()["name"] == "HR Operations"
    assert update_department_response.json()["code"] == "HRO"

    create_category_response = client.post(
        "/categories",
        headers=admin_headers,
        json={"name": "Client Meals", "code": "meal", "description": "Client dinner reimbursements"},
    )
    assert create_category_response.status_code == 201
    category = create_category_response.json()
    assert category["name"] == "Client Meals"
    assert category["code"] == "MEAL"
    assert category["is_active"] is True

    category_id = category["id"]

    update_category_response = client.patch(
        f"/categories/{category_id}",
        headers=admin_headers,
        json={"description": "Updated description", "is_active": False},
    )
    assert update_category_response.status_code == 200
    updated_category = update_category_response.json()
    assert updated_category["description"] == "Updated description"
    assert updated_category["is_active"] is False

    create_user_response = client.post(
        "/users",
        headers=admin_headers,
        json={
            "email": f"employee.{uuid4().hex[:8]}@example.com",
            "password": "EmployeePass1!",
            "first_name": "John",
            "last_name": "Analyst",
            "role": "EMPLOYEE",
            "is_approver": False,
            "department_id": department_id,
            "manager_id": None,
        },
    )
    assert create_user_response.status_code == 201
    created_user = create_user_response.json()
    assert created_user["department_id"] == department_id
    assert created_user["is_active"] is True

    users_response = client.get("/users", headers=admin_headers)
    assert users_response.status_code == 200
    users = users_response.json()
    assert len(users) >= 2

    admin_user = next(user for user in users if user["email"] == admin_email)

    update_user_response = client.patch(
        f"/users/{created_user['id']}",
        headers=admin_headers,
        json={
            "is_approver": True,
            "manager_id": admin_user["id"],
            "password": "NewEmployeePass1!",
        },
    )
    assert update_user_response.status_code == 200
    updated_user = update_user_response.json()
    assert updated_user["is_approver"] is True
    assert updated_user["manager_id"] == admin_user["id"]

    employee_headers = _login_headers(client, created_user["email"], "NewEmployeePass1!")
    my_profile = client.get("/users/me", headers=employee_headers)
    assert my_profile.status_code == 200
    assert my_profile.json()["user"]["email"] == created_user["email"]


def test_non_admin_cannot_use_admin_master_data_endpoints(client):
    signup_response = client.post("/auth/signup", json=_signup_payload())
    assert signup_response.status_code == 201

    signup_data = signup_response.json()
    admin_headers = {"Authorization": f"Bearer {signup_data['access_token']}"}

    create_user_response = client.post(
        "/users",
        headers=admin_headers,
        json={
            "email": f"staff.{uuid4().hex[:8]}@example.com",
            "password": "EmployeePass1!",
            "first_name": "Staff",
            "last_name": "Member",
            "role": "EMPLOYEE",
            "is_approver": False,
        },
    )
    assert create_user_response.status_code == 201
    employee_email = create_user_response.json()["email"]

    employee_headers = _login_headers(client, employee_email, "EmployeePass1!")

    users_response = client.get("/users", headers=employee_headers)
    assert users_response.status_code == 403
    assert users_response.json()["detail"] == "Admin access required"

    departments_response = client.get("/departments", headers=employee_headers)
    assert departments_response.status_code == 403
    assert departments_response.json()["detail"] == "Admin access required"

    categories_response = client.get("/categories", headers=employee_headers)
    assert categories_response.status_code == 403
    assert categories_response.json()["detail"] == "Admin access required"
