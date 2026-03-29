from uuid import uuid4


def _signup_payload() -> dict[str, str]:
    unique = uuid4().hex[:8]
    return {
        "company_name": f"Receipt Co {unique}",
        "country_code": "IN",
        "admin_first_name": "Receipt",
        "admin_last_name": "Owner",
        "email": f"receipt.owner.{unique}@example.com",
        "password": "TestPass123!",
    }


def _auth_header_from_signup(client) -> dict[str, str]:
    signup_response = client.post("/auth/signup", json=_signup_payload())
    assert signup_response.status_code == 201
    token = signup_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_receipt_upload_returns_metadata_and_ocr(client):
    headers = _auth_header_from_signup(client)

    content = b"Merchant: Airport Taxi\nAmount: USD 120.50\nDate: 2026-03-28\n"
    upload_response = client.post(
        "/receipts",
        headers=headers,
        files={"file": ("taxi_receipt.txt", content, "text/plain")},
    )
    assert upload_response.status_code == 201

    payload = upload_response.json()
    assert payload["receipt_file_id"] > 0
    assert payload["receipt"]["file_mime_type"] == "text/plain"
    assert payload["ocr_extraction"] is not None
    assert payload["ocr_extraction"]["parsed_fields"]["currency"] == "USD"
    assert payload["ocr_extraction"]["parsed_fields"]["date"] == "2026-03-28"
    assert payload["ocr_extraction"]["parsed_fields"]["amount"] == 120.5

    receipt_id = payload["receipt_file_id"]

    metadata_response = client.get(f"/receipts/{receipt_id}", headers=headers)
    assert metadata_response.status_code == 200
    assert metadata_response.json()["id"] == receipt_id

    ocr_response = client.get(f"/receipts/{receipt_id}/ocr", headers=headers)
    assert ocr_response.status_code == 200
    assert ocr_response.json()["receipt_file_id"] == receipt_id


def test_exchange_preview_and_submit_claim_with_snapshot(client):
    headers = _auth_header_from_signup(client)

    preview_response = client.get(
        "/exchange_rates/preview",
        headers=headers,
        params={
            "base_currency": "INR",
            "foreign_currency": "USD",
            "amount": 100,
        },
    )
    assert preview_response.status_code == 200
    preview_payload = preview_response.json()
    assert preview_payload["converted_amount"] > 100
    assert preview_payload["provider"] == "static-demo-rates"

    categories_response = client.get("/claims/categories", headers=headers)
    assert categories_response.status_code == 200
    category_id = categories_response.json()[0]["id"]

    upload_response = client.post(
        "/receipts",
        headers=headers,
        files={
            "file": (
                "flight_receipt.txt",
                b"Merchant: AirFly\nAmount: USD 250.00\nDate: 2026-03-20\n",
                "text/plain",
            )
        },
    )
    assert upload_response.status_code == 201
    receipt_file_id = upload_response.json()["receipt_file_id"]

    create_response = client.post(
        "/claims",
        headers=headers,
        json={
            "title": "Flight reimbursement",
            "description": "Customer workshop travel",
            "category_id": category_id,
            "receipt_file_id": receipt_file_id,
            "original_currency": "USD",
            "original_amount": 250,
            "expense_date": "2026-03-20",
        },
    )
    assert create_response.status_code == 201

    claim_payload = create_response.json()
    assert claim_payload["status"] == "DRAFT"
    assert claim_payload["receipt_file_id"] == receipt_file_id
    assert claim_payload["converted_amount"] is None

    claim_id = claim_payload["id"]

    submit_response = client.post(f"/claims/{claim_id}/submit", headers=headers)
    assert submit_response.status_code == 200

    submitted = submit_response.json()
    assert submitted["status"] == "IN_REVIEW"
    assert submitted["exchange_rate_snapshot_id"] is not None
    assert submitted["exchange_rate"] is not None
    assert submitted["converted_amount"] is not None
    assert submitted["converted_amount"] > submitted["original_amount"]
