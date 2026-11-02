"""Shared test setup. The settings must be chosen before the application is imported."""

import os

os.environ["ENVIRONMENT"] = "test"
# The fixtures delete all tables, so TEST_DATABASE_URL must name a disposable database.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "sqlite:///./test_devinsight.db"
)
os.environ["SECRET_KEY"] = "test-only-key-that-is-long-enough-for-the-signature"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import Issue, Project, User
from app.security import create_access_token, hash_password

PASSWORD = "correct horse battery"
# Hashing is slow by design. Doing it once keeps the whole suite fast.
PASSWORD_HASH = hash_password(PASSWORD)


@pytest.fixture(autouse=True)
def fresh_database():
    """Every test starts from empty tables, so tests can never affect each other."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def make_user(db, email: str, role: str = "member") -> User:
    user = User(
        full_name=email.split("@")[0].title(),
        email=email,
        role=role,
        password_hash=PASSWORD_HASH,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def admin(db) -> User:
    return make_user(db, "admin@example.com", role="admin")


@pytest.fixture
def lina(db) -> User:
    return make_user(db, "lina@example.com")


@pytest.fixture
def omar(db) -> User:
    return make_user(db, "omar@example.com")


@pytest.fixture
def project(db) -> Project:
    project = Project(key="SHOP", name="Online Store", description="A test project")
    db.add(project)
    db.commit()
    return project


@pytest.fixture
def issue(db, project, lina) -> Issue:
    """An open issue reported by Lina."""
    issue = Issue(
        project_id=project.id,
        reporter_id=lina.id,
        title="Checkout button does nothing",
        description="Tapping the pay button on a phone has no effect.",
        category="bug",
        priority="high",
    )
    db.add(issue)
    db.commit()
    return issue


def auth(user: User) -> dict[str, str]:
    """Return the header that makes a request come from this user."""
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


def pytest_sessionfinish(session, exitstatus):
    """Remove the temporary database file after the last test."""
    engine.dispose()
    if os.path.exists("test_devinsight.db"):
        os.remove("test_devinsight.db")
