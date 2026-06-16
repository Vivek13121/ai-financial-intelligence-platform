"""
scripts/backfill_entities.py — One-off script to enqueue entity extraction
for all existing articles.

Usage:
    cd <repo_root>
    $env:PYTHONPATH="d:\ai sentiment analysis"
    python scripts/backfill_entities.py

This script queries all article IDs from the database and pushes each one
into the entity_extraction queue. The entity worker (run_entity.py)
processes them asynchronously. The entity_job is idempotent — articles
that already have entities will be skipped.
"""

import os
import sys
import logging

# Setup paths
_here = os.path.dirname(os.path.abspath(__file__))
_repo_root = os.path.abspath(os.path.join(_here, ".."))
_api_root = os.path.join(_repo_root, "apps", "api")

for _path in [_repo_root, _api_root]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def main():
    from app.database import SessionLocal
    from app.models.article import Article
    from packages.queue.queues import get_entity_queue
    from rq import Retry as RqRetry

    logger.info("=" * 60)
    logger.info("Entity Backfill Script")
    logger.info("=" * 60)

    # Get all article IDs
    db = SessionLocal()
    try:
        article_ids = [str(row[0]) for row in db.query(Article.id).all()]
        logger.info("Found %d articles to backfill.", len(article_ids))
    finally:
        db.close()

    if not article_ids:
        logger.info("No articles found. Nothing to do.")
        return

    # Enqueue all articles into the entity queue
    entity_queue = get_entity_queue()
    enqueued = 0

    for article_id in article_ids:
        try:
            entity_queue.enqueue(
                "worker.jobs.entity_job.run_entity_job",
                article_id,
                retry=RqRetry(max=2, interval=[10, 30]),
                job_timeout=120,
            )
            enqueued += 1
        except Exception as exc:
            logger.error("Failed to enqueue article_id=%s: %s", article_id, exc)

    logger.info("Backfill complete: %d / %d articles enqueued.", enqueued, len(article_ids))
    logger.info("Start the entity worker (run_entity.py) to process them.")


if __name__ == "__main__":
    main()
