"""
worker/run_entity.py — Manual entry point for the entity extraction worker.

Usage:
    cd apps/worker
    python run_entity.py

Workflow:
    T1: redis-server
    T2: cd apps/api && uvicorn app.main:app --reload
    T3: cd apps/worker && python run.py               ← article worker
    T4: cd apps/worker && python run_sentiment.py      ← sentiment worker
    T5: cd apps/worker && python run_entity.py         ← entity worker (this)

Why a separate worker?
    Entity extraction uses spaCy NER (~10-50ms per article on CPU).
    Running it in a dedicated worker ensures:
    1. Zero impact on article ingestion or sentiment processing.
    2. The spaCy model is only loaded in this worker's memory.
    3. Can scale independently if article volume increases.
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
from packages.queue.queues import ENTITY_EXTRACTION_QUEUE_NAME


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
    logger.info("AI Financial Intelligence Platform — Entity Worker")
    logger.info("Redis  : %s", settings.redis_url)
    logger.info("Queue  : %s", ENTITY_EXTRACTION_QUEUE_NAME)
    logger.info("Model  : spaCy en_core_web_sm + alias normalization")
    logger.info("Burst  : %s", settings.worker_burst)
    logger.info("=" * 60)

    # Connect to Redis
    try:
        conn = get_redis_connection()
        conn.ping()
        logger.info("Redis connection OK")
    except Exception as exc:
        logger.error("Cannot connect to Redis: %s", exc)
        sys.exit(1)

    # Create and start the entity worker
    queues = [rq.Queue(ENTITY_EXTRACTION_QUEUE_NAME, connection=conn)]

    worker = SimpleWorker(
        queues=queues,
        connection=conn,
    )

    logger.info("Entity worker started. Listening on queue '%s'...", ENTITY_EXTRACTION_QUEUE_NAME)
    logger.info("Press Ctrl+C to stop.")

    worker.work(burst=settings.worker_burst)


if __name__ == "__main__":
    main()
