"""
scheduler/run.py — Continuous pipeline scheduler.

Responsibility:
  Automate the pipeline by triggering ingestion and forecast jobs at set intervals.
  Runs as an independent service alongside the API and workers.
"""

import os
import sys
import time
import logging
import schedule

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_here = os.path.dirname(os.path.abspath(__file__))              # apps/scheduler/
_apps_root = os.path.abspath(os.path.join(_here, ".."))         # apps/
_repo_root = os.path.abspath(os.path.join(_here, "..", ".."))   # monorepo root
_api_root = os.path.join(_repo_root, "apps", "api")             # apps/api/
_ingest_root = os.path.join(_repo_root, "apps", "ingest")       # apps/ingest/

for _path in [_repo_root, _apps_root, _api_root, _ingest_root]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

# Ensure config loaded before importing pipelines
import ingest.config
from packages.queue.queues import get_forecast_queue

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("scheduler")

# ---------------------------------------------------------------------------
# Job Definitions
# ---------------------------------------------------------------------------

def run_ingestion():
    """Trigger the ingestion pipeline to fetch, transform, and queue new articles."""
    logger.info("TRIGGERING INGESTION PIPELINE")
    try:
        from ingest.pipeline import run
        result = run()
        logger.info(
            "Ingestion completed. Fetched: %d | Transformed: %d | Queued: %d | Failed: %d",
            result.fetched, result.transformed, result.queued, result.failed
        )
    except Exception as e:
        logger.error("Failed to run ingestion: %s", e)


def run_forecast():
    """Trigger a new forecast job by enqueueing it."""
    logger.info("TRIGGERING FORECAST JOB")
    try:
        queue = get_forecast_queue()
        # Enqueue the job string, ensuring the worker handles imports
        job = queue.enqueue("apps.worker.jobs.forecast_job.run_forecast_job")
        logger.info("Forecast job enqueued successfully (Job ID: %s)", job.id)
    except Exception as e:
        logger.error("Failed to enqueue forecast job: %s", e)

# ---------------------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------------------

def main():
    logger.info("=" * 60)
    logger.info("AI Financial Intelligence Platform — Scheduler Service")
    logger.info("=" * 60)

    # Configurable Intervals
    ingest_minutes = int(os.getenv("INGEST_INTERVAL_MINUTES", "5"))
    forecast_hours = int(os.getenv("FORECAST_INTERVAL_HOURS", "1"))

    logger.info("Scheduling Ingestion every %d minutes.", ingest_minutes)
    logger.info("Scheduling Forecast every %d hours.", forecast_hours)

    schedule.every(ingest_minutes).minutes.do(run_ingestion)
    schedule.every(forecast_hours).hours.do(run_forecast)

    # Initial run on startup
    logger.info("Running initial startup jobs...")
    run_ingestion()
    # run_forecast() # Optional: Run immediately, or wait for next interval to avoid heavy load on startup

    logger.info("Scheduler loop started. Press CTRL+C to quit.")

    import redis
    from datetime import datetime
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        r = redis.Redis.from_url(redis_url)
    except Exception as e:
        logger.error("Failed to connect to Redis for heartbeat: %s", e)
        r = None

    while True:
        try:
            if r:
                r.set("scheduler:heartbeat", datetime.utcnow().isoformat())
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user.")
            break
        except Exception as e:
            logger.error("Unexpected error in scheduler loop: %s", e)
            time.sleep(5) # Avoid tight error loop

if __name__ == "__main__":
    main()
