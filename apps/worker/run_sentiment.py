"""
worker/run_sentiment.py — Manual entry point for the sentiment worker.

Usage:
    # From apps/worker/ directory:
    cd apps/worker
    python run_sentiment.py

    # With debug logging:
    LOG_LEVEL=DEBUG python run_sentiment.py

    # Burst mode (process queued jobs then exit — useful for testing):
    WORKER_BURST=true python run_sentiment.py

Workflow (start in this order):
    T1: redis-server
    T2: cd apps/api && uvicorn app.main:app --port 8000 --reload
    T3: cd apps/worker && python run.py               ← article worker
    T4: cd apps/worker && python run_sentiment.py     ← sentiment worker (this)

Why a separate entry point from run.py?
    - article_job and sentiment_job have very different resource profiles:
        article_job   : fast DB inserts (~5ms each), no ML
        sentiment_job : FinBERT inference (~100-500ms each), loads a 440MB model
    - Keeping them separate means:
        1. We can scale independently (more sentiment workers if needed).
        2. A crashed sentiment worker doesn't affect article storage.
        3. The model is only loaded in the sentiment worker process,
           not polluting the article worker's memory.

PYTHONPATH:
    Same setup as run.py — adds repo_root, apps/, apps/api/ to sys.path.
"""

import logging
import os
import sys

# ---------------------------------------------------------------------------
# PYTHONPATH setup — identical to run.py
# ---------------------------------------------------------------------------
_here = os.path.dirname(os.path.abspath(__file__))              # apps/worker/
_apps_root = os.path.abspath(os.path.join(_here, ".."))         # apps/
_repo_root = os.path.abspath(os.path.join(_here, "..", ".."))   # monorepo root
_api_root = os.path.join(_repo_root, "apps", "api")             # apps/api/

for _path in [_repo_root, _apps_root, _api_root]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

# ---------------------------------------------------------------------------
# Imports (after PYTHONPATH is set)
# ---------------------------------------------------------------------------
import rq
from rq import SimpleWorker

from worker.config import settings
from packages.queue.connection import get_redis_connection
from packages.queue.queues import SENTIMENT_PROCESS_QUEUE_NAME


def setup_logging() -> None:
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("AI Financial Intelligence Platform — Sentiment Worker")
    logger.info("Redis  : %s", settings.redis_url)
    logger.info("Queue  : %s", SENTIMENT_PROCESS_QUEUE_NAME)
    logger.info("Model  : ProsusAI/finbert")
    logger.info("Burst  : %s", settings.worker_burst)
    logger.info("=" * 60)
    logger.info(
        "NOTE: FinBERT model (~440MB) downloads on first run if not cached."
    )
    logger.info(
        "Subsequent runs use the local HuggingFace cache (~/.cache/huggingface)."
    )

    # Connect to Redis
    try:
        conn = get_redis_connection()
        conn.ping()
        logger.info("Redis connection OK")
    except Exception as exc:
        logger.error("Cannot connect to Redis: %s", exc)
        sys.exit(1)

    # Create and start the sentiment worker
    queues = [rq.Queue(SENTIMENT_PROCESS_QUEUE_NAME, connection=conn)]

    worker = SimpleWorker(
        queues=queues,
        connection=conn,
    )

    logger.info("Sentiment worker started. Listening on queue '%s'...", SENTIMENT_PROCESS_QUEUE_NAME)
    logger.info("Press Ctrl+C to stop.")

    worker.work(burst=settings.worker_burst)


if __name__ == "__main__":
    main()
