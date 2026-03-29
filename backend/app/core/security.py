import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def _bcrypt_safe_password(password: str) -> bytes:
    """Pre-hash password to avoid bcrypt 72-byte input limit."""
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    hashed_bytes = hashed_password.encode("utf-8")

    if bcrypt.checkpw(_bcrypt_safe_password(plain_password), hashed_bytes):
        return True

    # Backward compatibility for hashes created before the pre-hash strategy.
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_bytes)
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(_bcrypt_safe_password(password), salt)
    return hashed.decode("utf-8")


def _create_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(user_id: int, company_id: int, role: str, is_approver: bool) -> str:
    payload = {
        "sub": str(user_id),
        "company_id": company_id,
        "role": role,
        "is_approver": is_approver,
        "token_type": "access",
    }
    return _create_token(payload, timedelta(minutes=settings.access_token_expire_minutes))


def create_refresh_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "token_type": "refresh",
    }
    return _create_token(payload, timedelta(minutes=settings.refresh_token_expire_minutes))


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
