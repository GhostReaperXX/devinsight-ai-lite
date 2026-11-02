"""Measure how search and sort times grow as the list gets longer.

Run from the project root: python -m benchmarks.compare_search
"""

import random
import time
from datetime import date

from issue_tool.models import Issue
from issue_tool.search import binary_search, build_id_index, linear_search
from issue_tool.sorting import insertion_sort, merge_sort

SEARCH_SIZES = (1_000, 10_000, 100_000, 1_000_000)
SORT_SIZES = (500, 1_000, 2_000, 4_000)
LOOKUPS = 200


def make_issues(count: int) -> list[Issue]:
    """Create fake issues whose ids are 1, 2, 3 ... count, in sorted order."""
    return [
        Issue(i, f"Issue {i}", "", "bug", "low", "open", "bench", date(2026, 1, 1))
        for i in range(1, count + 1)
    ]


def measure(action, *arguments) -> float:
    """Call the action once and return the time it took, in milliseconds."""
    start = time.perf_counter()
    action(*arguments)
    return (time.perf_counter() - start) * 1000


def look_up_all(find, collection, targets: list[int]) -> None:
    """Run one kind of search for every target."""
    for target in targets:
        find(collection, target)


def compare_searches() -> None:
    print(f"{'n':>10} {'linear ms':>12} {'binary ms':>12} {'dict ms':>12}")
    for size in SEARCH_SIZES:
        issues = make_issues(size)
        index = build_id_index(issues)
        targets = [random.randint(1, size) for _ in range(LOOKUPS)]
        linear_ms = measure(look_up_all, linear_search, issues, targets) / LOOKUPS
        binary_ms = measure(look_up_all, binary_search, issues, targets) / LOOKUPS
        dict_ms = measure(look_up_all, dict.get, index, targets) / LOOKUPS
        print(f"{size:>10,} {linear_ms:>12.5f} {binary_ms:>12.5f} {dict_ms:>12.5f}")


def compare_sorts() -> None:
    print(f"\n{'n':>10} {'insertion ms':>14} {'merge ms':>12} {'built-in ms':>13}")
    for size in SORT_SIZES:
        numbers = random.sample(range(size * 10), size)
        insertion_ms = measure(insertion_sort, numbers)
        merge_ms = measure(merge_sort, numbers)
        builtin_ms = measure(sorted, numbers)
        print(f"{size:>10,} {insertion_ms:>14.2f} {merge_ms:>12.2f} {builtin_ms:>13.3f}")


if __name__ == "__main__":
    random.seed(42)
    compare_searches()
    compare_sorts()
