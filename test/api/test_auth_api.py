from uuid import uuid4


def _signup_payload() -> dict[str, str]:
    unique = uuid4().hex[:8]
    return {
        "company_name": f"Acme Corp {unique}",
        "country_code": "IN",
        "admin_first_name": "Alice",
        "admin_last_name": "Smith",
        "email": f"alice.{unique}@acme.com",
        "password": "TestPass123!",
    }


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_signup_login_refresh_and_me_flow(client):
    signup_payload = _signup_payload()

    signup_response = client.post("/auth/signup", json=signup_payload)
    assert signup_response.status_code == 201

    signup_data = signup_response.json()
    assert "access_token" in signup_data
    assert "refresh_token" in signup_data
    assert signup_data["user"]["email"] == signup_payload["email"]
    assert signup_data["company"]["name"] == signup_payload["company_name"]

    login_response = client.post(
        "/auth/login",
        json={
            "email": signup_payload["email"],
            "password": signup_payload["password"],
        },
    )
    assert login_response.status_code == 200

    login_data = login_response.json()
    me_response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {login_data['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["user"]["email"] == signup_payload["email"]

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": login_data["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.json()


def test_signup_duplicate_email_returns_400(client):
    signup_payload = _signup_payload()

    first_response = client.post("/auth/signup", json=signup_payload)
    assert first_response.status_code == 201

    second_payload = _signup_payload()
    second_payload["email"] = signup_payload["email"]
    second_response = client.post("/auth/signup", json=second_payload)

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "A user with this email already exists"


def test_signup_invalid_country_returns_400(client):
    signup_payload = _signup_payload()
    signup_payload["country_code"] = "ZZ"

    response = client.post("/auth/signup", json=signup_payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported country code for base currency"


def test_users_me_requires_auth(client):
    response = client.get("/users/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authorization token"
