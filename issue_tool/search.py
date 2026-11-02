"""Three ways to find issues, each with a different cost."""

from issue_tool.models import Issue


def linear_search(issues: list[Issue], issue_id: int) -> Issue | None:
    """Check every issue in turn. O(n): works on an unsorted list."""
    for issue in issues:
        if issue.issue_id == issue_id:
            return issue
    return None


def binary_search(issues_sorted_by_id: list[Issue], issue_id: int) -> Issue | None:
    """Halve the range each step. O(log n): the list must be sorted by id."""
    low = 0
    high = len(issues_sorted_by_id) - 1
    while low <= high:
        middle = (low + high) // 2
        candidate = issues_sorted_by_id[middle]
        if candidate.issue_id == issue_id:
            return candidate
        if candidate.issue_id < issue_id:
            low = middle + 1
        else:
            high = middle - 1
    return None


def build_id_index(issues: list[Issue]) -> dict[int, Issue]:
    """Build a dictionary from id to issue. Each later lookup is O(1) on average."""
    return {issue.issue_id: issue for issue in issues}


def build_word_index(issues: list[Issue]) -> dict[str, set[int]]:
    """Map every word to the set of issue ids that contain that word."""
    index: dict[str, set[int]] = {}
    for issue in issues:
        words = f"{issue.title} {issue.description}".lower().split()
        for word in words:
            index.setdefault(word.strip(".,:;!?()'\""), set()).add(issue.issue_id)
    return index


def search_all_words(index: dict[str, set[int]], query: str) -> set[int]:
    """Return the ids of issues that contain every word of the query."""
    results = [index.get(word, set()) for word in query.lower().split()]
    return set.intersection(*results) if results else set()
