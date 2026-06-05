"""
pipeline.py — Ingestion pipeline orchestrator (Phase 3: Queue-based).

Phase 3 change: Step 4 is now "Push to Redis Queue" instead of "POST to API".

Responsibility:
  Wires together the ingestion layers:

    1. Fetch     → ingest.fetchers.rss        (collect raw RSS articles)
    2. Transform → ingest.services.transformer (clean and normalise)
    3. Enqueue   → Redis via rq               (push article_job to queue)

  The worker service (apps/worker/) consumes jobs from the queue and
  writes directly to PostgreSQL — no HTTP roundtrip needed.

Why no more httpx here?
  The ingest service's responsibility ends at the queue boundary.
  It does not need to know HOW articles are stored, only THAT they
  are pushed for processing. This is the core value of a queue:
  producers and consumers are fully decoupled.

Retry strategy:
  rq.Retry(max=3, interval=[10, 30, 60]) means:
    - Job fails → retry after 10s
    - Still fails → retry after 30s
    - Still fails → retry after 60s
    - 3rd failure → job moves to rq's "failed" queue for inspection
  This handles transient DB connection issues, postgres restarts, etc.

IngestionResult:
  .queued  : number of jobs successfully pushed to the queue
  .failed  : number of articles that could not be enqueued (Redis error)
  (no longer .stored — storage is the worker's responsibility)
"""

import logging
import sys
import os

# ---------------------------------------------------------------------------
# PYTHONPATH setup for shared packages
# When run from apps/ingest/, packages/ is two levels up.
# We add it here so 'import packages.queue' works without installation.
# ---------------------------------------------------------------------------
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

import rq
from rq import Retry

from ingest.fetchers.rss import RawArticle, fetch_all_feeds
from ingest.services.transformer import ArticlePayload, transform_many
from packages.queue.queues import get_article_queue

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result tracker
# ---------------------------------------------------------------------------

class IngestionResult:
    """
    Summary of a completed ingestion run.

    Phase 3: 'stored' replaced by 'queued' — the ingest service no longer
    stores articles directly. That is now the worker's responsibility.
    """
    __slots__ = ("fetched", "transformed", "queued", "failed")

    def __init__(self) -> None:
        self.fetched: int = 0
        self.transformed: int = 0
        self.queued: int = 0
        self.failed: int = 0

    def __repr__(self) -> str:
        return (
            f"IngestionResult("
            f"fetched={self.fetched}, "
            f"transformed={self.transformed}, "
            f"queued={self.queued}, "
            f"failed={self.failed})"
        )


# ---------------------------------------------------------------------------
# Queue enqueue helper
# ---------------------------------------------------------------------------

def _enqueue_article(queue: rq.Queue, payload: ArticlePayload) -> bool:
    """
    Push a single article job onto the Redis queue.

    Returns True on success, False on any Redis/serialisation error.

    rq.Queue.enqueue() arguments:
      - func: the job function to call. Must be importable by the worker.
              We pass it as the string path to avoid importing worker code
              from the ingest service (keeps the boundary clean).
      - payload.to_dict(): plain dict — JSON-serialisable, safe across
              process boundaries. rq pickles job arguments.
      - retry: Retry(max=3, interval=[10, 30, 60]) — exponential back-off.
              If the worker fails to process the job 3 times, rq moves it
              to the "failed" queue where it can be inspected with `rq info`.
    """
    try:
        queue.enqueue(
            "worker.jobs.article_job.store_article_job",
            payload.to_dict(),
            retry=Retry(max=3, interval=[10, 30, 60]),
            job_timeout=60,
        )
        logger.debug("Enqueued: %s", payload.title[:80])
        return True
    except Exception as exc:
        logger.error(
            "Failed to enqueue article '%s': %s",
            payload.title[:60],
            exc,
        )
        return False


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------

def run() -> IngestionResult:
    """
    Execute a full ingestion cycle (Phase 3: queue-based).

    Steps:
      1. Fetch all articles from registered RSS feeds.
      2. Transform into clean ArticlePayload objects.
      3. Get a handle to the Redis article_ingest queue.
      4. Enqueue each article as an rq job for the worker to consume.

    Returns IngestionResult with counters.

    The queue is obtained once and reused for all articles in the run.
    This is efficient — each enqueue() call is a single Redis RPUSH command.
    """
    result = IngestionResult()

    # --- Step 1: Fetch ---
    logger.info("Starting ingestion run...")
    from ingest.fetchers.rss import FEED_SOURCES
    logger.info("Fetching from %d feed sources...", len(FEED_SOURCES))

    raw_articles: list[RawArticle] = list(fetch_all_feeds())
    result.fetched = len(raw_articles)
    logger.info("Total raw articles fetched: %d", result.fetched)

    if not raw_articles:
        logger.warning("No articles fetched. Check feed URLs and network connectivity.")
        return result

    # --- Step 2: Transform ---
    payloads: list[ArticlePayload] = transform_many(raw_articles)
    result.transformed = len(payloads)

    if not payloads:
        logger.warning("No articles passed transformation.")
        return result

    # --- Step 3: Enqueue ---
    logger.info("Connecting to Redis queue...")
    try:
        queue = get_article_queue()
        # Verify the connection is alive before looping
        queue.connection.ping()
        logger.info("Redis connection OK. Queue: '%s'", queue.name)
    except Exception as exc:
        logger.error(
            "Cannot connect to Redis: %s. "
            "Start Redis with: redis-server",
            exc,
        )
        result.failed = result.transformed
        return result

    logger.info("Enqueuing %d articles...", result.transformed)

    for payload in payloads:
        success = _enqueue_article(queue, payload)
        if success:
            result.queued += 1
        else:
            result.failed += 1

    logger.info(
        "Ingestion run complete. "
        "Fetched: %d | Transformed: %d | Queued: %d | Failed: %d",
        result.fetched,
        result.transformed,
        result.queued,
        result.failed,
    )

    return result
