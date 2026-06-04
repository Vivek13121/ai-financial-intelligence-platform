"""
fetchers/rss.py — RSS/Atom feed fetcher layer.

Responsibility:
  This module ONLY fetches and parses RSS feeds. It returns raw,
  unvalidated data dictionaries — it does NOT transform into internal
  schemas. That is the service layer's job.

Why feedparser?
  feedparser is the de facto standard for RSS/Atom parsing in Python.
  It handles RSS 0.9x, 1.0, 2.0, and Atom 0.3/1.0 transparently,
  deals with encoding issues, bozo feeds (malformed XML), and network
  errors gracefully. Used in production systems for 20+ years.

Why return raw dicts instead of dataclasses?
  Keeping the fetcher output as plain dicts avoids tight coupling.
  If we swap feedparser for a different library later, only this file
  changes — the service layer stays untouched.

Feed sources chosen:
  - Reuters Business: authoritative, high-frequency, well-structured
  - Yahoo Finance: broad coverage, large volume
  - MarketWatch: market-focused, real-time oriented
  - CNBC Finance: widely cited, business news authority
  - Seeking Alpha: analyst opinions, earnings commentary

  All are free, publicly accessible RSS feeds — no API key required.
"""

import logging
from dataclasses import dataclass
from typing import Iterator

import feedparser

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Feed registry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FeedSource:
    """
    Represents a single RSS feed source.

    name : human-readable publisher label (becomes the 'source' field in the DB)
    url  : public RSS/Atom feed URL
    """
    name: str
    url: str


# Registry of financial news RSS feeds.
# Adding a new source = adding one line here. No other code changes needed.
FEED_SOURCES: list[FeedSource] = [
    FeedSource(
        name="Reuters Business",
        url="https://feeds.reuters.com/reuters/businessNews",
    ),
    FeedSource(
        name="Yahoo Finance",
        url="https://finance.yahoo.com/news/rssindex",
    ),
    FeedSource(
        name="MarketWatch",
        url="https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines",
    ),
    FeedSource(
        name="CNBC Finance",
        url="https://www.cnbc.com/id/10001147/device/rss/rss.html",
    ),
    FeedSource(
        name="Seeking Alpha",
        url="https://seekingalpha.com/market_currents.xml",
    ),
]


# ---------------------------------------------------------------------------
# Raw article type
# ---------------------------------------------------------------------------

@dataclass
class RawArticle:
    """
    Minimal raw representation of a fetched RSS entry.

    All fields are Optional[str] because RSS feeds are inconsistent —
    some omit summaries, some have no dates. The transformer layer
    handles defaults and coercion.

    source_name : the FeedSource.name this article came from
    title       : article headline (from <title>)
    summary     : article body/summary (from <summary> or <description>)
    link        : canonical URL of the article (from <link>)
    published   : raw published date string (from <published> or <pubDate>)
    """
    source_name: str
    title: str | None
    summary: str | None
    link: str | None
    published: str | None


# ---------------------------------------------------------------------------
# Fetcher
# ---------------------------------------------------------------------------

def fetch_feed(source: FeedSource) -> list[RawArticle]:
    """
    Fetch and parse a single RSS feed.

    Returns a list of RawArticle objects. Returns an empty list on any
    network or parse error (logged as a warning, not raised) so that
    one broken feed does not abort the entire ingestion run.

    feedparser.parse() behaviour:
      - Makes an HTTP GET internally (no extra httpx call needed here).
      - bozo=True means the feed was malformed; we still try to process
        any entries feedparser managed to extract.
      - Each entry is a dict-like object; we use .get() for safety.
    """
    logger.info("Fetching feed: %s (%s)", source.name, source.url)

    try:
        parsed = feedparser.parse(source.url)
    except Exception as exc:
        logger.warning("Failed to fetch feed '%s': %s", source.name, exc)
        return []

    if parsed.bozo:
        # bozo_exception is set when the XML was malformed.
        # We log but continue — feedparser often recovers partial data.
        logger.warning(
            "Feed '%s' is malformed (bozo=True): %s",
            source.name,
            parsed.bozo_exception,
        )

    entries = parsed.get("entries", [])
    logger.info("Fetched %d entries from '%s'", len(entries), source.name)

    raw_articles: list[RawArticle] = []
    for entry in entries:
        raw_articles.append(
            RawArticle(
                source_name=source.name,
                title=entry.get("title"),
                summary=entry.get("summary") or entry.get("description"),
                link=entry.get("link"),
                # feedparser normalises dates into 'published' (Atom) or
                # exposes the raw string in 'published' as well.
                published=entry.get("published"),
            )
        )

    return raw_articles


def fetch_all_feeds() -> Iterator[RawArticle]:
    """
    Iterate over all registered feed sources and yield RawArticle objects.

    Using a generator (yield from) means:
      - Articles from each feed are available immediately.
      - Memory usage stays constant regardless of total article count.
      - A slow/broken feed does not delay articles from other feeds
        (they are processed sequentially, not in parallel — Phase 3
        will introduce async/queue-based parallelism).
    """
    for source in FEED_SOURCES:
        articles = fetch_feed(source)
        yield from articles
