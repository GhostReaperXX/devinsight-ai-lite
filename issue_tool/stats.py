"""Summaries of a list of issues."""

from issue_tool.models import Issue


def count_by(issues: list[Issue], field: str) -> dict[str, int]:
    """Count how many issues share each value of a field such as 'status'."""
    counts: dict[str, int] = {}
    for issue in issues:
        value = getattr(issue, field)
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def summarize(issues: list[Issue]) -> dict:
    """Return the headline numbers for a list of issues."""
    active = [issue for issue in issues if issue.is_active()]
    return {
        "total": len(issues),
        "active": len(active),
        "by_status": count_by(issues, "status"),
        "by_category": count_by(issues, "category"),
        "by_priority": count_by(issues, "priority"),
        "reporters": len({issue.reporter for issue in issues}),
    }
