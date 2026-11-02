"""Accounts, logins and tokens."""

import jwt

from app.config import get_settings
from app.models import User
from app.security import hash_password, read_access_token, verify_password
from tests.conftest import PASSWORD, auth


def test_password_is_stored_as_a_hash_and_verifies():
    stored = hash_password(PASSWORD)
    assert stored != PASSWORD
    assert stored.startswith("$argon2")
    assert verify_password(PASSWORD, stored)
    assert not verify_password("wrong password", stored)


def test_same_password_gives_different_hashes():
    assert hash_password(PASSWORD) != hash_password(PASSWORD)


def test_register_creates_a_member_and_never_returns_the_password(client, db):
    response = client.post(
        "/api/auth/register",
        json={"full_name": "New Person", "email": "New@Example.com", "password": PASSWORD},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["role"] == "member"
    assert "password" not in str(body).lower()
    assert db.query(User).filter_by(email="new@example.com").one().password_hash != PASSWORD


def test_register_refuses_a_repeated_email(client, lina):
    response = client.post(
        "/api/auth/register",
        json={"full_name": "Copy Cat", "email": lina.email, "password": PASSWORD},
    )
    assert response.status_code == 409


def test_register_refuses_a_short_password(client):
    response = client.post(
        "/api/auth/register",
        json={"full_name": "Short Pass", "email": "s@example.com", "password": "short"},
    )
    assert response.status_code == 422


def test_login_returns_a_token_that_identifies_the_user(client, lina):
    response = client.post(
        "/api/auth/login", data={"username": lina.email, "password": PASSWORD}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert read_access_token(token) == lina.id
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["email"] == lina.email


def test_wrong_password_and_unknown_email_look_identical(client, lina):
    wrong_password = client.post(
        "/api/auth/login", data={"username": lina.email, "password": "nope"}
    )
    unknown_email = client.post(
        "/api/auth/login", data={"username": "no@example.com", "password": "nope"}
    )
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_api_needs_a_token(client):
    assert client.get("/api/issues").status_code == 401


def test_a_tampered_token_is_rejected(client, lina):
    forged = jwt.encode(
        {"sub": str(lina.id)}, "not-the-real-key-but-long-enough-to-sign", algorithm="HS256"
    )
    assert (
        client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {forged}"}
        ).status_code
        == 401
    )


def test_an_expired_token_is_rejected(client, lina):
    expired = jwt.encode(
        {"sub": str(lina.id), "exp": 1_000_000_000},
        get_settings().secret_key,
        algorithm="HS256",
    )
    assert (
        client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {expired}"}
        ).status_code
        == 401
    )


def test_me_shows_only_my_own_details(client, lina):
    body = client.get("/api/auth/me", headers=auth(lina)).json()
    assert set(body) == {"id", "full_name", "email", "role"}
