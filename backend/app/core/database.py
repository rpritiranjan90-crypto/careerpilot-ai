"""Database connection and session management.

SQLAlchemy 2.0 with async-compatible sync sessions.
Connection is lazy: only created when DATABASE_URL is set.
Use Alembic for migrations; use init_db() only for dev or first-run.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 declarative base."""
    pass


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine | None:
    """Create and cache the database engine (singleton)."""
    global _engine
    if _engine is None:
        if not settings.database_url:
            return None
        connect_args: dict = {}
        # If a non-default schema is configured, set search_path so all
        # unqualified table references resolve to the CareerPilot schema.
        schema = settings.db_schema.strip() if settings.db_schema else ""
        if schema and schema != "public":
            connect_args = {"options": f"-c search_path={schema},public"}
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,
            echo=settings.debug,  # SQL echo only in debug mode
            connect_args=connect_args,
        )
    return _engine


def get_session_factory() -> sessionmaker[Session] | None:
    """Create and cache the session factory (singleton)."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        if engine is None:
            return None
        _SessionLocal = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a database session, always close it.

    Returns None if no database is configured (dev/demo mode).
    """
    session_factory = get_session_factory()
    if session_factory is None:
        yield None  # type: ignore[misc]
        return

    db = session_factory()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions outside of FastAPI routes."""
    session_factory = get_session_factory()
    if session_factory is None:
        raise RuntimeError("Database not configured (DATABASE_URL not set)")
    db = session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Create all tables defined on Base.metadata.

    Use Alembic for production migrations. This function is for:
    - local development (first run)
    - test fixtures (pytest conftest)
    """
    engine = get_engine()
    if engine is None:
        raise RuntimeError(
            "Cannot initialize DB: DATABASE_URL is not set. "
            "Set DATABASE_URL in your .env file."
        )
    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    """Return True if the database is reachable, False otherwise."""
    engine = get_engine()
    if engine is None:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
