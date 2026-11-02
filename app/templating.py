"""The Jinja2 environment shared by every page, with its display helpers."""

from datetime import datetime

from fastapi import Request
from fastapi.templating import Jinja2Templates

STATUS_LABELS = {
    "open": "Open",
    "in_progress": "In progress",
    "resolved": "Resolved",
    "closed": "Closed",
}
CATEGORY_LABELS = {
    "bug": "Bug",
    "feature": "Feature",
    "documentation": "Documentation",
    "performance": "Performance",
    "security": "Security",
}
PRIORITY_LABELS = {
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "critical": "Critical",
}


def format_datetime(value: datetime | None) -> str:
    """Show a timestamp in one short, unambiguous format."""
    return value.strftime("%d %b %Y, %H:%M") if value else ""


def add_current_user(request: Request) -> dict:
    """Make the logged-in user available to every template, for the navigation bar."""
    return {"current_user": getattr(request.state, "user", None)}


templates = Jinja2Templates(
    directory="app/templates", context_processors=[add_current_user]
)
templates.env.filters["datetime"] = format_datetime
# Jinja2 sorts keys in its tojson filter by default, which would list statuses
# alphabetically. Keep our own order: the life cycle of an issue.
templates.env.policies["json.dumps_kwargs"] = {"sort_keys": False}
templates.env.globals.update(
    STATUS_LABELS=STATUS_LABELS,
    CATEGORY_LABELS=CATEGORY_LABELS,
    PRIORITY_LABELS=PRIORITY_LABELS,
)
