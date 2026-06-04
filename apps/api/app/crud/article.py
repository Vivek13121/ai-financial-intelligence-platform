"""
crud/article.py — Database operations for Articles.

Why a separate CRUD layer?
  Routers handle HTTP concerns: status codes, request parsing, response shaping.
  CRUD functions handle database concerns: queries, inserts, transactions.
  Keeping them separate means:
  - CRUD functions are testable without spinning up a full HTTP server.
  - Multiple routes can reuse the same CRUD function.
  - When we add background workers (Phase 3), they can call CRUD directly
    without going through HTTP.

Pagination in get_articles():
  `skip` and `limit` implement cursor-style pagination at the DB level.
  This is more efficient than fetching all rows and slicing in Python.
  Later we'll upgrade to keyset pagination for very large datasets.
"""

from typing import List

from sqlalchemy.orm import Session

from app.models.article import Article
from app.schemas.article import ArticleCreate


def create_article(db: Session, article_in: ArticleCreate) -> Article:
    """
    Insert a new article record and return the persisted ORM object.

    Steps:
      1. Convert the Pydantic schema to a dict and unpack into the ORM model.
      2. Add to the session (queues the INSERT).
      3. Commit the transaction (executes INSERT and persists to DB).
      4. Refresh to load DB-generated values (id, created_at).
    """
    db_article = Article(**article_in.model_dump())
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article


def get_articles(db: Session, skip: int = 0, limit: int = 20) -> List[Article]:
    """
    Return a paginated list of articles ordered by creation time (newest first).

    Args:
      skip:  number of rows to skip (for pagination offset).
      limit: maximum number of rows to return (capped in the router).
    """
    return (
        db.query(Article)
        .order_by(Article.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
