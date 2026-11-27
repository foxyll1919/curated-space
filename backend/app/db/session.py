from collections.abc import Iterator
from pathlib import Path

from fastapi import Request
from sqlalchemy import Engine, URL, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings


def make_database_url(path: Path) -> URL:
    return URL.create("sqlite", database=str(path.resolve()))


def normalize_database_url(raw: str) -> str:
    url = raw.strip()
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


def resolve_database_url(settings: Settings) -> str | URL:
    if settings.database_url is not None:
        raw = settings.database_url.get_secret_value().strip()
        if raw:
            return normalize_database_url(raw)
    return make_database_url(settings.database_path)


def is_sqlite_url(url: str | URL) -> bool:
    return str(url).startswith("sqlite")


def create_database_engine(settings: Settings) -> Engine:
    url = resolve_database_url(settings)
    if not is_sqlite_url(url):
        return create_engine(url, pool_pre_ping=True)

    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragmas(connection, _record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session(request: Request) -> Iterator[Session]:
    session_factory = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
