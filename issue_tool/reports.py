"""Report classes: the same interface, a different output for each format."""

import json

from issue_tool.models import Issue
from issue_tool.stats import summarize


class Report:
    """Parent class. Every report knows how to turn issues into text."""

    file_suffix = ".txt"

    def render(self, issues: list[Issue]) -> str:
        raise NotImplementedError("each report type must define render()")


class TextReport(Report):
    """A plain table that people can read in a terminal."""

    def render(self, issues: list[Issue]) -> str:
        lines = [f"{'ID':>5}  {'PRIORITY':<9} {'STATUS':<12} TITLE"]
        for issue in issues:
            lines.append(
                f"{issue.issue_id:>5}  {issue.priority:<9} {issue.status:<12} {issue.title}"
            )
        lines.append(f"\n{len(issues)} issue(s)")
        return "\n".join(lines)


class JsonReport(Report):
    """Structured data that another program can read."""

    file_suffix = ".json"

    def render(self, issues: list[Issue]) -> str:
        document = {
            "summary": summarize(issues),
            "issues": [issue.to_dict() for issue in issues],
        }
        return json.dumps(document, indent=2)


REPORT_TYPES = {"text": TextReport, "json": JsonReport}
