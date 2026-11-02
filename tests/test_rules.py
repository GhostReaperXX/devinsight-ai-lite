"""Business rules and access control."""

import pytest

from app.models import Comment, Issue
from tests.conftest import auth


@pytest.mark.parametrize(
    ("start", "target", "expected_code"),
    [
        ("open", "in_progress", 200),
        ("in_progress", "resolved", 200),
        ("resolved", "closed", 200),
        ("closed", "open", 200),
        ("resolved", "open", 422),
        ("closed", "resolved", 422),
    ],
)
def test_status_life_cycle(client, db, lina, issue, start, target, expected_code):
    issue.status = start
    db.commit()
    response = client.patch(
        f"/api/issues/{issue.id}/status", json={"status": target}, headers=auth(lina)
    )
    assert response.status_code == expected_code


def test_status_and_comment_are_saved_together(client, db, lina, issue):
    response = client.patch(
        f"/api/issues/{issue.id}/status",
        json={"status": "resolved", "comment": "Fixed in build 12."},
        headers=auth(lina),
    )
    assert response.status_code == 200
    assert db.query(Comment).filter_by(issue_id=issue.id).one().body == "Fixed in build 12."


def test_a_refused_status_change_also_refuses_its_comment(client, db, lina, issue):
    issue.status = "closed"
    db.commit()
    client.patch(
        f"/api/issues/{issue.id}/status",
        json={"status": "resolved", "comment": "This must not be saved."},
        headers=auth(lina),
    )
    assert db.query(Comment).filter_by(issue_id=issue.id).count() == 0


def test_outsider_cannot_edit_someone_elses_issue(client, omar, issue):
    response = client.patch(
        f"/api/issues/{issue.id}", json={"priority": "low"}, headers=auth(omar)
    )
    assert response.status_code == 403


def test_assignee_can_change_status(client, db, omar, issue):
    issue.assignee_id = omar.id
    db.commit()
    response = client.patch(
        f"/api/issues/{issue.id}/status", json={"status": "in_progress"}, headers=auth(omar)
    )
    assert response.status_code == 200


def test_admin_can_edit_any_issue(client, admin, issue):
    response = client.patch(
        f"/api/issues/{issue.id}", json={"priority": "low"}, headers=auth(admin)
    )
    assert response.status_code == 200


def test_only_admin_can_delete(client, lina, admin, issue):
    assert client.delete(f"/api/issues/{issue.id}", headers=auth(lina)).status_code == 403
    assert client.delete(f"/api/issues/{issue.id}", headers=auth(admin)).status_code == 204


def test_only_admin_can_create_a_project(client, lina, admin):
    payload = {"key": "NEW", "name": "New Project"}
    assert client.post("/api/projects", json=payload, headers=auth(lina)).status_code == 403
    assert (
        client.post("/api/projects", json=payload, headers=auth(admin)).status_code == 201
    )


def test_project_key_must_be_unique(client, admin, project):
    payload = {"key": "shop", "name": "Same key in lower case"}
    assert (
        client.post("/api/projects", json=payload, headers=auth(admin)).status_code == 409
    )


@pytest.fixture
def second_issue(db, project, lina) -> Issue:
    other = Issue(
        project_id=project.id,
        reporter_id=lina.id,
        title="Pay button is not responding on phones",
        description="The payment button has no effect on mobile browsers.",
        category="bug",
    )
    db.add(other)
    db.commit()
    return other


def test_mark_duplicate_closes_and_links(client, db, lina, issue, second_issue):
    response = client.post(
        f"/api/issues/{second_issue.id}/duplicate",
        json={"duplicate_of_id": issue.id},
        headers=auth(lina),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "closed"
    assert response.json()["duplicate_of_id"] == issue.id
    assert "duplicate" in db.query(Comment).filter_by(issue_id=second_issue.id).one().body


def test_issue_cannot_be_a_duplicate_of_itself(client, lina, issue):
    response = client.post(
        f"/api/issues/{issue.id}/duplicate",
        json={"duplicate_of_id": issue.id},
        headers=auth(lina),
    )
    assert response.status_code == 422


def test_deleting_an_issue_removes_its_comments(client, db, admin, issue):
    client.post(
        f"/api/issues/{issue.id}/comments", json={"body": "A comment."}, headers=auth(admin)
    )
    client.delete(f"/api/issues/{issue.id}", headers=auth(admin))
    assert db.query(Comment).count() == 0
