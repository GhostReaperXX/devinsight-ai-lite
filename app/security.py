"""Password hashing and login tokens. Nothing else in the project touches these details."""

from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.config import get_settings

ALGORITHM = "HS256"

_hasher = PasswordHasher()
# Checked when an e-mail is unknown, so a wrong e-mail and a wrong password take equal time.
_UNUSED_HASH = _hasher.hash("timing-protection-only")


def hash_password(password: str) -> str:
    """Return a salted Argon2 hash. The same password gives a different hash every time."""
    return _hasher.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        return _hasher.verify(stored_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def spend_password_check_time(password: str) -> None:
    verify_password(password, _UNUSED_HASH)


def create_access_token(user_id: int) -> str:
    """Return a signed token that says who the user is and when that stops being valid."""
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_minutes)
    claims = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(claims, settings.secret_key, algorithm=ALGORITHM)


def read_access_token(token: str) -> int | None:
    """Return the user id if the signature and expiry are valid, otherwise None."""
    try:
        claims = jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])
        return int(claims["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None
