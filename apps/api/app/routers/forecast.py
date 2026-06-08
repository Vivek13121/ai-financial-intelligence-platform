"""
routers/forecast.py — API endpoints for retrieving sentiment forecasts.
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas.forecast_result import ForecastResultResponse


router = APIRouter(
    prefix="/forecasts",
    tags=["forecasts"],
)


@router.get("/", response_model=List[ForecastResultResponse])
def read_forecasts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Retrieve historical and current forecast records.
    Ordered by the time they were generated (newest generation first),
    then by forecast date.
    """
    return crud.forecast_result.get_forecasts(db, skip=skip, limit=limit)


@router.get("/latest", response_model=List[ForecastResultResponse])
def read_latest_forecasts(db: Session = Depends(get_db)):
    """
    Retrieve ONLY the forecasts generated during the most recent forecasting run.
    This gives the current "active" forecast curve (e.g. the next 7 days).
    """
    return crud.forecast_result.get_latest_forecasts_batch(db)

from app.schemas.forecast_result import ForecastRunStats

@router.get("/runs", response_model=List[ForecastRunStats])
def read_recent_forecast_runs(limit: int = 5, db: Session = Depends(get_db)):
    """
    Retrieve summary statistics for recent forecast runs.
    """
    return crud.forecast_result.get_recent_forecast_runs(db, limit=limit)
