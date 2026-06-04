"""
models/article.py — SQLAlchemy ORM model for the Article table.

Why UUID primary key?
  Auto-increment integers are fine for small apps but cause problems at scale:
  - They reveal how many records exist (security issue).
  - Merging data from multiple services or ingestion workers causes ID collisions.
  - UUIDs are globally unique — safe for distributed systems from day one.

Why separate `published_at` and `created_at`?
  - published_at: when the article was published by its source (may be NULL
    if the source doesn't provide it, or can be set retroactively).
  - created_at: when WE stored it in our database. Always set by the server.
  This distinction matters for time-series sentiment analysis — we'll want to
  plot sentiment over *publication* time, not ingestion time.

How it fits the architecture:
  This table is the first landing zone for all financial news articles.
  Later, a separate SentimentResult table will reference this via FK.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    title = Column(String(512), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(256), nullable=True)   # e.g. "Reuters", "Bloomberg"
    company = Column(String(256), nullable=True)   # e.g. "Apple", "TSLA"
    published_at = Column(DateTime(timezone=True), nullable=True)
    # article_url: canonical link to the original news article.
    # Nullable — manually created articles may not have a URL.
    # Used for deduplication in Phase 3 and deep-linking in the dashboard.
    article_url = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Article id={self.id} title={self.title!r}>"
