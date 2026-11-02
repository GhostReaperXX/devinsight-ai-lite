"""The Issue class: one cleaned software issue held in memory."""

from datetime import date

CATEGORIES = {"bug", "feature", "documentation", "performance", "security"}
STATUSES = {"open", "in_progress", "resolved", "closed"}

# A tuple keeps its order, so a priority's position doubles as its rank.
PRIORITIES = ("low", "medium", "high", "critical")


class Issue:
    """A software issue whose fields have already been validated."""

    def __init__(
        self,
        issue_id: int,
        title: str,
        description: str,
        category: str,
        priority: str,
        status: str,
        reporter: str,
        created_at: date,
    ) -> None:
        self.issue_id = issue_id
        self.title = title
        self.description = description
        self.category = category
        self.priority = priority
        self.status = status
        self.reporter = reporter
        self.created_at = created_at

    @property
    def priority_rank(self) -> int:
        """Return 0 for low up to 3 for critical, so issues can be compared."""
        return PRIORITIES.index(self.priority)

    def is_active(self) -> bool:
        """Return True while someone still has work to do on this issue."""
        return self.status in ("open", "in_progress")

    def contains_word(self, word: str) -> bool:
        """Return True if the word appears in the title or the description."""
        word = word.lower()
        return word in self.title.lower() or word in self.description.lower()

    def to_dict(self) -> dict:
        """Return plain data that the json module knows how to write."""
        return {
            "issue_id": self.issue_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "reporter": self.reporter,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"Issue(#{self.issue_id}, {self.priority}, {self.status}, {self.title!r})"
