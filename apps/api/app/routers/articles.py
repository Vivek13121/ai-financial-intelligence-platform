"""
routers/articles.py — HTTP routes for the Article resource.

Why APIRouter instead of putting routes directly in main.py?
  APIRouter is FastAPI's way of grouping related routes into a module.
  main.py stays clean (it just mounts routers). As we add more resources
  (SentimentResult, Forecast, etc.) each gets its own router file.

Route design:
  POST /articles  → 201 Created with the full article response.
  GET  /articles  → 200 OK with a list, paginated via ?skip and ?limit.

Status code 201:
  Returning 201 (Created) instead of 200 for POST is the correct REST
  convention — it signals that a new resource was created on the server.

Query parameter limits:
  `limit` is capped at 100 to prevent clients from accidentally requesting
  tens of thousands of rows. This is a basic safeguard before we add
  proper pagination tokens.
"""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas.article import ArticleCreate, ArticleResponse

router = APIRouter(
    prefix="/articles",
    tags=["Articles"],
)


@router.post(
    "/",
    response_model=ArticleResponse,
    status_code=201,
    summary="Create a new article",
    description="Accepts a financial news article and persists it to the database.",
)
def create_article(
    article_in: ArticleCreate,
    db: Session = Depends(get_db),
):
    return crud.article.create_article(db=db, article_in=article_in)


@router.get(
    "/",
    response_model=List[ArticleResponse],
    summary="List articles",
    description="Returns a paginated list of articles ordered by newest first.",
)
def list_articles(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
    db: Session = Depends(get_db),
):
    return crud.article.get_articles(db=db, skip=skip, limit=limit)
