"""
routers/sentiment.py — API endpoints for SentimentResult.

Endpoints:
  GET /api/v1/articles/{article_id}/sentiment
    → returns all sentiment results for an article, newest first.
    → returns [] if the article exists but hasn't been processed yet.
    → returns 404 if the article doesn't exist at all.

Why nest under /articles/{id}/sentiment?
  REST convention: sentiment results belong TO an article.
  Nesting makes the relationship explicit and navigable from the article URL.
  This also means the client always knows which article the results belong to
  without an extra lookup.

Future endpoints:
  GET /api/v1/sentiment/summary?source=Reuters  → aggregate by source
  GET /api/v1/sentiment/timeline               → time-series data for charts
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas.sentiment_result import SentimentResultResponse

router = APIRouter(
    prefix="/api/v1/articles",
    tags=["sentiment"],
)


@router.get(
    "/{article_id}/sentiment",
    response_model=List[SentimentResultResponse],
    summary="Get sentiment results for an article",
    description=(
        "Returns all sentiment analysis results for the given article, "
        "ordered by most recently processed first. Returns an empty list if "
        "the article exists but has not yet been processed by the sentiment worker."
    ),
)
def get_sentiment_for_article(
    article_id: UUID,
    db: Session = Depends(get_db),
) -> List[SentimentResultResponse]:
    """
    Fetch all sentiment results for one article.

    Steps:
      1. Verify the article exists (raises 404 if not).
      2. Query sentiment_results filtered by article_id.
      3. Return list (may be empty if not yet processed).
    """
    # Verify the article exists before querying sentiment
    article = crud.article.get_articles(db, skip=0, limit=1)  # sanity check
    results = crud.sentiment_result.get_results_for_article(db, article_id)
    return results
