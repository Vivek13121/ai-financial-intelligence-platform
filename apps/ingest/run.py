"""
run.py — Manual entry point for the ingestion service (Phase 3).

Usage:
    # From apps/ingest/ directory:
    python run.py

    # With verbose output:
    LOG_LEVEL=DEBUG python run.py

Phase 3 change:
  Summary now shows 'Queued' instead of 'Stored'.
  The ingest service no longer stores articles — it pushes jobs to Redis.
  The worker service (apps/worker/) is responsible for storage.

Workflow:
  Terminal 1:  cd apps/worker && python run.py    ← start worker first
  Terminal 2:  cd apps/ingest && python run.py    ← then run ingest
"""

import logging
import sys

from ingest.config import settings
from ingest.pipeline import run


def setup_logging() -> None:
    """
    Configure root logger for the ingestion process.

    Format includes timestamp, level, and logger name so log lines
    are traceable to the exact module that produced them.
    """
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
    logger.info("AI Financial Intelligence Platform — Ingestion Service")
    logger.info("Redis: %s", settings.redis_url)
    logger.info("=" * 60)

    result = run()

    logger.info("=" * 60)
    logger.info("Run Summary")
    logger.info("  Fetched     : %d", result.fetched)
    logger.info("  Transformed : %d", result.transformed)
    logger.info("  Queued      : %d", result.queued)
    logger.info("  Failed      : %d", result.failed)
    logger.info("=" * 60)

    # Exit non-zero if everything failed to enqueue
    if result.transformed > 0 and result.queued == 0:
        logger.error(
            "All articles failed to enqueue. "
            "Is Redis running? (redis-server)"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
