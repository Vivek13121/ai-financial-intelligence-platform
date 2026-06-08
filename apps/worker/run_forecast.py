"""
worker/run_forecast.py — Entry point for the sentiment forecasting worker.

Responsibility:
  Listen on the `forecast_generation` queue and execute forecast jobs.
  This is a separate worker from article ingestion and sentiment processing
  because Prophet training can be CPU-intensive and we don't want it to
  block live article ingestion or FinBERT inference.
"""

import logging
import sys
import os
from pathlib import Path

import rq
from rq import SimpleWorker

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
# The worker runs in apps/worker/ but needs to import from apps/api/app/
# and packages/queue/. We add the repository root to sys.path.
_here = os.path.dirname(os.path.abspath(__file__))              # apps/worker/
_apps_root = os.path.abspath(os.path.join(_here, ".."))         # apps/
_repo_root = os.path.abspath(os.path.join(_here, "..", ".."))   # monorepo root
_api_root = os.path.join(_repo_root, "apps", "api")             # apps/api/

for _path in [_repo_root, _apps_root, _api_root]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from packages.queue.queues import get_forecast_queue

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("forecast_worker")


def main():
    """
    Start the forecast worker.
    """
    logger.info("Starting forecast worker...")

    queue = get_forecast_queue()
    logger.info("Listening on queue: %s", queue.name)

    # Use SimpleWorker because Windows does not support os.fork() which the
    # default rq.Worker relies on.
    worker = SimpleWorker([queue], connection=queue.connection)
    
    try:
        worker.work(with_scheduler=True)
    except KeyboardInterrupt:
        logger.info("Worker stopped by user.")


if __name__ == "__main__":
    main()
