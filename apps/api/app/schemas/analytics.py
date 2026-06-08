from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

class QueueStatus(BaseModel):
    name: str
    size: int

class SystemStatus(BaseModel):
    status: str
    redis: str
    db: str
    worker: str
    active_workers: int
    queue_sizes: List[QueueStatus]
    last_activity: Optional[datetime]
    last_sentiment_time: Optional[datetime]
    scheduler_heartbeat: Optional[datetime]
    articles_per_hour: int

class SentimentDistribution(BaseModel):
    positive: int
    negative: int
    neutral: int

class TrendingCompany(BaseModel):
    company: str
    mentions: int
    sentiment: str
    direction: str

class AnalyticsStats(BaseModel):
    window_used: str
    total_articles: int
    total_forecasts: int
    market_sentiment_score: float
    sentiment_distribution: SentimentDistribution
    market_mood: str
    mood_change: float
    articles_today: int
    sentiment_change: float
    trending_companies: List[TrendingCompany]

class ActivityEvent(BaseModel):
    id: str
    timestamp: datetime
    type: str
    message: str

class TimeSeriesDataPoint(BaseModel):
    date: str
    sentiment_score: float
    positive_count: int
    negative_count: int
    neutral_count: int
    article_count: int

class TopicStats(BaseModel):
    topic: str
    mentions: int
    sentiment_score: float
