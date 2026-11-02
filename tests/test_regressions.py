"""Regression tests: each one pins down a real defect found during Chapter 8.

The names match the entries in docs/defect_log.md. Each test failed before the fix,
and it now stops the same defect from ever coming back unnoticed.
"""

from sqlalchemy import event

from app.database import engine
from app.models import Issue, User
from tests.conftest import PASSWORD, PASSWORD_HASH, auth


def count_queries(action) -> int:
    """Run the action and return how many SQL statements it sent to the database."""
    statements = []

    def remember(_connection, _cursor, statement, *_rest):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", remember)
    try:
        action()
    finally:
        event.remove(engine, "before_cursor_execute", remember)
    return len(statements)


def add_issues_from_different_people(db, project, how_many: int, start: int = 0) -> None:
    for number in range(start, start + how_many):
        person = User(
            full_name=f"Person {number}",
            email=f"person{number}@example.com",
            password_hash=PASSWORD_HASH,
        )
        db.add(person)
        db.flush()
        db.add(
            Issue(
                project_id=project.id,
                reporter_id=person.id,
                title=f"Issue number {number}",
                description="Reported by a different person each time.",
                category="bug",
            )
        )
    db.commit()


def test_defect_1_issue_list_query_count_does_not_grow_with_rows(client, db, lina, project):
    headers = auth(lina)
    add_issues_from_different_people(db, project, 3)
    few = count_queries(lambda: client.get("/api/issues?limit=100", headers=headers))
    add_issues_from_different_people(db, project, 12, start=3)
    many = count_queries(lambda: client.get("/api/issues?limit=100", headers=headers))
    assert many == few, f"{few} queries for 3 issues but {many} queries for 15 issues"


def test_defect_2_null_title_is_refused_and_is_not_a_server_error(client, lina, issue):
    response = client.patch(
        f"/api/issues/{issue.id}", json={"title": None}, headers=auth(lina)
    )
    assert response.status_code == 422


def test_defect_2_assignee_may_still_be_cleared_with_null(client, db, lina, omar, issue):
    issue.assignee_id = omar.id
    db.commit()
    response = client.patch(
        f"/api/issues/{issue.id}", json={"assignee_id": None}, headers=auth(lina)
    )
    assert response.status_code == 200
    assert response.json()["assignee"] is None


def test_defect_3_reopening_removes_the_duplicate_link(client, db, lina, project, issue):
    copy = Issue(
        project_id=project.id,
        reporter_id=lina.id,
        title="Same problem described again",
        description="This report was closed as a duplicate by mistake.",
        category="bug",
    )
    db.add(copy)
    db.commit()
    headers = auth(lina)
    client.post(
        f"/api/issues/{copy.id}/duplicate",
        json={"duplicate_of_id": issue.id},
        headers=headers,
    )
    response = client.patch(
        f"/api/issues/{copy.id}/status", json={"status": "open"}, headers=headers
    )
    assert response.json()["status"] == "open"
    assert response.json()["duplicate_of_id"] is None


def test_defect_4_filters_survive_the_redirect_to_login(client):
    response = client.get(
        "/issues?status=open&sort=priority",
        headers={"Accept": "text/html"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert (
        response.headers["location"]
        == "/login?next=/issues%3Fstatus%3Dopen%26sort%3Dpriority"
    )


def test_defect_4_login_returns_to_the_filtered_page(client, lina):
    response = client.post(
        "/login",
        data={
            "email": lina.email,
            "password": PASSWORD,
            "next": "/issues?status=open&sort=priority",
        },
        follow_redirects=False,
    )
    assert response.headers["location"] == "/issues?status=open&sort=priority"


def test_defect_5_times_on_pages_are_labelled_utc(client, lina, issue):
    client.post("/login", data={"email": lina.email, "password": PASSWORD})
    page = client.get(f"/issues/{issue.id}", headers={"Accept": "text/html"})
    assert "UTC" in page.text


def test_defect_6_dashboard_summary_query_count_stays_small(client, db, lina, project):
    add_issues_from_different_people(db, project, 15)
    queries = count_queries(lambda: client.get("/api/insights/summary", headers=auth(lina)))
    assert queries <= 10
