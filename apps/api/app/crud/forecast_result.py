"""
crud/forecast_result.py — Database operations for ForecastResult.
"""

from typing import List

from sqlalchemy.orm import Session

from app.models.forecast_result import ForecastResult
from app.schemas.forecast_result import ForecastResultCreate


def create_forecast_result(
    db: Session,
    result_in: ForecastResultCreate,
) -> ForecastResult:
    """Insert a new ForecastResult row."""
    db_result = ForecastResult(**result_in.model_dump())
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result


def get_forecasts(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> List[ForecastResult]:
    """
    Return recent forecast records, ordered by generated_at desc, then forecast_date asc.
    """
    return (
        db.query(ForecastResult)
        .order_by(ForecastResult.generated_at.desc(), ForecastResult.forecast_date.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_latest_forecasts_batch(db: Session) -> List[ForecastResult]:
    """
    Return all forecast records from the single most recent generation run.
    This fetches the max(generated_at) and returns all rows with that timestamp.
    """
    # 1. Find the maximum generated_at timestamp
    latest_record = (
        db.query(ForecastResult.generated_at)
        .order_by(ForecastResult.generated_at.desc())
        .first()
    )
    
    if not latest_record:
        return []
        
    latest_time = latest_record[0]
    
    # 2. Fetch all records generated at that exact time
    return (
        db.query(ForecastResult)
        .filter(ForecastResult.generated_at == latest_time)
        .order_by(ForecastResult.forecast_date.asc())
        .all()
    )

def get_recent_forecast_runs(db: Session, limit: int = 5):
    """
    Returns summary statistics of the most recent forecast runs.
    Uses only the absolute latest forecast batch.
    """
    from datetime import timedelta
    
    latest_record = (
        db.query(ForecastResult.generated_at)
        .order_by(ForecastResult.generated_at.desc())
        .first()
    )
    
    if not latest_record:
        return []
        
    latest_time = latest_record[0]
    threshold = latest_time - timedelta(minutes=1)
    
    # Fetch records for the latest batch
    records = (
        db.query(ForecastResult)
        .filter(ForecastResult.generated_at >= threshold)
        .order_by(ForecastResult.forecast_date.asc())
        .all()
    )
    
    if not records:
        return []
        
    horizon_days = len(records)
    avg_sentiment = sum(r.predicted_sentiment for r in records) / horizon_days
    
    first_val = records[0].predicted_sentiment
    last_val = records[-1].predicted_sentiment
    trend = "Stable"
    if last_val > first_val + 5:
        trend = "Improving"
    elif last_val < first_val - 5:
        trend = "Declining"
        
    return [{
        "generated_at": latest_time,
        "horizon_days": horizon_days,
        "average_sentiment": avg_sentiment,
        "trend": trend
    }]
