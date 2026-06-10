from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.schemas.article import ArticleResponse
from app.schemas.analytics import TimeSeriesDataPoint, SentimentDistribution

class ForecastDataPoint(BaseModel):
    date: str
    predicted_sentiment: float

class IntelligenceOverview(BaseModel):
    total_articles: int
    current_sentiment: float
    forecast_direction: str

class CompanyIntelligence(BaseModel):
    company_name: str
    overview: IntelligenceOverview
    news_feed: List[ArticleResponse]
    sentiment_trend: List[TimeSeriesDataPoint]
    forecast: List[ForecastDataPoint]
    insights: str
    sentiment_distribution: SentimentDistribution
    related_topics: List[str]

class AISummaryResponse(BaseModel):
    executive_summary: str
    risks: List[str]
    opportunities: List[str]
    forecast_outlook: str
    generated_at: Optional[str] = None

class AISummaryStatusResponse(BaseModel):
    is_cached: bool
    generated_at: Optional[str] = None

