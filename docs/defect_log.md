# Defect log

Defects found during final integration in Chapter 8. Each one has a regression test in
`tests/test_regressions.py`, written first, seen to fail, and then made to pass by the fix.

| ID | Severity | Symptom | Root cause | Fix | Test |
|---|---|---|---|---|---|
| D1 | Medium | The issue list slows down as the number of different people grows | The list loads each row's project, reporter and assignee with a separate query (the N+1 problem) | Load them with `selectinload`, so the query count stays constant | `test_defect_1_...` |
| D2 | High | `PATCH /api/issues/1` with `{"title": null}` returns 500 | `IssueUpdate` allows `None`, and `None` reached a NOT NULL column | A validator refuses null everywhere except `assignee_id`, returning 422 | `test_defect_2_...` |
| D3 | Medium | A reopened issue still says "Closed as a duplicate" | `change_status` did not clear `duplicate_of_id` | Clear the link when the status returns to open | `test_defect_3_...` |
| D4 | Low | Filters in a saved link are lost after logging in | The redirect kept the path but not the query string | Keep and encode the query string in `next` | `test_defect_4_...` |
| D5 | Low | A new comment shows one time, and a different time after refreshing | JavaScript showed local time, the server showed UTC, neither was labelled | Both show the same format, labelled UTC | `test_defect_5_...` |
| D6 | Medium | The dashboard gets slower as issues are added | Every visit recomputed all pairs and read issues one at a time | Cache the pairs with the index, and read issues in one query | `test_defect_6_...` |

## Severity scale

| Severity | Meaning |
|---|---|
| Critical | Data loss or a security breach. Stop and fix now |
| High | A main function fails, or the server returns 500 for ordinary input |
| Medium | Works, but wrong in some cases, or noticeably slow |
| Low | A cosmetic or minor usability problem |
