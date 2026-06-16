"""
worker/jobs/article_job.py — rq job function for storing articles.

This is the core of the worker layer.

Responsibility:
  Receive an article dict (published by the ingest service),
  validate it minimally, open a DB session, and persist it.

Why write directly to PostgreSQL instead of calling POST /api/v1/articles?
  The requirement explicitly says: "Avoid unnecessary HTTP calls between
  internal services." The worker is a trusted internal process — it does
  not need to go through the HTTP API, which would:
    1. Add network latency (even on localhost)
    2. Require the API to be running for the worker to function
    3. Go through request validation, routing, and serialisation layers
       that are designed for external clients, not internal services

  Instead, the worker imports the same SQLAlchemy models and CRUD functions
  that the API uses and calls them directly. Both the API and the worker
  share the same database connection pool config (DATABASE_URL from .env).

How rq calls this function:
  When the ingest service enqueues:
      queue.enqueue("worker.jobs.article_job.store_article_job", payload_dict)
  rq deserialises the job and calls:
      store_article_job(payload_dict)
  in the worker process. The function must be importable from the worker's
  working directory (apps/worker/).

Retry behaviour:
  If this function raises ANY exception, rq marks the job as failed and
  schedules a retry (configured by Retry(max=3) in the ingest pipeline).
  So we raise on real failures (DB error) and only return cleanly on success.
  We do NOT silently swallow errors — silent failures mean lost articles.

PYTHONPATH:
  The worker needs to import from:
    - apps/api/app/  (SQLAlchemy models, CRUD, database session)
    - packages/      (shared queue package)
  run.py handles PYTHONPATH setup before importing this module.
"""

import logging
import sys
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def store_article_job(article_dict: dict) -> None:
    """
    rq job function — deserialise article dict and persist to PostgreSQL.

    This function is called by the rq worker in a separate process.
    It runs synchronously inside the worker's event loop.

    Args:
        article_dict: plain dict produced by ArticlePayload.to_dict()
                      in the ingest service. Expected keys:
                        title        (str, required)
                        content      (str, required)
                        source       (str | None)
                        company      (str | None)
                        published_at (ISO 8601 str | None)
                        article_url  (str | None)

    Raises:
        ValueError  : if required fields (title, content) are missing.
        Exception   : any SQLAlchemy/psycopg2 error — causes rq to retry.

    Why raise instead of logging and returning?
        Raising tells rq "this job failed, please retry".
        Returning tells rq "this job succeeded".
        Silent failures (return without storing) would mean lost data with
        no retry and no visibility. Always raise on real errors.
    """
    # --- Import DB layer (deferred to avoid import-time side effects) ---
    # These imports happen at call time, not at module load time.
    # This way run.py can set up sys.path before any DB code runs.
    from app.database import SessionLocal
    from app.schemas.article import ArticleCreate
    from app import crud

    # --- Validate required fields ---
    title = (article_dict.get("title") or "").strip()
    content = (article_dict.get("content") or "").strip()

    if not title:
        raise ValueError(f"article_job: 'title' is required. Got: {article_dict!r}")
    if not content:
        raise ValueError(f"article_job: 'content' is required. Got: {article_dict!r}")

    # --- Parse published_at ---
    published_at: Optional[datetime] = None
    raw_date = article_dict.get("published_at")
    if raw_date:
        try:
            # ISO 8601 string → datetime (as produced by ArticlePayload.to_dict)
            published_at = datetime.fromisoformat(raw_date)
        except (ValueError, TypeError) as exc:
            # Non-fatal: store the article without a date rather than failing
            logger.warning("Could not parse published_at '%s': %s", raw_date, exc)

    # --- Build Pydantic schema (same validation the API uses) ---
    article_in = ArticleCreate(
        title=title,
        content=content,
        source=article_dict.get("source"),
        company=article_dict.get("company"),
        published_at=published_at,
        article_url=article_dict.get("article_url"),
    )

    # --- Persist to database ---
    db = SessionLocal()
    try:
        # Check for duplicates before inserting
        if article_in.article_url:
            from app.models.article import Article
            existing = db.query(Article).filter(Article.article_url == article_in.article_url).first()
            if existing:
                logger.info("Duplicate skipped: Article URL already exists: %s", article_in.article_url)
                return
        article = crud.article.create_article(db=db, article_in=article_in)
        logger.info(
            "Stored article id=%s source=%r title=%r",
            article.id,
            article.source,
            article.title[:60],
        )
    except Exception as exc:
        logger.error(
            "DB error storing article '%s': %s",
            title[:60],
            exc,
        )
        # Re-raise so rq knows to retry this job
        raise
    finally:
        # Always close the session — prevents connection pool exhaustion
        db.close()

    # --- Enqueue sentiment job ---
    # Done AFTER db.close() so the article is fully committed before
    # the sentiment worker tries to fetch it by ID.
    #
    # Why pass article_id as a string instead of UUID?
    #   rq serialises arguments with pickle. UUID objects serialise fine,
    #   but a plain str is simpler and avoids any cross-version pickle issues.
    #
    # Retry(max=3, interval=[30, 60, 120]):
    #   FinBERT failures may be transient (model loading, OOM) so we wait
    #   longer between retries than the article storage job.
    try:
        from packages.queue.queues import get_sentiment_queue
        from rq import Retry as RqRetry

        sentiment_queue = get_sentiment_queue()
        sentiment_queue.enqueue(
            "worker.jobs.sentiment_job.run_sentiment_job",
            str(article.id),
            retry=RqRetry(max=3, interval=[30, 60, 120]),
            job_timeout=300,
        )
        logger.info("Enqueued sentiment job for article_id=%s", article.id)
    except Exception as exc:
        # Sentiment enqueue failure is non-fatal — the article is already stored.
        # Log the error but do NOT re-raise (which would cause article_job to retry
        # and store a duplicate article).
        logger.error(
            "Failed to enqueue sentiment job for article_id=%s: %s "
            "(article is stored; sentiment can be retried manually)",
            article.id,
            exc,
        )

    # --- Enqueue entity extraction job ---
    try:
        from packages.queue.queues import get_entity_queue
        from rq import Retry as RqRetry

        entity_queue = get_entity_queue()
        entity_queue.enqueue(
            "worker.jobs.entity_job.run_entity_job",
            str(article.id),
            retry=RqRetry(max=3, interval=[10, 30, 60]),
            job_timeout=120,
        )
        logger.info("Enqueued entity extraction job for article_id=%s", article.id)
    except Exception as exc:
        logger.error(
            "Failed to enqueue entity job for article_id=%s: %s "
            "(article is stored; entity extraction can be retried manually)",
            article.id,
            exc,
        )

