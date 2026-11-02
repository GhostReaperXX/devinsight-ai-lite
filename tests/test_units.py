"""Unit tests: one small function at a time, with no server and no database."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.database import normalize_database_url
from app.ml.text import combine_text
from app.routers.pages import safe_next_path
from app.schemas import IssueCreate, IssueFilters, as_utc_text
from app.services.issues import ALLOWED_TRANSITIONS


def test_combine_text_keeps_title_and_description():
    text = combine_text("Login fails", "Error 500 appears")
    assert "Login fails" in text
    assert "Error 500 appears" in text


def test_naive_datetime_is_treated_as_utc():
    assert as_utc_text(datetime(2026, 3, 14, 9, 30)) == "2026-03-14T09:30:00Z"


def test_other_time_zones_are_converted_to_utc():
    amman = timezone(timedelta(hours=3))
    assert as_utc_text(datetime(2026, 3, 14, 12, 0, tzinfo=amman)) == "2026-03-14T09:00:00Z"
    assert as_utc_text(datetime(2026, 3, 14, 9, 0, tzinfo=UTC)) == "2026-03-14T09:00:00Z"


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("sqlite:///./app.db", "sqlite:///./app.db"),
        ("postgres://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("postgresql://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
    ],
)
def test_database_url_names_the_driver(given, expected):
    assert normalize_database_url(given) == expected


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ("/issues/5", "/issues/5"),
        ("https://evil.example/", "/"),
        ("//evil.example/", "/"),
        ("/\\evil.example/", "/"),
        ("", "/"),
    ],
)
def test_login_never_redirects_to_another_site(target, expected):
    assert safe_next_path(target) == expected


def test_every_status_can_reach_another_status():
    for status, next_statuses in ALLOWED_TRANSITIONS.items():
        assert next_statuses, f"{status} is a dead end"
        assert status not in next_statuses


def test_title_is_stripped_before_it_is_checked():
    data = IssueCreate(
        project_id=1,
        title="  Cart total is wrong  ",
        description="The total ignores the discount code.",
        category="bug",
    )
    assert data.title == "Cart total is wrong"


def test_blank_filter_means_no_filter():
    filters = IssueFilters(status="", project_id="", q="")
    assert filters.status is None
    assert filters.project_id is None
    assert filters.q is None
