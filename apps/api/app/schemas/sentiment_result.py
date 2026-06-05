"""
schemas/sentiment_result.py — Pydantic request/response schemas for SentimentResult.

Schema hierarchy (mirrors the article schema pattern):
  SentimentResultBase   → shared fields
  SentimentResultCreate → what the sentiment worker sends when storing a result
  SentimentResultResponse → what the API returns to external clients

Why include model_name in the response?
  So API consumers can filter/compare results from different models.
  If we run both FinBERT and a custom model on the same article, the
  client can distinguish them without knowing internal IDs.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SentimentResultBase(BaseModel):
    # Suppress Pydantic v2 warning: 'model_name' starts with 'model_' which
    # conflicts with Pydantic's protected namespace. protected_namespaces=()
    # disables this check — our field is not a Pydantic internal.
    model_config = {"protected_namespaces": ()}

    article_id: UUID = Field(..., description="UUID of the article this result belongs to")
    sentiment_label: str = Field(
        ...,
        description="Sentiment classification: 'positive', 'negative', or 'neutral'",
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence score (0.0 – 1.0)",
    )
    model_name: str = Field(
        default="ProsusAI/finbert",
        max_length=128,
        description="HuggingFace model identifier that produced this result",
    )


class SentimentResultCreate(SentimentResultBase):
    """
    Payload sent by the sentiment worker to create a new result row.
    Inherits all fields from SentimentResultBase.
    """
    pass


class SentimentResultResponse(SentimentResultBase):
    """
    Response shape returned by GET /articles/{id}/sentiment.
    Adds server-generated fields: id and processed_at.
    """
    id: UUID
    processed_at: datetime

    class Config:
        from_attributes = True   # read from SQLAlchemy ORM objects directly
