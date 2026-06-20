"""
database.py — SQLAlchemy engine, session factory, and FastAPI dependency.

Why SQLAlchemy Core + ORM?
  - Industry standard for Python/PostgreSQL. Mature, battle-tested.
  - The ORM layer lets us define tables as Python classes (see models/).
  - The Core layer gives us raw SQL control when we need it (future queries).

Components:
  engine       — single persistent connection pool to PostgreSQL.
  SessionLocal — factory that creates a new DB session per request.
  Base         — declarative base that all ORM models inherit from.
  get_db()     — FastAPI dependency that opens/closes a session per request.

How get_db() works:
  FastAPI's Depends() injects get_db() into any route that declares it.
  The try/finally ensures the session is always closed — even on errors.
  This prevents connection leaks, which would exhaust the pool under load.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# Replace postgres:// or postgresql:// with postgresql+psycopg:// for psycopg3
db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

# create_engine sets up a connection pool (default: 5 connections).
# pool_pre_ping=True checks each connection is alive before using it —
# protects against stale connections after a Postgres restart.
engine = create_engine(
    db_url,
    pool_pre_ping=True,
)

# autocommit=False  → we control transactions explicitly (commit/rollback).
# autoflush=False   → changes are not flushed to DB until we call commit().
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# All ORM models inherit from Base. SQLAlchemy uses it to track table metadata.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency — yields a database session for one request lifetime.

    Usage in a router:
        @router.post("/articles")
        def create(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
