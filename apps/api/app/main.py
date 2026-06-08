"""
main.py — FastAPI application entry point.

Responsibilities:
  1. Create the FastAPI application instance with metadata.
  2. Create all database tables on startup (dev-mode convenience).
  3. Mount all routers.
  4. Expose the /health endpoint.

Base.metadata.create_all():
  This tells SQLAlchemy to inspect all registered ORM models and create
  their tables in PostgreSQL if they don't exist yet.
  - Safe to call repeatedly — uses "CREATE TABLE IF NOT EXISTS" under the hood.
  - Fine for development. In production (Phase 2+) this will be replaced
    by Alembic migrations which support schema evolution (ALTER TABLE etc).

Import side-effect — `app.models` must be imported BEFORE create_all():
  SQLAlchemy only knows about tables that have been imported and registered
  against Base. The `app.models` __init__.py imports all model classes,
  ensuring they are all registered before we call create_all().
"""

from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine

# Side-effect import: registers all ORM models against Base.
import app.models  # noqa: F401

from app.routers import articles
from app.routers import sentiment
from app.routers import forecast
from app.routers import analytics
from app.routers import system
from app.routers import intelligence

# ---------------------------------------------------------------------------
# Create tables (development convenience — replace with Alembic in production)
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend API for the AI Financial Intelligence Platform. "
        "Collects, stores, and retrieves financial news articles."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(articles.router, prefix="/api/v1")
app.include_router(sentiment.router, prefix="/api/v1")
app.include_router(forecast.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(intelligence.router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    description="Returns a simple OK response. Used by load balancers and monitoring tools.",
)
def health_check():
    """
    Liveness probe endpoint.

    Returns {"status": "ok"} when the application is running.
    In later phases this can be extended to check DB connectivity,
    queue health, worker status, etc.
    """
    return {"status": "ok"}
