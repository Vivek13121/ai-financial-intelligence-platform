"""
worker/run.py — Manual entry point for the worker service.

Usage:
    # Start the worker (run indefinitely, consume from article_ingest queue):
    cd apps/worker
    python run.py

    # Burst mode (process all queued jobs, then exit — useful for testing):
    WORKER_BURST=true python run.py

    # With debug logging:
    LOG_LEVEL=DEBUG python run.py

Workflow:
    Terminal 1: cd apps/worker && python run.py   ← start FIRST
    Terminal 2: cd apps/ingest && python run.py   ← then run ingest

How rq.Worker works:
    - Connects to Redis and subscribes to the specified queue(s).
    - When a job arrives, it forks a child process to execute it.
    - The child imports the job function by its dotted string path
      (e.g. "worker.jobs.article_job.store_article_job").
    - If the job raises, the child exits non-zero → rq marks as failed
      and schedules a retry (based on Retry config set during enqueue).
    - The parent process waits for the child and picks up the next job.

Why fork-based execution?
    Forking isolates job failures — a crash in one job does not kill
    the worker process itself. The worker keeps running and consuming.

PYTHONPATH setup:
    This script adds:
      - monorepo root (for 'import packages.queue')
      - apps/api     (for 'import app.database', 'import app.crud')
      - apps/worker  (for 'import worker.jobs.article_job')
    before any imports so rq can resolve all job function paths.
"""

import logging
import os
import sys

# ---------------------------------------------------------------------------
# PYTHONPATH: must be set BEFORE importing anything that touches app/ or packages/
# ---------------------------------------------------------------------------
_here = os.path.dirname(os.path.abspath(__file__))              # apps/worker/
_apps_root = os.path.abspath(os.path.join(_here, ".."))         # apps/
_repo_root = os.path.abspath(os.path.join(_here, "..", ".."))   # monorepo root
_api_root = os.path.join(_repo_root, "apps", "api")             # apps/api/

# sys.path needs:
#   _repo_root  → enables 'import packages.queue'
#   _apps_root  → enables 'import worker.config', 'import worker.jobs.*'
#   _api_root   → enables 'import app.database', 'import app.crud', 'import app.models'
for _path in [_repo_root, _apps_root, _api_root]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

# ---------------------------------------------------------------------------
# Imports (after PYTHONPATH is set)
# ---------------------------------------------------------------------------
import rq
from rq import SimpleWorker  # Windows-compatible: no os.fork() required

from worker.config import settings
from packages.queue.connection import get_redis_connection
from packages.queue.queues import ARTICLE_INGEST_QUEUE_NAME


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
    logger.info("AI Financial Intelligence Platform — Worker Service")
    logger.info("Redis : %s", settings.redis_url)
    logger.info("Queue : %s", ARTICLE_INGEST_QUEUE_NAME)
    logger.info("Burst : %s", settings.worker_burst)
    logger.info("=" * 60)

    # Connect to Redis
    try:
        conn = get_redis_connection()
        conn.ping()
        logger.info("Redis connection OK")
    except Exception as exc:
        logger.error("Cannot connect to Redis: %s", exc)
        logger.error("Start Redis with: redis-server")
        sys.exit(1)

    # Create and start the worker
    # NOTE: SimpleWorker is used instead of Worker because Windows does not
    # support os.fork(). SimpleWorker runs jobs in the same process (thread-
    # based) rather than forking a child. This is slightly less isolated but
    # fully functional for development. In production on Linux, swap back to
    # Worker for process isolation.
    queues = [rq.Queue(ARTICLE_INGEST_QUEUE_NAME, connection=conn)]

    worker = SimpleWorker(
        queues=queues,
        connection=conn,
    )

    logger.info(
        "Worker started. Listening on queue '%s'...",
        ARTICLE_INGEST_QUEUE_NAME,
    )
    logger.info("Press Ctrl+C to stop.")

    worker.work(burst=settings.worker_burst)


if __name__ == "__main__":
    main()
