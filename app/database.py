"""Database connection: one engine for the whole app, one session per request."""

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

database_url = get_settings().database_url
is_sqlite = database_url.startswith("sqlite")

# check_same_thread=False: FastAPI may serve a request on any worker thread.
engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if is_sqlite else {},
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
