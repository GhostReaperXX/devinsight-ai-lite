"""REST endpoints for issues, comments and statistics."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.deps import AdminUser, CurrentUser, DbSession, Predictor
from app.schemas import (
    CommentCreate,
    CommentRead,
    DuplicateMark,
    IssueCreate,
    IssueFilters,
    IssuePage,
    IssueRead,
    IssueUpdate,
    Stats,
    StatusChange,
)
from app.services import issues as service

router = APIRouter(prefix="/api", tags=["Issues"])


@router.get("/issues", response_model=IssuePage, summary="List issues with filters")
def list_issues(
    filters: Annotated[IssueFilters, Query()], db: DbSession, _user: CurrentUser
):
    items, total = service.list_issues(db, filters)
    return IssuePage(
        items=[IssueRead.model_validate(item) for item in items],
        total=total,
        limit=filters.limit,
        offset=filters.offset,
    )


@router.post(
    "/issues",
    response_model=IssueRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an issue",
)
def create_issue(data: IssueCreate, db: DbSession, user: CurrentUser, predictor: Predictor):
    return service.create_issue(db, data, reporter=user, predictor=predictor)


@router.get("/issues/{issue_id}", response_model=IssueRead, summary="Read one issue")
def get_issue(issue_id: int, db: DbSession, _user: CurrentUser):
    return service.get_issue(db, issue_id)


@router.patch(
    "/issues/{issue_id}", response_model=IssueRead, summary="Edit some fields of an issue"
)
def update_issue(issue_id: int, data: IssueUpdate, db: DbSession, user: CurrentUser):
    return service.update_issue(db, issue_id, data, actor=user)


@router.patch(
    "/issues/{issue_id}/status",
    response_model=IssueRead,
    summary="Change the status of an issue",
)
def change_status(issue_id: int, data: StatusChange, db: DbSession, user: CurrentUser):
    return service.change_status(db, issue_id, data, actor=user)


@router.post(
    "/issues/{issue_id}/duplicate",
    response_model=IssueRead,
    summary="Close an issue as a duplicate of another",
)
def mark_duplicate(issue_id: int, data: DuplicateMark, db: DbSession, user: CurrentUser):
    return service.mark_duplicate(db, issue_id, data, actor=user)


@router.delete(
    "/issues/{issue_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an issue (administrators)",
)
def delete_issue(issue_id: int, db: DbSession, _admin: AdminUser) -> None:
    service.delete_issue(db, issue_id)


@router.get(
    "/issues/{issue_id}/comments", response_model=list[CommentRead], summary="List comments"
)
def list_comments(issue_id: int, db: DbSession, _user: CurrentUser):
    return service.list_comments(db, issue_id)


@router.post(
    "/issues/{issue_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment",
)
def add_comment(issue_id: int, data: CommentCreate, db: DbSession, user: CurrentUser):
    return service.add_comment(db, issue_id, data, author=user)


@router.get("/stats", response_model=Stats, summary="Dashboard numbers")
def get_stats(db: DbSession, _user: CurrentUser, project_id: int | None = None):
    return service.get_stats(db, project_id)
