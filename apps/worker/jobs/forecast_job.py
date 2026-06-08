"""
worker/jobs/forecast_job.py — rq job function for sentiment forecasting using Prophet.

Responsibility:
  Aggregate historical sentiment from the database, train a Prophet model,
  predict the next N days of sentiment, and store the predictions.
"""

import logging
from datetime import date, timedelta
from uuid import uuid4

logger = logging.getLogger(__name__)

# Number of future days to forecast
FORECAST_DAYS = 7


def run_forecast_job() -> None:
    """
    rq job function — run Prophet forecasting and store the results.

    Called by rq when a job is placed on the forecast_generation queue.
    """
    # Deferred imports
    import pandas as pd
    from prophet import Prophet
    from app.database import SessionLocal
    from app import crud
    from app.models.sentiment_result import SentimentResult
    from app.schemas.forecast_result import ForecastResultCreate
    
    logger.info("Starting sentiment forecast generation job.")
    db = SessionLocal()
    
    try:
        # 1. Fetch historical sentiment data
        results = db.query(SentimentResult).all()
        if not results:
            logger.warning("No sentiment results found in DB. Cannot generate forecast.")
            return

        # 2. Convert to DataFrame and calculate sentiment index
        data = []
        for r in results:
            # Map labels to numeric multipliers
            multiplier = 0.0
            if r.sentiment_label == "positive":
                multiplier = 1.0
            elif r.sentiment_label == "negative":
                multiplier = -1.0
                
            # Compute a sentiment index: e.g. positive with 0.9 score = 0.9
            # negative with 0.8 score = -0.8
            sentiment_index = multiplier * r.score
            
            # Extract just the date part for daily aggregation
            dt_date = r.processed_at.date()
            data.append({"ds": dt_date, "y": sentiment_index})

        df = pd.DataFrame(data)
        
        # 3. Aggregate by day (average sentiment per day)
        # Prophet expects 'ds' and 'y' columns.
        df_daily = df.groupby("ds", as_index=False)["y"].mean()
        
        if len(df_daily) < 2:
            logger.warning("Not enough daily data points to run Prophet (need at least 2 days).")
            return

        # 4. Train Prophet model
        logger.info("Training Prophet model on %d daily data points...", len(df_daily))
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True, # Financial news often has weekly patterns
            yearly_seasonality=False
        )
        model.fit(df_daily)

        # 5. Predict future dates
        logger.info("Generating forecast for the next %d days...", FORECAST_DAYS)
        future = model.make_future_dataframe(periods=FORECAST_DAYS)
        forecast = model.predict(future)

        # 6. Filter only the future dates to store
        max_historical_date = df_daily["ds"].max()
        # Convert max_historical_date to a pandas Timestamp if it's a date to compare with forecast ds
        max_historical_ts = pd.to_datetime(max_historical_date)
        
        future_forecasts = forecast[forecast["ds"] > max_historical_ts]
        
        # 7. Store results in the database
        logger.info("Storing %d forecast records in the database.", len(future_forecasts))
        for _, row in future_forecasts.iterrows():
            forecast_date: date = row["ds"].date()
            predicted_y = float(row["yhat"])
            
            result_in = ForecastResultCreate(
                forecast_date=forecast_date,
                predicted_sentiment=predicted_y,
                model_name="prophet",
            )
            crud.forecast_result.create_forecast_result(db=db, result_in=result_in)
            
        logger.info("Forecast generation completed successfully.")

    except Exception as exc:
        logger.error("Forecast generation job failed: %s", exc)
        raise
    finally:
        db.close()
