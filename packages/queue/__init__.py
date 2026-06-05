"""
packages/queue/__init__.py — marks this directory as a Python package.

Why packages/queue/ instead of putting this in ingest/ or worker/?

  Both the ingestion service AND the worker need to reference the same
  Redis connection and queue name. If each service defined its own copy,
  we'd risk drift — ingest pushing to "article_ingest" while worker
  listens on "articles". A shared package prevents that entirely.

  packages/ is the monorepo convention for cross-service shared code.
  Future packages here:
    packages/schemas/   — shared Pydantic models (later)
    packages/utils/     — logging helpers, etc. (later)
"""
