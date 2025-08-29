from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .settings import get_settings


class Base(DeclarativeBase):
    pass

_engine = None
_SessionLocal = None
_db_checked = False

def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings.database_url(), future=True)
    return _engine

def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False)
    return _SessionLocal


def ensure_database_exists() -> None:
    """Ensure the target Postgres database exists.

    Connects to the default 'postgres' maintenance database and creates the
    configured database if it is missing. Safe to call multiple times.
    Swallows errors to avoid blocking app startup in restricted environments.
    """
    global _db_checked
    if _db_checked:
        return
    settings = get_settings()
    # Determine driver (mirror logic in Settings.database_url)
    driver = "psycopg"
    try:  # pragma: no cover
        import psycopg  # type: ignore  # noqa: F401
    except Exception:  # pragma: no cover
        driver = "psycopg2"
    server_url = f"postgresql+{driver}://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/postgres"
    try:
        server_engine = create_engine(server_url, isolation_level="AUTOCOMMIT", future=True)
        with server_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :d"), {"d": settings.db_name}
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{settings.db_name}"'))
    except Exception:
        # Intentionally ignore; database may already exist or user lacks permission.
        pass
    finally:
        _db_checked = True

__all__ = ["Base", "get_engine", "get_session_factory", "ensure_database_exists"]
