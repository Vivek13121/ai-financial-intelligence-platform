"""
run.py — Manual entry point for the ingestion service.

Usage:
    # From apps/ingest/ directory:
    python run.py

    # With custom log level:
    LOG_LEVEL=DEBUG python run.py

    # Targeting a different backend:
    API_BASE_URL=http://staging-api:8000 python run.py

Why a separate run.py?
  - Keeps the ingest/ package importable without side effects.
    (importing ingest.pipeline does not trigger a run)
  - Clear, single entry point — anyone reading the code knows
    exactly where manual execution starts.
  - Easy to wrap with a cron job, task scheduler, or queue consumer
    in later phases without touching any business logic.

Logging setup:
  We configure the root logger here (only in the entry point).
  Library modules use getLogger(__name__) — they inherit the root config.
  Setting it only in run.py ensures logging is never double-configured
  when pipeline.py is imported by other callers (e.g., a queue worker).
"""

import logging
import sys

from ingest.config import settings
from ingest.pipeline import run


def setup_logging() -> None:
    """
    Configure root logger for the ingestion process.

    Format includes timestamp, level, and logger name so log lines
    are traceable to the exact module that produced them — essential
    when debugging multi-layer pipelines.
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
    logger.info("Backend API: %s", settings.api_base_url)
    logger.info("=" * 60)

    result = run()

    logger.info("=" * 60)
    logger.info("Run Summary")
    logger.info("  Fetched     : %d", result.fetched)
    logger.info("  Transformed : %d", result.transformed)
    logger.info("  Stored      : %d", result.stored)
    logger.info("  Failed      : %d", result.failed)
    logger.info("=" * 60)

    # Exit with non-zero code if everything failed (useful for CI/CD checks)
    if result.transformed > 0 and result.stored == 0:
        logger.error("All articles failed to store. Check backend API connectivity.")
        sys.exit(1)


if __name__ == "__main__":
    main()
