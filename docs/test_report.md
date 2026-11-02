# Test report

## Summary

| Item | Result |
|---|---|
| Automated tests | 105 passed, 0 failed |
| Statement coverage of `app/` | 91 percent |
| Lint | `ruff check .` reports no problems |
| Continuous integration | Runs on every push to main and every pull request |

## What is tested

| File | Level | What it protects |
|---|---|---|
| `tests/test_units.py` | Unit | Small pure functions: text, time zones, URLs, safe redirects |
| `tests/test_auth.py` | API | Hashing, registration, login, forged and expired tokens |
| `tests/test_issues_api.py` | API | Create, read, update, filter, search, paging, statistics |
| `tests/test_rules.py` | API | Status life cycle, transactions, access control, duplicates |
| `tests/test_pages.py` | System | Login flow, forms, output encoding, friendly errors |
| `tests/test_ml.py` | Integration | Model shape and quality gate, similarity, working without a model |
| `tests/test_operations.py` | System | Health check, secret checks, safe errors, security headers |
| `tests/test_regressions.py` | Regression | One test for each defect in `docs/defect_log.md` |

## How to run

```bash
pytest --cov --cov-report=term-missing
```

## What is not covered by automation

- The JavaScript in the browser. It is covered by the manual checklist in `docs/deployment.md`.
- Real PostgreSQL behaviour, which is verified once on the hosted database after each deployment.
