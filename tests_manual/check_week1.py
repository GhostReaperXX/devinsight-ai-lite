"""A quick self check for Week 1.

Run from the project root: python tests_manual/check_week1.py

Formal automated tests with pytest arrive in Week 7. Until then this script gives
you confidence that the main behaviour has not been broken by your latest change.
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from issue_tool.cleaning import clean_text, normalize_label, parse_date
from issue_tool.errors import InvalidRowError
from issue_tool.loader import load_issues
from issue_tool.models import Issue
from issue_tool.search import (
    binary_search,
    build_word_index,
    linear_search,
    search_all_words,
)
from issue_tool.sorting import insertion_sort, merge_sort, sort_for_triage


def make_issue(
    issue_id: int, priority: str = "low", when: date = date(2026, 1, 1)
) -> Issue:
    return Issue(issue_id, f"Issue {issue_id}", "text", "bug", priority, "open", "me", when)


assert clean_text("  too   many  spaces ") == "too many spaces"
assert normalize_label(" In-Progress ") == "in_progress"
assert parse_date("14/03/2026", 2) == date(2026, 3, 14)
try:
    parse_date("yesterday", 2)
    raise AssertionError("an invalid date should be rejected")
except InvalidRowError:
    pass

issues = [make_issue(i) for i in range(1, 101)]
assert linear_search(issues, 57).issue_id == 57
assert binary_search(issues, 57).issue_id == 57
assert binary_search(issues, 999) is None

numbers = [5, 2, 9, 1, 5, 6]
assert insertion_sort(numbers) == sorted(numbers)
assert merge_sort(numbers) == sorted(numbers)
assert numbers == [5, 2, 9, 1, 5, 6], "sorting must not change the original list"

triage = sort_for_triage(
    [make_issue(1, "low"), make_issue(2, "critical"), make_issue(3, "high")]
)
assert [issue.issue_id for issue in triage] == [2, 3, 1]

index = build_word_index([make_issue(1)])
assert search_all_words(index, "ISSUE text") == {1}
assert search_all_words(index, "missing") == set()

accepted, rejected = load_issues(Path("data/issues_raw.csv"))
assert accepted and rejected, "the sample file contains both good and bad rows"
assert len({issue.issue_id for issue in accepted}) == len(accepted), "ids must be unique"

print(f"All checks passed. {len(accepted)} rows accepted, {len(rejected)} rejected.")
