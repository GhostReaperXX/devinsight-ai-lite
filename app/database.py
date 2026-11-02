"""Database connection: one engine for the whole app, one session per request."""

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


def normalize_database_url(url: str) -> str:
    """Hosting services give postgres:// or postgresql://. Name the installed driver."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


database_url = normalize_database_url(get_settings().database_url)
is_sqlite = database_url.startswith("sqlite")

if is_sqlite:
    # FastAPI may serve a request on any worker thread.
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
else:
    # A hosted database may close idle connections, so test each one before using it
    # and replace it after five minutes. The free plans allow only a few connections.
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=3,
        max_overflow=2,
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


if is_sqlite:

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(connection, _record) -> None:
        """SQLite ignores foreign keys unless each new connection switches them on."""
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()


class Base(DeclarativeBase):
    """Parent class of every table model."""


def get_db() -> Iterator[Session]:
    """Give one request its own session, and always close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
