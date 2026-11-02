"""User operations: registration and login."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import AuthenticationError, ConflictError, NotFoundError
from app.models import User
from app.schemas import UserRegister
from app.security import hash_password, spend_password_check_time, verify_password


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.full_name)))


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError(f"user {user_id} does not exist")
    return user


def register_user(db: Session, data: UserRegister) -> User:
    """Create a member account. Becoming an administrator is never self-service."""
    user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password),
        role="member",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("This e-mail is already registered.") from None
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    """Return the user, or raise one identical error for every kind of failure."""
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None:
        spend_password_check_time(password)
        raise AuthenticationError("Wrong e-mail or password.")
    if not verify_password(password, user.password_hash):
        raise AuthenticationError("Wrong e-mail or password.")
    return user
