from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.analytics import AnalyticsStats, ActivityEvent, TimeSeriesDataPoint, TopicStats
from app.crud.analytics import get_stats, get_activity_feed

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)

@router.get("/stats", response_model=AnalyticsStats)
def get_analytics_stats(db: Session = Depends(get_db)):
    """
    Returns aggregate statistics for the dashboard.
    """
    return get_stats(db)

@router.get("/activity-feed", response_model=List[ActivityEvent])
def get_recent_activity(limit: int = 10, db: Session = Depends(get_db)):
    """
    Returns a unified feed of recent pipeline activity.
    """
    return get_activity_feed(db, limit=limit)

from typing import Dict, Any

@router.get("/timeseries", response_model=List[TimeSeriesDataPoint])
def get_analytics_timeseries(days: int = 30, db: Session = Depends(get_db)):
    """
    Returns historical timeseries data for charts.
    """
    from app.crud.analytics import get_timeseries
    return get_timeseries(db, days=days)

@router.get("/topics", response_model=Dict[str, List[TopicStats]])
def get_analytics_topics(days: int = 7, db: Session = Depends(get_db)):
    """
    Returns top positive and negative topics.
    """
    from app.crud.analytics import get_topics
    return get_topics(db, days=days)
