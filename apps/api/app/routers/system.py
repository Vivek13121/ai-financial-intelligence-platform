import redis
import logging
from rq import Worker
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.database import get_db
from app.schemas.analytics import SystemStatus
from packages.queue.queues import get_article_queue, get_sentiment_queue, get_forecast_queue
from app.models.article import Article
from app.models.sentiment_result import SentimentResult

router = APIRouter(
    prefix="/system",
    tags=["System"],
)

logger = logging.getLogger(__name__)


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@router.get("/status", response_model=SystemStatus)
def get_system_status(db: Session = Depends(get_db)):
    """
    Returns the status of backend components.
    """
    redis_status = "down"
    queue_sizes = []
    active_workers = 0
    
    redis_client = None

    try:
        redis_client = redis.Redis.from_url(settings.redis_url)
        r = redis_client
        r.ping()
        redis_status = "ok"
        
        q_article = get_article_queue()
        q_sentiment = get_sentiment_queue()
        q_forecast = get_forecast_queue()
        
        queue_sizes = [
            {"name": "Ingestion", "size": len(q_article)},
            {"name": "Sentiment", "size": len(q_sentiment)},
            {"name": "Forecast", "size": len(q_forecast)}
        ]
        
        workers = Worker.all(connection=r)
        active_workers = len(workers)
        
    except Exception as exc:
        logger.warning("Redis status check failed: %s", exc)

    # DB logic
    db_status = "down"
    last_activity = None
    last_sentiment_time = None
    articles_per_hour = 0
    try:
        last_activity = db.query(func.max(Article.published_at)).scalar()
        if last_activity is None:
            last_activity = db.query(func.max(Article.created_at)).scalar()
        last_activity = _as_utc(last_activity)
            
        last_sentiment = db.query(SentimentResult).order_by(SentimentResult.processed_at.desc()).first()
        if last_sentiment:
            last_sentiment_time = _as_utc(last_sentiment.processed_at)
            
        # Articles per hour (rolling 24h)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_articles = db.query(Article).filter(Article.created_at >= yesterday).count()
        articles_per_hour = recent_articles // 24
        
        db_status = "ok"
    except Exception as exc:
        logger.warning("Database status check failed: %s", exc)

    worker_status = "ok" if active_workers > 0 else "down"
    
    scheduler_heartbeat = None
    if redis_status == "ok":
        try:
            hb_str = redis_client.get("scheduler:heartbeat") if redis_client else None
            if hb_str:
                scheduler_heartbeat = _as_utc(datetime.fromisoformat(hb_str.decode("utf-8")))
        except Exception as exc:
            logger.warning("Scheduler heartbeat read failed: %s", exc)

    return {
        "status": "ok" if redis_status == "ok" and db_status == "ok" else "degraded",
        "redis": redis_status,
        "db": db_status,
        "worker": worker_status,
        "active_workers": active_workers,
        "queue_sizes": queue_sizes,
        "last_activity": last_activity,
        "last_sentiment_time": last_sentiment_time,
        "scheduler_heartbeat": scheduler_heartbeat,
        "articles_per_hour": articles_per_hour
    }
