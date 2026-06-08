"""
schemas/forecast_result.py — Pydantic schemas for ForecastResult.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ForecastResultBase(BaseModel):
    # Suppress Pydantic v2 warning: 'model_name' starts with 'model_' which
    # conflicts with Pydantic's protected namespace.
    model_config = {"protected_namespaces": ()}

    forecast_date: date = Field(..., description="The date this forecast applies to")
    predicted_sentiment: float = Field(
        ...,
        description="Predicted sentiment index (-1.0 to 1.0, though Prophet can sometimes slightly exceed this bound)",
    )
    model_name: str = Field(
        default="prophet",
        max_length=128,
        description="Forecasting model identifier that produced this result",
    )


class ForecastResultCreate(ForecastResultBase):
    """Schema for inserting a new forecast result."""
    pass


class ForecastResultResponse(ForecastResultBase):
    """Schema for returning a forecast result via API."""
    id: UUID
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ForecastRunStats(BaseModel):
    generated_at: datetime
    horizon_days: int
    average_sentiment: float
    trend: str
