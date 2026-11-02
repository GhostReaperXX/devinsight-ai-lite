"""Turn the untidy text of a raw row into a validated Issue."""

from datetime import date, datetime

from issue_tool.errors import InvalidRowError
from issue_tool.models import CATEGORIES, PRIORITIES, STATUSES, Issue

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y")


def clean_text(value: str | None) -> str:
    """Remove outer spaces and squeeze inner runs of spaces into one."""
    if value is None:
        return ""
    return " ".join(value.split())


def normalize_label(value: str | None) -> str:
    """Reduce 'In Progress', 'in-progress' and 'IN_PROGRESS' to 'in_progress'."""
    text = clean_text(value).lower()
    return text.replace("-", "_").replace(" ", "_")


def parse_issue_id(value: str | None, row_number: int) -> int:
    """Return the id as a positive whole number, or reject the row."""
    text = clean_text(value)
    if not text.isdigit() or int(text) == 0:
        raise InvalidRowError(row_number, f"issue_id {text!r} is not a positive number")
    return int(text)


def parse_date(value: str | None, row_number: int) -> date:
    """Accept the two date formats found in the export, or reject the row."""
    text = clean_text(value)
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    raise InvalidRowError(row_number, f"created_at {text!r} is not a known date format")


def require_member(label: str, allowed, field: str, row_number: int) -> str:
    """Return the label if it is allowed, otherwise reject the row."""
    if label not in allowed:
        raise InvalidRowError(row_number, f"{field} {label!r} is not allowed")
    return label


def clean_row(row: dict, row_number: int) -> Issue:
    """Build one Issue from one raw row, raising InvalidRowError on bad data."""
    title = clean_text(row.get("title"))
    if not title:
        raise InvalidRowError(row_number, "title is empty")

    return Issue(
        issue_id=parse_issue_id(row.get("issue_id"), row_number),
        title=title,
        description=clean_text(row.get("description")),
        category=require_member(
            normalize_label(row.get("category")), CATEGORIES, "category", row_number
        ),
        priority=require_member(
            normalize_label(row.get("priority")), PRIORITIES, "priority", row_number
        ),
        status=require_member(
            normalize_label(row.get("status")), STATUSES, "status", row_number
        ),
        reporter=clean_text(row.get("reporter")) or "unknown",
        created_at=parse_date(row.get("created_at"), row_number),
    )
