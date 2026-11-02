"""Issue operations: the core business rules of the tracker."""

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.errors import NotFoundError, PermissionDeniedError, RuleViolationError
from app.ml.predictor import CategoryPredictor
from app.models import Comment, Issue, Project, User
from app.schemas import (
    CommentCreate,
    DuplicateMark,
    IssueCreate,
    IssueFilters,
    IssueUpdate,
    StatusChange,
)

# Which status may follow which: the life cycle agreed in the requirements.
ALLOWED_TRANSITIONS = {
    "open": {"in_progress", "resolved", "closed"},
    "in_progress": {"open", "resolved", "closed"},
    "resolved": {"in_progress", "closed"},
    "closed": {"open"},
}

PRIORITY_ORDER = case(
    {"critical": 0, "high": 1, "medium": 2, "low": 3},
    value=Issue.priority,
)

SORT_ORDERS = {
    "newest": (Issue.created_at.desc(), Issue.id.desc()),
    "oldest": (Issue.created_at.asc(), Issue.id.asc()),
    "priority": (PRIORITY_ORDER, Issue.created_at.desc(), Issue.id.desc()),
}


def _filter_conditions(filters: IssueFilters) -> list:
    """Translate the requested filters into SQL conditions."""
    conditions = []
    if filters.project_id is not None:
        conditions.append(Issue.project_id == filters.project_id)
    if filters.status is not None:
        conditions.append(Issue.status == filters.status)
    if filters.category is not None:
        conditions.append(Issue.category == filters.category)
    if filters.priority is not None:
        conditions.append(Issue.priority == filters.priority)
    if filters.assignee_id is not None:
        conditions.append(Issue.assignee_id == filters.assignee_id)
    if filters.q:
        conditions.append(
            or_(
                Issue.title.icontains(filters.q, autoescape=True),
                Issue.description.icontains(filters.q, autoescape=True),
            )
        )
    return conditions


def list_issues(db: Session, filters: IssueFilters) -> tuple[list[Issue], int]:
    """Return one page of matching issues, and how many match in total."""
    conditions = _filter_conditions(filters)
    total = db.scalar(select(func.count()).select_from(Issue).where(*conditions))
    statement = (
        select(Issue)
        .options(
            selectinload(Issue.project),
            selectinload(Issue.reporter),
            selectinload(Issue.assignee),
        )
        .where(*conditions)
        .order_by(*SORT_ORDERS[filters.sort])
        .limit(filters.limit)
        .offset(filters.offset)
    )
    return list(db.scalars(statement)), total


def get_issue(db: Session, issue_id: int) -> Issue:
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise NotFoundError(f"issue {issue_id} does not exist")
    return issue


def can_change(user: User, issue: Issue) -> bool:
    """The access rule: the reporter, the assignee or an administrator may change it."""
    return user.role == "admin" or user.id in (issue.reporter_id, issue.assignee_id)


def _require_can_change(user: User, issue: Issue) -> None:
    if not can_change(user, issue):
        raise PermissionDeniedError(
            "Only the reporter, the assignee or an administrator can change this issue."
        )


def _require_exists(db: Session, model, row_id: int | None, label: str) -> None:
    """Reject a reference to a project or user that is not there."""
    if row_id is not None and db.get(model, row_id) is None:
        raise RuleViolationError(f"{label} {row_id} does not exist")


def create_issue(
    db: Session, data: IssueCreate, reporter: User, predictor: CategoryPredictor | None
) -> Issue:
    _require_exists(db, Project, data.project_id, "project")
    _require_exists(db, User, data.assignee_id, "assignee")
    issue = Issue(**data.model_dump(), reporter_id=reporter.id)
    if predictor is not None:
        prediction = predictor.predict(data.title, data.description)
        issue.predicted_category = prediction.category
        issue.prediction_confidence = prediction.confidence
    db.add(issue)
    db.commit()
    return issue


