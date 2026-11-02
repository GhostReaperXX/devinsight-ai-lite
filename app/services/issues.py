"""Issue operations: the core business rules of the tracker."""

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.errors import NotFoundError, RuleViolationError
from app.models import Comment, Issue, Project, User
from app.schemas import CommentCreate, IssueCreate, IssueFilters, IssueUpdate, StatusChange

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


def _require_exists(db: Session, model, row_id: int | None, label: str) -> None:
    """Reject a reference to a project or user that is not there."""
    if row_id is not None and db.get(model, row_id) is None:
        raise RuleViolationError(f"{label} {row_id} does not exist")


def create_issue(db: Session, data: IssueCreate) -> Issue:
    _require_exists(db, Project, data.project_id, "project")
    _require_exists(db, User, data.reporter_id, "reporter")
    _require_exists(db, User, data.assignee_id, "assignee")
    issue = Issue(**data.model_dump())
    db.add(issue)
    db.commit()
    return issue


def update_issue(db: Session, issue_id: int, data: IssueUpdate) -> Issue:
    issue = get_issue(db, issue_id)
    # exclude_unset: only the fields the client actually sent are changed.
    changes = data.model_dump(exclude_unset=True)
    _require_exists(db, User, changes.get("assignee_id"), "assignee")
    for field, value in changes.items():
        setattr(issue, field, value)
    db.commit()
    return issue


def change_status(db: Session, issue_id: int, data: StatusChange) -> Issue:
    """Move an issue to a new status, optionally with a comment, as one transaction."""
    issue = get_issue(db, issue_id)
    if data.status == issue.status:
        return issue
    if data.status not in ALLOWED_TRANSITIONS[issue.status]:
        raise RuleViolationError(
            f"an issue cannot move from {issue.status} to {data.status}"
        )

    issue.status = data.status
    if data.comment:
        if data.author_id is None:
            raise RuleViolationError("a comment needs an author_id")
        _require_exists(db, User, data.author_id, "author")
        db.add(Comment(issue_id=issue.id, author_id=data.author_id, body=data.comment))
    # Both changes are saved together, or neither is.
    db.commit()
    return issue


def allowed_next_statuses(issue: Issue) -> set[str]:
    """Return the statuses this issue may move to, for a page to offer as buttons."""
    return ALLOWED_TRANSITIONS[issue.status]


def delete_issue(db: Session, issue_id: int) -> None:
    db.delete(get_issue(db, issue_id))
    db.commit()


def list_comments(db: Session, issue_id: int) -> list[Comment]:
    return list(get_issue(db, issue_id).comments)


def add_comment(db: Session, issue_id: int, data: CommentCreate) -> Comment:
    get_issue(db, issue_id)
    _require_exists(db, User, data.author_id, "author")
    comment = Comment(issue_id=issue_id, **data.model_dump())
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
