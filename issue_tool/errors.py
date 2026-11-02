"""Errors that this tool raises on purpose."""


class IssueToolError(Exception):
    """Parent of every error the tool raises deliberately."""


class InvalidRowError(IssueToolError):
    """A row from the input file cannot be turned into a valid Issue."""

    def __init__(self, row_number: int, reason: str) -> None:
        super().__init__(f"row {row_number}: {reason}")
        self.row_number = row_number
        self.reason = reason
