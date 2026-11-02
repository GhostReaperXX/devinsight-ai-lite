"""REST endpoints for users."""

from fastapi import APIRouter

from app.deps import CurrentUser, DbSession
from app.schemas import UserBrief
from app.services import users as service

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("", response_model=list[UserBrief], summary="List users (names only)")
def list_users(db: DbSession, _user: CurrentUser):
    # Privacy: colleagues need names to assign work, not each other's e-mail addresses.
    return service.list_users(db)