def update_issue(db: Session, issue_id: int, data: IssueUpdate, actor: User) -> Issue:
    issue = get_issue(db, issue_id)
    _require_can_change(actor, issue)
    # exclude_unset: only the fields the client actually sent are changed.
    changes = data.model_dump(exclude_unset=True)
    _require_exists(db, User, changes.get("assignee_id"), "assignee")
    for field, value in changes.items():
        setattr(issue, field, value)
    db.commit()
    return issue


def allowed_next_statuses(issue: Issue) -> set[str]:
    """Return the statuses this issue may move to, for the page to offer as buttons."""
    return ALLOWED_TRANSITIONS[issue.status]


def change_status(db: Session, issue_id: int, data: StatusChange, actor: User) -> Issue:
    """Move an issue to a new status, optionally with a comment, as one transaction."""
    issue = get_issue(db, issue_id)
    _require_can_change(actor, issue)
    if data.status == issue.status:
        return issue
    if data.status not in ALLOWED_TRANSITIONS[issue.status]:
        raise RuleViolationError(
            f"An issue cannot move from {issue.status} to {data.status}."
        )

    issue.status = data.status
    # A reopened issue is no longer closed as a duplicate of anything.
    if data.status == "open":
        issue.duplicate_of_id = None
    if data.comment:
        db.add(Comment(issue_id=issue.id, author_id=actor.id, body=data.comment))
    # Both changes are saved together, or neither is.
    db.commit()
    return issue


def mark_duplicate(db: Session, issue_id: int, data: DuplicateMark, actor: User) -> Issue:
    """Close an issue as a duplicate of another, recording why, as one transaction."""
    issue = get_issue(db, issue_id)
    _require_can_change(actor, issue)
    original = get_issue(db, data.duplicate_of_id)
    if original.id == issue.id:
        raise RuleViolationError("An issue cannot be a duplicate of itself.")
    if original.project_id != issue.project_id:
        raise RuleViolationError("Both issues must belong to the same project.")
    if original.duplicate_of_id == issue.id:
        raise RuleViolationError(
            f"Issue {original.id} is already a duplicate of this issue."
        )

    issue.duplicate_of_id = original.id
    issue.status = "closed"
    db.add(
        Comment(
            issue_id=issue.id,
            author_id=actor.id,
            body=f"Closed as a duplicate of #{original.id}.",
        )
    )
    db.commit()
    return issue


def delete_issue(db: Session, issue_id: int) -> None:
    """Administrators only. The router enforces that with its AdminUser dependency."""
    db.delete(get_issue(db, issue_id))
    db.commit()


def list_comments(db: Session, issue_id: int) -> list[Comment]:
    return list(get_issue(db, issue_id).comments)


def add_comment(db: Session, issue_id: int, data: CommentCreate, author: User) -> Comment:
    get_issue(db, issue_id)
    comment = Comment(issue_id=issue_id, author_id=author.id, body=data.body)
    db.add(comment)
    db.commit()
    return comment


def _count_by(db: Session, column, project_id: int | None) -> dict[str, int]:
    statement = select(column, func.count()).group_by(column)
    if project_id is not None:
        statement = statement.where(Issue.project_id == project_id)
    return {value: count for value, count in db.execute(statement)}


def get_stats(db: Session, project_id: int | None = None) -> dict:
    """Return the numbers shown on the dashboard."""
    by_status = _count_by(db, Issue.status, project_id)
    # A LEFT JOIN keeps projects that have no issues yet, with a count of zero.
    per_project = db.execute(
        select(Project.key, Project.name, func.count(Issue.id))
        .join(Issue, Issue.project_id == Project.id, isouter=True)
        .group_by(Project.id, Project.key, Project.name)
        .order_by(Project.key)
    )
    return {
        "total": sum(by_status.values()),
        "active": by_status.get("open", 0) + by_status.get("in_progress", 0),
        "by_status": by_status,
        "by_category": _count_by(db, Issue.category, project_id),
        "by_priority": _count_by(db, Issue.priority, project_id),
        "per_project": [
            {"key": key, "name": name, "issues": count} for key, name, count in per_project
        ],
    }
