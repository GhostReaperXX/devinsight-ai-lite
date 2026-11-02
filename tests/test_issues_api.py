"""The issue API: normal use, invalid input, filtering and paging."""

import pytest

from app.models import Issue
from tests.conftest import auth


def valid_issue(project: int, **overrides) -> dict:
    return {
        "project_id": project,
        "title": "Report export is missing a column",
        "description": "The monthly export no longer contains the totals column.",
        "category": "bug",
        "priority": "medium",
    } | overrides


def test_create_issue_sets_reporter_from_the_login(client, lina, project):
    response = client.post("/api/issues", json=valid_issue(project.id), headers=auth(lina))
    assert response.status_code == 201
    body = response.json()
    assert body["reporter"]["id"] == lina.id
    assert body["status"] == "open"
    assert body["project"]["key"] == "SHOP"


def test_client_cannot_claim_to_be_someone_else(client, lina, omar, project):
    payload = valid_issue(project.id, reporter_id=omar.id)
    response = client.post("/api/issues", json=payload, headers=auth(lina))
    assert response.json()["reporter"]["id"] == lina.id


@pytest.mark.parametrize(
    "bad_fields",
    [
        {"title": "abc"},
        {"title": "x" * 151},
        {"description": "short"},
        {"category": "nonsense"},
        {"priority": "urgent"},
        {"project_id": "not-a-number"},
    ],
)
def test_invalid_input_is_rejected(client, lina, project, bad_fields):
    response = client.post(
        "/api/issues", json=valid_issue(project.id, **bad_fields), headers=auth(lina)
    )
    assert response.status_code == 422


def test_unknown_project_is_rejected(client, lina):
    response = client.post("/api/issues", json=valid_issue(999), headers=auth(lina))
    assert response.status_code == 422
    assert "project 999" in response.json()["detail"]


def test_read_missing_issue_gives_404(client, lina):
    assert client.get("/api/issues/999", headers=auth(lina)).status_code == 404


def test_patch_changes_only_the_fields_sent(client, lina, issue):
    response = client.patch(
        f"/api/issues/{issue.id}", json={"priority": "low"}, headers=auth(lina)
    )
    assert response.status_code == 200
    assert response.json()["priority"] == "low"
    assert response.json()["title"] == issue.title


@pytest.fixture
def many_issues(db, project, lina):
    rows = [
        ("Login page is blank", "bug", "critical", "open"),
        ("Add dark theme", "feature", "low", "open"),
        ("Search results load slowly", "performance", "high", "in_progress"),
        ("Update the install guide", "documentation", "low", "resolved"),
        ("Passwords appear in the log", "security", "critical", "closed"),
    ]
    for title, category, priority, status in rows:
        db.add(
            Issue(
                project_id=project.id,
                reporter_id=lina.id,
                title=title,
                description=f"Details about: {title}.",
                category=category,
                priority=priority,
                status=status,
            )
        )
    db.commit()


@pytest.mark.parametrize(
    ("query", "expected_titles"),
    [
        ("status=open", {"Login page is blank", "Add dark theme"}),
        ("category=security", {"Passwords appear in the log"}),
        ("priority=critical&status=open", {"Login page is blank"}),
        ("q=login", {"Login page is blank"}),
        ("q=LOGIN", {"Login page is blank"}),
        ("q=nothing-matches-this", set()),
    ],
)
def test_filters(client, lina, many_issues, query, expected_titles):
    response = client.get(f"/api/issues?{query}", headers=auth(lina))
    assert {item["title"] for item in response.json()["items"]} == expected_titles


def test_percent_sign_in_search_is_taken_literally(client, lina, many_issues):
    response = client.get("/api/issues", params={"q": "%"}, headers=auth(lina))
    assert response.json()["total"] == 0


def test_sort_by_priority_puts_critical_first(client, lina, many_issues):
    items = client.get("/api/issues?sort=priority", headers=auth(lina)).json()["items"]
    assert items[0]["priority"] == "critical"
    assert items[-1]["priority"] == "low"


def test_paging_reports_the_total_and_returns_one_page(client, lina, many_issues):
    body = client.get("/api/issues?limit=2&offset=4", headers=auth(lina)).json()
    assert body["total"] == 5
    assert len(body["items"]) == 1


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "sort=sideways"])
def test_bad_paging_values_are_rejected(client, lina, query):
    assert client.get(f"/api/issues?{query}", headers=auth(lina)).status_code == 422


def test_stats_count_correctly(client, lina, many_issues):
    stats = client.get("/api/stats", headers=auth(lina)).json()
    assert stats["total"] == 5
    assert stats["active"] == 3
    assert stats["by_priority"]["critical"] == 2
    assert stats["per_project"] == [{"key": "SHOP", "name": "Online Store", "issues": 5}]


def test_comments_are_saved_with_the_logged_in_author(client, omar, issue):
    created = client.post(
        f"/api/issues/{issue.id}/comments",
        json={"body": "I can repeat this."},
        headers=auth(omar),
    )
    assert created.status_code == 201
    listed = client.get(f"/api/issues/{issue.id}/comments", headers=auth(omar)).json()
    assert listed[0]["body"] == "I can repeat this."
    assert listed[0]["author"]["id"] == omar.id
