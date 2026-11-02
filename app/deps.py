"""Shared FastAPI dependencies: the database session and the logged-in user."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml.predictor import CategoryPredictor
from app.models import User
from app.security import read_access_token

SESSION_COOKIE = "devinsight_session"

DbSession = Annotated[Session, Depends(get_db)]

# Adds the Authorize button to the interactive documentation.
bearer_token = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


class LoginRequired(Exception):
    """A browser page needs a login. The handler answers with a redirect to /login."""

    def __init__(self, next_path: str) -> None:
        self.next_path = next_path


def get_optional_user(
    request: Request, db: DbSession, token: Annotated[str | None, Depends(bearer_token)]
) -> User | None:
    """Read the token from the Authorization header, or else from the session cookie."""
    raw_token = token or request.cookies.get(SESSION_COOKIE)
    user_id = read_access_token(raw_token) if raw_token else None
    user = db.get(User, user_id) if user_id else None
    # Remember the user so that the page templates can show who is logged in.
    request.state.user = user
    return user


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def require_user(user: OptionalUser) -> User:
    """For the API: no valid login means 401."""
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(require_user)]


def require_admin(user: CurrentUser) -> User:
    """For the API: logged in but not an administrator means 403."""
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only an administrator can do this.")
    return user


AdminUser = Annotated[User, Depends(require_admin)]


def require_page_user(request: Request, user: OptionalUser) -> User:
    """For browser pages: no valid login means a redirect to the login page."""
    if user is None:
        query = f"?{request.url.query}" if request.url.query else ""
        raise LoginRequired(f"{request.url.path}{query}")
    return user


PageUser = Annotated[User, Depends(require_page_user)]


def get_predictor(request: Request) -> CategoryPredictor | None:
    """Return the model loaded at startup, or None if the file was not available."""
    return request.app.state.predictor


Predictor = Annotated[CategoryPredictor | None, Depends(get_predictor)]
