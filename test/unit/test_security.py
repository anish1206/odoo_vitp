from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


def test_password_hash_and_verify_round_trip():
    password = "TestPass123!"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)


def test_password_hash_supports_long_passwords():
    long_password = "A" * 150
    hashed = get_password_hash(long_password)

    assert verify_password(long_password, hashed)
    assert not verify_password("A" * 149 + "B", hashed)


def test_access_token_payload_round_trip():
    token = create_access_token(
        user_id=7,
        company_id=42,
        role="ADMIN",
        is_approver=True,
    )
    payload = decode_token(token)

    assert payload is not None
    assert payload["sub"] == "7"
    assert payload["company_id"] == 42
    assert payload["role"] == "ADMIN"
    assert payload["is_approver"] is True
    assert payload["token_type"] == "access"


def test_refresh_token_payload_round_trip():
    token = create_refresh_token(user_id=9)
    payload = decode_token(token)

    assert payload is not None
    assert payload["sub"] == "9"
    assert payload["token_type"] == "refresh"
