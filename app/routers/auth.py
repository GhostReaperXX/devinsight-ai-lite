"""REST endpoints for accounts and logins."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.deps import CurrentUser, DbSession
from app.schemas import Token, UserRead, UserRegister
from app.security import create_access_token
from app.services import users as service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account",
)
def register(data: UserRegister, db: DbSession):
    return service.register_user(db, data)


@router.post(
    "/login", response_model=Token, summary="Exchange e-mail and password for a token"
)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    user = service.authenticate(db, form.username, form.password)
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead, summary="Who am I?")
def read_me(user: CurrentUser):
    return user
