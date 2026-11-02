"""Health checks, configuration, safe errors and security headers."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import DEVELOPMENT_KEY, Settings
from app.main import app


def test_health_reports_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["model"] == "loaded"


def test_health_needs_no_login_and_reveals_no_secrets(client):
    text = client.get("/health").text.lower()
    assert "secret" not in text
    assert "postgres" not in text
    assert "password" not in text


def test_security_headers_are_present(client):
    headers = client.get("/health").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in headers["content-security-policy"]


def test_api_documentation_is_available(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").json()["info"]["title"] == "DevInsight AI Lite"


@pytest.mark.parametrize("weak_key", [DEVELOPMENT_KEY, "too-short"])
def test_production_refuses_a_weak_secret_key(weak_key):
    with pytest.raises(ValidationError) as caught:
        Settings(
            environment="production",
            secret_key=weak_key,
            seed_password="private-value",
            _env_file=None,
        )
    # This message reaches the logs, so it must not quote any setting.
    assert "private-value" not in str(caught.value)


def test_production_accepts_a_strong_secret_key():
    settings = Settings(environment="production", secret_key="k" * 40, _env_file=None)
    assert settings.is_production


def test_unexpected_errors_reveal_nothing_to_the_client(caplog):
    """Force a crash inside a route and check what the outside world and the log can see."""

    @app.get("/test-only-crash", include_in_schema=False)
    def crash():
        raise RuntimeError("database password is hunter2")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/test-only-crash")
    app.router.routes.pop()

    assert response.status_code == 500
    assert "hunter2" not in response.text
    assert response.json() == {"detail": "Internal server error."}
    # The client learns nothing, but developers must get the whole traceback.
    logged = [record for record in caplog.records if record.name == "app.error_handlers"]
    assert logged[-1].exc_info[0] is RuntimeError
