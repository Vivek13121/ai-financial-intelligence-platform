"""
services/transformer.py — transforms RawArticle → ArticlePayload.

Responsibility:
  This layer owns the data-cleaning and normalization logic. It bridges
  the gap between "what the external world gives us" (inconsistent RSS
  data) and "what our backend API expects" (a clean, validated payload).

Why not transform inside the fetcher?
  The fetcher's job is I/O: go get data. The transformer's job is
  logic: make the data correct. Separating them means:
    - We can unit test transformation without network calls.
    - We can plug in different fetchers (paid APIs, WebSockets) without
      touching any transformation logic.
    - Each layer has one clear reason to change.

Transform decisions made here:
  title     : strip whitespace; skip if empty after stripping.
  content   : use summary; strip HTML tags (RSS often embeds HTML in
              <description>); fall back to title if summary is missing.
  source    : taken directly from RawArticle.source_name.
  published_at : parse with dateutil.parser which handles dozens of
                 date formats (RFC 2822, ISO 8601, and many variations).
                 Falls back to None — the DB column is nullable.
  article_url : taken from RawArticle.link.
  company   : left as None for now (Phase 5 adds NER-based extraction).
"""

import logging
import re
from datetime import datetime, timezone
from typing import Optional

from dateutil import parser as dateutil_parser

from ingest.fetchers.rss import RawArticle

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal article payload (mirrors backend ArticleCreate schema)
# ---------------------------------------------------------------------------

class ArticlePayload:
    """
    Clean, validated representation of a news article ready to be sent
    to the backend POST /api/v1/articles endpoint.

    Why not use a Pydantic model?
      We could, and it would give us free validation. For now a plain
      dataclass keeps the dependency surface small. When we add
      deduplication or enrichment services, migrating to Pydantic here
      is a one-line change.

    Fields match ArticleCreate in apps/api/app/schemas/article.py exactly
    so the JSON payload is accepted without modification.
    """

    __slots__ = (
        "title",
        "content",
        "source",
        "company",
        "published_at",
        "article_url",
    )

    def __init__(
        self,
        title: str,
        content: str,
        source: Optional[str],
        company: Optional[str],
        published_at: Optional[datetime],
        article_url: Optional[str],
    ) -> None:
        self.title = title
        self.content = content
        self.source = source
        self.company = company
        self.published_at = published_at
        self.article_url = article_url

    def to_dict(self) -> dict:
        """
        Serialize to a plain dict for JSON POST body.
        datetime is converted to ISO 8601 string (FastAPI accepts this).
        None values are included so the API can apply its own defaults.
        """
        return {
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "company": self.company,
            "published_at": (
                self.published_at.isoformat() if self.published_at else None
            ),
            "article_url": self.article_url,
        }

    def __repr__(self) -> str:
        return (
            f"ArticlePayload(source={self.source!r}, "
            f"title={self.title[:60]!r}...)"
        )


# ---------------------------------------------------------------------------
# HTML stripping helper
# ---------------------------------------------------------------------------

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def _strip_html(text: str) -> str:
    """
    Remove HTML tags from a string and collapse whitespace.

    RSS <description> fields often contain embedded HTML like:
      <p>Apple reported record quarterly <b>revenue</b>...</p>
    We want plain text for the database and later NLP processing.

    Why not use BeautifulSoup?
      For simple tag stripping a regex is fast and dependency-free.
      If we later need to handle entities (&amp; → &) or complex
      nested HTML, we can swap this for BeautifulSoup with no
      interface change.
    """
    no_tags = _HTML_TAG_RE.sub(" ", text)
    collapsed = _WHITESPACE_RE.sub(" ", no_tags)
    return collapsed.strip()


# ---------------------------------------------------------------------------
# Date parsing helper
# ---------------------------------------------------------------------------

def _parse_date(raw_date: Optional[str]) -> Optional[datetime]:
    """
    Parse an RSS date string into a timezone-aware datetime.

    RSS dates arrive in many formats:
      - RFC 2822: "Thu, 04 Jun 2026 06:00:00 +0000"   (RSS 2.0)
      - ISO 8601: "2026-06-04T06:00:00Z"              (Atom)
      - Ambiguous: "4 Jun 2026 06:00:00 GMT"          (non-standard)

    dateutil.parser.parse handles all of these.
    We normalise to UTC so all timestamps in the DB are comparable.
    Returns None if parsing fails so the article is still stored.
    """
    if not raw_date:
        return None
    try:
        dt = dateutil_parser.parse(raw_date)
        # Make timezone-aware if naive (assume UTC for RSS feeds)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, OverflowError) as exc:
        logger.debug("Could not parse date '%s': %s", raw_date, exc)
        return None


# ---------------------------------------------------------------------------
# Transformer
# ---------------------------------------------------------------------------

def transform(raw: RawArticle) -> Optional[ArticlePayload]:
    """
    Transform a RawArticle into an ArticlePayload.

    Returns None if the article cannot produce a valid payload
    (e.g. missing title). Callers should skip None results.

    Transform steps:
      1. Validate title exists and is non-empty.
      2. Build content from summary (HTML-stripped) or fall back to title.
      3. Parse date with dateutil.
      4. Pass source name and URL through directly.
      5. Leave company as None (NER comes in Phase 5).
    """
    # --- Title ---
    title = (raw.title or "").strip()
    if not title:
        logger.debug(
            "Skipping article from '%s': missing title", raw.source_name
        )
        return None

    # --- Content ---
    if raw.summary:
        content = _strip_html(raw.summary)
    else:
        # Some feeds provide no summary at all — use the title as a
        # minimal stand-in so the article is still stored.
        content = title
        logger.debug(
            "Article from '%s' has no summary; using title as content. "
            "Title: %s",
            raw.source_name,
            title[:80],
        )

    # Ensure content is not empty after stripping
    if not content:
        content = title

    # --- Published date ---
    published_at = _parse_date(raw.published)

    return ArticlePayload(
        title=title,
        content=content,
        source=raw.source_name,
        company=None,           # Phase 5: NER will populate this
        published_at=published_at,
        article_url=raw.link,
    )


def transform_many(
    raw_articles: list[RawArticle],
) -> list[ArticlePayload]:
    """
    Transform a list of RawArticles into valid ArticlePayloads.

    Invalid articles (transform returns None) are silently dropped and
    a count is logged so we can monitor data quality over time.
    """
    payloads: list[ArticlePayload] = []
    skipped = 0

    for raw in raw_articles:
        payload = transform(raw)
        if payload is not None:
            payloads.append(payload)
        else:
            skipped += 1

    if skipped:
        logger.info("Skipped %d invalid articles during transformation", skipped)

    logger.info("Transformed %d articles successfully", len(payloads))
    return payloads
