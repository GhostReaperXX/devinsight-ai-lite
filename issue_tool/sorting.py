"""Sorting algorithms, written out by hand so their cost can be studied."""

from collections.abc import Callable

from issue_tool.models import Issue


def insertion_sort(items: list, key: Callable = lambda item: item) -> list:
    """Return a new sorted list. O(n squared) in the worst case."""
    result = list(items)
    for i in range(1, len(result)):
        current = result[i]
        j = i - 1
        while j >= 0 and key(result[j]) > key(current):
            result[j + 1] = result[j]
            j -= 1
        result[j + 1] = current
    return result


def merge_sort(items: list, key: Callable = lambda item: item) -> list:
    """Return a new sorted list. O(n log n) in every case."""
    if len(items) <= 1:
        return list(items)
    middle = len(items) // 2
    left = merge_sort(items[:middle], key)
    right = merge_sort(items[middle:], key)
    return _merge(left, right, key)


def _merge(left: list, right: list, key: Callable) -> list:
    """Combine two sorted lists into one sorted list."""
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def sort_for_triage(issues: list[Issue]) -> list[Issue]:
    """Most urgent first. Equal priorities are ordered oldest first."""
    return sorted(issues, key=lambda issue: (-issue.priority_rank, issue.created_at))
