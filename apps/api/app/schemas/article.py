"""
schemas/article.py — Pydantic request and response schemas for Articles.

Why are schemas separate from ORM models?
  The ORM model (models/article.py) describes the DATABASE shape.
  The schema describes the API contract — what clients send and receive.
  Keeping them separate means:
  - We can add DB-only columns (e.g. internal flags) without exposing them.
  - We can rename/reshape API fields independently of the DB schema.
  - Pydantic validates and coerces incoming data before it ever touches the DB.

Schema hierarchy:
  ArticleBase      → shared fields (title, content, source, company, published_at)
  ArticleCreate    → what the client sends in POST /articles (inherits Base)
  ArticleResponse  → what the API returns (adds id, created_at)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ArticleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=512, description="Article headline")
    content: str = Field(..., min_length=1, description="Full article body text")
    source: Optional[str] = Field(None, max_length=256, description="Publisher name, e.g. 'Reuters'")
    company: Optional[str] = Field(None, max_length=256, description="Company mentioned, e.g. 'Apple'")
    published_at: Optional[datetime] = Field(None, description="Original publication timestamp (ISO 8601)")
    # article_url: link to the original article. Optional — manually created
    # articles may not have one. Used for deduplication and dashboard deep-links.
    article_url: Optional[str] = Field(None, description="Canonical URL of the source article")


class ArticleCreate(ArticleBase):
    """
    Request body for POST /articles.
    Inherits all fields from ArticleBase — no extra fields needed at creation.
    """
    pass


class ArticleResponse(ArticleBase):
    """
    Response shape for GET /articles and POST /articles.
    Adds server-generated fields: id and created_at.
    """
    id: UUID
    created_at: datetime

    class Config:
        # Allows Pydantic to read data from SQLAlchemy ORM objects directly
        # (i.e. model.id instead of model["id"]).
        from_attributes = True
