from uuid import uuid4


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
