"""
Connection management. Reads config.settings.DB_URL — SQLite by default
(zero setup), Postgres in production. Nothing else in the codebase should
import sqlalchemy.create_engine directly; go through get_engine()/
get_session() so there's exactly one place that knows the connection string.
"""
from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings
from database.models import Base

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        connect_args = {"check_same_thread": False} if settings.DB_URL.startswith("sqlite") else {}
        _engine = create_engine(settings.DB_URL, connect_args=connect_args, future=True)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)
    return _SessionLocal


def init_db() -> None:
    """Create all tables if they don't exist. Safe to call every boot."""
    Base.metadata.create_all(bind=get_engine())


@contextmanager
def session_scope() -> Session:
    """Context-managed session: commits on success, rolls back on error, always closes."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
