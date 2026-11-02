"""The browser pages: login flow, forms and safe display."""

from tests.conftest import PASSWORD

HTML = {"Accept": "text/html"}


def log_in(client, user) -> None:
    response = client.post(
        "/login", data={"email": user.email, "password": PASSWORD}, follow_redirects=False
    )
    assert response.status_code == 303


def test_pages_redirect_to_login_when_not_logged_in(client):
    response = client.get("/issues", headers=HTML, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/login")


def test_session_cookie_is_protected(client, lina):
    response = client.post(
        "/login", data={"email": lina.email, "password": PASSWORD}, follow_redirects=False
    )
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie


def test_failed_login_stays_on_the_page(client, lina):
    response = client.post("/login", data={"email": lina.email, "password": "wrong"})
    assert response.status_code == 401
    assert "Wrong e-mail or password" in response.text


def test_login_does_not_redirect_to_another_site(client, lina):
    response = client.post(
        "/login",
        data={"email": lina.email, "password": PASSWORD, "next": "https://evil.example/"},
        follow_redirects=False,
    )
    assert response.headers["location"] == "/"


def test_main_pages_load_after_login(client, lina, issue):
    log_in(client, lina)
    for path in (
        "/",
        "/issues",
        "/issues/new",
        f"/issues/{issue.id}",
        "/projects",
        "/duplicates",
        "/model",
    ):
        assert client.get(path, headers=HTML).status_code == 200, path


def test_new_issue_form_shows_errors_and_keeps_the_typing(client, lina, project):
    log_in(client, lina)
    response = client.post(
        "/issues/new",
        data={
            "project_id": project.id,
            "title": "abc",
            "description": "Long enough description.",
            "category": "bug",
        },
    )
    assert response.status_code == 422
    assert "at least 5 characters" in response.text
    assert "Long enough description." in response.text


def test_new_issue_form_creates_and_redirects(client, lina, project):
    log_in(client, lina)
    response = client.post(
        "/issues/new",
        data={
            "project_id": project.id,
            "title": "Cart total is wrong",
            "description": "The total ignores the discount code.",
            "category": "bug",
            "priority": "high",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].endswith("?msg=created")


def test_script_in_a_title_is_displayed_as_text(client, lina, project):
    log_in(client, lina)
    attack = "<script>alert(1)</script> title"
    response = client.post(
        "/issues/new",
        data={
            "project_id": project.id,
            "title": attack,
            "description": "Testing output encoding.",
            "category": "bug",
        },
    )
    assert response.status_code == 200
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text


def test_unknown_page_gives_a_friendly_404(client, lina):
    log_in(client, lina)
    response = client.get("/no/such/page", headers=HTML)
    assert response.status_code == 404
    assert "could not find" in response.text
