"""
crud/sentiment_result.py — Database operations for SentimentResult.

Why a CRUD module instead of writing SQL in the job function?
  1. Testability: CRUD functions can be unit-tested without HTTP or rq.
  2. Reuse: The API router and the worker both call the same function.
  3. Separation: Job functions handle orchestration; CRUD handles persistence.

Functions:
  create_sentiment_result  — insert a new result row.
  get_results_for_article  — fetch all results for one article (for API endpoint).
  get_latest_for_article   — fetch the most recent result for an article.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.sentiment_result import SentimentResult
from app.schemas.sentiment_result import SentimentResultCreate


def create_sentiment_result(
    db: Session,
    result_in: SentimentResultCreate,
) -> SentimentResult:
    """
    Insert a new SentimentResult row and return the persisted ORM object.

    Steps:
      1. Convert Pydantic schema → dict → ORM model.
      2. Add to session (queues the INSERT).
      3. Commit (executes INSERT, persists to DB).
      4. Refresh to load server-generated fields (id, processed_at).
    """
    db_result = SentimentResult(**result_in.model_dump())
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result


def get_results_for_article(
    db: Session,
    article_id: UUID,
) -> List[SentimentResult]:
    """
    Return all sentiment results for a given article, newest first.

    An article may have multiple results if:
      - Multiple models processed it (e.g. FinBERT + custom model).
      - It was reprocessed after a model update.
    """
    return (
        db.query(SentimentResult)
        .filter(SentimentResult.article_id == article_id)
        .order_by(SentimentResult.processed_at.desc())
        .all()
    )


def get_latest_for_article(
    db: Session,
    article_id: UUID,
) -> Optional[SentimentResult]:
    """
    Return the single most recent sentiment result for an article.
    Returns None if no results exist yet (article not yet processed).

    Useful for dashboard cards that only need one summary label.
    """
    return (
        db.query(SentimentResult)
        .filter(SentimentResult.article_id == article_id)
        .order_by(SentimentResult.processed_at.desc())
        .first()
    )
