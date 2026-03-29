from uuid import uuid4

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models import User, UserRole


def _signup_payload() -> dict[str, str]:
    unique = uuid4().hex[:8]
    return {
        "company_name": f"Claims Co {unique}",
        "country_code": "IN",
        "admin_first_name": "Claim",
        "admin_last_name": "Owner",
        "email": f"claim.owner.{unique}@example.com",
        "password": "TestPass123!",
    }


def _auth_header_from_signup(client) -> dict[str, str]:
    signup_response = client.post("/auth/signup", json=_signup_payload())
    assert signup_response.status_code == 201
    access_token = signup_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def _login_headers(client, email: str, password: str = "TestPass123!") -> dict[str, str]:
    login_response = client.post("/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_claim_draft_update_submit_and_filter_flow(client):
    headers = _auth_header_from_signup(client)

    category_response = client.get("/claims/categories", headers=headers)
    assert category_response.status_code == 200
    categories = category_response.json()
    assert len(categories) > 0
    category_id = categories[0]["id"]

    create_response = client.post(
        "/claims",
        headers=headers,
        json={
            "title": "Taxi to client office",
            "description": "Airport to downtown",
            "category_id": category_id,
            "original_currency": "INR",
            "original_amount": 845.50,
            "expense_date": "2026-03-28",
        },
    )
    assert create_response.status_code == 201
    claim = create_response.json()
    assert claim["status"] == "DRAFT"
    claim_id = claim["id"]

    update_response = client.patch(
        f"/claims/{claim_id}",
        headers=headers,
        json={
            "title": "Taxi to client office (updated)",
            "original_amount": 900,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Taxi to client office (updated)"

    submit_response = client.post(f"/claims/{claim_id}/submit", headers=headers)
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "IN_REVIEW"

    invalid_update_response = client.patch(
        f"/claims/{claim_id}",
        headers=headers,
        json={"title": "Should fail"},
    )
    assert invalid_update_response.status_code == 400
    assert invalid_update_response.json()["detail"] == "Only draft claims can be edited"

    review_filter_response = client.get("/claims/my?status=IN_REVIEW", headers=headers)
    assert review_filter_response.status_code == 200
    review_claims = review_filter_response.json()["claims"]
    assert len(review_claims) == 1
    assert review_claims[0]["id"] == claim_id


def test_claims_require_auth(client):
    response = client.get("/claims/my")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authorization token"


def test_admin_can_view_company_claim_records(client):
    unique = uuid4().hex[:8]
    signup_response = client.post("/auth/signup", json=_signup_payload())
    assert signup_response.status_code == 201

    admin_headers = {
        "Authorization": f"Bearer {signup_response.json()['access_token']}",
    }
    company_id = signup_response.json()["company"]["id"]

    with SessionLocal() as db:
        employee = User(
            company_id=company_id,
            email=f"viewer.employee.{unique}@example.com",
            hashed_password=get_password_hash("TestPass123!"),
            first_name="Viewer",
            last_name="Employee",
            role=UserRole.EMPLOYEE,
            is_approver=False,
            is_active=True,
        )
        db.add(employee)
        db.commit()

    employee_headers = _login_headers(client, f"viewer.employee.{unique}@example.com")

    category_id = client.get("/claims/categories", headers=employee_headers).json()[0]["id"]

    claim_id = client.post(
        "/claims",
        headers=employee_headers,
        json={
            "title": "Conference registration",
            "description": "Annual conference",
            "category_id": category_id,
            "original_currency": "USD",
            "original_amount": 300,
            "expense_date": "2026-03-26",
        },
    ).json()["id"]

    submit_response = client.post(f"/claims/{claim_id}/submit", headers=employee_headers)
    assert submit_response.status_code == 200

    company_list_response = client.get("/claims/company", headers=admin_headers)
    assert company_list_response.status_code == 200
    claims = company_list_response.json()["claims"]
    assert any(claim["id"] == claim_id for claim in claims)

    detail_response = client.get(f"/claims/company/{claim_id}", headers=admin_headers)
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["employee_name"] == "Viewer Employee"
    assert "approval_timeline" in detail_payload
    assert isinstance(detail_payload["approval_tasks"], list)
