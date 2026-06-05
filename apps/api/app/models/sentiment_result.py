"""
models/sentiment_result.py — SQLAlchemy ORM for the sentiment_results table.

Why a separate table instead of columns on `articles`?
  An article can be processed by multiple models over its lifetime:
    - Phase 4: FinBERT  (financial BERT)
    - Phase 6: Custom fine-tuned model
    - Phase 7: Ensemble / re-run after model update
  If we put sentiment columns directly on `articles`, each model update
  requires an ALTER TABLE and overwrites previous results.
  A separate table with `model_name` column keeps ALL historical results
  and lets us compare models side-by-side.

Why `article_id` as a FK instead of embedding the article text again?
  The job passes only the UUID — the worker fetches the article text from DB.
  This avoids duplicating content in the queue payload (which could be large)
  and ensures sentiment is always computed against the canonical stored text.

Indexes:
  article_id is indexed because the most common query will be:
    "give me all sentiment results for article X"
  processed_at is set server-side (db default) so it's always accurate
  even if the worker's clock drifts.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class SentimentResult(Base):
    __tablename__ = "sentiment_results"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    # Foreign key to the article this result belongs to.
    # ON DELETE CASCADE: if the article is deleted, its sentiment results go too.
    article_id = Column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,           # fast lookup by article
    )
    # "positive" | "negative" | "neutral"
    sentiment_label = Column(String(16), nullable=False)

    # Confidence score from the model's softmax output (0.0 – 1.0).
    # Stored as Float (double precision in PG) for full precision.
    score = Column(Float, nullable=False)

    # Which model produced this result — essential for comparing model versions.
    # e.g. "ProsusAI/finbert", "custom-finbert-v2"
    model_name = Column(String(128), nullable=False, default="ProsusAI/finbert")

    # Set by the database on INSERT — always accurate regardless of worker clock.
    processed_at = Column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<SentimentResult article={self.article_id} "
            f"label={self.sentiment_label!r} score={self.score:.3f}>"
        )
