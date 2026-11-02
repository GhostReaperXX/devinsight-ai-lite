"""Read a CSV export from disk and separate good rows from bad rows."""

import csv
from pathlib import Path

from issue_tool.cleaning import clean_row
from issue_tool.errors import InvalidRowError, IssueToolError
from issue_tool.models import Issue

REQUIRED_COLUMNS = {
    "issue_id",
    "title",
    "description",
    "category",
    "priority",
    "status",
    "reporter",
    "created_at",
}


def read_rows(path: Path) -> list[dict]:
    """Return every row of the CSV file as a dictionary keyed by column name."""
    try:
        # utf-8-sig also removes the invisible marker that Excel adds to files.
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
            if missing:
                raise IssueToolError(f"missing columns: {sorted(missing)}")
            return list(reader)
    except FileNotFoundError:
        raise IssueToolError(f"file not found: {path}") from None
    except UnicodeDecodeError:
        raise IssueToolError(f"file is not UTF-8 text: {path}") from None


def load_issues(path: Path) -> tuple[list[Issue], list[InvalidRowError]]:
    """Return (clean issues, rejected rows). Repeated ids are kept only once."""
    issues: list[Issue] = []
    rejected: list[InvalidRowError] = []
    seen_ids: set[int] = set()

    # The header is line 1 of the file, so the first data row is row 2.
    for row_number, row in enumerate(read_rows(path), start=2):
        try:
            issue = clean_row(row, row_number)
        except InvalidRowError as error:
            rejected.append(error)
            continue

        if issue.issue_id in seen_ids:
            rejected.append(InvalidRowError(row_number, f"duplicate id {issue.issue_id}"))
            continue

        seen_ids.add(issue.issue_id)
        issues.append(issue)

    return issues, rejected
