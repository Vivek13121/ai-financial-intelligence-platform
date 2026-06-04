"""
pipeline.py — Ingestion pipeline orchestrator.

Responsibility:
  Wires together the three layers of the ingestion service:

    1. Fetch  → ingest.fetchers.rss   (collect raw articles from RSS)
    2. Transform → ingest.services.transformer (clean and normalise)
    3. Send   → HTTP POST to backend API (store in PostgreSQL)

Why separate this from run.py?
  run.py is the CLI entry point — it sets up logging and calls run().
  pipeline.py is the business logic — testable without subprocess/CLI.
  This split means we can later call pipeline.run() from a queue
  consumer (Phase 3) or a FastAPI background task without any changes.

API client (httpx):
  We use httpx (synchronous client) rather than requests because httpx
  is actively maintained, has a clean context-manager API, and its
  async variant (AsyncClient) requires zero code changes to adopt later.
  For Phase 3 we'll switch to httpx.AsyncClient when running inside
  an async event loop.

Error handling strategy:
  - Network errors: logged as warnings, article skipped.
  - 4xx responses: logged as errors (likely a schema mismatch), skipped.
  - 5xx responses: logged as errors (backend problem), skipped.
  - We never raise — a broken article must not kill the entire run.
    Phase 3 will add retry logic via the queue.
"""

import logging
from typing import Iterator

import httpx

from ingest.config import settings
from ingest.fetchers.rss import RawArticle, fetch_all_feeds
from ingest.services.transformer import ArticlePayload, transform_many

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# API client helpers
# ---------------------------------------------------------------------------

def _post_article(client: httpx.Client, payload: ArticlePayload) -> bool:
    """
    POST a single ArticlePayload to the backend API.

    Returns True if the article was stored (HTTP 201), False otherwise.

    Why check for 201 specifically?
      Our API returns 201 Created for a successful POST /articles.
      Any other 2xx (e.g. 200) would indicate unexpected behaviour.
      We treat non-201 responses as failures so we notice API contract
      changes early.
    """
    url = f"{settings.api_base_url}/api/v1/articles/"
    body = payload.to_dict()

    try:
        response = client.post(url, json=body)
    except httpx.RequestError as exc:
        logger.warning(
            "Network error posting article '%s': %s",
            payload.title[:60],
            exc,
        )
        return False

    if response.status_code == 201:
        logger.debug("Stored: %s", payload.title[:80])
        return True

    # Log the full response body on failure to aid debugging
    logger.error(
        "Failed to store article '%s'. Status: %d. Body: %s",
        payload.title[:60],
        response.status_code,
        response.text[:200],
    )
    return False


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------

class IngestionResult:
    """
    Summary of a completed ingestion run.
    Useful for logging and later for monitoring dashboards.
    """
    __slots__ = ("fetched", "transformed", "stored", "failed")

    def __init__(self) -> None:
        self.fetched: int = 0
        self.transformed: int = 0
        self.stored: int = 0
        self.failed: int = 0

    def __repr__(self) -> str:
        return (
            f"IngestionResult("
            f"fetched={self.fetched}, "
            f"transformed={self.transformed}, "
            f"stored={self.stored}, "
            f"failed={self.failed})"
        )


def run() -> IngestionResult:
    """
    Execute a full ingestion cycle.

    Steps:
      1. Fetch all articles from registered RSS feeds.
      2. Collect raw articles into a list (so we can log total count).
      3. Transform into ArticlePayload objects.
      4. Open a single httpx.Client session (connection pooling) and POST
         each article to the backend API.

    Returns IngestionResult with counters for monitoring/logging.

    Note on batching:
      We POST one article at a time for now. This is deliberately simple.
      Phase 3 will introduce a queue + batch workers so the API is not
      the bottleneck. For a few hundred articles per run, individual
      POSTs are perfectly fine.
    """
    result = IngestionResult()

    # --- Step 1 & 2: Fetch ---
    logger.info("Starting ingestion run...")
    logger.info("Fetching from %d feed sources...", len(_get_feed_source_count()))

    raw_articles: list[RawArticle] = list(fetch_all_feeds())
    result.fetched = len(raw_articles)
    logger.info("Total raw articles fetched: %d", result.fetched)

    if not raw_articles:
        logger.warning("No articles fetched. Check feed URLs and network connectivity.")
        return result

    # --- Step 3: Transform ---
    payloads: list[ArticlePayload] = transform_many(raw_articles)
    result.transformed = len(payloads)

    if not payloads:
        logger.warning("No articles passed transformation. Check transformer logic.")
        return result

    # --- Step 4: Send to API ---
    logger.info(
        "Sending %d articles to backend API at %s...",
        result.transformed,
        settings.api_base_url,
    )

    with httpx.Client(timeout=settings.request_timeout_seconds) as client:
        for payload in payloads:
            success = _post_article(client, payload)
            if success:
                result.stored += 1
            else:
                result.failed += 1

    logger.info(
        "Ingestion run complete. "
        "Fetched: %d | Transformed: %d | Stored: %d | Failed: %d",
        result.fetched,
        result.transformed,
        result.stored,
        result.failed,
    )

    return result


def _get_feed_source_count() -> list:
    """Helper to import feed sources list for logging without circular imports."""
    from ingest.fetchers.rss import FEED_SOURCES
    return FEED_SOURCES
