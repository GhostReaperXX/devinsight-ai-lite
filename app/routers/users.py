"""REST endpoints for users."""

from fastapi import APIRouter, status

from app.deps import DbSession
from app.schemas import UserCreate, UserRead
from app.services import users as service

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("", response_model=list[UserRead], summary="List users")
def list_users(db: DbSession):
    return service.list_users(db)


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user",
)
def create_user(data: UserCreate, db: DbSession):
    return service.create_user(db, data)
